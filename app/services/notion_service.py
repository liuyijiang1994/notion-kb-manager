"""
Notion service for Notion API integration
Handles workspace access, database listing, and content operations
"""
import logging
import requests
from typing import Dict, Any, List, Optional
from app.utils.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)


class NotionService:
    """Service for interacting with Notion API"""

    def __init__(self):
        self.base_url = 'https://api.notion.com/v1'
        self.notion_version = '2022-06-28'  # Notion API version
        self.timeout = 30

    def test_connection(self, api_token: str) -> Dict[str, Any]:
        """
        Test connection to Notion API and fetch workspace info

        Args:
            api_token: Notion integration token

        Returns:
            Dictionary with connection test results:
            {
                'success': bool,
                'workspace_info': dict,
                'databases': list,
                'error': str (if failed)
            }
        """
        try:
            headers = self._build_headers(api_token)

            # Test 1: Get bot user info
            bot_response = requests.get(
                f'{self.base_url}/users/me',
                headers=headers,
                timeout=self.timeout
            )

            if bot_response.status_code != 200:
                error_msg = self._parse_error_response(bot_response)
                logger.error(f"Notion API connection failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': bot_response.status_code
                }

            bot_info = bot_response.json()

            # Test 2: Search for databases (to verify access)
            search_response = requests.post(
                f'{self.base_url}/search',
                headers=headers,
                json={
                    'filter': {
                        'value': 'database',
                        'property': 'object'
                    },
                    'page_size': 10
                },
                timeout=self.timeout
            )

            databases = []
            if search_response.status_code == 200:
                search_data = search_response.json()
                databases = [
                    {
                        'id': db['id'],
                        'title': self._extract_title(db.get('title', [])),
                        'url': db.get('url', ''),
                        'created_time': db.get('created_time', ''),
                        'last_edited_time': db.get('last_edited_time', '')
                    }
                    for db in search_data.get('results', [])
                ]

            workspace_info = {
                'bot_id': bot_info.get('id'),
                'bot_name': bot_info.get('name'),
                'bot_type': bot_info.get('type'),
                'workspace_name': bot_info.get('bot', {}).get('workspace_name'),
                'owner': bot_info.get('bot', {}).get('owner', {})
            }

            logger.info(f"Successfully connected to Notion workspace: {workspace_info.get('workspace_name')}")

            return {
                'success': True,
                'workspace_info': workspace_info,
                'databases_count': len(databases),
                'databases': databases,
                'message': f'Connected successfully. Found {len(databases)} accessible databases.'
            }

        except requests.exceptions.Timeout:
            logger.error(f"Notion API connection timeout after {self.timeout}s")
            return {
                'success': False,
                'error': f'Connection timeout after {self.timeout} seconds'
            }

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Notion API connection error: {e}")
            return {
                'success': False,
                'error': 'Connection error: Unable to reach Notion API'
            }

        except Exception as e:
            logger.error(f"Unexpected error testing Notion connection: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    def list_databases(self, api_token: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """
        List all accessible databases in the workspace

        Args:
            api_token: Notion integration token
            page_size: Number of results per page (max 100)

        Returns:
            List of database objects

        Raises:
            ExternalAPIError: If API request fails
        """
        try:
            headers = self._build_headers(api_token)

            response = requests.post(
                f'{self.base_url}/search',
                headers=headers,
                json={
                    'filter': {
                        'value': 'database',
                        'property': 'object'
                    },
                    'page_size': min(page_size, 100)
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        'id': db['id'],
                        'title': self._extract_title(db.get('title', [])),
                        'url': db.get('url', ''),
                        'properties': db.get('properties', {}),
                        'created_time': db.get('created_time', ''),
                        'last_edited_time': db.get('last_edited_time', '')
                    }
                    for db in data.get('results', [])
                ]
            else:
                error_msg = self._parse_error_response(response)
                raise ExternalAPIError('Notion API', error_msg)

        except requests.exceptions.Timeout:
            raise ExternalAPIError('Notion API', f'Request timeout after {self.timeout} seconds')

        except requests.exceptions.ConnectionError as e:
            raise ExternalAPIError('Notion API', f'Connection error: {str(e)}')

    def get_database(self, api_token: str, database_id: str) -> Dict[str, Any]:
        """
        Get database details by ID

        Args:
            api_token: Notion integration token
            database_id: Database ID

        Returns:
            Database object

        Raises:
            ExternalAPIError: If API request fails
        """
        try:
            headers = self._build_headers(api_token)

            response = requests.get(
                f'{self.base_url}/databases/{database_id}',
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = self._parse_error_response(response)
                raise ExternalAPIError('Notion API', error_msg)

        except requests.exceptions.Timeout:
            raise ExternalAPIError('Notion API', f'Request timeout after {self.timeout} seconds')

        except requests.exceptions.ConnectionError as e:
            raise ExternalAPIError('Notion API', f'Connection error: {str(e)}')

    def _build_headers(self, api_token: str) -> Dict[str, str]:
        """Build request headers for Notion API"""
        return {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'Notion-Version': self.notion_version
        }

    def _extract_title(self, title_array: List[Dict]) -> str:
        """Extract plain text title from Notion title array"""
        if not title_array:
            return 'Untitled'

        try:
            return ''.join([
                item.get('plain_text', '')
                for item in title_array
            ]) or 'Untitled'
        except Exception:
            return 'Untitled'

    def _parse_error_response(self, response: requests.Response) -> str:
        """Parse error message from Notion API response"""
        try:
            error_data = response.json()
            return error_data.get('message', f'API error: {response.status_code}')
        except Exception:
            return f'HTTP {response.status_code}: {response.text[:200]}'


# Global instance
_notion_service: Optional[NotionService] = None


def get_notion_service() -> NotionService:
    """Get or create global NotionService instance"""
    global _notion_service
    if _notion_service is None:
        _notion_service = NotionService()
    return _notion_service
