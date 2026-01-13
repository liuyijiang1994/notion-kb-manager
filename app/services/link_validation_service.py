"""Link validation service for checking URL accessibility"""
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from app.models.link import Link
from app import db

logger = logging.getLogger(__name__)


class LinkValidationService:
    """Service for validating link accessibility"""

    def __init__(self):
        self.timeout = 10  # seconds
        self.max_workers = 5  # concurrent requests
        self.user_agent = 'Mozilla/5.0 (compatible; NotionKBManager/1.0)'

    def validate_single(self, url: str, link_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate a single URL

        Args:
            url: URL to validate
            link_id: Optional link ID to update in database

        Returns:
            Dict with validation result
        """
        result = {
            'url': url,
            'is_valid': False,
            'status_code': None,
            'status': 'unknown',
            'message': '',
            'redirect_url': None,
            'response_time': None
        }

        try:
            start_time = datetime.utcnow()

            response = requests.head(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                headers={'User-Agent': self.user_agent}
            )

            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()

            result['status_code'] = response.status_code
            result['response_time'] = response_time

            # Check if redirected
            if response.url != url:
                result['redirect_url'] = response.url

            # Determine validity based on status code
            if 200 <= response.status_code < 300:
                result['is_valid'] = True
                result['status'] = 'valid'
                result['message'] = 'URL is accessible'
            elif 300 <= response.status_code < 400:
                result['is_valid'] = True
                result['status'] = 'redirect'
                result['message'] = f'Redirects to {result["redirect_url"]}'
            elif response.status_code == 404:
                result['status'] = 'not_found'
                result['message'] = 'Page not found (404)'
            elif response.status_code == 403:
                result['status'] = 'forbidden'
                result['message'] = 'Access forbidden (403)'
            elif response.status_code >= 500:
                result['status'] = 'server_error'
                result['message'] = f'Server error ({response.status_code})'
            else:
                result['status'] = 'error'
                result['message'] = f'HTTP status {response.status_code}'

        except requests.Timeout:
            result['status'] = 'timeout'
            result['message'] = f'Request timeout after {self.timeout}s'
        except requests.ConnectionError:
            result['status'] = 'connection_error'
            result['message'] = 'Connection failed'
        except requests.TooManyRedirects:
            result['status'] = 'too_many_redirects'
            result['message'] = 'Too many redirects'
        except Exception as e:
            result['status'] = 'error'
            result['message'] = f'Validation error: {str(e)}'
            logger.error(f"Validation error for {url}: {e}", exc_info=True)

        # Update database if link_id provided
        if link_id:
            self._update_link_validation(link_id, result)

        return result

    def validate_batch(self, link_ids: List[int], update_db: bool = True) -> Dict[str, Any]:
        """
        Validate multiple links concurrently

        Args:
            link_ids: List of link IDs to validate
            update_db: Whether to update database with results

        Returns:
            Dict with validation results and statistics
        """
        links = db.session.query(Link).filter(Link.id.in_(link_ids)).all()

        if not links:
            return {
                'success': False,
                'error': 'No links found',
                'results': []
            }

        results = []
        valid_count = 0
        invalid_count = 0
        error_count = 0

        # Use ThreadPoolExecutor for concurrent validation
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all validation tasks
            future_to_link = {
                executor.submit(self.validate_single, link.url, link.id if update_db else None): link
                for link in links
            }

            # Collect results as they complete
            for future in as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    result = future.result()
                    results.append({
                        'link_id': link.id,
                        'url': link.url,
                        **result
                    })

                    if result['is_valid']:
                        valid_count += 1
                    elif result['status'] in ['not_found', 'forbidden', 'server_error']:
                        invalid_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    logger.error(f"Validation failed for link {link.id}: {e}")
                    error_count += 1
                    results.append({
                        'link_id': link.id,
                        'url': link.url,
                        'is_valid': False,
                        'status': 'error',
                        'message': str(e)
                    })

        logger.info(f"Batch validation completed: {valid_count} valid, "
                   f"{invalid_count} invalid, {error_count} errors")

        return {
            'success': True,
            'total': len(links),
            'valid': valid_count,
            'invalid': invalid_count,
            'errors': error_count,
            'results': results
        }

    def validate_all_pending(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate all links that haven't been validated yet

        Args:
            limit: Optional limit on number of links to validate

        Returns:
            Dict with validation results
        """
        query = db.session.query(Link).filter(Link.is_valid.is_(None))

        if limit:
            query = query.limit(limit)

        pending_links = query.all()
        link_ids = [link.id for link in pending_links]

        if not link_ids:
            return {
                'success': True,
                'message': 'No pending validations',
                'total': 0,
                'valid': 0,
                'invalid': 0,
                'errors': 0
            }

        return self.validate_batch(link_ids, update_db=True)

    def _update_link_validation(self, link_id: int, result: Dict[str, Any]) -> None:
        """
        Update link validation status in database
        """
        try:
            link = db.session.query(Link).get(link_id)
            if link:
                link.is_valid = result['is_valid']
                link.validation_status = result['status']
                link.validation_time = datetime.utcnow()
                db.session.commit()
                logger.debug(f"Updated validation for link {link_id}: {result['status']}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update link {link_id} validation: {e}")

    def revalidate_failed(self, days_old: int = 7) -> Dict[str, Any]:
        """
        Re-validate links that failed validation

        Args:
            days_old: Only revalidate links validated more than this many days ago

        Returns:
            Dict with revalidation results
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        failed_links = db.session.query(Link).filter(
            Link.is_valid == False,
            Link.validation_time < cutoff_date
        ).all()

        if not failed_links:
            return {
                'success': True,
                'message': 'No failed links to revalidate',
                'total': 0
            }

        link_ids = [link.id for link in failed_links]
        return self.validate_batch(link_ids, update_db=True)

    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics

        Returns:
            Dict with counts by validation status
        """
        total = db.session.query(Link).count()
        valid = db.session.query(Link).filter_by(is_valid=True).count()
        invalid = db.session.query(Link).filter_by(is_valid=False).count()
        pending = db.session.query(Link).filter(Link.is_valid.is_(None)).count()

        # Get counts by validation status
        by_status = db.session.query(
            Link.validation_status,
            db.func.count(Link.id)
        ).filter(
            Link.validation_status.isnot(None)
        ).group_by(Link.validation_status).all()

        return {
            'total': total,
            'valid': valid,
            'invalid': invalid,
            'pending': pending,
            'by_status': {status: count for status, count in by_status}
        }


def get_link_validation_service() -> LinkValidationService:
    """Get singleton instance of LinkValidationService"""
    return LinkValidationService()
