"""
Async parsing API routes for background processing
"""
from flask import Blueprint, request
from app.services.background_task_service import get_background_task_service
from app.utils.response import success_response, error_response
from app.utils.validators import validate_required
from config.workers import WorkerConfig
import logging

logger = logging.getLogger(__name__)

async_parsing_bp = Blueprint('async_parsing', __name__, url_prefix='/parsing/async')


@async_parsing_bp.route('/batch', methods=['POST'])
def parse_batch_async():
    """
    Parse multiple links asynchronously

    Request Body:
        - link_ids: Array of link IDs to parse

    Response (202):
        {
          "success": true,
          "task_id": 123,
          "total_items": 3,
          "status": "queued",
          "message": "Parsing batch queued: 3 links"
        }
    """
    try:
        data = request.get_json()
        validate_required(data, ['link_ids'])

        link_ids = data['link_ids']
        if not isinstance(link_ids, list) or len(link_ids) == 0:
            return error_response('VAL_001', 'link_ids must be a non-empty array', None, 400)

        task_service = get_background_task_service()

        # Create background task
        task = task_service.create_task(
            type='parsing',
            total_items=len(link_ids),
            config={'link_ids': link_ids},
            queue_name=WorkerConfig.PARSING_QUEUE
        )

        # Enqueue batch dispatch job
        job_id = task_service.enqueue_job(
            task.id,  # task_id for enqueue_job
            WorkerConfig.PARSING_QUEUE,  # queue_name
            'app.workers.parsing_worker.batch_parse_job',  # job_func
            # Job function arguments (positional via *args):
            task.id,  # task_id for batch_parse_job
            link_ids   # link_ids for batch_parse_job
        )

        logger.info(f"Queued async parsing task {task.id} with {len(link_ids)} links")

        return success_response(
            data={
                'task_id': task.id,
                'job_id': job_id,
                'total_items': len(link_ids),
                'status': 'queued'
            },
            message=f'Parsing batch queued: {len(link_ids)} links',
            status=202
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Failed to queue batch parsing: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to queue batch: {str(e)}', None, 500)


@async_parsing_bp.route('/single/<int:link_id>', methods=['POST'])
def parse_single_async(link_id):
    """
    Parse single link asynchronously

    Path Parameters:
        link_id: Link ID to parse

    Response (202):
        {
          "success": true,
          "task_id": 124,
          "link_id": 5,
          "status": "queued",
          "job_id": "rq-job-uuid"
        }
    """
    try:
        task_service = get_background_task_service()

        # Create task for single link
        task = task_service.create_task(
            type='parsing',
            total_items=1,
            config={'link_id': link_id},
            queue_name=WorkerConfig.PARSING_QUEUE
        )

        # Create task item
        task_service.create_task_item(
            task_id=task.id,
            item_id=link_id,
            item_type='link'
        )

        # Enqueue parse job
        job_id = task_service.enqueue_job(
            task.id,  # task_id for enqueue_job
            WorkerConfig.PARSING_QUEUE,  # queue_name
            'app.workers.parsing_worker.parse_content_job',  # job_func
            # Job function arguments (positional via *args):
            task.id,  # task_id for parse_content_job
            link_id    # link_id for parse_content_job
        )

        return success_response(
            data={
                'task_id': task.id,
                'job_id': job_id,
                'link_id': link_id,
                'status': 'queued'
            },
            message=f'Parsing queued for link {link_id}',
            status=202
        )

    except Exception as e:
        logger.error(f"Failed to queue parsing for link {link_id}: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to queue parsing: {str(e)}', None, 500)


@async_parsing_bp.route('/status/<int:task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Get task status and progress

    Path Parameters:
        task_id: ProcessingTask ID

    Query Parameters:
        include_items: Include item details (default: false)

    Response (200):
        {
          "success": true,
          "task": {
            "id": 123,
            "type": "parsing",
            "status": "running",
            "progress": 66,
            "completed_items": 2,
            "failed_items": 0,
            "total_items": 3,
            "started_at": "2026-01-13T10:00:00",
            "items": [...]  // If include_items=true
          }
        }
    """
    try:
        include_items = request.args.get('include_items', 'false').lower() == 'true'

        task_service = get_background_task_service()
        status = task_service.get_task_status(task_id)

        if not status:
            return error_response('RES_001', f'Task {task_id} not found', None, 404)

        # Remove items if not requested
        if not include_items:
            status.pop('items', None)

        return success_response(data={'task': status})

    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get status: {str(e)}', None, 500)


@async_parsing_bp.route('/cancel/<int:task_id>', methods=['DELETE'])
def cancel_task(task_id):
    """
    Cancel running task

    Path Parameters:
        task_id: ProcessingTask ID

    Response (200):
        {
          "success": true,
          "message": "Task 123 cancelled"
        }
    """
    try:
        task_service = get_background_task_service()
        cancelled = task_service.cancel_task(task_id)

        if not cancelled:
            return error_response('RES_001', f'Task {task_id} not found', None, 404)

        return success_response(
            data={'task_id': task_id},
            message=f'Task {task_id} cancelled'
        )

    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to cancel task: {str(e)}', None, 500)


@async_parsing_bp.route('/retry/<int:task_id>', methods=['POST'])
def retry_failed(task_id):
    """
    Retry failed items in a task

    Path Parameters:
        task_id: ProcessingTask ID

    Response (200):
        {
          "success": true,
          "task_id": 123,
          "retried_count": 2,
          "message": "Retrying 2 failed items"
        }
    """
    try:
        task_service = get_background_task_service()

        # Retry failed items
        count = task_service.retry_failed_items(
            task_id=task_id,
            queue_name=WorkerConfig.PARSING_QUEUE,
            job_func='app.workers.parsing_worker.parse_content_job'
        )

        if count == 0:
            return success_response(
                data={'task_id': task_id, 'retried_count': 0},
                message='No failed items to retry'
            )

        return success_response(
            data={'task_id': task_id, 'retried_count': count},
            message=f'Retrying {count} failed items'
        )

    except Exception as e:
        logger.error(f"Failed to retry task {task_id}: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to retry: {str(e)}', None, 500)
