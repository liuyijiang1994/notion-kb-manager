"""Content parsing service for extracting and processing web content"""
import re
import logging
import requests
import html2text
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from readability import Document
from app.models.link import Link
from app.models.content import ParsedContent
from app import db

logger = logging.getLogger(__name__)


class ContentParsingService:
    """Service for fetching and parsing web content"""

    def __init__(self):
        self.timeout = 30
        self.user_agent = 'Mozilla/5.0 (compatible; NotionKBManager/1.0)'
        self.max_content_size = 10 * 1024 * 1024  # 10MB

        # Initialize HTML to Markdown converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.ignore_tables = False
        self.html_converter.body_width = 0  # No wrapping

    def fetch_and_parse(self, link_id: int) -> Dict[str, Any]:
        """
        Fetch URL content and parse it

        Args:
            link_id: Link ID to fetch and parse

        Returns:
            Dict with parsing result
        """
        try:
            # Get link from database
            link = db.session.query(Link).get(link_id)
            if not link:
                return {
                    'success': False,
                    'error': f'Link {link_id} not found'
                }

            # Fetch content
            html_content = self._fetch_url(link.url)
            if not html_content:
                return {
                    'success': False,
                    'error': 'Failed to fetch URL content'
                }

            # Parse content
            parsed_data = self._parse_html(html_content, link.url)

            # Save to database
            parsed_content = self._save_parsed_content(link_id, parsed_data)

            logger.info(f"Successfully parsed content for link {link_id}")

            return {
                'success': True,
                'parsed_content_id': parsed_content.id,
                'quality_score': parsed_content.quality_score,
                'word_count': len(parsed_data['formatted_content'].split()),
                'images_count': len(parsed_data['images']),
                'tables_count': len(parsed_data['tables'])
            }

        except Exception as e:
            logger.error(f"Failed to parse link {link_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from URL

        Args:
            url: URL to fetch

        Returns:
            HTML content as string, or None if failed
        """
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={'User-Agent': self.user_agent},
                allow_redirects=True,
                stream=True
            )

            response.raise_for_status()

            # Check content size
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_content_size:
                logger.warning(f"Content too large: {content_length} bytes")
                return None

            # Read content with size limit
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > self.max_content_size:
                    logger.warning(f"Content exceeded max size during download")
                    break

            # Detect encoding
            encoding = response.encoding or 'utf-8'
            html_content = content.decode(encoding, errors='ignore')

            return html_content

        except requests.Timeout:
            logger.error(f"Timeout fetching {url}")
            return None
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None

    def _parse_html(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """
        Parse HTML content and extract structured data

        Args:
            html_content: Raw HTML content
            base_url: Base URL for resolving relative URLs

        Returns:
            Dict with parsed data
        """
        # Extract main content using readability
        doc = Document(html_content)
        main_html = doc.summary()
        title = doc.title()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(main_html, 'lxml')

        # Extract images
        images = self._extract_images(soup, base_url)

        # Extract tables
        tables = self._extract_tables(soup)

        # Convert to Markdown
        markdown_content = self.html_converter.handle(main_html)

        # Calculate quality score
        quality_score = self._calculate_quality_score(
            soup, markdown_content, len(images), len(tables)
        )

        # Extract paper information if present
        paper_info = self._extract_paper_info(soup, markdown_content)

        return {
            'title': title,
            'raw_content': html_content[:100000],  # Limit raw content size
            'formatted_content': markdown_content,
            'quality_score': quality_score,
            'images': images,
            'tables': tables,
            'paper_info': paper_info,
            'parsing_method': 'readability+html2text'
        }

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract images from HTML

        Returns:
            List of image dicts with url, alt, title
        """
        images = []

        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue

            # Resolve relative URLs
            absolute_url = urljoin(base_url, src)

            # Skip tiny images (likely icons/tracking pixels)
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    if int(width) < 50 or int(height) < 50:
                        continue
                except (ValueError, TypeError):
                    pass

            images.append({
                'url': absolute_url,
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })

        return images

    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract tables from HTML

        Returns:
            List of table dicts with headers and rows
        """
        tables = []

        for table in soup.find_all('table'):
            headers = []
            rows = []

            # Extract headers
            header_row = table.find('thead')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            else:
                # Try first row as headers
                first_row = table.find('tr')
                if first_row:
                    headers = [th.get_text(strip=True) for th in first_row.find_all('th')]

            # Extract rows
            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)

            if rows:
                tables.append({
                    'headers': headers,
                    'rows': rows,
                    'row_count': len(rows),
                    'column_count': len(rows[0]) if rows else 0
                })

        return tables

    def _calculate_quality_score(self, soup: BeautifulSoup, markdown: str,
                                 image_count: int, table_count: int) -> int:
        """
        Calculate content quality score (0-100)

        Factors:
        - Text length
        - Paragraph count
        - Heading structure
        - Image presence
        - Table presence
        - Code blocks
        - List presence
        """
        score = 0

        # Text length (0-30 points)
        word_count = len(markdown.split())
        if word_count > 2000:
            score += 30
        elif word_count > 1000:
            score += 25
        elif word_count > 500:
            score += 20
        elif word_count > 200:
            score += 15
        elif word_count > 50:
            score += 10

        # Paragraph count (0-15 points)
        paragraphs = soup.find_all('p')
        if len(paragraphs) > 10:
            score += 15
        elif len(paragraphs) > 5:
            score += 10
        elif len(paragraphs) > 2:
            score += 5

        # Heading structure (0-15 points)
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if len(headings) > 5:
            score += 15
        elif len(headings) > 3:
            score += 10
        elif len(headings) > 0:
            score += 5

        # Images (0-10 points)
        if image_count > 5:
            score += 10
        elif image_count > 2:
            score += 7
        elif image_count > 0:
            score += 5

        # Tables (0-10 points)
        if table_count > 3:
            score += 10
        elif table_count > 1:
            score += 7
        elif table_count > 0:
            score += 5

        # Code blocks (0-10 points)
        code_blocks = soup.find_all(['pre', 'code'])
        if len(code_blocks) > 5:
            score += 10
        elif len(code_blocks) > 2:
            score += 7
        elif len(code_blocks) > 0:
            score += 5

        # Lists (0-10 points)
        lists = soup.find_all(['ul', 'ol'])
        if len(lists) > 5:
            score += 10
        elif len(lists) > 2:
            score += 7
        elif len(lists) > 0:
            score += 5

        return min(score, 100)

    def _extract_paper_info(self, soup: BeautifulSoup, markdown: str) -> Optional[Dict[str, Any]]:
        """
        Extract academic paper information if present

        Returns:
            Dict with title, authors, year, abstract, or None
        """
        paper_info = {}

        # Try to find paper title (usually in h1 or title)
        title_tag = soup.find('h1')
        if title_tag:
            paper_info['title'] = title_tag.get_text(strip=True)

        # Try to find authors
        # Common patterns: class="author", class="authors", meta name="author"
        author_tags = soup.find_all(class_=re.compile(r'author', re.I))
        if author_tags:
            authors = [tag.get_text(strip=True) for tag in author_tags]
            paper_info['authors'] = authors

        # Try to find year in text
        year_match = re.search(r'\b(19|20)\d{2}\b', markdown[:1000])
        if year_match:
            paper_info['year'] = year_match.group()

        # Try to find abstract
        abstract_tag = soup.find(class_=re.compile(r'abstract', re.I))
        if abstract_tag:
            paper_info['abstract'] = abstract_tag.get_text(strip=True)[:500]

        return paper_info if paper_info else None

    def _save_parsed_content(self, link_id: int, parsed_data: Dict[str, Any]) -> ParsedContent:
        """
        Save parsed content to database

        Args:
            link_id: Link ID
            parsed_data: Parsed content data

        Returns:
            Created ParsedContent object
        """
        # Check if already exists
        existing = db.session.query(ParsedContent).filter_by(link_id=link_id).first()
        if existing:
            # Update existing
            existing.raw_content = parsed_data['raw_content']
            existing.formatted_content = parsed_data['formatted_content']
            existing.quality_score = parsed_data['quality_score']
            existing.parsing_method = parsed_data['parsing_method']
            existing.images = parsed_data['images']
            existing.tables = parsed_data['tables']
            existing.paper_info = parsed_data['paper_info']
            existing.status = 'completed'
            existing.parsed_at = datetime.utcnow()
            db.session.commit()
            return existing

        # Create new
        parsed_content = ParsedContent(
            link_id=link_id,
            raw_content=parsed_data['raw_content'],
            formatted_content=parsed_data['formatted_content'],
            quality_score=parsed_data['quality_score'],
            parsing_method=parsed_data['parsing_method'],
            images=parsed_data['images'],
            tables=parsed_data['tables'],
            paper_info=parsed_data['paper_info'],
            status='completed',
            parsed_at=datetime.utcnow()
        )

        db.session.add(parsed_content)
        db.session.commit()

        return parsed_content

    def parse_batch(self, link_ids: List[int]) -> Dict[str, Any]:
        """
        Parse multiple links in batch

        Args:
            link_ids: List of link IDs to parse

        Returns:
            Dict with batch results
        """
        results = {
            'success': True,
            'total': len(link_ids),
            'completed': 0,
            'failed': 0,
            'results': []
        }

        for link_id in link_ids:
            result = self.fetch_and_parse(link_id)
            if result['success']:
                results['completed'] += 1
            else:
                results['failed'] += 1
            results['results'].append({
                'link_id': link_id,
                **result
            })

        return results

    def get_parsed_content(self, content_id: int) -> Optional[ParsedContent]:
        """
        Get parsed content by ID

        Args:
            content_id: ParsedContent ID

        Returns:
            ParsedContent object or None
        """
        return db.session.query(ParsedContent).get(content_id)

    def get_parsed_content_by_link(self, link_id: int) -> Optional[ParsedContent]:
        """
        Get parsed content by link ID

        Args:
            link_id: Link ID

        Returns:
            ParsedContent object or None
        """
        return db.session.query(ParsedContent).filter_by(link_id=link_id).first()

    def get_parsing_statistics(self) -> Dict[str, Any]:
        """
        Get parsing statistics

        Returns:
            Dict with statistics
        """
        total = db.session.query(ParsedContent).count()
        completed = db.session.query(ParsedContent).filter_by(status='completed').count()
        failed = db.session.query(ParsedContent).filter_by(status='failed').count()

        # Average quality score
        avg_quality = db.session.query(
            db.func.avg(ParsedContent.quality_score)
        ).scalar() or 0

        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'average_quality': round(avg_quality, 2)
        }


def get_content_parsing_service() -> ContentParsingService:
    """Get singleton instance of ContentParsingService"""
    return ContentParsingService()
