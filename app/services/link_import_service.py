"""Link import service for handling various import sources"""
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from app.models.link import Link, ImportTask
from app import db
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class LinkImportService:
    """Service for importing links from various sources"""

    def __init__(self):
        self.supported_sources = ['favorites', 'manual', 'history']
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )

    def import_from_favorites(self, file_content: str, file_type: str = 'html',
                             task_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Import links from browser favorites/bookmarks file

        Args:
            file_content: Content of the bookmarks file
            file_type: File type (html, json)
            task_id: Associated import task ID

        Returns:
            Dict with import statistics and links
        """
        try:
            if file_type == 'html':
                links = self._parse_html_bookmarks(file_content)
            elif file_type == 'json':
                links = self._parse_json_bookmarks(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Import links to database
            result = self._save_links(links, source='favorites', task_id=task_id)

            logger.info(f"Favorites import completed: {result['imported']} imported, "
                       f"{result['duplicates']} duplicates, {result['failed']} failed")

            return {
                'success': True,
                'total': len(links),
                'imported': result['imported'],
                'duplicates': result['duplicates'],
                'failed': result['failed'],
                'links': result['links']
            }

        except Exception as e:
            logger.error(f"Favorites import failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'total': 0,
                'imported': 0,
                'duplicates': 0,
                'failed': 0
            }

    def import_manual(self, text: str, task_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Import links from manual text input

        Args:
            text: Text containing URLs (one per line or comma/space separated)
            task_id: Associated import task ID

        Returns:
            Dict with import statistics and links
        """
        try:
            # Extract URLs from text
            urls = self._extract_urls_from_text(text)

            if not urls:
                return {
                    'success': False,
                    'error': 'No valid URLs found in input',
                    'total': 0,
                    'imported': 0
                }

            # Create link objects
            links = []
            for url in urls:
                links.append({
                    'url': url,
                    'title': self._extract_title_from_url(url),
                    'source': 'manual'
                })

            # Save to database
            result = self._save_links(links, source='manual', task_id=task_id)

            logger.info(f"Manual import completed: {result['imported']} imported, "
                       f"{result['duplicates']} duplicates")

            return {
                'success': True,
                'total': len(links),
                'imported': result['imported'],
                'duplicates': result['duplicates'],
                'failed': result['failed'],
                'links': result['links']
            }

        except Exception as e:
            logger.error(f"Manual import failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'total': 0,
                'imported': 0
            }

    def _parse_html_bookmarks(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse HTML bookmarks file (Netscape Bookmark format)

        Supports Chrome, Firefox, Safari, Edge bookmark exports
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []

        # Find all <A> tags with HREF attribute
        for anchor in soup.find_all('a'):
            url = anchor.get('href')
            if not url:
                continue

            # Validate URL
            if not self._is_valid_url(url):
                continue

            title = anchor.get_text(strip=True) or self._extract_title_from_url(url)
            add_date = anchor.get('add_date')

            # Try to parse timestamp
            imported_at = None
            if add_date:
                try:
                    imported_at = datetime.fromtimestamp(int(add_date))
                except (ValueError, TypeError):
                    pass

            links.append({
                'url': url,
                'title': title,
                'imported_at': imported_at or datetime.utcnow()
            })

        logger.info(f"Parsed {len(links)} links from HTML bookmarks")
        return links

    def _parse_json_bookmarks(self, json_content: str) -> List[Dict[str, Any]]:
        """
        Parse JSON bookmarks file (Chrome bookmark format)
        """
        try:
            data = json.loads(json_content)
            links = []

            def extract_bookmarks(node):
                """Recursively extract bookmarks from JSON structure"""
                if isinstance(node, dict):
                    # Check if it's a bookmark
                    if node.get('type') == 'url' and node.get('url'):
                        url = node['url']
                        if self._is_valid_url(url):
                            links.append({
                                'url': url,
                                'title': node.get('name', self._extract_title_from_url(url)),
                                'imported_at': datetime.utcnow()
                            })

                    # Check for children
                    if 'children' in node:
                        for child in node['children']:
                            extract_bookmarks(child)

                    # Also check all values
                    for value in node.values():
                        if isinstance(value, (dict, list)):
                            extract_bookmarks(value)

                elif isinstance(node, list):
                    for item in node:
                        extract_bookmarks(item)

            # Start extraction from root
            extract_bookmarks(data)

            logger.info(f"Parsed {len(links)} links from JSON bookmarks")
            return links

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            raise ValueError(f"Invalid JSON bookmarks file: {e}")

    def _extract_urls_from_text(self, text: str) -> List[str]:
        """
        Extract URLs from free-form text

        Handles:
        - One URL per line
        - Multiple URLs separated by commas, spaces, or newlines
        - Mixed text with URLs
        """
        urls = []

        # First, try to find URLs using regex
        matches = self.url_pattern.findall(text)
        for match in matches:
            if self._is_valid_url(match):
                urls.append(match)

        # Also split by common delimiters and validate
        parts = re.split(r'[\s,;]+', text)
        for part in parts:
            part = part.strip()
            if part and self._is_valid_url(part) and part not in urls:
                urls.append(part)

        return list(set(urls))  # Remove duplicates

    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format
        """
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except Exception:
            return False

    def _extract_title_from_url(self, url: str) -> str:
        """
        Extract a basic title from URL (domain name)
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc or 'Untitled'
        except Exception:
            return 'Untitled'

    def _save_links(self, links: List[Dict[str, Any]], source: str,
                    task_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Save links to database with duplicate detection

        Returns:
            Dict with counts and saved link objects
        """
        imported = 0
        duplicates = 0
        failed = 0
        saved_links = []

        for link_data in links:
            try:
                # Check for existing URL
                existing = db.session.query(Link).filter_by(url=link_data['url']).first()

                if existing:
                    duplicates += 1
                    logger.debug(f"Duplicate URL skipped: {link_data['url']}")
                    continue

                # Create new link
                link = Link(
                    title=link_data.get('title'),
                    url=link_data['url'],
                    source=source,
                    task_id=task_id,
                    priority=link_data.get('priority', 'medium'),
                    tags=link_data.get('tags'),
                    notes=link_data.get('notes'),
                    imported_at=link_data.get('imported_at', datetime.utcnow())
                )

                db.session.add(link)
                imported += 1
                saved_links.append(link)

            except IntegrityError as e:
                db.session.rollback()
                duplicates += 1
                logger.warning(f"Integrity error for URL {link_data.get('url')}: {e}")
            except Exception as e:
                db.session.rollback()
                failed += 1
                logger.error(f"Failed to save link {link_data.get('url')}: {e}")

        # Commit all successful inserts
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit links: {e}")
            raise

        return {
            'imported': imported,
            'duplicates': duplicates,
            'failed': failed,
            'links': saved_links
        }

    def check_duplicate(self, url: str) -> Tuple[bool, Optional[Link]]:
        """
        Check if URL already exists in database

        Returns:
            Tuple of (is_duplicate, existing_link)
        """
        existing = db.session.query(Link).filter_by(url=url).first()
        return (existing is not None, existing)

    def get_import_statistics(self) -> Dict[str, Any]:
        """
        Get overall import statistics

        Returns:
            Dict with counts by source and status
        """
        total_links = db.session.query(Link).count()
        by_source = db.session.query(
            Link.source,
            db.func.count(Link.id)
        ).group_by(Link.source).all()

        valid_links = db.session.query(Link).filter_by(is_valid=True).count()
        invalid_links = db.session.query(Link).filter_by(is_valid=False).count()
        pending_validation = db.session.query(Link).filter(Link.is_valid.is_(None)).count()

        return {
            'total_links': total_links,
            'by_source': {source: count for source, count in by_source},
            'valid': valid_links,
            'invalid': invalid_links,
            'pending_validation': pending_validation
        }


def get_link_import_service() -> LinkImportService:
    """Get singleton instance of LinkImportService"""
    return LinkImportService()
