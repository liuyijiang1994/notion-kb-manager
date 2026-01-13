"""
Async Notion import API routes for background Notion imports
"""
from flask import Blueprint, request
from app.services.background_task_service import get_background_task_service
from app.utils.response import success_response, error_response
from app.utils.validators import validate_required
from config.workers import WorkerConfig
import logging

logger = logging.getLogger(__name__)

async_notion_bp = Blueprint('async_notion', __name__, url_prefix='/notion/async')


@async_notion_bp.route('/batch', methods=['POST'])
def import_batch_async():
    """
    Import multiple AI contents to Notion asynchronously

    Request Body:
        - ai_content_ids: Array of AIProcessedContent IDs to import
        - database_id: Target Notion database ID
        - properties: Optional additional properties for Notion pages

    Response (202):
        {
          "success": true,
          "task_id": 123,
          "total_items": 3,
          "status": "queued",
          "message": "Notion import batch queued: 3 contents"
        }
    """
    try:
        data = request.get_json()
        validate_required(data, ['ai_content_ids', 'database_id'])

        ai_content_ids = data['ai_content_ids']
        if not isinstance(ai_content_ids, list) or len(ai_content_ids) == 0:
            return error_response('VAL_001', 'ai_content_ids must be a non-empty array', None, 400)

        database_id = data['database_id']
        properties = data.get('properties', {})

        task_service = get_background_task_service()

        # Create background task (using ImportNotionTask)
        task = task_service.create_notion_task(
            type='import',
            total_items=len(ai_content_ids),
            config={
                'ai_content_ids': ai_content_ids,
                'database_id': database_id,
                'properties': properties
            },
            queue_name=WorkerConfig.NOTION_QUEUE
        )

        # Enqueue batch dispatch job
        job_id = task_service.enqueue_job(
            task.id,  # task_id for enqueue_job
            WorkerConfig.NOTION_QUEUE,  # queue_name
            'app.workers.notion_worker.batch_notion_import_job',  # job_func
            # Job function arguments (positional):
            task.id,  # task_id for batch_notion_import_job
            ai_content_ids,  # ai_content_ids
            database_id,  # database_id
            properties  # properties
        )

        logger.info(f"Queued async Notion import task {task.id} with {len(ai_content_ids)} contents")

        return success_response(
            data={
                'task_id': task.id,
                'job_id': job_id,
                'total_items': len(ai_content_ids),
                'status': 'queued'
            },
            message=f'Notion import batch queued: {len(ai_content_ids)} contents',
            status=202
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Failed to queue batch Notion import: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to queue batch: {str(e)}', None, 500)


@async_notion_bp.route('/single/<int:ai_content_id>', methods=['POST'])
def import_single_async(ai_content_id):
    """
    Import single AI content to Notion asynchronously

    Path Parameters:
        ai_content_id: AIProcessedContent ID to import

    Request Body:
        - database_id: Target Notion database ID
        - properties: Optional additional properties for Notion page

    Response (202):
        {
          "success": true,
          "task_id": 124,
          "ai_content_id": 5,
          "status": "queued",
          "job_id": "rq-job-uuid"
        }
    """
    try:
        data = request.get_json()
        validate_required(data, ['database_id'])

        database_id = data['database_id']
        properties = data.get('properties', {})

        task_service = get_background_task_service()

        # Create task for single import
        task = task_service.create_notion_task(
            type='import',
            total_items=1,
            config={
                'ai_content_id': ai_content_id,
                'database_id': database_id,
                'properties': properties
            },
            queue_name=WorkerConfig.NOTION_QUEUE
        )

        # Create task item
        task_service.create_task_item(
            task_id=task.id,
            item_id=ai_content_id,
            item_type='ai_content'
        )

        # Enqueue import job
        job_id = task_service.enqueue_job(
            task.id,  # task_id for enqueue_job
            WorkerConfig.NOTION_QUEUE,  # queue_name
            'app.workers.notion_worker.import_to_notion_job',  # job_func
            # Job function arguments (positional):
            task.id,  # task_id for import_to_notion_job
            ai_content_id,  # ai_content_id
            database_id,  # database_id
            properties  # properties
        )

        return success_response(
            data={
                'task_id': task.id,
                'job_id': job_id,
                'ai_content_id': ai_content_id,
                'status': 'queued'
            },
            message=f'Notion import queued for AI content {ai_content_id}',
            status=202
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Failed to queue Notion import for AI content {ai_content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to queue Notion import: {str(e)}', None, 500)


@async_notion_bp.route('/status/<int:task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Get Notion import task status and progress

    Path Parameters:
        task_id: ImportNotionTask ID

    Query Parameters:
        include_items: Include item details (default: false)

    Response (200):
        {
          "success": true,
          "task": {
            "id": 123,
            "type": "import",
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

        # Note: get_task_status works for both ProcessingTask and ImportNotionTask
        # since they share the same structure
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


@async_notion_bp.route('/cancel/<int:task_id>', methods=['DELETE'])
def cancel_task(task_id):
    """
    Cancel running Notion import task

    Path Parameters:
        task_id: ImportNotionTask ID

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


@async_notion_bp.route('/retry/<int:task_id>', methods=['POST'])
def retry_failed(task_id):
    """
    Retry failed items in a Notion import task

    Path Parameters:
        task_id: ImportNotionTask ID

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
            queue_name=WorkerConfig.NOTION_QUEUE,
            job_func='app.workers.notion_worker.import_to_notion_job'
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
