"""
Backup and restore API routes
"""
from flask import Blueprint, request, send_file
from app.services.backup_service import get_backup_service
from app.utils.response import success_response, error_response
from app.utils.validators import validate_required
from app.middleware.auth import require_auth
from app.middleware.rate_limiter import backup_rate_limit
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')


@backup_bp.route('/', methods=['POST'])
@require_auth()
@backup_rate_limit()
def create_backup():
    """
    Create a new backup

    Request Body:
        {
          "type": "manual",
          "include_database": true,
          "include_files": true,
          "retention_days": 30
        }

    Response (200):
        {
          "success": true,
          "data": {
            "backup_id": 1,
            "filename": "backup_manual_20240113_143000.zip",
            "size": 1048576
          }
        }
    """
    try:
        data = request.get_json() or {}

        backup_type = data.get('type', 'manual')
        include_database = data.get('include_database', True)
        include_files = data.get('include_files', True)
        retention_days = data.get('retention_days')

        # Validate type
        if backup_type not in ['manual', 'auto']:
            return error_response('VAL_001', 'type must be "manual" or "auto"', None, 400)

        # Validate retention_days
        if retention_days is not None:
            if not isinstance(retention_days, int) or retention_days <= 0:
                return error_response('VAL_001', 'retention_days must be a positive integer', None, 400)

        service = get_backup_service()
        result = service.create_backup(
            backup_type=backup_type,
            include_database=include_database,
            include_files=include_files,
            retention_days=retention_days
        )

        if not result['success']:
            return error_response('SYS_001', result['error'], None, 500)

        return success_response(
            data=result,
            message='Backup created successfully'
        )

    except Exception as e:
        logger.error(f"Failed to create backup: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to create backup: {str(e)}', None, 500)


@backup_bp.route('/', methods=['GET'])
def list_backups():
    """
    List all backups

    Query Parameters:
        - type: Filter by type (manual/auto)
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
        backup_type = request.args.get('type')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Validate pagination
        if page < 1:
            return error_response('VAL_001', 'Page must be >= 1', None, 400)
        if per_page < 1 or per_page > 100:
            return error_response('VAL_001', 'Per page must be between 1 and 100', None, 400)

        service = get_backup_service()
        result = service.list_backups(
            backup_type=backup_type,
            page=page,
            per_page=per_page
        )

        if not result['success']:
            return error_response('SYS_001', result['error'], None, 500)

        return success_response(data=result)

    except Exception as e:
        logger.error(f"Failed to list backups: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to list backups: {str(e)}', None, 500)


@backup_bp.route('/<int:backup_id>', methods=['GET'])
def get_backup_details(backup_id):
    """
    Get backup details

    Path Parameters:
        backup_id: Backup ID

    Response (200):
        {
          "success": true,
          "data": {
            "id": 1,
            "filename": "backup_manual_20240113.zip",
            "size": 1048576,
            "files_by_type": {...}
          }
        }
    """
    try:
        service = get_backup_service()
        result = service.get_backup_details(backup_id)

        if not result:
            return error_response('RES_001', f'Backup {backup_id} not found', None, 404)

        return success_response(data=result)

    except Exception as e:
        logger.error(f"Failed to get backup details: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get backup: {str(e)}', None, 500)


@backup_bp.route('/<int:backup_id>/download', methods=['GET'])
def download_backup(backup_id):
    """
    Download backup file

    Path Parameters:
        backup_id: Backup ID

    Response (200):
        Binary file download
    """
    try:
        service = get_backup_service()
        backup_details = service.get_backup_details(backup_id)

        if not backup_details:
            return error_response('RES_001', f'Backup {backup_id} not found', None, 404)

        if not backup_details['file_exists']:
            return error_response('RES_001', 'Backup file not found on disk', None, 404)

        filepath = Path(backup_details['filepath'])

        return send_file(
            filepath,
            as_attachment=True,
            download_name=backup_details['filename'],
            mimetype='application/zip'
        )

    except Exception as e:
        logger.error(f"Failed to download backup: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to download backup: {str(e)}', None, 500)


@backup_bp.route('/<int:backup_id>/restore', methods=['POST'])
@require_auth()
def restore_backup(backup_id):
    """
    Restore from backup

    Path Parameters:
        backup_id: Backup ID

    Request Body:
        {
          "restore_database": true,
          "restore_files": true
        }

    Response (200):
        {
          "success": true,
          "data": {
            "restored_files_count": 150
          },
          "message": "Restore completed. Please restart application."
        }
    """
    try:
        data = request.get_json() or {}

        restore_database = data.get('restore_database', True)
        restore_files = data.get('restore_files', True)

        if not restore_database and not restore_files:
            return error_response('VAL_001', 'Must restore database or files', None, 400)

        service = get_backup_service()
        result = service.restore_backup(
            backup_id=backup_id,
            restore_database=restore_database,
            restore_files=restore_files
        )

        if not result['success']:
            return error_response('SYS_001', result['error'], None, 500)

        return success_response(
            data=result,
            message=result.get('message', 'Restore completed successfully')
        )

    except Exception as e:
        logger.error(f"Failed to restore backup: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to restore backup: {str(e)}', None, 500)


@backup_bp.route('/<int:backup_id>', methods=['DELETE'])
@require_auth()
def delete_backup(backup_id):
    """
    Delete backup

    Path Parameters:
        backup_id: Backup ID

    Query Parameters:
        - delete_file: Also delete physical file (default: true)

    Response (200):
        {
          "success": true,
          "message": "Backup deleted successfully"
        }
    """
    try:
        delete_file = request.args.get('delete_file', 'true').lower() == 'true'

        service = get_backup_service()
        success = service.delete_backup(backup_id, delete_file=delete_file)

        if not success:
            return error_response('RES_001', f'Backup {backup_id} not found', None, 404)

        return success_response(message='Backup deleted successfully')

    except Exception as e:
        logger.error(f"Failed to delete backup: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to delete backup: {str(e)}', None, 500)


@backup_bp.route('/cleanup', methods=['POST'])
@require_auth()
def cleanup_expired():
    """
    Cleanup expired backups

    Response (200):
        {
          "success": true,
          "data": {
            "deleted_count": 5
          },
          "message": "Cleaned up 5 expired backups"
        }
    """
    try:
        service = get_backup_service()
        result = service.cleanup_expired_backups()

        if not result['success']:
            return error_response('SYS_001', result['error'], None, 500)

        return success_response(
            data=result,
            message=f"Cleaned up {result['deleted_count']} expired backups"
        )

    except Exception as e:
        logger.error(f"Failed to cleanup expired backups: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to cleanup: {str(e)}', None, 500)


@backup_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Get backup statistics

    Response (200):
        {
          "success": true,
          "data": {
            "total_backups": 10,
            "manual_backups": 7,
            "auto_backups": 3,
            "total_size": 52428800
          }
        }
    """
    try:
        service = get_backup_service()
        stats = service.get_backup_statistics()

        return success_response(data=stats)

    except Exception as e:
        logger.error(f"Failed to get backup statistics: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get statistics: {str(e)}', None, 500)
