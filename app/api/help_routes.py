"""
Help and feedback API routes
"""
from flask import Blueprint, request
from app.services.feedback_service import get_feedback_service, get_help_service
from app.utils.response import success_response, error_response
from app.utils.validators import validate_required
import logging

logger = logging.getLogger(__name__)

help_bp = Blueprint('help', __name__, url_prefix='/help')
feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')


# Help endpoints
@help_bp.route('/topics', methods=['GET'])
def get_help_topics():
    """
    Get list of help topics

    Response (200):
        {
          "success": true,
          "data": {
            "topics": [
              {
                "id": "getting_started",
                "title": "Getting Started",
                "category": "basics"
              }
            ]
          }
        }
    """
    try:
        service = get_help_service()
        topics = service.get_help_topics()

        return success_response(data={'topics': topics})

    except Exception as e:
        logger.error(f"Failed to get help topics: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get help topics: {str(e)}', None, 500)


@help_bp.route('/topics/<topic_id>', methods=['GET'])
def get_help_topic(topic_id):
    """
    Get help topic content

    Path Parameters:
        topic_id: Topic ID

    Response (200):
        {
          "success": true,
          "data": {
            "id": "getting_started",
            "title": "Getting Started",
            "content": "...",
            "category": "basics"
          }
        }
    """
    try:
        service = get_help_service()
        topic = service.get_help_topic(topic_id)

        if not topic:
            return error_response('RES_001', f'Help topic {topic_id} not found', None, 404)

        return success_response(data=topic)

    except Exception as e:
        logger.error(f"Failed to get help topic: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get help topic: {str(e)}', None, 500)


@help_bp.route('/search', methods=['GET'])
def search_help():
    """
    Search help topics

    Query Parameters:
        - q: Search query

    Response (200):
        {
          "success": true,
          "data": {
            "results": [...]
          }
        }
    """
    try:
        query = request.args.get('q', '')

        if not query:
            return error_response('VAL_001', 'Search query is required', None, 400)

        service = get_help_service()
        results = service.search_help(query)

        return success_response(data={'results': results})

    except Exception as e:
        logger.error(f"Failed to search help: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to search help: {str(e)}', None, 500)


# Feedback endpoints
@feedback_bp.route('/', methods=['POST'])
def submit_feedback():
    """
    Submit user feedback

    Request Body:
        {
          "type": "bug",
          "content": "Description of the issue...",
          "user_email": "user@example.com",
          "screenshot_path": "/path/to/screenshot.png"
        }

    Response (200):
        {
          "success": true,
          "data": {
            "feedback_id": 1,
            "status": "new"
          },
          "message": "Feedback submitted successfully"
        }
    """
    try:
        data = request.get_json()
        validate_required(data, ['type', 'content'])

        feedback_type = data['type']
        content = data['content']
        user_email = data.get('user_email')
        screenshot_path = data.get('screenshot_path')

        # Validate type
        if feedback_type not in ['bug', 'feature', 'other']:
            return error_response('VAL_001', 'type must be bug, feature, or other', None, 400)

        # Validate content length
        if len(content) < 10:
            return error_response('VAL_001', 'content must be at least 10 characters', None, 400)

        service = get_feedback_service()
        result = service.submit_feedback(
            feedback_type=feedback_type,
            content=content,
            user_email=user_email,
            screenshot_path=screenshot_path
        )

        if not result['success']:
            return error_response('SYS_001', result['error'], None, 500)

        return success_response(
            data=result,
            message='Feedback submitted successfully'
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to submit feedback: {str(e)}', None, 500)


@feedback_bp.route('/', methods=['GET'])
def get_feedback_list():
    """
    Get feedback list

    Query Parameters:
        - type: Filter by type (bug/feature/other)
        - status: Filter by status
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)

    Response (200):
        {
          "success": true,
          "data": {
            "items": [...],
            "pagination": {...}
          }
        }
    """
    try:
        feedback_type = request.args.get('type')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Validate pagination
        if page < 1:
            return error_response('VAL_001', 'Page must be >= 1', None, 400)
        if per_page < 1 or per_page > 100:
            return error_response('VAL_001', 'Per page must be between 1 and 100', None, 400)

        service = get_feedback_service()
        result = service.get_feedback_list(
            feedback_type=feedback_type,
            status=status,
            page=page,
            per_page=per_page
        )

        if not result['success']:
            return error_response('SYS_001', result['error'], None, 500)

        return success_response(data=result)

    except Exception as e:
        logger.error(f"Failed to get feedback list: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get feedback: {str(e)}', None, 500)


@feedback_bp.route('/<int:feedback_id>', methods=['GET'])
def get_feedback_details(feedback_id):
    """
    Get feedback details

    Path Parameters:
        feedback_id: Feedback ID

    Response (200):
        {
          "success": true,
          "data": {
            "id": 1,
            "type": "bug",
            "content": "...",
            "status": "new"
          }
        }
    """
    try:
        service = get_feedback_service()
        result = service.get_feedback_details(feedback_id)

        if not result:
            return error_response('RES_001', f'Feedback {feedback_id} not found', None, 404)

        return success_response(data=result)

    except Exception as e:
        logger.error(f"Failed to get feedback details: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get feedback: {str(e)}', None, 500)


@feedback_bp.route('/<int:feedback_id>', methods=['PUT'])
def update_feedback_status(feedback_id):
    """
    Update feedback status

    Path Parameters:
        feedback_id: Feedback ID

    Request Body:
        {
          "status": "reviewed"
        }

    Response (200):
        {
          "success": true,
          "message": "Feedback status updated"
        }
    """
    try:
        data = request.get_json()
        validate_required(data, ['status'])

        status = data['status']

        service = get_feedback_service()
        success = service.update_feedback_status(feedback_id, status)

        if not success:
            return error_response('RES_001', f'Feedback {feedback_id} not found', None, 404)

        return success_response(message='Feedback status updated')

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Failed to update feedback: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to update feedback: {str(e)}', None, 500)


@feedback_bp.route('/<int:feedback_id>', methods=['DELETE'])
def delete_feedback(feedback_id):
    """
    Delete feedback

    Path Parameters:
        feedback_id: Feedback ID

    Response (200):
        {
          "success": true,
          "message": "Feedback deleted successfully"
        }
    """
    try:
        service = get_feedback_service()
        success = service.delete_feedback(feedback_id)

        if not success:
            return error_response('RES_001', f'Feedback {feedback_id} not found', None, 404)

        return success_response(message='Feedback deleted successfully')

    except Exception as e:
        logger.error(f"Failed to delete feedback: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to delete feedback: {str(e)}', None, 500)


@feedback_bp.route('/statistics', methods=['GET'])
def get_feedback_statistics():
    """
    Get feedback statistics

    Response (200):
        {
          "success": true,
          "data": {
            "total_feedback": 50,
            "by_type": {...},
            "by_status": {...}
          }
        }
    """
    try:
        service = get_feedback_service()
        stats = service.get_feedback_statistics()

        return success_response(data=stats)

    except Exception as e:
        logger.error(f"Failed to get feedback statistics: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get statistics: {str(e)}', None, 500)
