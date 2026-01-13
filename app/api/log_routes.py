"""
Log management API routes
"""
from flask import Blueprint, request, jsonify
from app.services.log_service import get_log_service
from app.utils.response import success_response, error_response
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

log_bp = Blueprint('logs', __name__, url_prefix='/logs')


@log_bp.route('/', methods=['GET'])
def get_logs():
    """
    Get operation logs with filtering

    Query Parameters:
        - level: Filter by level (info/warning/error)
        - module: Filter by module
        - search: Search in action and message
        - start_date: Start date (ISO format)
        - end_date: End date (ISO format)
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50)

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
        level = request.args.get('level')
        module = request.args.get('module')
        search = request.args.get('search')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        # Validate level
        if level and level not in ['info', 'warning', 'error']:
            return error_response('VAL_001', 'level must be info, warning, or error', None, 400)

        # Validate pagination
        if page < 1:
            return error_response('VAL_001', 'Page must be >= 1', None, 400)
        if per_page < 1 or per_page > 200:
            return error_response('VAL_001', 'Per page must be between 1 and 200', None, 400)

        # Parse dates
        start_date = None
        end_date = None

        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except ValueError:
                return error_response('VAL_001', 'Invalid start_date format', None, 400)

        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except ValueError:
                return error_response('VAL_001', 'Invalid end_date format', None, 400)

        service = get_log_service()
        result = service.get_logs(
            level=level,
            module=module,
            search=search,
            start_date=start_date,
            end_date=end_date,
            page=page,
            per_page=per_page
        )

        return success_response(data=result)

    except Exception as e:
        logger.error(f"Failed to get logs: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get logs: {str(e)}', None, 500)


@log_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Get log statistics

    Query Parameters:
        - days: Number of recent days (default: 7)

    Response (200):
        {
          "success": true,
          "data": {
            "total_logs": 1500,
            "by_level": {...},
            "by_module": {...},
            "recent_errors": [...]
          }
        }
    """
    try:
        days = request.args.get('days', 7, type=int)

        if days < 1 or days > 365:
            return error_response('VAL_001', 'days must be between 1 and 365', None, 400)

        service = get_log_service()
        stats = service.get_log_statistics(days=days)

        return success_response(data=stats)

    except Exception as e:
        logger.error(f"Failed to get log statistics: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get statistics: {str(e)}', None, 500)


@log_bp.route('/export', methods=['GET'])
def export_logs():
    """
    Export logs to JSON

    Query Parameters:
        - level: Filter by level
        - module: Filter by module
        - start_date: Start date (ISO format)
        - end_date: End date (ISO format)
        - format: Export format (json/csv, default: json)

    Response (200):
        JSON array of log entries
    """
    try:
        level = request.args.get('level')
        module = request.args.get('module')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        format_type = request.args.get('format', 'json')

        # Validate level
        if level and level not in ['info', 'warning', 'error']:
            return error_response('VAL_001', 'level must be info, warning, or error', None, 400)

        # Parse dates
        start_date = None
        end_date = None

        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except ValueError:
                return error_response('VAL_001', 'Invalid start_date format', None, 400)

        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except ValueError:
                return error_response('VAL_001', 'Invalid end_date format', None, 400)

        service = get_log_service()
        logs = service.export_logs(
            level=level,
            module=module,
            start_date=start_date,
            end_date=end_date,
            format=format_type
        )

        if format_type == 'csv':
            # TODO: Implement CSV export
            return error_response('VAL_001', 'CSV format not yet implemented', None, 400)

        return jsonify(logs)

    except Exception as e:
        logger.error(f"Failed to export logs: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to export logs: {str(e)}', None, 500)


@log_bp.route('/cleanup', methods=['POST'])
def cleanup_old_logs():
    """
    Delete old logs

    Request Body:
        {
          "days": 90
        }

    Response (200):
        {
          "success": true,
          "data": {
            "deleted_count": 1000
          },
          "message": "Deleted 1000 old logs"
        }
    """
    try:
        data = request.get_json() or {}
        days = data.get('days', 90)

        if not isinstance(days, int) or days < 1:
            return error_response('VAL_001', 'days must be a positive integer', None, 400)

        service = get_log_service()
        deleted_count = service.cleanup_old_logs(days=days)

        return success_response(
            data={'deleted_count': deleted_count},
            message=f'Deleted {deleted_count} old logs'
        )

    except Exception as e:
        logger.error(f"Failed to cleanup logs: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to cleanup logs: {str(e)}', None, 500)


@log_bp.route('/modules', methods=['GET'])
def get_modules():
    """
    Get list of unique modules

    Response (200):
        {
          "success": true,
          "data": {
            "modules": ["parsing", "ai_processing", "notion_import", ...]
          }
        }
    """
    try:
        service = get_log_service()
        modules = service.get_modules()

        return success_response(data={'modules': modules})

    except Exception as e:
        logger.error(f"Failed to get modules: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get modules: {str(e)}', None, 500)
