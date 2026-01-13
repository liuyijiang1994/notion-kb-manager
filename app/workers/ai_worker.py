"""
AI processing worker for background AI content processing jobs
"""
import logging
from rq import get_current_job
from flask import Flask
from app import create_app
from app.services.ai_processing_service import get_ai_processing_service
from app.services.background_task_service import get_background_task_service

logger = logging.getLogger(__name__)

# Flask app context for worker
app: Flask = None


def get_app() -> Flask:
    """Get or create Flask app for worker"""
    global app
    if app is None:
        app = create_app()
    return app


def process_ai_content_job(task_id: int, parsed_content_id: int,
                          model_id: int = None, processing_config: dict = None):
    """
    Process single parsed content with AI as background job

    Args:
        task_id: ProcessingTask ID
        parsed_content_id: ParsedContent ID to process
        model_id: Optional model ID (uses default if not provided)
        processing_config: Optional processing configuration

    Returns:
        Dict with processing result
    """
    # Get Flask app context
    flask_app = get_app()

    with flask_app.app_context():
        job = get_current_job()
        task_service = get_background_task_service()
        ai_service = get_ai_processing_service()

        logger.info(f"Starting AI processing job for parsed_content {parsed_content_id} (task={task_id}, job={job.id})")

        try:
            # Update item status to running
            task_service.update_item_status(
                task_id=task_id,
                item_id=parsed_content_id,
                status='running',
                job_id=job.id
            )

            # Perform AI processing
            result = ai_service.process_content(
                parsed_content_id=parsed_content_id,
                model_id=model_id,
                processing_config=processing_config or {}
            )

            # Update result based on success/failure
            if result.get('success'):
                task_service.update_item_status(
                    task_id=task_id,
                    item_id=parsed_content_id,
                    status='completed',
                    result_data=result
                )
                logger.info(f"Successfully processed parsed_content {parsed_content_id} with AI")
            else:
                task_service.update_item_status(
                    task_id=task_id,
                    item_id=parsed_content_id,
                    status='failed',
                    error_message=result.get('error', 'Unknown error'),
                    result_data=result
                )
                logger.error(f"Failed to process parsed_content {parsed_content_id}: {result.get('error')}")

            # Update overall task progress
            task_service.update_task_progress(task_id)

            return result

        except Exception as e:
            logger.error(f"AI processing job exception for parsed_content {parsed_content_id}: {e}", exc_info=True)

            # Update item status to failed
            task_service.update_item_status(
                task_id=task_id,
                item_id=parsed_content_id,
                status='failed',
                error_message=str(e)
            )

            # Update task progress
            task_service.update_task_progress(task_id)

            # Re-raise for RQ to handle retry
            raise


def batch_ai_process_job(task_id: int, parsed_content_ids: list,
                        model_id: int = None, processing_config: dict = None):
    """
    Batch AI process multiple parsed contents (dispatches individual jobs)

    This is a coordinator job that creates individual AI processing jobs
    for each parsed content in the batch.

    Args:
        task_id: ProcessingTask ID
        parsed_content_ids: List of ParsedContent IDs to process
        model_id: Optional model ID (uses default if not provided)
        processing_config: Optional processing configuration

    Returns:
        Dict with batch dispatch result
    """
    flask_app = get_app()

    with flask_app.app_context():
        from app.workers import get_queue
        from config.workers import WorkerConfig

        task_service = get_background_task_service()
        queue = get_queue(WorkerConfig.AI_QUEUE)

        logger.info(f"Dispatching batch AI processing for task {task_id}: {len(parsed_content_ids)} contents")

        job_ids = []
        for parsed_content_id in parsed_content_ids:
            # Create task item
            task_service.create_task_item(
                task_id=task_id,
                item_id=parsed_content_id,
                item_type='parsed_content'
            )

            # Enqueue individual AI processing job
            job = queue.enqueue(
                'app.workers.ai_worker.process_ai_content_job',
                task_id=task_id,
                parsed_content_id=parsed_content_id,
                model_id=model_id,
                processing_config=processing_config,
                timeout=WorkerConfig.AI_TIMEOUT
            )

            job_ids.append(job.id)

            # Update task item with job ID
            task_service.update_item_status(
                task_id=task_id,
                item_id=parsed_content_id,
                status='queued',
                job_id=job.id
            )

        logger.info(f"Dispatched {len(job_ids)} AI processing jobs for task {task_id}")

        return {
            'success': True,
            'task_id': task_id,
            'total_jobs': len(job_ids),
            'job_ids': job_ids
        }
