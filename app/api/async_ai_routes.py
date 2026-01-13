"""
Async AI processing API routes for background AI processing
"""
from flask import Blueprint, request
from app.services.background_task_service import get_background_task_service
from app.utils.response import success_response, error_response
from app.utils.validators import validate_required
from config.workers import WorkerConfig
import logging

logger = logging.getLogger(__name__)

async_ai_bp = Blueprint('async_ai', __name__, url_prefix='/ai/async')


@async_ai_bp.route('/batch', methods=['POST'])
def process_batch_async():
    """
    Process multiple parsed contents with AI asynchronously

    Request Body:
        - parsed_content_ids: Array of ParsedContent IDs to process
        - model_id: Optional model ID (uses default if not provided)
        - processing_config: Optional processing configuration
            - generate_summary: bool (default: true)
            - generate_keywords: bool (default: true)
            - generate_insights: bool (default: false)

    Response (202):
        {
          "success": true,
          "task_id": 123,
          "total_items": 3,
          "status": "queued",
          "message": "AI processing batch queued: 3 contents"
        }
    """
    try:
        data = request.get_json()
        validate_required(data, ['parsed_content_ids'])

        parsed_content_ids = data['parsed_content_ids']
        if not isinstance(parsed_content_ids, list) or len(parsed_content_ids) == 0:
            return error_response('VAL_001', 'parsed_content_ids must be a non-empty array', None, 400)

        model_id = data.get('model_id')
        processing_config = data.get('processing_config', {})

        task_service = get_background_task_service()

        # Create background task
        task = task_service.create_task(
            type='ai_processing',
            total_items=len(parsed_content_ids),
            config={
                'parsed_content_ids': parsed_content_ids,
                'model_id': model_id,
                'processing_config': processing_config
            },
            queue_name=WorkerConfig.AI_QUEUE
        )

        # Enqueue batch dispatch job
        job_id = task_service.enqueue_job(
            task.id,  # task_id for enqueue_job
            WorkerConfig.AI_QUEUE,  # queue_name
            'app.workers.ai_worker.batch_ai_process_job',  # job_func
            # Job function arguments (positional):
            task.id,  # task_id for batch_ai_process_job
            parsed_content_ids,  # parsed_content_ids
            model_id,  # model_id
            processing_config  # processing_config
        )

        logger.info(f"Queued async AI processing task {task.id} with {len(parsed_content_ids)} contents")

        return success_response(
            data={
                'task_id': task.id,
                'job_id': job_id,
                'total_items': len(parsed_content_ids),
                'status': 'queued'
            },
            message=f'AI processing batch queued: {len(parsed_content_ids)} contents',
            status=202
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Failed to queue batch AI processing: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to queue batch: {str(e)}', None, 500)


@async_ai_bp.route('/single/<int:parsed_content_id>', methods=['POST'])
def process_single_async(parsed_content_id):
    """
    Process single parsed content with AI asynchronously

    Path Parameters:
        parsed_content_id: ParsedContent ID to process

    Request Body:
        - model_id: Optional model ID (uses default if not provided)
        - processing_config: Optional processing configuration

    Response (202):
        {
          "success": true,
          "task_id": 124,
          "parsed_content_id": 5,
          "status": "queued",
          "job_id": "rq-job-uuid"
        }
    """
    try:
        data = request.get_json() or {}
        model_id = data.get('model_id')
        processing_config = data.get('processing_config', {})

        task_service = get_background_task_service()

        # Create task for single content
        task = task_service.create_task(
            type='ai_processing',
            total_items=1,
            config={
                'parsed_content_id': parsed_content_id,
                'model_id': model_id,
                'processing_config': processing_config
            },
            queue_name=WorkerConfig.AI_QUEUE
        )

        # Create task item
        task_service.create_task_item(
            task_id=task.id,
            item_id=parsed_content_id,
            item_type='parsed_content'
        )

        # Enqueue processing job
        job_id = task_service.enqueue_job(
            task.id,  # task_id for enqueue_job
            WorkerConfig.AI_QUEUE,  # queue_name
            'app.workers.ai_worker.process_ai_content_job',  # job_func
            # Job function arguments (positional):
            task.id,  # task_id for process_ai_content_job
            parsed_content_id,  # parsed_content_id
            model_id,  # model_id
            processing_config  # processing_config
        )

        return success_response(
            data={
                'task_id': task.id,
                'job_id': job_id,
                'parsed_content_id': parsed_content_id,
                'status': 'queued'
            },
            message=f'AI processing queued for parsed content {parsed_content_id}',
            status=202
        )

    except Exception as e:
        logger.error(f"Failed to queue AI processing for parsed content {parsed_content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to queue AI processing: {str(e)}', None, 500)


@async_ai_bp.route('/status/<int:task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Get AI processing task status and progress

    Path Parameters:
        task_id: ProcessingTask ID

    Query Parameters:
        include_items: Include item details (default: false)

    Response (200):
        {
          "success": true,
          "task": {
            "id": 123,
            "type": "ai_processing",
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


@async_ai_bp.route('/cancel/<int:task_id>', methods=['DELETE'])
def cancel_task(task_id):
    """
    Cancel running AI processing task

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


@async_ai_bp.route('/retry/<int:task_id>', methods=['POST'])
def retry_failed(task_id):
    """
    Retry failed items in an AI processing task

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
            queue_name=WorkerConfig.AI_QUEUE,
            job_func='app.workers.ai_worker.process_ai_content_job'
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
