"""Notion import service for importing content into Notion databases"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.models.content import ParsedContent, AIProcessedContent
from app.models.notion import NotionImport
from app.services.notion_service import get_notion_service
from app.services.config_service import ConfigurationService
from app import db

logger = logging.getLogger(__name__)


class NotionImportService:
    """Service for importing content into Notion"""

    def __init__(self):
        self.notion_service = get_notion_service()
        self.config_service = ConfigurationService()

    def import_to_notion(self, ai_content_id: int,
                        database_id: str,
                        properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Import AI processed content into Notion database

        Args:
            ai_content_id: AIProcessedContent ID to import
            database_id: Target Notion database ID
            properties: Additional properties for the Notion page

        Returns:
            Dict with import result
        """
        try:
            # Get AI processed content
            ai_content = db.session.query(AIProcessedContent).get(ai_content_id)
            if not ai_content:
                return {
                    'success': False,
                    'error': f'AI content {ai_content_id} not found'
                }

            # Get parsed content
            parsed_content = ai_content.parsed_content
            if not parsed_content:
                return {
                    'success': False,
                    'error': 'Parsed content not found'
                }

            # Get Notion configuration
            notion_config = self.config_service.get_notion_config(decrypt_token=True)
            if not notion_config:
                return {
                    'success': False,
                    'error': 'Notion not configured'
                }

            # Prepare page properties
            page_properties = self._prepare_properties(
                parsed_content,
                ai_content,
                properties or {}
            )

            # Prepare page content blocks
            blocks = self._prepare_blocks(parsed_content, ai_content)

            # Create page in Notion
            result = self._create_notion_page(
                api_token=notion_config.api_token,
                database_id=database_id,
                properties=page_properties,
                blocks=blocks
            )

            if not result['success']:
                return result

            # Save import record
            notion_import = self._save_notion_import(
                ai_content_id=ai_content_id,
                notion_page_id=result['page_id'],
                notion_url=result['url']
            )

            logger.info(f"Successfully imported AI content {ai_content_id} into Notion")

            return {
                'success': True,
                'notion_page_id': result['page_id'],
                'notion_url': result['url'],
                'notion_import_id': notion_import.id
            }

        except Exception as e:
            logger.error(f"Failed to import AI content {ai_content_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _prepare_properties(self, parsed_content: ParsedContent,
                           ai_content: AIProcessedContent,
                           custom_properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare Notion page properties

        Args:
            parsed_content: ParsedContent object
            ai_content: AIProcessedContent object
            custom_properties: Custom properties to include

        Returns:
            Dict of Notion properties
        """
        # Get link
        link = parsed_content.link

        properties = {
            'Name': {
                'title': [
                    {
                        'text': {
                            'content': link.title or link.url
                        }
                    }
                ]
            }
        }

        # Add URL if available
        if link:
            properties['URL'] = {
                'url': link.url
            }

        # Add quality score
        if parsed_content.quality_score:
            properties['Quality Score'] = {
                'number': parsed_content.quality_score
            }

        # Add keywords as multi-select
        if ai_content.keywords:
            properties['Keywords'] = {
                'multi_select': [
                    {'name': keyword} for keyword in ai_content.keywords[:10]
                ]
            }

        # Add custom properties
        properties.update(custom_properties)

        return properties

    def _prepare_blocks(self, parsed_content: ParsedContent,
                       ai_content: AIProcessedContent) -> List[Dict[str, Any]]:
        """
        Prepare Notion content blocks

        Args:
            parsed_content: ParsedContent object
            ai_content: AIProcessedContent object

        Returns:
            List of Notion blocks
        """
        blocks = []

        # Add AI summary if available
        if ai_content.summary:
            blocks.append({
                'object': 'block',
                'type': 'callout',
                'callout': {
                    'icon': {'emoji': '📝'},
                    'rich_text': [
                        {
                            'text': {
                                'content': ai_content.summary
                            }
                        }
                    ],
                    'color': 'blue_background'
                }
            })

            # Add divider
            blocks.append({
                'object': 'block',
                'type': 'divider',
                'divider': {}
            })

        # Convert markdown content to Notion blocks
        markdown_blocks = self._markdown_to_notion_blocks(
            parsed_content.formatted_content
        )
        blocks.extend(markdown_blocks)

        # Add insights if available
        if ai_content.insights:
            blocks.append({
                'object': 'block',
                'type': 'divider',
                'divider': {}
            })

            blocks.append({
                'object': 'block',
                'type': 'heading_2',
                'heading_2': {
                    'rich_text': [
                        {
                            'text': {
                                'content': 'Key Insights'
                            }
                        }
                    ]
                }
            })

            blocks.append({
                'object': 'block',
                'type': 'callout',
                'callout': {
                    'icon': {'emoji': '💡'},
                    'rich_text': [
                        {
                            'text': {
                                'content': ai_content.insights
                            }
                        }
                    ],
                    'color': 'yellow_background'
                }
            })

        return blocks[:100]  # Notion API limit

    def _markdown_to_notion_blocks(self, markdown: str) -> List[Dict[str, Any]]:
        """
        Convert markdown content to Notion blocks (simplified)

        Args:
            markdown: Markdown content

        Returns:
            List of Notion blocks
        """
        blocks = []
        lines = markdown.split('\n')

        for line in lines[:50]:  # Limit to first 50 lines
            line = line.strip()

            if not line:
                continue

            # Heading 1
            if line.startswith('# '):
                blocks.append({
                    'object': 'block',
                    'type': 'heading_1',
                    'heading_1': {
                        'rich_text': [
                            {
                                'text': {
                                    'content': line[2:]
                                }
                            }
                        ]
                    }
                })
            # Heading 2
            elif line.startswith('## '):
                blocks.append({
                    'object': 'block',
                    'type': 'heading_2',
                    'heading_2': {
                        'rich_text': [
                            {
                                'text': {
                                    'content': line[3:]
                                }
                            }
                        ]
                    }
                })
            # Heading 3
            elif line.startswith('### '):
                blocks.append({
                    'object': 'block',
                    'type': 'heading_3',
                    'heading_3': {
                        'rich_text': [
                            {
                                'text': {
                                    'content': line[4:]
                                }
                            }
                        ]
                    }
                })
            # Bullet list
            elif line.startswith('- ') or line.startswith('* '):
                blocks.append({
                    'object': 'block',
                    'type': 'bulleted_list_item',
                    'bulleted_list_item': {
                        'rich_text': [
                            {
                                'text': {
                                    'content': line[2:]
                                }
                            }
                        ]
                    }
                })
            # Regular paragraph
            else:
                # Truncate very long paragraphs
                content = line[:2000] if len(line) > 2000 else line
                blocks.append({
                    'object': 'block',
                    'type': 'paragraph',
                    'paragraph': {
                        'rich_text': [
                            {
                                'text': {
                                    'content': content
                                }
                            }
                        ]
                    }
                })

        return blocks

    def _create_notion_page(self, api_token: str, database_id: str,
                           properties: Dict[str, Any],
                           blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a page in Notion database

        Args:
            api_token: Notion API token
            database_id: Database ID
            properties: Page properties
            blocks: Page content blocks

        Returns:
            Dict with creation result
        """
        try:
            import requests

            url = 'https://api.notion.com/v1/pages'
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json',
                'Notion-Version': '2022-06-28'
            }

            payload = {
                'parent': {'database_id': database_id},
                'properties': properties,
                'children': blocks
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'page_id': data['id'],
                    'url': data['url']
                }
            else:
                error_data = response.json()
                error_message = error_data.get('message', 'Unknown error')
                logger.error(f"Notion API error: {error_message}")
                return {
                    'success': False,
                    'error': f'Notion API error: {error_message}'
                }

        except Exception as e:
            logger.error(f"Failed to create Notion page: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _save_notion_import(self, ai_content_id: int, notion_page_id: str,
                           notion_url: str) -> NotionImport:
        """
        Save Notion import record

        Args:
            ai_content_id: AIProcessedContent ID
            notion_page_id: Notion page ID
            notion_url: Notion page URL

        Returns:
            Created NotionImport object
        """
        notion_import = NotionImport(
            ai_content_id=ai_content_id,
            notion_page_id=notion_page_id,
            notion_url=notion_url,
            status='completed',
            imported_at=datetime.utcnow()
        )

        db.session.add(notion_import)
        db.session.commit()

        return notion_import

    def get_notion_import(self, import_id: int) -> Optional[NotionImport]:
        """
        Get Notion import by ID

        Args:
            import_id: NotionImport ID

        Returns:
            NotionImport object or None
        """
        return db.session.query(NotionImport).get(import_id)

    def get_imports_by_ai_content(self, ai_content_id: int) -> List[NotionImport]:
        """
        Get all Notion imports for an AI content

        Args:
            ai_content_id: AIProcessedContent ID

        Returns:
            List of NotionImport objects
        """
        return db.session.query(NotionImport).filter_by(
            ai_content_id=ai_content_id
        ).all()

    def batch_import(self, ai_content_ids: List[int],
                    database_id: str) -> Dict[str, Any]:
        """
        Import multiple AI contents into Notion in batch

        Args:
            ai_content_ids: List of AIProcessedContent IDs
            database_id: Target database ID

        Returns:
            Dict with batch results
        """
        results = {
            'success': True,
            'total': len(ai_content_ids),
            'completed': 0,
            'failed': 0,
            'results': []
        }

        for content_id in ai_content_ids:
            result = self.import_to_notion(content_id, database_id)
            if result['success']:
                results['completed'] += 1
            else:
                results['failed'] += 1
            results['results'].append({
                'ai_content_id': content_id,
                **result
            })

        return results

    def get_import_statistics(self) -> Dict[str, Any]:
        """
        Get Notion import statistics

        Returns:
            Dict with statistics
        """
        total = db.session.query(NotionImport).count()
        completed = db.session.query(NotionImport).filter_by(status='completed').count()
        failed = db.session.query(NotionImport).filter_by(status='failed').count()

        return {
            'total_imports': total,
            'completed': completed,
            'failed': failed
        }


def get_notion_import_service() -> NotionImportService:
    """Get singleton instance of NotionImportService"""
    return NotionImportService()
