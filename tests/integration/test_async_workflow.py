"""
Integration tests for async background task workflow
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from fakeredis import FakeStrictRedis
from rq import Queue
from app import create_app, db
from app.models.link import Link
from app.models.content import ParsedContent, AIProcessedContent, ProcessingTask, TaskItem
from app.models.notion import ImportNotionTask, NotionImport
from app.models.configuration import ModelConfiguration, NotionConfiguration
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
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def fake_redis():
    """Create fake Redis connection for testing"""
    redis_conn = FakeStrictRedis()
    with patch('app.services.background_task_service.Redis') as mock_redis:
        mock_redis.from_url.return_value = redis_conn
        with patch('app.workers.get_redis_connection') as mock_worker_redis:
            mock_worker_redis.return_value = redis_conn
            yield redis_conn


@pytest.fixture
def sample_links(app):
    """Create sample links for testing"""
    with app.app_context():
        links = []
        for i in range(5):
            link = Link(
                url=f'https://example.com/page{i}',
                title=f'Test Page {i}',
                source='manual',
                status='pending'
            )
            db.session.add(link)
            links.append(link)

        db.session.commit()
        return [link.id for link in links]


@pytest.fixture
def sample_parsed_contents(app, sample_links):
    """Create sample parsed contents for testing"""
    with app.app_context():
        parsed_contents = []
        for link_id in sample_links[:3]:
            parsed = ParsedContent(
                link_id=link_id,
                raw_html='<html><body>Test content</body></html>',
                formatted_content='Test content',
                content_type='article',
                quality_score=85
            )
            db.session.add(parsed)
            parsed_contents.append(parsed)

        db.session.commit()
        return [p.id for p in parsed_contents]


@pytest.fixture
def sample_ai_contents(app, sample_parsed_contents):
    """Create sample AI processed contents for testing"""
    with app.app_context():
        # Create model config first
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

        ai_contents = []
        for parsed_id in sample_parsed_contents[:2]:
            ai_content = AIProcessedContent(
                parsed_content_id=parsed_id,
                model_id=model.id,
                summary='Test summary',
                keywords=['test', 'example'],
                insights='Test insights',
                is_active=True,
                version=1,
                tokens_used=100
            )
            db.session.add(ai_content)
            ai_contents.append(ai_content)

        db.session.commit()
        return [ac.id for ac in ai_contents]


class TestAsyncParsingWorkflow:
    """Test async parsing workflow"""

    def test_parse_batch_async_creates_task(self, client, app, fake_redis, sample_links):
        """Test that batch parsing creates a task"""
        with app.app_context():
            response = client.post(
                '/api/parsing/async/batch',
                json={'link_ids': sample_links[:3]},
                content_type='application/json'
            )

            assert response.status_code == 202
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'task_id' in data['data']
            assert data['data']['total_items'] == 3
            assert data['data']['status'] == 'queued'

            # Verify task was created in database
            task = db.session.query(ProcessingTask).get(data['data']['task_id'])
            assert task is not None
            assert task.type == 'parsing'
            assert task.total_items == 3
            assert task.status == 'queued'

    def test_parse_single_async_creates_task(self, client, app, fake_redis, sample_links):
        """Test that single parsing creates a task"""
        with app.app_context():
            link_id = sample_links[0]
            response = client.post(f'/api/parsing/async/single/{link_id}')

            assert response.status_code == 202
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'task_id' in data['data']
            assert data['data']['link_id'] == link_id
            assert data['data']['status'] == 'queued'

            # Verify task item was created
            task = db.session.query(ProcessingTask).get(data['data']['task_id'])
            items = db.session.query(TaskItem).filter_by(task_id=task.id).all()
            assert len(items) == 1
            assert items[0].item_id == link_id
            assert items[0].item_type == 'link'

    def test_get_task_status(self, client, app, sample_links):
        """Test getting task status"""
        with app.app_context():
            # Create a task manually
            task = ProcessingTask(
                type='parsing',
                status='running',
                progress=50,
                total_items=4,
                completed_items=2,
                failed_items=0,
                queue_name=WorkerConfig.PARSING_QUEUE
            )
            db.session.add(task)
            db.session.commit()

            # Create task items
            for i, link_id in enumerate(sample_links[:4]):
                status = 'completed' if i < 2 else 'pending'
                item = TaskItem(
                    task_id=task.id,
                    item_id=link_id,
                    item_type='link',
                    status=status
                )
                db.session.add(item)
            db.session.commit()

            # Get status
            response = client.get(f'/api/parsing/async/status/{task.id}')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert data['data']['task']['id'] == task.id
            assert data['data']['task']['status'] == 'running'
            assert data['data']['task']['progress'] == 50
            assert data['data']['task']['completed_items'] == 2

    def test_get_task_status_with_items(self, client, app, sample_links):
        """Test getting task status with items included"""
        with app.app_context():
            task = ProcessingTask(
                type='parsing',
                status='running',
                total_items=2,
                queue_name=WorkerConfig.PARSING_QUEUE
            )
            db.session.add(task)
            db.session.commit()

            # Create task items
            for link_id in sample_links[:2]:
                item = TaskItem(
                    task_id=task.id,
                    item_id=link_id,
                    item_type='link',
                    status='completed'
                )
                db.session.add(item)
            db.session.commit()

            # Get status with items
            response = client.get(f'/api/parsing/async/status/{task.id}?include_items=true')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert 'items' in data['data']['task']
            assert len(data['data']['task']['items']) == 2

    def test_cancel_task(self, client, app, fake_redis, sample_links):
        """Test cancelling a task"""
        with app.app_context():
            # Create a running task
            task = ProcessingTask(
                type='parsing',
                status='running',
                total_items=3,
                queue_name=WorkerConfig.PARSING_QUEUE
            )
            db.session.add(task)
            db.session.commit()

            # Create pending items
            for link_id in sample_links[:3]:
                item = TaskItem(
                    task_id=task.id,
                    item_id=link_id,
                    item_type='link',
                    status='pending'
                )
                db.session.add(item)
            db.session.commit()

            # Cancel task
            response = client.delete(f'/api/parsing/async/cancel/{task.id}')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True

            # Verify task was cancelled
            task = db.session.query(ProcessingTask).get(task.id)
            assert task.status == 'failed'

            # Verify items were marked as failed
            items = db.session.query(TaskItem).filter_by(task_id=task.id).all()
            for item in items:
                assert item.status == 'failed'
                assert 'Cancelled by user' in item.error_message

    def test_retry_failed_items(self, client, app, fake_redis, sample_links):
        """Test retrying failed items"""
        with app.app_context():
            # Create a task with failed items
            task = ProcessingTask(
                type='parsing',
                status='completed',
                total_items=3,
                completed_items=1,
                failed_items=2,
                queue_name=WorkerConfig.PARSING_QUEUE
            )
            db.session.add(task)
            db.session.commit()

            # Create items: 1 completed, 2 failed
            statuses = ['completed', 'failed', 'failed']
            for i, link_id in enumerate(sample_links[:3]):
                item = TaskItem(
                    task_id=task.id,
                    item_id=link_id,
                    item_type='link',
                    status=statuses[i],
                    retry_count=0 if statuses[i] == 'failed' else 1
                )
                db.session.add(item)
            db.session.commit()

            # Retry failed items
            response = client.post(f'/api/parsing/async/retry/{task.id}')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert data['data']['retried_count'] == 2


class TestAsyncAIProcessingWorkflow:
    """Test async AI processing workflow"""

    def test_process_batch_async_creates_task(self, client, app, fake_redis, sample_parsed_contents):
        """Test that batch AI processing creates a task"""
        with app.app_context():
            response = client.post(
                '/api/ai/async/batch',
                json={
                    'parsed_content_ids': sample_parsed_contents,
                    'processing_config': {
                        'generate_summary': True,
                        'generate_keywords': True
                    }
                },
                content_type='application/json'
            )

            assert response.status_code == 202
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'task_id' in data['data']
            assert data['data']['total_items'] == len(sample_parsed_contents)
            assert data['data']['status'] == 'queued'

            # Verify task was created
            task = db.session.query(ProcessingTask).get(data['data']['task_id'])
            assert task is not None
            assert task.type == 'ai_processing'
            assert task.queue_name == WorkerConfig.AI_QUEUE

    def test_process_single_async_creates_task(self, client, app, fake_redis, sample_parsed_contents):
        """Test that single AI processing creates a task"""
        with app.app_context():
            parsed_id = sample_parsed_contents[0]
            response = client.post(
                f'/api/ai/async/single/{parsed_id}',
                json={'processing_config': {'generate_summary': True}},
                content_type='application/json'
            )

            assert response.status_code == 202
            data = json.loads(response.data)

            assert data['success'] is True
            assert data['data']['parsed_content_id'] == parsed_id

    def test_ai_task_status(self, client, app, sample_parsed_contents):
        """Test getting AI task status"""
        with app.app_context():
            task = ProcessingTask(
                type='ai_processing',
                status='completed',
                progress=100,
                total_items=2,
                completed_items=2,
                failed_items=0,
                queue_name=WorkerConfig.AI_QUEUE
            )
            db.session.add(task)
            db.session.commit()

            response = client.get(f'/api/ai/async/status/{task.id}')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['data']['task']['type'] == 'ai_processing'
            assert data['data']['task']['status'] == 'completed'


class TestAsyncNotionImportWorkflow:
    """Test async Notion import workflow"""

    def test_import_batch_async_creates_task(self, client, app, fake_redis, sample_ai_contents):
        """Test that batch Notion import creates a task"""
        with app.app_context():
            response = client.post(
                '/api/notion/async/batch',
                json={
                    'ai_content_ids': sample_ai_contents,
                    'database_id': 'test-db-123',
                    'properties': {}
                },
                content_type='application/json'
            )

            assert response.status_code == 202
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'task_id' in data['data']
            assert data['data']['total_items'] == len(sample_ai_contents)

            # Verify ImportNotionTask was created
            task = db.session.query(ImportNotionTask).get(data['data']['task_id'])
            assert task is not None
            assert task.type == 'import'
            assert task.queue_name == WorkerConfig.NOTION_QUEUE

    def test_import_single_async_creates_task(self, client, app, fake_redis, sample_ai_contents):
        """Test that single Notion import creates a task"""
        with app.app_context():
            ai_content_id = sample_ai_contents[0]
            response = client.post(
                f'/api/notion/async/single/{ai_content_id}',
                json={'database_id': 'test-db-123'},
                content_type='application/json'
            )

            assert response.status_code == 202
            data = json.loads(response.data)

            assert data['success'] is True
            assert data['data']['ai_content_id'] == ai_content_id

    def test_notion_task_status(self, client, app):
        """Test getting Notion task status"""
        with app.app_context():
            task = ImportNotionTask(
                type='import',
                status='running',
                progress=50,
                total_items=2,
                completed_items=1,
                failed_items=0,
                queue_name=WorkerConfig.NOTION_QUEUE
            )
            db.session.add(task)
            db.session.commit()

            response = client.get(f'/api/notion/async/status/{task.id}')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['data']['task']['type'] == 'import'
            assert data['data']['task']['progress'] == 50


class TestMonitoringEndpoints:
    """Test monitoring endpoints"""

    def test_get_workers(self, client, app, fake_redis):
        """Test getting worker status"""
        with app.app_context():
            response = client.get('/api/monitoring/workers')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'workers' in data['data']
            assert 'total_workers' in data['data']

    def test_get_queues(self, client, app, fake_redis):
        """Test getting queue statistics"""
        with app.app_context():
            response = client.get('/api/monitoring/queues')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'queues' in data['data']

            # Verify all queues are present
            queues = data['data']['queues']
            for queue_name in WorkerConfig.QUEUE_NAMES:
                assert queue_name in queues
                assert 'count' in queues[queue_name]

    def test_get_statistics(self, client, app, sample_links):
        """Test getting task statistics"""
        with app.app_context():
            # Create some tasks
            task1 = ProcessingTask(
                type='parsing',
                status='completed',
                total_items=3,
                completed_items=3,
                failed_items=0
            )
            task2 = ProcessingTask(
                type='ai_processing',
                status='running',
                total_items=2,
                completed_items=1,
                failed_items=0
            )
            db.session.add_all([task1, task2])
            db.session.commit()

            response = client.get('/api/monitoring/statistics')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            stats = data['data']['statistics']

            assert stats['total_tasks'] >= 2
            assert stats['completed_tasks'] >= 1
            assert stats['running_tasks'] >= 1
            assert 'by_type' in stats
            assert 'parsing' in stats['by_type']

    def test_get_health(self, client, app, fake_redis):
        """Test getting system health"""
        with app.app_context():
            response = client.get('/api/monitoring/health')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            health = data['data']['health']

            assert 'redis' in health
            assert 'workers' in health
            assert 'queues_healthy' in health
            assert 'queues' in health


class TestBackgroundTaskService:
    """Test BackgroundTaskService directly"""

    def test_create_task(self, app):
        """Test creating a background task"""
        with app.app_context():
            from app.services.background_task_service import get_background_task_service

            service = get_background_task_service()
            task = service.create_task(
                type='parsing',
                total_items=5,
                config={'test': 'config'},
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            assert task is not None
            assert task.id is not None
            assert task.type == 'parsing'
            assert task.total_items == 5
            assert task.status == 'pending'
            assert task.config == {'test': 'config'}

    def test_create_task_item(self, app):
        """Test creating a task item"""
        with app.app_context():
            from app.services.background_task_service import get_background_task_service

            service = get_background_task_service()
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

            assert item is not None
            assert item.task_id == task.id
            assert item.item_id == 123
            assert item.item_type == 'link'
            assert item.status == 'pending'

    def test_update_item_status(self, app):
        """Test updating task item status"""
        with app.app_context():
            from app.services.background_task_service import get_background_task_service

            service = get_background_task_service()
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

            # Update to running
            service.update_item_status(
                task_id=task.id,
                item_id=123,
                status='running',
                job_id='test-job-123'
            )

            updated_item = db.session.query(TaskItem).get(item.id)
            assert updated_item.status == 'running'
            assert updated_item.job_id == 'test-job-123'
            assert updated_item.started_at is not None

            # Update to completed
            service.update_item_status(
                task_id=task.id,
                item_id=123,
                status='completed',
                result_data={'success': True}
            )

            updated_item = db.session.query(TaskItem).get(item.id)
            assert updated_item.status == 'completed'
            assert updated_item.completed_at is not None
            assert updated_item.result_data == {'success': True}

    def test_update_task_progress(self, app):
        """Test updating task progress"""
        with app.app_context():
            from app.services.background_task_service import get_background_task_service

            service = get_background_task_service()
            task = service.create_task(
                type='parsing',
                total_items=4,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            # Create items with different statuses
            for i in range(4):
                item = service.create_task_item(
                    task_id=task.id,
                    item_id=i,
                    item_type='link'
                )

                if i < 2:
                    service.update_item_status(task.id, i, 'completed')
                elif i == 2:
                    service.update_item_status(task.id, i, 'failed', error_message='Test error')

            # Update progress
            service.update_task_progress(task.id)

            updated_task = db.session.query(ProcessingTask).get(task.id)
            assert updated_task.completed_items == 2
            assert updated_task.failed_items == 1
            assert updated_task.progress == 75  # (2 + 1) / 4 * 100
            assert updated_task.status == 'running'

    def test_get_task_status(self, app):
        """Test getting task status"""
        with app.app_context():
            from app.services.background_task_service import get_background_task_service

            service = get_background_task_service()
            task = service.create_task(
                type='parsing',
                total_items=2,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            for i in range(2):
                service.create_task_item(task.id, i, 'link')

            status = service.get_task_status(task.id)

            assert status is not None
            assert status['id'] == task.id
            assert status['type'] == 'parsing'
            assert status['total_items'] == 2
            assert 'items' in status
            assert len(status['items']) == 2

    def test_cancel_task(self, app, fake_redis):
        """Test cancelling a task"""
        with app.app_context():
            from app.services.background_task_service import get_background_task_service

            service = get_background_task_service()
            task = service.create_task(
                type='parsing',
                total_items=2,
                queue_name=WorkerConfig.PARSING_QUEUE
            )

            # Create pending items
            service.create_task_item(task.id, 1, 'link')
            service.create_task_item(task.id, 2, 'link')

            # Cancel
            result = service.cancel_task(task.id)

            assert result is True

            cancelled_task = db.session.query(ProcessingTask).get(task.id)
            assert cancelled_task.status == 'failed'

            items = db.session.query(TaskItem).filter_by(task_id=task.id).all()
            for item in items:
                assert item.status == 'failed'


class TestValidation:
    """Test input validation"""

    def test_parse_batch_empty_array(self, client, app):
        """Test parsing with empty link_ids array"""
        with app.app_context():
            response = client.post(
                '/api/parsing/async/batch',
                json={'link_ids': []},
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] is False

    def test_parse_batch_missing_field(self, client, app):
        """Test parsing without required field"""
        with app.app_context():
            response = client.post(
                '/api/parsing/async/batch',
                json={},
                content_type='application/json'
            )

            assert response.status_code == 400

    def test_ai_batch_missing_database_id(self, client, app):
        """Test Notion import without database_id"""
        with app.app_context():
            response = client.post(
                '/api/notion/async/batch',
                json={'ai_content_ids': [1, 2]},
                content_type='application/json'
            )

            assert response.status_code == 400

    def test_task_status_not_found(self, client, app):
        """Test getting status of non-existent task"""
        with app.app_context():
            response = client.get('/api/parsing/async/status/99999')

            assert response.status_code == 404
            data = json.loads(response.data)
            assert data['success'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
