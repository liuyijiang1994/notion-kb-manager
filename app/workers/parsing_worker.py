"""
Parsing worker for background content parsing jobs
"""
import logging
from rq import get_current_job
from flask import Flask
from app import create_app
from app.services.content_parsing_service import get_content_parsing_service
from app.services.background_task_service import get_background_task_service

logger = logging.getLogger(__name__)

# Flask app context for worker
app: Flask = None


def get_app() -> Flask:
    """Get or create Flask app for worker"""
    global app
    if app is None:
        import os
        config_name = os.getenv('FLASK_ENV', 'development')
        app = create_app(config_name)
    return app


def parse_content_job(task_id: int, link_id: int, **kwargs):
    """
    Parse single link as background job

    Args:
        task_id: ProcessingTask ID
        link_id: Link ID to parse
        **kwargs: Additional RQ parameters (ignored)

    Returns:
        Dict with parsing result
    """
    # Get Flask app context
    flask_app = get_app()

    with flask_app.app_context():
        job = get_current_job()
        task_service = get_background_task_service()
        parsing_service = get_content_parsing_service()

        logger.info(f"Starting parse job for link {link_id} (task={task_id}, job={job.id})")

        try:
            # Update item status to running
            task_service.update_item_status(
                task_id=task_id,
                item_id=link_id,
                status='running',
                job_id=job.id
            )

            # Perform parsing
            result = parsing_service.fetch_and_parse(link_id)

            # Update result based on success/failure
            if result.get('success'):
                task_service.update_item_status(
                    task_id=task_id,
                    item_id=link_id,
                    status='completed',
                    result_data=result
                )
                logger.info(f"Successfully parsed link {link_id}")
            else:
                task_service.update_item_status(
                    task_id=task_id,
                    item_id=link_id,
                    status='failed',
                    error_message=result.get('error', 'Unknown error'),
                    result_data=result
                )
                logger.error(f"Failed to parse link {link_id}: {result.get('error')}")

            # Update overall task progress
            task_service.update_task_progress(task_id)

            return result

        except Exception as e:
            logger.error(f"Parse job exception for link {link_id}: {e}", exc_info=True)

            # Update item status to failed
            task_service.update_item_status(
                task_id=task_id,
                item_id=link_id,
                status='failed',
                error_message=str(e)
            )

            # Update task progress
            task_service.update_task_progress(task_id)

            # Re-raise for RQ to handle retry
            raise


def batch_parse_job(task_id: int, link_ids: list, **kwargs):
    """
    Batch parse multiple links (dispatches individual jobs)

    This is a coordinator job that creates individual parse jobs
    for each link in the batch.

    Args:
        task_id: ProcessingTask ID
        link_ids: List of link IDs to parse
        **kwargs: Additional RQ parameters (ignored)

    Returns:
        Dict with batch dispatch result
    """
    flask_app = get_app()

    with flask_app.app_context():
        from app.workers import get_queue
        from config.workers import WorkerConfig

        task_service = get_background_task_service()
        queue = get_queue(WorkerConfig.PARSING_QUEUE)

        logger.info(f"Dispatching batch parse for task {task_id}: {len(link_ids)} links")

        job_ids = []
        for link_id in link_ids:
            # Create task item
            task_service.create_task_item(
                task_id=task_id,
                item_id=link_id,
                item_type='link'
            )

            # Enqueue individual parse job
            job = queue.enqueue(
                'app.workers.parsing_worker.parse_content_job',
                task_id,
                link_id,
                job_timeout=WorkerConfig.PARSING_TIMEOUT
            )

            job_ids.append(job.id)

            # Update task item with job ID
            task_service.update_item_status(
                task_id=task_id,
                item_id=link_id,
                status='queued',
                job_id=job.id
            )

        logger.info(f"Dispatched {len(job_ids)} parse jobs for task {task_id}")

        return {
            'success': True,
            'task_id': task_id,
            'total_jobs': len(job_ids),
            'job_ids': job_ids
        }
