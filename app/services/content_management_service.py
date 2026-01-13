"""
Content management service for local content operations
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy import or_, desc, asc, func
from app import db
from app.models.link import Link
from app.models.content import ParsedContent, AIProcessedContent
from app.models.notion import NotionImport

logger = logging.getLogger(__name__)


class ContentManagementService:
    """Service for managing local content"""

    def get_local_content(self, page: int = 1, per_page: int = 20,
                         status: Optional[str] = None,
                         search: Optional[str] = None,
                         sort: str = 'parsed_at',
                         order: str = 'desc') -> Dict[str, Any]:
        """
        Get all local content with filtering and pagination

        Args:
            page: Page number
            per_page: Items per page
            status: Filter by status
            search: Search term
            sort: Sort field
            order: Sort order (asc/desc)

        Returns:
            Dict with items and pagination info
        """
        # Build query
        query = db.session.query(ParsedContent).join(Link)

        # Apply status filter
        if status:
            if status == 'parsed':
                # Has parsed content only
                query = query.outerjoin(AIProcessedContent).filter(
                    AIProcessedContent.id == None
                )
            elif status == 'ai_processed':
                # Has AI processed content
                query = query.join(AIProcessedContent).filter(
                    AIProcessedContent.is_active == True
                )
            elif status == 'imported':
                # Has been imported to Notion
                query = query.join(AIProcessedContent).join(NotionImport)

        # Apply search filter
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                or_(
                    Link.title.ilike(search_term),
                    ParsedContent.formatted_content.ilike(search_term)
                )
            )

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        sort_column = getattr(ParsedContent, sort, ParsedContent.parsed_at)
        if order == 'asc':
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # Apply pagination
        offset = (page - 1) * per_page
        items = query.limit(per_page).offset(offset).all()

        # Format results
        result_items = []
        for parsed_content in items:
            # Get AI content if available
            ai_content = db.session.query(AIProcessedContent).filter_by(
                parsed_content_id=parsed_content.id,
                is_active=True
            ).first()

            # Get Notion imports
            notion_imports = []
            if ai_content:
                notion_imports = db.session.query(NotionImport).filter_by(
                    ai_content_id=ai_content.id
                ).all()

            item = {
                'id': parsed_content.id,
                'link_id': parsed_content.link_id,
                'title': parsed_content.link.title if parsed_content.link else None,
                'url': parsed_content.link.url if parsed_content.link else None,
                'parsing_method': parsed_content.parsing_method,
                'quality_score': parsed_content.quality_score,
                'has_ai_content': ai_content is not None,
                'has_notion_import': len(notion_imports) > 0,
                'parsed_at': parsed_content.parsed_at.isoformat() if parsed_content.parsed_at else None,
                'ai_processed_at': ai_content.created_at.isoformat() if ai_content and ai_content.created_at else None
            }
            result_items.append(item)

        # Calculate pagination
        pages = (total + per_page - 1) // per_page

        return {
            'items': result_items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages
            }
        }

    def get_content_details(self, content_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed content information

        Args:
            content_id: ParsedContent ID

        Returns:
            Dict with full content details or None if not found
        """
        parsed_content = db.session.query(ParsedContent).get(content_id)
        if not parsed_content:
            return None

        # Get AI content
        ai_content = db.session.query(AIProcessedContent).filter_by(
            parsed_content_id=content_id,
            is_active=True
        ).first()

        # Get all AI versions
        ai_versions = db.session.query(AIProcessedContent).filter_by(
            parsed_content_id=content_id
        ).order_by(desc(AIProcessedContent.version)).all()

        # Get Notion imports
        notion_imports = []
        if ai_content:
            imports = db.session.query(NotionImport).filter_by(
                ai_content_id=ai_content.id
            ).all()

            for notion_import in imports:
                notion_imports.append({
                    'id': notion_import.id,
                    'notion_page_id': notion_import.notion_page_id,
                    'notion_url': notion_import.notion_url,
                    'status': notion_import.status,
                    'imported_at': notion_import.imported_at.isoformat() if notion_import.imported_at else None
                })

        result = {
            'parsed_content': {
                'id': parsed_content.id,
                'link_id': parsed_content.link_id,
                'title': parsed_content.link.title if parsed_content.link else None,
                'url': parsed_content.link.url if parsed_content.link else None,
                'raw_content': parsed_content.raw_content,
                'formatted_content': parsed_content.formatted_content,
                'parsing_method': parsed_content.parsing_method,
                'quality_score': parsed_content.quality_score,
                'parsed_at': parsed_content.parsed_at.isoformat() if parsed_content.parsed_at else None
            }
        }

        if ai_content:
            result['ai_content'] = {
                'id': ai_content.id,
                'model_id': ai_content.model_id,
                'summary': ai_content.summary,
                'keywords': ai_content.keywords,
                'insights': ai_content.insights,
                'version': ai_content.version,
                'tokens_used': ai_content.tokens_used,
                'cost': ai_content.cost,
                'created_at': ai_content.created_at.isoformat() if ai_content.created_at else None
            }

            result['ai_versions'] = [
                {
                    'id': v.id,
                    'version': v.version,
                    'is_active': v.is_active,
                    'created_at': v.created_at.isoformat() if v.created_at else None
                }
                for v in ai_versions
            ]

        result['notion_imports'] = notion_imports

        return result

    def update_content(self, content_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update content manually

        Args:
            content_id: ParsedContent ID
            updates: Dict with fields to update

        Returns:
            True if updated, False if not found
        """
        parsed_content = db.session.query(ParsedContent).get(content_id)
        if not parsed_content:
            return False

        # Update parsed content fields
        if 'formatted_content' in updates:
            parsed_content.formatted_content = updates['formatted_content']

        # Update AI content if exists
        if 'summary' in updates or 'keywords' in updates or 'insights' in updates:
            ai_content = db.session.query(AIProcessedContent).filter_by(
                parsed_content_id=content_id,
                is_active=True
            ).first()

            if ai_content:
                if 'summary' in updates:
                    ai_content.summary = updates['summary']
                if 'keywords' in updates:
                    ai_content.keywords = updates['keywords']
                if 'insights' in updates:
                    ai_content.insights = updates['insights']

        db.session.commit()
        logger.info(f"Updated content {content_id}")
        return True

    def delete_content_batch(self, content_ids: List[int]) -> int:
        """
        Batch delete content

        Args:
            content_ids: List of ParsedContent IDs

        Returns:
            Number of deleted items
        """
        # Delete AI content first (foreign key constraint)
        ai_deleted = db.session.query(AIProcessedContent).filter(
            AIProcessedContent.parsed_content_id.in_(content_ids)
        ).delete(synchronize_session=False)

        # Delete parsed content
        parsed_deleted = db.session.query(ParsedContent).filter(
            ParsedContent.id.in_(content_ids)
        ).delete(synchronize_session=False)

        db.session.commit()

        logger.info(f"Deleted {parsed_deleted} parsed content items and {ai_deleted} AI content items")
        return parsed_deleted

    def reparse_content(self, content_ids: List[int]) -> Dict[str, Any]:
        """
        Queue content for reparsing

        Args:
            content_ids: List of ParsedContent IDs

        Returns:
            Dict with task info
        """
        # Get link IDs from parsed content
        parsed_contents = db.session.query(ParsedContent).filter(
            ParsedContent.id.in_(content_ids)
        ).all()

        link_ids = [pc.link_id for pc in parsed_contents if pc.link_id]

        if not link_ids:
            raise ValueError('No valid links found for reparsing')

        # Queue for async parsing
        from app.services.background_task_service import get_background_task_service
        from config.workers import WorkerConfig

        task_service = get_background_task_service()

        # Create background task
        task = task_service.create_task(
            type='parsing',
            total_items=len(link_ids),
            config={'link_ids': link_ids, 'reparse': True},
            queue_name=WorkerConfig.PARSING_QUEUE
        )

        # Enqueue batch dispatch job
        job_id = task_service.enqueue_job(
            task.id,
            WorkerConfig.PARSING_QUEUE,
            'app.workers.parsing_worker.batch_parse_job',
            task.id,
            link_ids
        )

        logger.info(f"Queued {len(link_ids)} items for reparsing (task {task.id})")

        return {
            'task_id': task.id,
            'job_id': job_id,
            'queued_count': len(link_ids)
        }

    def regenerate_ai_content(self, content_ids: List[int],
                             model_id: Optional[int] = None,
                             processing_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Queue content for AI regeneration

        Args:
            content_ids: List of ParsedContent IDs
            model_id: Optional model ID
            processing_config: Optional processing config

        Returns:
            Dict with task info
        """
        # Validate content exists
        parsed_contents = db.session.query(ParsedContent).filter(
            ParsedContent.id.in_(content_ids)
        ).all()

        valid_ids = [pc.id for pc in parsed_contents]

        if not valid_ids:
            raise ValueError('No valid content found for AI regeneration')

        # Queue for async AI processing
        from app.services.background_task_service import get_background_task_service
        from config.workers import WorkerConfig

        task_service = get_background_task_service()

        # Create background task
        task = task_service.create_task(
            type='ai_processing',
            total_items=len(valid_ids),
            config={
                'parsed_content_ids': valid_ids,
                'model_id': model_id,
                'processing_config': processing_config or {},
                'regenerate': True
            },
            queue_name=WorkerConfig.AI_QUEUE
        )

        # Enqueue batch dispatch job
        job_id = task_service.enqueue_job(
            task.id,
            WorkerConfig.AI_QUEUE,
            'app.workers.ai_worker.batch_ai_process_job',
            task.id,
            valid_ids,
            model_id,
            processing_config or {}
        )

        logger.info(f"Queued {len(valid_ids)} items for AI regeneration (task {task.id})")

        return {
            'task_id': task.id,
            'job_id': job_id,
            'queued_count': len(valid_ids)
        }

    def get_content_statistics(self) -> Dict[str, Any]:
        """
        Get content statistics

        Returns:
            Dict with statistics
        """
        # Total counts
        total_parsed = db.session.query(ParsedContent).count()
        total_ai_processed = db.session.query(AIProcessedContent).filter_by(is_active=True).count()
        total_imported = db.session.query(NotionImport).filter_by(status='completed').count()

        # Average quality score
        avg_quality = db.session.query(func.avg(ParsedContent.quality_score)).scalar() or 0

        # By content type
        by_type = db.session.query(
            ParsedContent.parsing_method,
            func.count(ParsedContent.id)
        ).group_by(ParsedContent.parsing_method).all()

        # By status
        parsed_only = total_parsed - total_ai_processed
        ai_processed_only = total_ai_processed - total_imported

        return {
            'total_parsed': total_parsed,
            'total_ai_processed': total_ai_processed,
            'total_imported': total_imported,
            'average_quality_score': round(float(avg_quality), 2),
            'by_type': {parsing_method: count for parsing_method, count in by_type},
            'by_status': {
                'parsed_only': parsed_only,
                'ai_processed_only': ai_processed_only,
                'imported': total_imported
            }
        }


# Singleton instance
_content_management_service = None


def get_content_management_service() -> ContentManagementService:
    """Get singleton instance of ContentManagementService"""
    global _content_management_service
    if _content_management_service is None:
        _content_management_service = ContentManagementService()
    return _content_management_service
