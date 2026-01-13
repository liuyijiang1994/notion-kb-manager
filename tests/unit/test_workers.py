"""
Unit tests for RQ workers
"""
import pytest
from unittest.mock import patch, MagicMock, call
from app import create_app, db
from app.models.link import Link
from app.models.content import ParsedContent, AIProcessedContent, ProcessingTask, TaskItem
from app.models.configuration import ModelConfiguration


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


class TestParsingWorker:
    """Test parsing worker functions"""

    def test_parse_content_job_success(self, app):
        """Test successful parsing job"""
        with app.app_context():
            # Setup
            link = Link(url='https://example.com', title='Test', source='manual', status='pending')
            db.session.add(link)

            task = ProcessingTask(
                type='parsing',
                status='running',
                total_items=1,
                queue_name='parsing-queue'
            )
            db.session.add(task)

            db.session.commit()

            item = TaskItem(
                task_id=task.id,
                item_id=link.id,
                item_type='link',
                status='pending'
            )
            db.session.add(item)
            db.session.commit()

            # Mock dependencies
            with patch('app.workers.parsing_worker.get_current_job') as mock_job:
                mock_job.return_value = MagicMock(id='test-job-123')

                with patch('app.workers.parsing_worker.get_content_parsing_service') as mock_service:
                    mock_parsing_service = MagicMock()
                    mock_parsing_service.fetch_and_parse.return_value = {
                        'success': True,
                        'parsed_content_id': 1,
                        'content_type': 'article'
                    }
                    mock_service.return_value = mock_parsing_service

                    # Execute
                    from app.workers.parsing_worker import parse_content_job
                    result = parse_content_job(task.id, link.id)

                    # Verify
                    assert result['success'] is True

                    # Check item was updated
                    item = db.session.query(TaskItem).filter_by(
                        task_id=task.id,
                        item_id=link.id
                    ).first()

                    assert item.status == 'completed'
                    assert item.result_data is not None

    def test_parse_content_job_failure(self, app):
        """Test parsing job with failure"""
        with app.app_context():
            link = Link(url='https://invalid-url', title='Test', source='manual', status='pending')
            db.session.add(link)

            task = ProcessingTask(
                type='parsing',
                status='running',
                total_items=1,
                queue_name='parsing-queue'
            )
            db.session.add(task)
            db.session.commit()

            item = TaskItem(
                task_id=task.id,
                item_id=link.id,
                item_type='link',
                status='pending'
            )
            db.session.add(item)
            db.session.commit()

            # Mock dependencies
            with patch('app.workers.parsing_worker.get_current_job') as mock_job:
                mock_job.return_value = MagicMock(id='test-job-456')

                with patch('app.workers.parsing_worker.get_content_parsing_service') as mock_service:
                    mock_parsing_service = MagicMock()
                    mock_parsing_service.fetch_and_parse.return_value = {
                        'success': False,
                        'error': 'Failed to fetch URL'
                    }
                    mock_service.return_value = mock_parsing_service

                    # Execute
                    from app.workers.parsing_worker import parse_content_job
                    result = parse_content_job(task.id, link.id)

                    # Verify
                    assert result['success'] is False

                    # Check item was marked as failed
                    item = db.session.query(TaskItem).filter_by(
                        task_id=task.id,
                        item_id=link.id
                    ).first()

                    assert item.status == 'failed'
                    assert item.error_message == 'Failed to fetch URL'

    def test_parse_content_job_exception(self, app):
        """Test parsing job with exception"""
        with app.app_context():
            link = Link(url='https://example.com', title='Test', source='manual', status='pending')
            db.session.add(link)

            task = ProcessingTask(
                type='parsing',
                status='running',
                total_items=1,
                queue_name='parsing-queue'
            )
            db.session.add(task)
            db.session.commit()

            item = TaskItem(
                task_id=task.id,
                item_id=link.id,
                item_type='link',
                status='pending'
            )
            db.session.add(item)
            db.session.commit()

            # Mock dependencies to raise exception
            with patch('app.workers.parsing_worker.get_current_job') as mock_job:
                mock_job.return_value = MagicMock(id='test-job-789')

                with patch('app.workers.parsing_worker.get_content_parsing_service') as mock_service:
                    mock_parsing_service = MagicMock()
                    mock_parsing_service.fetch_and_parse.side_effect = Exception('Network error')
                    mock_service.return_value = mock_parsing_service

                    # Execute (should raise exception)
                    from app.workers.parsing_worker import parse_content_job

                    with pytest.raises(Exception) as exc_info:
                        parse_content_job(task.id, link.id)

                    assert 'Network error' in str(exc_info.value)

                    # Check item was marked as failed
                    item = db.session.query(TaskItem).filter_by(
                        task_id=task.id,
                        item_id=link.id
                    ).first()

                    assert item.status == 'failed'
                    assert 'Network error' in item.error_message

    def test_batch_parse_job_dispatches_individual_jobs(self, app):
        """Test that batch parse job dispatches individual jobs"""
        with app.app_context():
            # Create links
            links = []
            for i in range(3):
                link = Link(url=f'https://example.com/{i}', title=f'Test {i}', source='manual', status='pending')
                db.session.add(link)
                links.append(link)

            task = ProcessingTask(
                type='parsing',
                status='queued',
                total_items=3,
                queue_name='parsing-queue'
            )
            db.session.add(task)
            db.session.commit()

            link_ids = [link.id for link in links]

            # Mock queue
            with patch('app.workers.parsing_worker.get_queue') as mock_get_queue:
                mock_queue = MagicMock()
                mock_job = MagicMock()
                mock_job.id = 'batch-job-123'
                mock_queue.enqueue.return_value = mock_job
                mock_get_queue.return_value = mock_queue

                # Execute
                from app.workers.parsing_worker import batch_parse_job
                result = batch_parse_job(task.id, link_ids)

                # Verify
                assert result['success'] is True
                assert result['total_jobs'] == 3
                assert len(result['job_ids']) == 3

                # Verify task items were created
                items = db.session.query(TaskItem).filter_by(task_id=task.id).all()
                assert len(items) == 3

                # Verify individual jobs were enqueued
                assert mock_queue.enqueue.call_count == 3


class TestAIWorker:
    """Test AI worker functions"""

    def test_process_ai_content_job_success(self, app):
        """Test successful AI processing job"""
        with app.app_context():
            # Setup
            link = Link(url='https://example.com', title='Test', source='manual', status='completed')
            db.session.add(link)
            db.session.commit()

            parsed = ParsedContent(
                link_id=link.id,
                raw_html='<html>Test</html>',
                formatted_content='Test content',
                content_type='article'
            )
            db.session.add(parsed)

            task = ProcessingTask(
                type='ai_processing',
                status='running',
                total_items=1,
                queue_name='ai-queue'
            )
            db.session.add(task)
            db.session.commit()

            item = TaskItem(
                task_id=task.id,
                item_id=parsed.id,
                item_type='parsed_content',
                status='pending'
            )
            db.session.add(item)
            db.session.commit()

            # Mock dependencies
            with patch('app.workers.ai_worker.get_current_job') as mock_job:
                mock_job.return_value = MagicMock(id='ai-job-123')

                with patch('app.workers.ai_worker.get_ai_processing_service') as mock_service:
                    mock_ai_service = MagicMock()
                    mock_ai_service.process_content.return_value = {
                        'success': True,
                        'ai_content_id': 1,
                        'summary': 'Test summary',
                        'keywords': ['test', 'example']
                    }
                    mock_service.return_value = mock_ai_service

                    # Execute
                    from app.workers.ai_worker import process_ai_content_job
                    result = process_ai_content_job(task.id, parsed.id)

                    # Verify
                    assert result['success'] is True

                    # Check item was updated
                    item = db.session.query(TaskItem).filter_by(
                        task_id=task.id,
                        item_id=parsed.id
                    ).first()

                    assert item.status == 'completed'

    def test_batch_ai_process_job(self, app):
        """Test batch AI processing job"""
        with app.app_context():
            link = Link(url='https://example.com', title='Test', source='manual', status='completed')
            db.session.add(link)
            db.session.commit()

            # Create parsed contents
            parsed_ids = []
            for i in range(2):
                parsed = ParsedContent(
                    link_id=link.id,
                    raw_html=f'<html>Test {i}</html>',
                    formatted_content=f'Test content {i}',
                    content_type='article'
                )
                db.session.add(parsed)
                db.session.flush()
                parsed_ids.append(parsed.id)

            task = ProcessingTask(
                type='ai_processing',
                status='queued',
                total_items=2,
                queue_name='ai-queue'
            )
            db.session.add(task)
            db.session.commit()

            # Mock queue
            with patch('app.workers.ai_worker.get_queue') as mock_get_queue:
                mock_queue = MagicMock()
                mock_job = MagicMock()
                mock_job.id = 'ai-batch-job-123'
                mock_queue.enqueue.return_value = mock_job
                mock_get_queue.return_value = mock_queue

                # Execute
                from app.workers.ai_worker import batch_ai_process_job
                result = batch_ai_process_job(task.id, parsed_ids)

                # Verify
                assert result['success'] is True
                assert result['total_jobs'] == 2

                # Verify task items were created
                items = db.session.query(TaskItem).filter_by(task_id=task.id).all()
                assert len(items) == 2


class TestNotionWorker:
    """Test Notion worker functions"""

    def test_import_to_notion_job_success(self, app):
        """Test successful Notion import job"""
        with app.app_context():
            # Setup
            link = Link(url='https://example.com', title='Test', source='manual', status='completed')
            db.session.add(link)

            model = ModelConfiguration(
                name='gpt-4',
                provider='openai',
                api_url='https://api.openai.com/v1',
                api_token='test-token',
                is_active=True,
                timeout=30
            )
            db.session.add(model)
            db.session.commit()

            parsed = ParsedContent(
                link_id=link.id,
                raw_html='<html>Test</html>',
                formatted_content='Test content',
                content_type='article'
            )
            db.session.add(parsed)
            db.session.commit()

            ai_content = AIProcessedContent(
                parsed_content_id=parsed.id,
                model_id=model.id,
                summary='Test summary',
                keywords=['test'],
                is_active=True,
                version=1,
                tokens_used=100
            )
            db.session.add(ai_content)

            from app.models.notion import ImportNotionTask
            task = ImportNotionTask(
                type='import',
                status='running',
                total_items=1,
                queue_name='notion-queue'
            )
            db.session.add(task)
            db.session.commit()

            item = TaskItem(
                task_id=task.id,
                item_id=ai_content.id,
                item_type='ai_content',
                status='pending'
            )
            db.session.add(item)
            db.session.commit()

            # Mock dependencies
            with patch('app.workers.notion_worker.get_current_job') as mock_job:
                mock_job.return_value = MagicMock(id='notion-job-123')

                with patch('app.workers.notion_worker.get_notion_import_service') as mock_service:
                    mock_notion_service = MagicMock()
                    mock_notion_service.import_to_notion.return_value = {
                        'success': True,
                        'notion_page_id': 'page-123',
                        'notion_url': 'https://notion.so/page-123'
                    }
                    mock_service.return_value = mock_notion_service

                    # Execute
                    from app.workers.notion_worker import import_to_notion_job
                    result = import_to_notion_job(
                        task.id,
                        ai_content.id,
                        'test-db-123'
                    )

                    # Verify
                    assert result['success'] is True

                    # Check item was updated
                    item = db.session.query(TaskItem).filter_by(
                        task_id=task.id,
                        item_id=ai_content.id
                    ).first()

                    assert item.status == 'completed'


class TestWorkerConfiguration:
    """Test worker configuration"""

    def test_worker_config_values(self):
        """Test that worker config has expected values"""
        from config.workers import WorkerConfig

        assert WorkerConfig.PARSING_QUEUE == 'parsing-queue'
        assert WorkerConfig.AI_QUEUE == 'ai-queue'
        assert WorkerConfig.NOTION_QUEUE == 'notion-queue'

        assert WorkerConfig.PARSING_TIMEOUT == 60
        assert WorkerConfig.AI_TIMEOUT == 120
        assert WorkerConfig.NOTION_TIMEOUT == 60

        assert WorkerConfig.MAX_RETRIES == 3
        assert len(WorkerConfig.RETRY_DELAYS) == 3

    def test_get_queue_config(self):
        """Test getting queue configuration"""
        from config.workers import WorkerConfig

        parsing_config = WorkerConfig.get_queue_config('parsing-queue')
        assert parsing_config['timeout'] == 60
        assert 'result_ttl' in parsing_config
        assert 'worker_count' in parsing_config

        ai_config = WorkerConfig.get_queue_config('ai-queue')
        assert ai_config['timeout'] == 120

        notion_config = WorkerConfig.get_queue_config('notion-queue')
        assert notion_config['timeout'] == 60


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
