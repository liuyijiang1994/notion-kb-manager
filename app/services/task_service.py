"""Task management service for import and processing tasks"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.link import ImportTask, Link
from app import db

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing import and processing tasks"""

    def create_import_task(self, name: str, config: Optional[Dict[str, Any]] = None) -> ImportTask:
        """
        Create a new import task

        Args:
            name: Task name
            config: Task configuration (processing scope, parameters)

        Returns:
            Created ImportTask object
        """
        try:
            task = ImportTask(
                name=name,
                status='pending',
                total_links=0,
                processed_links=0,
                config=config or {}
            )

            db.session.add(task)
            db.session.commit()

            logger.info(f"Created import task: {task.id} - {task.name}")
            return task

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create import task: {e}", exc_info=True)
            raise

    def get_task(self, task_id: int) -> Optional[ImportTask]:
        """
        Get task by ID

        Args:
            task_id: Task ID

        Returns:
            ImportTask object or None
        """
        return db.session.query(ImportTask).get(task_id)

    def get_all_tasks(self, status: Optional[str] = None, limit: Optional[int] = None) -> List[ImportTask]:
        """
        Get all import tasks with optional filtering

        Args:
            status: Filter by status (pending/running/completed/failed)
            limit: Limit number of results

        Returns:
            List of ImportTask objects
        """
        query = db.session.query(ImportTask)

        if status:
            query = query.filter_by(status=status)

        query = query.order_by(ImportTask.created_at.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def update_task_status(self, task_id: int, status: str,
                          total_links: Optional[int] = None,
                          processed_links: Optional[int] = None) -> Optional[ImportTask]:
        """
        Update task status and progress

        Args:
            task_id: Task ID
            status: New status
            total_links: Total links count (optional)
            processed_links: Processed links count (optional)

        Returns:
            Updated ImportTask object or None
        """
        try:
            task = db.session.query(ImportTask).get(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found")
                return None

            task.status = status

            if total_links is not None:
                task.total_links = total_links

            if processed_links is not None:
                task.processed_links = processed_links

            # Update timestamps based on status
            if status == 'running' and not task.started_at:
                task.started_at = datetime.utcnow()
            elif status in ['completed', 'failed']:
                task.completed_at = datetime.utcnow()

            db.session.commit()
            logger.info(f"Updated task {task_id} status to {status}")
            return task

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update task {task_id}: {e}", exc_info=True)
            raise

    def start_task(self, task_id: int) -> Optional[ImportTask]:
        """
        Start a pending task

        Args:
            task_id: Task ID

        Returns:
            Updated ImportTask object or None
        """
        task = db.session.query(ImportTask).get(task_id)
        if not task:
            return None

        if task.status != 'pending':
            raise ValueError(f"Cannot start task with status '{task.status}'")

        return self.update_task_status(task_id, 'running')

    def complete_task(self, task_id: int) -> Optional[ImportTask]:
        """
        Mark task as completed

        Args:
            task_id: Task ID

        Returns:
            Updated ImportTask object or None
        """
        return self.update_task_status(task_id, 'completed')

    def fail_task(self, task_id: int, error_message: Optional[str] = None) -> Optional[ImportTask]:
        """
        Mark task as failed

        Args:
            task_id: Task ID
            error_message: Optional error message to store in config

        Returns:
            Updated ImportTask object or None
        """
        task = db.session.query(ImportTask).get(task_id)
        if task and error_message:
            config = task.config or {}
            config['error'] = error_message
            task.config = config

        return self.update_task_status(task_id, 'failed')

    def update_progress(self, task_id: int, processed_links: int) -> Optional[ImportTask]:
        """
        Update task progress

        Args:
            task_id: Task ID
            processed_links: Number of processed links

        Returns:
            Updated ImportTask object or None
        """
        try:
            task = db.session.query(ImportTask).get(task_id)
            if not task:
                return None

            task.processed_links = processed_links
            db.session.commit()
            return task

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update task {task_id} progress: {e}")
            raise

    def delete_task(self, task_id: int, delete_links: bool = False) -> bool:
        """
        Delete a task

        Args:
            task_id: Task ID
            delete_links: If True, also delete associated links

        Returns:
            True if deleted successfully
        """
        try:
            task = db.session.query(ImportTask).get(task_id)
            if not task:
                return False

            if delete_links:
                # Delete associated links (cascade should handle this)
                db.session.query(Link).filter_by(task_id=task_id).delete()

            db.session.delete(task)
            db.session.commit()

            logger.info(f"Deleted task {task_id}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete task {task_id}: {e}", exc_info=True)
            raise

    def get_task_statistics(self) -> Dict[str, Any]:
        """
        Get overall task statistics

        Returns:
            Dict with task counts by status
        """
        total = db.session.query(ImportTask).count()
        pending = db.session.query(ImportTask).filter_by(status='pending').count()
        running = db.session.query(ImportTask).filter_by(status='running').count()
        completed = db.session.query(ImportTask).filter_by(status='completed').count()
        failed = db.session.query(ImportTask).filter_by(status='failed').count()

        return {
            'total': total,
            'pending': pending,
            'running': running,
            'completed': completed,
            'failed': failed
        }

    def get_task_links(self, task_id: int, include_details: bool = False) -> List[Link]:
        """
        Get all links associated with a task

        Args:
            task_id: Task ID
            include_details: If True, eager load related data

        Returns:
            List of Link objects
        """
        query = db.session.query(Link).filter_by(task_id=task_id)

        if include_details:
            # Eager load parsed_content if needed
            from sqlalchemy.orm import joinedload
            query = query.options(joinedload(Link.parsed_content))

        return query.all()

    def get_task_summary(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed task summary including link statistics

        Args:
            task_id: Task ID

        Returns:
            Dict with task details and statistics
        """
        task = db.session.query(ImportTask).get(task_id)
        if not task:
            return None

        links = self.get_task_links(task_id)
        valid_links = sum(1 for link in links if link.is_valid == True)
        invalid_links = sum(1 for link in links if link.is_valid == False)
        pending_validation = sum(1 for link in links if link.is_valid is None)

        return {
            'id': task.id,
            'name': task.name,
            'status': task.status,
            'total_links': task.total_links,
            'processed_links': task.processed_links,
            'config': task.config,
            'created_at': task.created_at,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
            'link_statistics': {
                'total': len(links),
                'valid': valid_links,
                'invalid': invalid_links,
                'pending_validation': pending_validation
            }
        }


def get_task_service() -> TaskService:
    """Get singleton instance of TaskService"""
    return TaskService()
