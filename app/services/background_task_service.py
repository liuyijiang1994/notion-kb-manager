"""
Background task service for managing RQ job lifecycle
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from redis import Redis
from rq import Queue, Retry
from rq.job import Job
from flask import current_app
from app.models.content import ProcessingTask, TaskItem
from app.models.notion import ImportNotionTask
from app import db
from config.workers import WorkerConfig

logger = logging.getLogger(__name__)


class BackgroundTaskService:
    """Service for managing background task lifecycle"""

    def __init__(self):
        self.redis_conn = None
        self.queues = {}

    def _get_redis_connection(self) -> Redis:
        """Get or create Redis connection"""
        if self.redis_conn is None:
            redis_url = current_app.config.get('REDIS_URL', WorkerConfig.REDIS_URL)
            self.redis_conn = Redis.from_url(redis_url)
        return self.redis_conn

    def _get_queue(self, queue_name: str) -> Queue:
        """Get or create RQ queue"""
        if queue_name not in self.queues:
            redis_conn = self._get_redis_connection()
            self.queues[queue_name] = Queue(queue_name, connection=redis_conn)
        return self.queues[queue_name]

    def create_task(self, type: str, total_items: int,
                   config: Optional[Dict[str, Any]] = None,
                   queue_name: Optional[str] = None) -> ProcessingTask:
        """
        Create new background task

        Args:
            type: Task type (parsing/ai_processing)
            total_items: Total number of items to process
            config: Task configuration
            queue_name: Queue to use for this task

        Returns:
            Created ProcessingTask object
        """
        task = ProcessingTask(
            type=type,
            status='pending',
            progress=0,
            total_items=total_items,
            completed_items=0,
            failed_items=0,
            config=config or {},
            queue_name=queue_name,
            error_log=[]
        )

        db.session.add(task)
        db.session.commit()

        logger.info(f"Created background task {task.id} (type={type}, items={total_items})")
        return task

    def create_notion_task(self, type: str, total_items: int,
                          config: Optional[Dict[str, Any]] = None,
                          queue_name: Optional[str] = None) -> ImportNotionTask:
        """
        Create new Notion import task

        Args:
            type: Task type (import/sync)
            total_items: Total number of items to import
            config: Task configuration
            queue_name: Queue to use for this task

        Returns:
            Created ImportNotionTask object
        """
        task = ImportNotionTask(
            type=type,
            status='pending',
            progress=0,
            total_items=total_items,
            completed_items=0,
            failed_items=0,
            config=config or {},
            queue_name=queue_name
        )

        db.session.add(task)
        db.session.commit()

        logger.info(f"Created Notion task {task.id} (type={type}, items={total_items})")
        return task

    def enqueue_job(self, task_id: int, queue_name: str,
                   job_func: str, *args, **kwargs) -> str:
        """
        Enqueue job to RQ

        Args:
            task_id: ProcessingTask ID
            queue_name: Queue name
            job_func: Full path to job function (e.g. 'app.workers.parsing_worker.parse_content_job')
            *args: Job arguments
            **kwargs: Job keyword arguments

        Returns:
            RQ job ID
        """
        queue = self._get_queue(queue_name)
        queue_config = WorkerConfig.get_queue_config(queue_name)

        # Set up retry policy
        retry = Retry(max=WorkerConfig.MAX_RETRIES, interval=WorkerConfig.RETRY_DELAYS)

        # Enqueue job
        job = queue.enqueue(
            job_func,
            *args,
            job_timeout=queue_config['timeout'],
            result_ttl=queue_config['result_ttl'],
            retry=retry
        )

        # Update task with job info
        task = db.session.query(ProcessingTask).get(task_id)
        if task:
            task.job_id = job.id
            task.status = 'queued'
            db.session.commit()

        logger.info(f"Enqueued job {job.id} for task {task_id} in queue {queue_name}")
        return job.id

    def create_task_item(self, task_id: int, item_id: int,
                        item_type: str, job_id: Optional[str] = None) -> TaskItem:
        """
        Create task item for tracking

        Args:
            task_id: ProcessingTask ID
            item_id: ID of item (link_id, parsed_content_id, ai_content_id)
            item_type: Type of item ('link', 'parsed_content', 'ai_content')
            job_id: Optional RQ job ID

        Returns:
            Created TaskItem object
        """
        item = TaskItem(
            task_id=task_id,
            item_id=item_id,
            item_type=item_type,
            status='pending',
            job_id=job_id,
            retry_count=0
        )

        db.session.add(item)
        db.session.commit()

        return item

    def update_item_status(self, task_id: int, item_id: int,
                          status: str, job_id: Optional[str] = None,
                          error_message: Optional[str] = None,
                          result_data: Optional[Dict] = None):
        """
        Update task item status

        Args:
            task_id: ProcessingTask ID
            item_id: Item ID
            status: New status ('pending', 'running', 'completed', 'failed')
            job_id: Optional job ID
            error_message: Optional error message
            result_data: Optional result data
        """
        item = db.session.query(TaskItem).filter_by(
            task_id=task_id,
            item_id=item_id
        ).first()

        if not item:
            logger.warning(f"TaskItem not found: task_id={task_id}, item_id={item_id}")
            return

        item.status = status

        if job_id:
            item.job_id = job_id

        if status == 'running':
            item.started_at = datetime.utcnow()
        elif status in ('completed', 'failed'):
            item.completed_at = datetime.utcnow()

        if error_message:
            item.error_message = error_message

        if result_data:
            item.result_data = result_data

        if status == 'failed':
            item.retry_count += 1

        db.session.commit()

    def update_task_progress(self, task_id: int):
        """
        Recalculate task progress from items

        Args:
            task_id: ProcessingTask ID
        """
        task = db.session.query(ProcessingTask).get(task_id)
        if not task:
            return

        # Count items by status
        items = db.session.query(TaskItem).filter_by(task_id=task_id).all()

        completed = sum(1 for item in items if item.status == 'completed')
        failed = sum(1 for item in items if item.status == 'failed')
        running = sum(1 for item in items if item.status == 'running')

        task.completed_items = completed
        task.failed_items = failed

        # Calculate progress percentage
        if task.total_items > 0:
            task.progress = int((completed + failed) / task.total_items * 100)
        else:
            task.progress = 0

        # Update task status
        if completed + failed == task.total_items:
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
        elif running > 0 or completed > 0:
            if task.status == 'pending' or task.status == 'queued':
                task.status = 'running'
                task.started_at = datetime.utcnow()

        db.session.commit()

        logger.debug(f"Updated task {task_id} progress: {task.progress}% ({completed}/{task.total_items})")

    def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Get complete task status with items

        Args:
            task_id: ProcessingTask ID

        Returns:
            Dict with task status and items, or None if not found
        """
        task = db.session.query(ProcessingTask).get(task_id)
        if not task:
            return None

        items = db.session.query(TaskItem).filter_by(task_id=task_id).all()

        return {
            'id': task.id,
            'type': task.type,
            'status': task.status,
            'progress': task.progress,
            'total_items': task.total_items,
            'completed_items': task.completed_items,
            'failed_items': task.failed_items,
            'queue_name': task.queue_name,
            'job_id': task.job_id,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'items': [
                {
                    'item_id': item.item_id,
                    'item_type': item.item_type,
                    'status': item.status,
                    'job_id': item.job_id,
                    'retry_count': item.retry_count,
                    'error_message': item.error_message,
                    'started_at': item.started_at.isoformat() if item.started_at else None,
                    'completed_at': item.completed_at.isoformat() if item.completed_at else None,
                }
                for item in items
            ]
        }

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get RQ job status

        Args:
            job_id: RQ job ID

        Returns:
            Dict with job status, or None if not found
        """
        try:
            redis_conn = self._get_redis_connection()
            job = Job.fetch(job_id, connection=redis_conn)

            return {
                'job_id': job.id,
                'status': job.get_status(),
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'ended_at': job.ended_at.isoformat() if job.ended_at else None,
                'result': job.result,
                'exc_info': job.exc_info,
            }
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None

    def cancel_task(self, task_id: int) -> bool:
        """
        Cancel running task

        Args:
            task_id: ProcessingTask ID

        Returns:
            True if cancelled, False otherwise
        """
        task = db.session.query(ProcessingTask).get(task_id)
        if not task:
            return False

        # Cancel all pending/running items
        items = db.session.query(TaskItem).filter_by(task_id=task_id).filter(
            TaskItem.status.in_(['pending', 'running'])
        ).all()

        for item in items:
            if item.job_id:
                try:
                    redis_conn = self._get_redis_connection()
                    job = Job.fetch(item.job_id, connection=redis_conn)
                    job.cancel()
                except Exception as e:
                    logger.error(f"Failed to cancel job {item.job_id}: {e}")

            item.status = 'failed'
            item.error_message = 'Cancelled by user'
            item.completed_at = datetime.utcnow()

        # Update task status
        task.status = 'failed'
        task.completed_at = datetime.utcnow()
        db.session.commit()

        logger.info(f"Cancelled task {task_id}")
        return True

    def retry_failed_items(self, task_id: int, queue_name: str,
                          job_func: str) -> int:
        """
        Retry only failed items in a task

        Args:
            task_id: ProcessingTask ID
            queue_name: Queue name
            job_func: Job function path

        Returns:
            Number of items requeued
        """
        failed_items = db.session.query(TaskItem).filter_by(
            task_id=task_id,
            status='failed'
        ).all()

        count = 0
        queue = self._get_queue(queue_name)
        queue_config = WorkerConfig.get_queue_config(queue_name)

        for item in failed_items:
            if item.retry_count >= WorkerConfig.MAX_RETRIES:
                logger.info(f"Skipping item {item.item_id} - max retries reached")
                continue

            # Re-enqueue job
            job = queue.enqueue(
                job_func,
                task_id=task_id,
                link_id=item.item_id,  # Adjust based on item_type
                timeout=queue_config['timeout']
            )

            # Reset item status
            item.status = 'pending'
            item.job_id = job.id
            item.error_message = None
            count += 1

        # Reset task status
        task = db.session.query(ProcessingTask).get(task_id)
        if task and count > 0:
            task.status = 'queued'
            task.completed_at = None

        db.session.commit()

        logger.info(f"Requeued {count} failed items for task {task_id}")
        return count

    def get_task_items(self, task_id: int,
                      status: Optional[str] = None) -> List[TaskItem]:
        """
        Get task items, optionally filtered by status

        Args:
            task_id: ProcessingTask ID
            status: Optional status filter

        Returns:
            List of TaskItem objects
        """
        query = db.session.query(TaskItem).filter_by(task_id=task_id)

        if status:
            query = query.filter_by(status=status)

        return query.all()


# Singleton instance
_background_task_service = None


def get_background_task_service() -> BackgroundTaskService:
    """Get singleton instance of BackgroundTaskService"""
    global _background_task_service
    if _background_task_service is None:
        _background_task_service = BackgroundTaskService()
    return _background_task_service
