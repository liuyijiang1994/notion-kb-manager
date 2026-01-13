"""
Notion import worker for background Notion import jobs
"""
import logging
from rq import get_current_job
from flask import Flask
from app import create_app
from app.services.notion_import_service import get_notion_import_service
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


def import_to_notion_job(task_id: int, ai_content_id: int,
                        database_id: str, properties: dict = None):
    """
    Import single AI content to Notion as background job

    Args:
        task_id: ProcessingTask ID (or ImportNotionTask ID)
        ai_content_id: AIProcessedContent ID to import
        database_id: Target Notion database ID
        properties: Optional additional properties for Notion page

    Returns:
        Dict with import result
    """
    # Get Flask app context
    flask_app = get_app()

    with flask_app.app_context():
        job = get_current_job()
        task_service = get_background_task_service()
        notion_service = get_notion_import_service()

        logger.info(f"Starting Notion import job for ai_content {ai_content_id} (task={task_id}, job={job.id})")

        try:
            # Update item status to running
            task_service.update_item_status(
                task_id=task_id,
                item_id=ai_content_id,
                status='running',
                job_id=job.id
            )

            # Perform Notion import
            result = notion_service.import_to_notion(
                ai_content_id=ai_content_id,
                database_id=database_id,
                properties=properties or {}
            )

            # Update result based on success/failure
            if result.get('success'):
                task_service.update_item_status(
                    task_id=task_id,
                    item_id=ai_content_id,
                    status='completed',
                    result_data=result
                )
                logger.info(f"Successfully imported ai_content {ai_content_id} to Notion")
            else:
                task_service.update_item_status(
                    task_id=task_id,
                    item_id=ai_content_id,
                    status='failed',
                    error_message=result.get('error', 'Unknown error'),
                    result_data=result
                )
                logger.error(f"Failed to import ai_content {ai_content_id}: {result.get('error')}")

            # Update overall task progress
            task_service.update_task_progress(task_id)

            return result

        except Exception as e:
            logger.error(f"Notion import job exception for ai_content {ai_content_id}: {e}", exc_info=True)

            # Update item status to failed
            task_service.update_item_status(
                task_id=task_id,
                item_id=ai_content_id,
                status='failed',
                error_message=str(e)
            )

            # Update task progress
            task_service.update_task_progress(task_id)

            # Re-raise for RQ to handle retry
            raise


def batch_notion_import_job(task_id: int, ai_content_ids: list,
                           database_id: str, properties: dict = None):
    """
    Batch import multiple AI contents to Notion (dispatches individual jobs)

    This is a coordinator job that creates individual Notion import jobs
    for each AI content in the batch.

    Args:
        task_id: ProcessingTask ID (or ImportNotionTask ID)
        ai_content_ids: List of AIProcessedContent IDs to import
        database_id: Target Notion database ID
        properties: Optional additional properties for Notion pages

    Returns:
        Dict with batch dispatch result
    """
    flask_app = get_app()

    with flask_app.app_context():
        from app.workers import get_queue
        from config.workers import WorkerConfig

        task_service = get_background_task_service()
        queue = get_queue(WorkerConfig.NOTION_QUEUE)

        logger.info(f"Dispatching batch Notion import for task {task_id}: {len(ai_content_ids)} contents")

        job_ids = []
        for ai_content_id in ai_content_ids:
            # Create task item
            task_service.create_task_item(
                task_id=task_id,
                item_id=ai_content_id,
                item_type='ai_content'
            )

            # Enqueue individual Notion import job
            job = queue.enqueue(
                'app.workers.notion_worker.import_to_notion_job',
                task_id=task_id,
                ai_content_id=ai_content_id,
                database_id=database_id,
                properties=properties,
                timeout=WorkerConfig.NOTION_TIMEOUT
            )

            job_ids.append(job.id)

            # Update task item with job ID
            task_service.update_item_status(
                task_id=task_id,
                item_id=ai_content_id,
                status='queued',
                job_id=job.id
            )

        logger.info(f"Dispatched {len(job_ids)} Notion import jobs for task {task_id}")

        return {
            'success': True,
            'task_id': task_id,
            'total_jobs': len(job_ids),
            'job_ids': job_ids
        }
