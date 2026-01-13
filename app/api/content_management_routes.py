"""
Content management API routes
"""
from flask import Blueprint, request
from app.services.content_management_service import get_content_management_service
from app.utils.response import success_response, error_response
from app.utils.validators import validate_required
import logging

logger = logging.getLogger(__name__)

content_management_bp = Blueprint('content_management', __name__, url_prefix='/content')


@content_management_bp.route('/local', methods=['GET'])
def get_local_content():
    """
    Get all local content with filtering and pagination

    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
        - status: Filter by status (parsed/ai_processed/imported)
        - search: Search in title and content
        - sort: Sort field (created_at/quality_score/title)
        - order: Sort order (asc/desc, default: desc)

    Response (200):
        {
          "success": true,
          "data": {
            "items": [...],
            "pagination": {
              "page": 1,
              "per_page": 20,
              "total": 100,
              "pages": 5
            }
          }
        }
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        search = request.args.get('search')
        sort = request.args.get('sort', 'created_at')
        order = request.args.get('order', 'desc')

        # Validate pagination
        if page < 1:
            return error_response('VAL_001', 'Page must be >= 1', None, 400)
        if per_page < 1 or per_page > 100:
            return error_response('VAL_001', 'Per page must be between 1 and 100', None, 400)

        service = get_content_management_service()
        result = service.get_local_content(
            page=page,
            per_page=per_page,
            status=status,
            search=search,
            sort=sort,
            order=order
        )

        return success_response(data=result)

    except Exception as e:
        logger.error(f"Failed to get local content: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get content: {str(e)}', None, 500)


@content_management_bp.route('/local/<int:content_id>', methods=['GET'])
def get_content_details(content_id):
    """
    Get detailed content information

    Path Parameters:
        content_id: Content ID

    Response (200):
        {
          "success": true,
          "data": {
            "parsed_content": {...},
            "ai_content": {...},
            "notion_imports": [...]
          }
        }
    """
    try:
        service = get_content_management_service()
        result = service.get_content_details(content_id)

        if not result:
            return error_response('RES_001', f'Content {content_id} not found', None, 404)

        return success_response(data=result)

    except Exception as e:
        logger.error(f"Failed to get content details for {content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get content: {str(e)}', None, 500)


@content_management_bp.route('/local/<int:content_id>', methods=['PUT'])
def update_content(content_id):
    """
    Update content manually

    Path Parameters:
        content_id: Content ID

    Request Body:
        {
          "formatted_content": "Updated content...",
          "summary": "Updated summary",
          "keywords": ["keyword1", "keyword2"]
        }

    Response (200):
        {
          "success": true,
          "message": "Content updated successfully"
        }
    """
    try:
        data = request.get_json()

        service = get_content_management_service()
        success = service.update_content(content_id, data)

        if not success:
            return error_response('RES_001', f'Content {content_id} not found', None, 404)

        return success_response(message='Content updated successfully')

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Failed to update content {content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to update content: {str(e)}', None, 500)


@content_management_bp.route('/local/batch', methods=['DELETE'])
def delete_content_batch():
    """
    Batch delete content

    Request Body:
        {
          "content_ids": [1, 2, 3]
        }

    Response (200):
        {
          "success": true,
          "data": {
            "deleted_count": 3
          },
          "message": "Deleted 3 content items"
        }
    """
    try:
        data = request.get_json()
        validate_required(data, ['content_ids'])

        content_ids = data['content_ids']
        if not isinstance(content_ids, list) or len(content_ids) == 0:
            return error_response('VAL_001', 'content_ids must be a non-empty array', None, 400)

        service = get_content_management_service()
        deleted_count = service.delete_content_batch(content_ids)

        return success_response(
            data={'deleted_count': deleted_count},
            message=f'Deleted {deleted_count} content items'
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Failed to delete content batch: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to delete content: {str(e)}', None, 500)


@content_management_bp.route('/reparse', methods=['POST'])
def reparse_content():
    """
    Reparse content (queue for re-parsing)

    Request Body:
        {
          "content_ids": [1, 2, 3]
        }

    Response (202):
        {
          "success": true,
          "data": {
            "task_id": 123,
            "queued_count": 3
          },
          "message": "Queued 3 items for reparsing"
        }
    """
    try:
        data = request.get_json()
        validate_required(data, ['content_ids'])

        content_ids = data['content_ids']
        if not isinstance(content_ids, list) or len(content_ids) == 0:
            return error_response('VAL_001', 'content_ids must be a non-empty array', None, 400)

        service = get_content_management_service()
        result = service.reparse_content(content_ids)

        return success_response(
            data=result,
            message=f'Queued {len(content_ids)} items for reparsing',
            status=202
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Failed to queue reparsing: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to queue reparsing: {str(e)}', None, 500)


@content_management_bp.route('/regenerate', methods=['POST'])
def regenerate_ai_content():
    """
    Regenerate AI content (queue for AI reprocessing)

    Request Body:
        {
          "content_ids": [1, 2, 3],
          "model_id": 1,
          "processing_config": {
            "generate_summary": true,
            "generate_keywords": true
          }
        }

    Response (202):
        {
          "success": true,
          "data": {
            "task_id": 124,
            "queued_count": 3
          },
          "message": "Queued 3 items for AI regeneration"
        }
    """
    try:
        data = request.get_json()
        validate_required(data, ['content_ids'])

        content_ids = data['content_ids']
        if not isinstance(content_ids, list) or len(content_ids) == 0:
            return error_response('VAL_001', 'content_ids must be a non-empty array', None, 400)

        model_id = data.get('model_id')
        processing_config = data.get('processing_config', {})

        service = get_content_management_service()
        result = service.regenerate_ai_content(content_ids, model_id, processing_config)

        return success_response(
            data=result,
            message=f'Queued {len(content_ids)} items for AI regeneration',
            status=202
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Failed to queue AI regeneration: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to queue AI regeneration: {str(e)}', None, 500)


@content_management_bp.route('/statistics', methods=['GET'])
def get_content_statistics():
    """
    Get content statistics

    Response (200):
        {
          "success": true,
          "data": {
            "total_parsed": 100,
            "total_ai_processed": 80,
            "total_imported": 60,
            "average_quality_score": 85.5,
            "by_status": {...}
          }
        }
    """
    try:
        service = get_content_management_service()
        stats = service.get_content_statistics()

        return success_response(data=stats)

    except Exception as e:
        logger.error(f"Failed to get content statistics: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get statistics: {str(e)}', None, 500)
