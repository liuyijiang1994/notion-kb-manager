"""
Task Management Routes
Unified interface for managing pending and historical tasks
"""
import logging
from flask import Blueprint, request, send_file
from app.services.task_service import get_task_service
from app.services.background_task_service import get_background_task_service
from app.utils.response import success_response, error_response

logger = logging.getLogger(__name__)

task_mgmt_bp = Blueprint('task_management', __name__, url_prefix='/tasks')


@task_mgmt_bp.route('/pending', methods=['GET'])
def get_pending_tasks():
    """
    Get all pending tasks across all types

    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
        - type: Filter by type (import/parsing/ai/notion)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        task_type = request.args.get('type')

        task_service = get_task_service()

        # Get ImportTask (pending status)
        import_tasks = task_service.get_all_tasks(status='pending', limit=1000)

        # Get ProcessingTasks (pending/queued status)
        from app.models.content import ProcessingTask
        from app import db
        processing_tasks = db.session.query(ProcessingTask).filter(
            ProcessingTask.status.in_(['pending', 'queued'])
        ).order_by(ProcessingTask.id.desc()).limit(1000).all()

        # Combine and filter
        all_tasks = _combine_tasks(import_tasks, processing_tasks, task_type)

        # Manual pagination
        total = len(all_tasks)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_tasks = all_tasks[start_idx:end_idx]

        pages = (total + per_page - 1) // per_page

        return success_response(data={
            'tasks': paginated_tasks,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages
            }
        })

    except Exception as e:
        logger.error(f"Failed to get pending tasks: {e}", exc_info=True)
        return error_response('SYS_001', 'Failed to retrieve pending tasks', str(e), 500)


@task_mgmt_bp.route('/pending/<int:task_id>', methods=['GET'])
def get_pending_task_details(task_id):
    """Get detailed information for pending task"""
    try:
        task = _get_task_by_id(task_id)

        if not task:
            return error_response('RES_001', 'Task not found', None, 404)

        # Check if task is actually pending
        task_status = task.get('status')
        if task_status not in ['pending', 'queued']:
            return error_response('RES_001', 'Task is not in pending state', None, 400)

        details = _format_task_details(task)
        return success_response(data=details)

    except Exception as e:
        logger.error(f"Failed to get pending task details: {e}", exc_info=True)
        return error_response('SYS_001', 'Failed to retrieve task details', str(e), 500)


@task_mgmt_bp.route('/pending/<int:task_id>', methods=['PUT'])
def edit_pending_task(task_id):
    """
    Edit pending task configuration

    Request Body:
        {
          "name": "New Task Name",
          "config": {...updated config...}
        }
    """
    try:
        data = request.get_json()

        if not data:
            return error_response('VAL_001', 'Request body is required', None, 400)

        task_service = get_task_service()

        # Update task
        success = task_service.update_task(
            task_id,
            name=data.get('name'),
            config=data.get('config')
        )

        if not success:
            return error_response('RES_001', 'Cannot edit task',
                                'Task not found or not in pending state', 400)

        return success_response(message='Task updated successfully')

    except Exception as e:
        logger.error(f"Failed to edit pending task: {e}", exc_info=True)
        return error_response('SYS_001', 'Failed to update task', str(e), 500)


@task_mgmt_bp.route('/pending/<int:task_id>/start', methods=['POST'])
def start_pending_task(task_id):
    """Start pending task"""
    try:
        task_service = get_task_service()
        success = task_service.start_task(task_id)

        if not success:
            return error_response('RES_001', 'Cannot start task',
                                'Task not found or not in pending state', 400)

        return success_response(message='Task started successfully')

    except Exception as e:
        logger.error(f"Failed to start pending task: {e}", exc_info=True)
        return error_response('SYS_001', 'Failed to start task', str(e), 500)


@task_mgmt_bp.route('/pending/<int:task_id>', methods=['DELETE'])
def delete_pending_task(task_id):
    """Delete pending task"""
    try:
        task_service = get_task_service()
        success = task_service.delete_task(task_id, delete_links=False)

        if not success:
            return error_response('RES_001', 'Task not found', None, 404)

        return success_response(message='Task deleted successfully')

    except Exception as e:
        logger.error(f"Failed to delete pending task: {e}", exc_info=True)
        return error_response('SYS_001', 'Failed to delete task', str(e), 500)


@task_mgmt_bp.route('/history', methods=['GET'])
def get_historical_tasks():
    """
    Get completed/failed tasks

    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
        - type: Filter by type (import/parsing/ai/notion)
        - status: Filter by status (completed/failed) - comma-separated
        - date_from: Start date filter (ISO format)
        - date_to: End date filter (ISO format)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        task_type = request.args.get('type')
        status = request.args.get('status', 'completed,failed,running,queued')

        statuses = [s.strip() for s in status.split(',')]

        task_service = get_task_service()

        # Get ImportTask with multiple statuses
        import_tasks = task_service.get_tasks_by_status_list(statuses, limit=1000)

        # Get ProcessingTasks
        from app.models.content import ProcessingTask
        from app import db
        processing_tasks = db.session.query(ProcessingTask).filter(
            ProcessingTask.status.in_(statuses)
        ).order_by(ProcessingTask.started_at.desc().nullslast()).limit(1000).all()

        # Combine and filter
        all_tasks = _combine_tasks(import_tasks, processing_tasks, task_type)

        # Manual pagination
        total = len(all_tasks)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_tasks = all_tasks[start_idx:end_idx]

        pages = (total + per_page - 1) // per_page

        return success_response(data={
            'tasks': paginated_tasks,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages
            }
        })

    except Exception as e:
        logger.error(f"Failed to get historical tasks: {e}", exc_info=True)
        return error_response('SYS_001', 'Failed to retrieve historical tasks', str(e), 500)


@task_mgmt_bp.route('/history/<int:task_id>', methods=['GET'])
def get_historical_task_details(task_id):
    """Get completed task details with full execution info"""
    try:
        task_service = get_task_service()

        # Get full task summary
        details = task_service.get_task_summary(task_id)

        if not details:
            return error_response('RES_001', 'Historical task not found', None, 404)

        # Check if task is actually completed/failed
        task_status = details.get('task', {}).get('status')
        if task_status not in ['completed', 'failed', 'cancelled']:
            return error_response('RES_001', 'Task is not in historical state', None, 400)

        return success_response(data=details)

    except Exception as e:
        logger.error(f"Failed to get historical task details: {e}", exc_info=True)
        return error_response('SYS_001', 'Failed to retrieve task details', str(e), 500)


@task_mgmt_bp.route('/history/<int:task_id>/rerun', methods=['POST'])
def rerun_historical_task(task_id):
    """
    Clone completed task and create new pending task

    Request Body:
        {
          "name": "Optional new name",
          "modify_config": {...optional config changes...}
        }
    """
    try:
        data = request.get_json() or {}

        task_service = get_task_service()
        new_task = task_service.clone_task(
            task_id,
            new_name=data.get('name'),
            config_overrides=data.get('modify_config')
        )

        if not new_task:
            return error_response('RES_001', 'Cannot clone task',
                                'Original task not found or cloning failed', 400)

        return success_response(
            data={'task_id': new_task.id, 'task_name': new_task.name},
            message='Task cloned successfully'
        )

    except Exception as e:
        logger.error(f"Failed to clone task: {e}", exc_info=True)
        return error_response('SYS_001', 'Failed to clone task', str(e), 500)


@task_mgmt_bp.route('/history/<int:task_id>/export', methods=['POST'])
def export_task_report(task_id):
    """
    Generate and download task execution report

    Request Body:
        {
          "format": "excel|pdf|json"
        }
    """
    try:
        from app.services.task_report_service import get_task_report_service

        data = request.get_json() or {}
        format_type = data.get('format', 'excel')

        if format_type not in ['excel', 'pdf', 'json']:
            return error_response('VAL_001', 'Invalid format type',
                                'Format must be excel, pdf, or json', 400)

        report_service = get_task_report_service()
        result = report_service.generate_report(task_id, format_type)

        if not result['success']:
            return error_response('SYS_001', 'Failed to generate report',
                                result.get('error'), 500)

        # Return file download
        return send_file(
            result['filepath'],
            as_attachment=True,
            download_name=result['filepath'].split('/')[-1]
        )

    except Exception as e:
        logger.error(f"Failed to export task report: {e}", exc_info=True)
        return error_response('SYS_001', 'Failed to generate report', str(e), 500)


# Helper functions

def _get_task_by_id(task_id):
    """Get task from any task type"""
    task_service = get_task_service()
    background_service = get_background_task_service()

    # Try ImportTask first
    import_task = task_service.get_task(task_id)
    if import_task:
        return {
            'id': import_task.id,
            'name': import_task.name,
            'type': 'import',
            'status': import_task.status,
            'config': import_task.config,
            'total_links': import_task.total_links,
            'processed_links': import_task.processed_links,
            'created_at': import_task.created_at.isoformat() if import_task.created_at else None,
            'started_at': import_task.started_at.isoformat() if import_task.started_at else None,
            'completed_at': import_task.completed_at.isoformat() if import_task.completed_at else None
        }

    # Try ProcessingTask
    processing_task = background_service.get_task_status(task_id)
    if processing_task and processing_task.get('success'):
        task_data = processing_task.get('data', {})
        return {
            'id': task_data.get('task_id'),
            'name': f"{task_data.get('type', 'Processing').title()} Task {task_data.get('task_id')}",
            'type': task_data.get('type'),
            'status': task_data.get('status'),
            'config': task_data.get('config'),
            'progress': task_data.get('progress'),
            'total_items': task_data.get('total_items'),
            'completed_items': task_data.get('completed_items'),
            'failed_items': task_data.get('failed_items'),
            'created_at': task_data.get('created_at')
        }

    return None


def _combine_tasks(import_tasks, processing_tasks, filter_type):
    """Combine tasks from different types"""
    combined = []

    # Add ImportTasks
    for task in import_tasks:
        if filter_type and filter_type != 'import':
            continue

        total_links = task.total_links or 0
        processed_links = task.processed_links or 0

        combined.append({
            'id': task.id,
            'name': task.name,
            'type': 'import',
            'status': task.status,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'progress': _calculate_import_task_progress(task),
            'total_items': total_links,
            'completed_items': processed_links,
            'failed_items': 0
        })

    # Add ProcessingTasks
    for task in processing_tasks:
        task_type = task.type if hasattr(task, 'type') and task.type else 'processing'

        if filter_type and filter_type != task_type:
            continue

        # Get values with safe defaults
        progress = task.progress if hasattr(task, 'progress') and task.progress is not None else 0
        total_items = task.total_items if hasattr(task, 'total_items') and task.total_items is not None else 0
        completed_items = task.completed_items if hasattr(task, 'completed_items') and task.completed_items is not None else 0

        # Get failed_items with safe default
        failed_items = task.failed_items if hasattr(task, 'failed_items') and task.failed_items is not None else 0

        combined.append({
            'id': task.id,
            'name': f"{task_type.title()} Task {task.id}",
            'type': task_type,
            'status': task.status if hasattr(task, 'status') else 'unknown',
            'created_at': None,  # ProcessingTask doesn't have created_at
            'started_at': task.started_at.isoformat() if hasattr(task, 'started_at') and task.started_at else None,
            'completed_at': task.completed_at.isoformat() if hasattr(task, 'completed_at') and task.completed_at else None,
            'progress': progress,
            'total_items': total_items,
            'completed_items': completed_items,
            'failed_items': failed_items
        })

    # Sort by the most recent date available (created_at, started_at, or completed_at)
    def get_sort_date(task):
        dates = [task.get('created_at'), task.get('started_at'), task.get('completed_at')]
        # Filter out None values and return the most recent, or empty string if all None
        valid_dates = [d for d in dates if d is not None]
        return max(valid_dates) if valid_dates else ''

    combined.sort(key=get_sort_date, reverse=True)

    return combined


def _calculate_import_task_progress(task):
    """Calculate progress percentage for ImportTask"""
    if task.total_links == 0:
        return 0
    return round((task.processed_links / task.total_links) * 100, 2)


def _format_task_details(task):
    """Format task details for response"""
    return {
        'id': task.get('id'),
        'name': task.get('name'),
        'type': task.get('type'),
        'status': task.get('status'),
        'config': task.get('config'),
        'progress': task.get('progress'),
        'total_items': task.get('total_items') or task.get('total_links'),
        'completed_items': task.get('completed_items') or task.get('processed_items') or task.get('processed_links'),
        'failed_items': task.get('failed_items', 0),
        'created_at': task.get('created_at'),
        'started_at': task.get('started_at'),
        'completed_at': task.get('completed_at')
    }
