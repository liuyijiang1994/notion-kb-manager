"""
Unit tests for BackgroundTaskService
"""
import pytest
from unittest.mock import patch, MagicMock
from fakeredis import FakeStrictRedis
from app import create_app, db
from app.models.content import ProcessingTask, TaskItem
from app.models.notion import ImportNotionTask
from app.services.background_task_service import BackgroundTaskService
from config.workers import WorkerConfig


@pytest.fixture
def app():
    """Create test Flask app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def service(app):
    """Create BackgroundTaskService instance"""
    with app.app_context():
        service = BackgroundTaskService()

        # Mock Redis connection
        fake_redis = FakeStrictRedis()
        with patch.object(service, '_get_redis_connection', return_value=fake_redis):
            yield service


class TestTaskCreation:
    """Test task creation"""

    def test_create_processing_task(self, app, service):
        """Test creating a ProcessingTask"""
        with app.app_context():
            task = service.create_task(
                type='parsing',
                total_items=5,
                config={'test': 'config'},
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            assert task is not None
            assert task.id is not None
            assert task.type == 'parsing'
            assert task.status == 'pending'
            assert task.progress == 0
            assert task.total_items == 5
            assert task.completed_items == 0
            assert task.failed_items == 0
            assert task.config == {'test': 'config'}
            assert task.queue_name == WorkerConfig.PARSING_QUEUE
            assert task.error_log == []

    def test_create_notion_task(self, app, service):
        """Test creating an ImportNotionTask"""
        with app.app_context():
            task = service.create_notion_task(
                type='import',
                total_items=3,
                config={'database_id': 'test-db'},
                queue_name=WorkerConfig.NOTION_QUEUE
            )

            assert task is not None
            assert isinstance(task, ImportNotionTask)
            assert task.type == 'import'
            assert task.total_items == 3
            assert task.queue_name == WorkerConfig.NOTION_QUEUE


class TestTaskItemManagement:
    """Test task item management"""

    def test_create_task_item(self, app, service):
        """Test creating a TaskItem"""
        with app.app_context():
            task = service.create_task(
                type='parsing',
                total_items=1,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            item = service.create_task_item(
                task_id=task.id,
                item_id=123,
                item_type='link',
                job_id='test-job-123'
            )

            assert item is not None
            assert item.task_id == task.id
            assert item.item_id == 123
            assert item.item_type == 'link'
            assert item.status == 'pending'
            assert item.job_id == 'test-job-123'
            assert item.retry_count == 0

    def test_update_item_status_to_running(self, app, service):
        """Test updating item status to running"""
        with app.app_context():
            task = service.create_task(
                type='parsing',
                total_items=1,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            item = service.create_task_item(
                task_id=task.id,
                item_id=123,
                item_type='link'
            )

            service.update_item_status(
                task_id=task.id,
                item_id=123,
                status='running',
                job_id='job-456'
            )

            updated_item = db.session.query(TaskItem).get(item.id)
            assert updated_item.status == 'running'
            assert updated_item.job_id == 'job-456'
            assert updated_item.started_at is not None

    def test_update_item_status_to_completed(self, app, service):
        """Test updating item status to completed"""
        with app.app_context():
            task = service.create_task(
                type='parsing',
                total_items=1,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            item = service.create_task_item(
                task_id=task.id,
                item_id=123,
                item_type='link'
            )

            service.update_item_status(
                task_id=task.id,
                item_id=123,
                status='completed',
                result_data={'success': True, 'parsed_content_id': 456}
            )

            updated_item = db.session.query(TaskItem).get(item.id)
            assert updated_item.status == 'completed'
            assert updated_item.completed_at is not None
            assert updated_item.result_data == {'success': True, 'parsed_content_id': 456}

    def test_update_item_status_to_failed(self, app, service):
        """Test updating item status to failed"""
        with app.app_context():
            task = service.create_task(
                type='parsing',
                total_items=1,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            item = service.create_task_item(
                task_id=task.id,
                item_id=123,
                item_type='link'
            )

            service.update_item_status(
                task_id=task.id,
                item_id=123,
                status='failed',
                error_message='Network timeout'
            )

            updated_item = db.session.query(TaskItem).get(item.id)
            assert updated_item.status == 'failed'
            assert updated_item.completed_at is not None
            assert updated_item.error_message == 'Network timeout'
            assert updated_item.retry_count == 1


class TestProgressTracking:
    """Test task progress tracking"""

    def test_update_task_progress_all_pending(self, app, service):
        """Test progress with all items pending"""
        with app.app_context():
            task = service.create_task(
                type='parsing',
                total_items=3,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            for i in range(3):
                service.create_task_item(task.id, i, 'link')

            service.update_task_progress(task.id)

            updated_task = db.session.query(ProcessingTask).get(task.id)
            assert updated_task.progress == 0
            assert updated_task.completed_items == 0
            assert updated_task.failed_items == 0
            assert updated_task.status == 'pending'

    def test_update_task_progress_partial_complete(self, app, service):
        """Test progress with some items completed"""
        with app.app_context():
            task = service.create_task(
                type='parsing',
                total_items=4,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            for i in range(4):
                service.create_task_item(task.id, i, 'link')

            # Mark 2 as completed, 1 as running
            service.update_item_status(task.id, 0, 'completed')
            service.update_item_status(task.id, 1, 'completed')
            service.update_item_status(task.id, 2, 'running')

            service.update_task_progress(task.id)

            updated_task = db.session.query(ProcessingTask).get(task.id)
            assert updated_task.completed_items == 2
            assert updated_task.progress == 50  # 2/4 * 100
            assert updated_task.status == 'running'

    def test_update_task_progress_all_complete(self, app, service):
        """Test progress with all items completed"""
        with app.app_context():
            task = service.create_task(
                type='parsing',
                total_items=2,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            for i in range(2):
                item = service.create_task_item(task.id, i, 'link')
                service.update_item_status(task.id, i, 'completed')

            service.update_task_progress(task.id)

            updated_task = db.session.query(ProcessingTask).get(task.id)
            assert updated_task.completed_items == 2
            assert updated_task.progress == 100
            assert updated_task.status == 'completed'
            assert updated_task.completed_at is not None

    def test_update_task_progress_with_failures(self, app, service):
        """Test progress with some failures"""
        with app.app_context():
            task = service.create_task(
                type='parsing',
                total_items=5,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            for i in range(5):
                service.create_task_item(task.id, i, 'link')

            # 3 completed, 2 failed
            for i in range(3):
                service.update_item_status(task.id, i, 'completed')
            for i in range(3, 5):
                service.update_item_status(task.id, i, 'failed', error_message='Error')

            service.update_task_progress(task.id)

            updated_task = db.session.query(ProcessingTask).get(task.id)
            assert updated_task.completed_items == 3
            assert updated_task.failed_items == 2
            assert updated_task.progress == 100  # (3+2)/5 * 100
            assert updated_task.status == 'completed'


class TestTaskStatus:
    """Test getting task status"""

    def test_get_task_status(self, app, service):
        """Test getting complete task status"""
        with app.app_context():
            task = service.create_task(
                type='parsing',
                total_items=2,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            service.create_task_item(task.id, 1, 'link')
            service.create_task_item(task.id, 2, 'link')

            status = service.get_task_status(task.id)

            assert status is not None
            assert status['id'] == task.id
            assert status['type'] == 'parsing'
            assert status['status'] == 'pending'
            assert status['total_items'] == 2
            assert status['queue_name'] == WorkerConfig.PARSING_QUEUE
            assert 'items' in status
            assert len(status['items']) == 2

    def test_get_task_status_not_found(self, app, service):
        """Test getting status of non-existent task"""
        with app.app_context():
            status = service.get_task_status(99999)
            assert status is None

    def test_get_task_items(self, app, service):
        """Test getting task items"""
        with app.app_context():
            task = service.create_task(
                type='parsing',
                total_items=3,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            for i in range(3):
                service.create_task_item(task.id, i, 'link')

            # Mark one as completed
            service.update_item_status(task.id, 0, 'completed')

            # Get all items
            all_items = service.get_task_items(task.id)
            assert len(all_items) == 3

            # Get only completed items
            completed_items = service.get_task_items(task.id, status='completed')
            assert len(completed_items) == 1

            # Get only pending items
            pending_items = service.get_task_items(task.id, status='pending')
            assert len(pending_items) == 2


class TestTaskCancellation:
    """Test task cancellation"""

    def test_cancel_task_with_pending_items(self, app, service):
        """Test cancelling task with pending items"""
        with app.app_context():
            # Mock Redis and RQ
            with patch('app.services.background_task_service.Job') as mock_job_class:
                task = service.create_task(
                    type='parsing',
                    total_items=3,
                    queue_name=WorkerConfig.PARSING_QUEUE
                )

                for i in range(3):
                    item = service.create_task_item(task.id, i, 'link')
                    item.job_id = f'job-{i}'
                    db.session.commit()

                # Mock job fetch and cancel
                mock_job = MagicMock()
                mock_job_class.fetch.return_value = mock_job

                result = service.cancel_task(task.id)

                assert result is True

                # Verify task was cancelled
                cancelled_task = db.session.query(ProcessingTask).get(task.id)
                assert cancelled_task.status == 'failed'
                assert cancelled_task.completed_at is not None

                # Verify all items were marked as failed
                items = db.session.query(TaskItem).filter_by(task_id=task.id).all()
                for item in items:
                    assert item.status == 'failed'
                    assert 'Cancelled by user' in item.error_message

    def test_cancel_nonexistent_task(self, app, service):
        """Test cancelling non-existent task"""
        with app.app_context():
            result = service.cancel_task(99999)
            assert result is False


class TestTaskRetry:
    """Test task retry functionality"""

    def test_retry_failed_items(self, app, service):
        """Test retrying failed items"""
        with app.app_context():
            # Mock queue
            with patch('app.services.background_task_service.Queue') as mock_queue_class:
                mock_queue = MagicMock()
                mock_job = MagicMock()
                mock_job.id = 'retry-job-123'
                mock_queue.enqueue.return_value = mock_job
                service._get_queue = MagicMock(return_value=mock_queue)

                task = service.create_task(
                    type='parsing',
                    total_items=3,
                    queue_name=WorkerConfig.PARSING_QUEUE
                )

                # Create items: 1 completed, 2 failed
                service.create_task_item(task.id, 0, 'link')
                service.update_item_status(task.id, 0, 'completed')

                service.create_task_item(task.id, 1, 'link')
                service.update_item_status(task.id, 1, 'failed', error_message='Error 1')

                service.create_task_item(task.id, 2, 'link')
                service.update_item_status(task.id, 2, 'failed', error_message='Error 2')

                # Mark task as completed (with failures)
                task.status = 'completed'
                db.session.commit()

                # Retry failed items
                count = service.retry_failed_items(
                    task_id=task.id,
                    queue_name=WorkerConfig.PARSING_QUEUE,
                    job_func='app.workers.parsing_worker.parse_content_job'
                )

                assert count == 2

                # Verify failed items were reset
                failed_items = db.session.query(TaskItem).filter_by(
                    task_id=task.id
                ).filter(
                    TaskItem.item_id.in_([1, 2])
                ).all()

                for item in failed_items:
                    assert item.status == 'pending'
                    assert item.error_message is None

                # Verify task status was reset
                updated_task = db.session.query(ProcessingTask).get(task.id)
                assert updated_task.status == 'queued'
                assert updated_task.completed_at is None

    def test_retry_no_failed_items(self, app, service):
        """Test retrying when no items are failed"""
        with app.app_context():
            task = service.create_task(
                type='parsing',
                total_items=2,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            # All items completed
            service.create_task_item(task.id, 0, 'link')
            service.update_item_status(task.id, 0, 'completed')

            service.create_task_item(task.id, 1, 'link')
            service.update_item_status(task.id, 1, 'completed')

            # Try to retry
            count = service.retry_failed_items(
                task_id=task.id,
                queue_name=WorkerConfig.PARSING_QUEUE,
                job_func='app.workers.parsing_worker.parse_content_job'
            )

            assert count == 0

    def test_retry_skips_max_retries(self, app, service):
        """Test that retry skips items that exceeded max retries"""
        with app.app_context():
            with patch('app.services.background_task_service.Queue') as mock_queue_class:
                mock_queue = MagicMock()
                mock_job = MagicMock()
                mock_job.id = 'retry-job-456'
                mock_queue.enqueue.return_value = mock_job
                service._get_queue = MagicMock(return_value=mock_queue)

                task = service.create_task(
                    type='parsing',
                    total_items=2,
                    queue_name=WorkerConfig.PARSING_QUEUE
                )

                # Item 1: failed but retryable
                item1 = service.create_task_item(task.id, 0, 'link')
                item1.status = 'failed'
                item1.retry_count = 1
                db.session.commit()

                # Item 2: failed and exceeded max retries
                item2 = service.create_task_item(task.id, 1, 'link')
                item2.status = 'failed'
                item2.retry_count = WorkerConfig.MAX_RETRIES
                db.session.commit()

                # Retry
                count = service.retry_failed_items(
                    task_id=task.id,
                    queue_name=WorkerConfig.PARSING_QUEUE,
                    job_func='app.workers.parsing_worker.parse_content_job'
                )

                # Only 1 item should be retried
                assert count == 1


class TestJobEnqueuing:
    """Test job enqueuing"""

    def test_enqueue_job(self, app, service):
        """Test enqueueing a job"""
        with app.app_context():
            # Mock queue
            with patch('app.services.background_task_service.Queue') as mock_queue_class:
                mock_queue = MagicMock()
                mock_job = MagicMock()
                mock_job.id = 'test-job-789'
                mock_queue.enqueue.return_value = mock_job

                service._get_queue = MagicMock(return_value=mock_queue)

                task = service.create_task(
                    type='parsing',
                    total_items=1,
                    queue_name=WorkerConfig.PARSING_QUEUE
                )

                job_id = service.enqueue_job(
                    task_id=task.id,
                    queue_name=WorkerConfig.PARSING_QUEUE,
                    job_func='app.workers.parsing_worker.parse_content_job',
                    link_id=123
                )

                assert job_id == 'test-job-789'

                # Verify task was updated
                updated_task = db.session.query(ProcessingTask).get(task.id)
                assert updated_task.job_id == 'test-job-789'
                assert updated_task.status == 'queued'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
