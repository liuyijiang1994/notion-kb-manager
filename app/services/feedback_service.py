"""
Feedback management service
"""
import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from sqlalchemy import desc
from app import db
from app.models.system import Feedback

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for managing user feedback"""

    def __init__(self):
        self.screenshot_dir = Path(os.getenv('SCREENSHOT_DIR', 'uploads/screenshots'))
        self.screenshot_dir.mkdir(exist_ok=True, parents=True)

    def submit_feedback(self, feedback_type: str, content: str,
                       user_email: Optional[str] = None,
                       screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit user feedback

        Args:
            feedback_type: Type of feedback (bug/feature/other)
            content: Feedback content
            user_email: Optional user email
            screenshot_path: Optional screenshot path

        Returns:
            Dict with feedback info
        """
        try:
            feedback = Feedback(
                type=feedback_type,
                content=content,
                user_email=user_email,
                screenshot_path=screenshot_path,
                status='new'
            )
            db.session.add(feedback)
            db.session.commit()

            logger.info(f"Feedback submitted: {feedback.id} (type: {feedback_type})")

            return {
                'success': True,
                'feedback_id': feedback.id,
                'status': feedback.status,
                'created_at': feedback.created_at.isoformat()
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to submit feedback: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_feedback_list(self, feedback_type: Optional[str] = None,
                         status: Optional[str] = None,
                         page: int = 1,
                         per_page: int = 20) -> Dict[str, Any]:
        """
        Get feedback list with filtering

        Args:
            feedback_type: Filter by type
            status: Filter by status
            page: Page number
            per_page: Items per page

        Returns:
            Dict with feedback items and pagination
        """
        try:
            # Build query
            query = db.session.query(Feedback)

            # Apply filters
            if feedback_type:
                query = query.filter(Feedback.type == feedback_type)

            if status:
                query = query.filter(Feedback.status == status)

            # Get total count
            total = query.count()

            # Apply sorting and pagination
            query = query.order_by(desc(Feedback.created_at))
            offset = (page - 1) * per_page
            items = query.limit(per_page).offset(offset).all()

            # Format results
            feedback_items = [
                {
                    'id': item.id,
                    'type': item.type,
                    'content': item.content,
                    'user_email': item.user_email,
                    'status': item.status,
                    'has_screenshot': item.screenshot_path is not None,
                    'created_at': item.created_at.isoformat()
                }
                for item in items
            ]

            pages = (total + per_page - 1) // per_page

            return {
                'success': True,
                'items': feedback_items,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': pages
                }
            }

        except Exception as e:
            logger.error(f"Failed to get feedback list: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_feedback_details(self, feedback_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed feedback information

        Args:
            feedback_id: Feedback ID

        Returns:
            Dict with feedback details or None
        """
        try:
            feedback = db.session.query(Feedback).get(feedback_id)
            if not feedback:
                return None

            return {
                'id': feedback.id,
                'type': feedback.type,
                'content': feedback.content,
                'user_email': feedback.user_email,
                'screenshot_path': feedback.screenshot_path,
                'status': feedback.status,
                'created_at': feedback.created_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get feedback details: {e}", exc_info=True)
            return None

    def update_feedback_status(self, feedback_id: int, status: str) -> bool:
        """
        Update feedback status

        Args:
            feedback_id: Feedback ID
            status: New status

        Returns:
            True if updated, False if not found
        """
        try:
            feedback = db.session.query(Feedback).get(feedback_id)
            if not feedback:
                return False

            feedback.status = status
            db.session.commit()

            logger.info(f"Updated feedback {feedback_id} status to {status}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update feedback status: {e}", exc_info=True)
            return False

    def delete_feedback(self, feedback_id: int) -> bool:
        """
        Delete feedback

        Args:
            feedback_id: Feedback ID

        Returns:
            True if deleted, False if not found
        """
        try:
            feedback = db.session.query(Feedback).get(feedback_id)
            if not feedback:
                return False

            # Delete screenshot if exists
            if feedback.screenshot_path:
                screenshot_path = Path(feedback.screenshot_path)
                if screenshot_path.exists():
                    screenshot_path.unlink()

            db.session.delete(feedback)
            db.session.commit()

            logger.info(f"Deleted feedback: {feedback_id}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete feedback: {e}", exc_info=True)
            return False

    def get_feedback_statistics(self) -> Dict[str, Any]:
        """
        Get feedback statistics

        Returns:
            Dict with statistics
        """
        try:
            from sqlalchemy import func

            # Total feedback
            total = db.session.query(Feedback).count()

            # By type
            by_type = db.session.query(
                Feedback.type,
                func.count(Feedback.id)
            ).group_by(Feedback.type).all()

            # By status
            by_status = db.session.query(
                Feedback.status,
                func.count(Feedback.id)
            ).group_by(Feedback.status).all()

            return {
                'total_feedback': total,
                'by_type': {type_: count for type_, count in by_type},
                'by_status': {status: count for status, count in by_status}
            }

        except Exception as e:
            logger.error(f"Failed to get feedback statistics: {e}", exc_info=True)
            return {}


class HelpService:
    """Service for help documentation"""

    def __init__(self):
        self.help_content = {
            'getting_started': {
                'title': 'Getting Started',
                'content': '''
# Getting Started with Notion KB Manager

## Quick Start
1. Configure your Notion integration token
2. Add browser bookmarks or links
3. Parse and process content
4. Import to Notion

## Key Features
- Automatic content parsing
- AI-powered summarization
- Batch processing
- Notion integration
                ''',
                'category': 'basics'
            },
            'configuration': {
                'title': 'Configuration Guide',
                'content': '''
# Configuration Guide

## Notion Setup
1. Create Notion integration at https://www.notion.so/my-integrations
2. Copy integration token
3. Configure in Settings > Notion
4. Share your database with the integration

## AI Models
Configure OpenAI or other AI providers in Settings > AI Models

## Processing Options
Customize parsing and AI processing settings in Settings
                ''',
                'category': 'configuration'
            },
            'content_management': {
                'title': 'Content Management',
                'content': '''
# Content Management

## Adding Content
- Import browser bookmarks
- Add individual links
- Bulk import from CSV

## Processing Pipeline
1. Parse: Extract content from web pages
2. AI Process: Generate summaries and keywords
3. Import: Send to Notion database

## Managing Content
- View all parsed content
- Edit summaries and keywords
- Reprocess content
- Delete unwanted items
                ''',
                'category': 'usage'
            },
            'api_reference': {
                'title': 'API Reference',
                'content': '''
# API Reference

## Authentication
All API endpoints require authentication (coming soon)

## Endpoints
- `/api/links` - Link management
- `/api/parsing` - Content parsing
- `/api/ai` - AI processing
- `/api/notion` - Notion import
- `/api/content` - Content management

## Response Format
All responses follow the format:
{
  "success": true,
  "data": {...},
  "message": "Success message"
}
                ''',
                'category': 'api'
            },
            'troubleshooting': {
                'title': 'Troubleshooting',
                'content': '''
# Troubleshooting

## Common Issues

### Notion Import Fails
- Check integration token is correct
- Ensure database is shared with integration
- Verify database ID is correct

### Parsing Fails
- Check URL is accessible
- Verify content is not behind paywall
- Try different parsing method

### AI Processing Fails
- Check API key is valid
- Verify API has credits
- Check rate limits

## Getting Help
Submit feedback through the Feedback form with detailed error information
                ''',
                'category': 'support'
            }
        }

    def get_help_topics(self) -> List[Dict[str, Any]]:
        """
        Get list of help topics

        Returns:
            List of help topic summaries
        """
        return [
            {
                'id': topic_id,
                'title': topic['title'],
                'category': topic['category']
            }
            for topic_id, topic in self.help_content.items()
        ]

    def get_help_topic(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """
        Get help topic content

        Args:
            topic_id: Topic ID

        Returns:
            Dict with topic content or None
        """
        if topic_id not in self.help_content:
            return None

        topic = self.help_content[topic_id]
        return {
            'id': topic_id,
            'title': topic['title'],
            'content': topic['content'],
            'category': topic['category']
        }

    def search_help(self, query: str) -> List[Dict[str, Any]]:
        """
        Search help topics

        Args:
            query: Search query

        Returns:
            List of matching topics
        """
        query_lower = query.lower()
        results = []

        for topic_id, topic in self.help_content.items():
            if (query_lower in topic['title'].lower() or
                query_lower in topic['content'].lower()):
                results.append({
                    'id': topic_id,
                    'title': topic['title'],
                    'category': topic['category']
                })

        return results


# Singleton instances
_feedback_service = None
_help_service = None


def get_feedback_service() -> FeedbackService:
    """Get singleton instance of FeedbackService"""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service


def get_help_service() -> HelpService:
    """Get singleton instance of HelpService"""
    global _help_service
    if _help_service is None:
        _help_service = HelpService()
    return _help_service
