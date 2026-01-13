"""
Integration tests for Phase 7: Task Management
Tests unified task management endpoints, task editing, cloning, and report generation
"""
import pytest
import os
from datetime import datetime
from pathlib import Path
from app import create_app, db
from app.models.link import ImportTask, Link
from app.services.task_service import get_task_service
from app.services.task_report_service import get_task_report_service


@pytest.fixture
def app():
    """Create and configure test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['REPORTS_DIR'] = 'test_reports'

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    # Cleanup test reports
    test_reports_dir = Path('test_reports')
    if test_reports_dir.exists():
        for file in test_reports_dir.glob('*'):
            file.unlink()
        test_reports_dir.rmdir()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def sample_tasks(app):
    """Create sample tasks for testing"""
    with app.app_context():
        tasks = []

        # Pending task
        pending = ImportTask(
            name='Pending Import Task',
            status='pending',
            total_links=0,
            processed_links=0,
            config={'scope': 'all', 'auto_parse': True}
        )
        db.session.add(pending)
        tasks.append(pending)

        # Running task
        running = ImportTask(
            name='Running Import Task',
            status='running',
            total_links=100,
            processed_links=45,
            config={'scope': 'recent'},
            started_at=datetime.utcnow()
        )
        db.session.add(running)
        tasks.append(running)

        # Completed task
        completed = ImportTask(
            name='Completed Import Task',
            status='completed',
            total_links=50,
            processed_links=50,
            config={'scope': 'all', 'auto_parse': True},
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.session.add(completed)
        tasks.append(completed)

        # Failed task
        failed = ImportTask(
            name='Failed Import Task',
            status='failed',
            total_links=20,
            processed_links=10,
            config={'scope': 'all', 'error': 'Connection timeout'},
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.session.add(failed)
        tasks.append(failed)

        db.session.commit()

        # Add some links to completed task for report testing
        for i in range(5):
            link = Link(
                task_id=completed.id,
                url=f'https://example.com/page-{i+1}',
                title=f'Test Page {i+1}',
                source='manual',
                is_valid=True if i < 4 else False,
                validation_status='valid' if i < 4 else 'invalid'
            )
            db.session.add(link)

        db.session.commit()

        # Refresh tasks to get updated IDs
        for task in tasks:
            db.session.refresh(task)

        return tasks


class TestPendingTasksAPI:
    """Test pending tasks endpoints"""

    def test_get_pending_tasks(self, client, app, sample_tasks):
        """Test listing all pending tasks"""
        response = client.get('/api/tasks/pending')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert 'tasks' in data['data']
        assert 'pagination' in data['data']

        # Should include pending task
        tasks = data['data']['tasks']
        assert len(tasks) >= 1

        pending_task = next((t for t in tasks if t['status'] == 'pending'), None)
        assert pending_task is not None
        assert pending_task['name'] == 'Pending Import Task'

    def test_get_pending_tasks_with_pagination(self, client, app, sample_tasks):
        """Test pending tasks pagination"""
        response = client.get('/api/tasks/pending?page=1&per_page=2')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert data['data']['pagination']['per_page'] == 2

    def test_get_pending_task_details(self, client, app, sample_tasks):
        """Test getting pending task details"""
        with app.app_context():
            task_id = sample_tasks[0].id  # Pending task

        response = client.get(f'/api/tasks/pending/{task_id}')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert data['data']['id'] == task_id
        assert data['data']['name'] == 'Pending Import Task'
        assert data['data']['status'] == 'pending'
        assert data['data']['config']['scope'] == 'all'

    def test_get_non_pending_task_fails(self, client, app, sample_tasks):
        """Test that getting non-pending task via pending endpoint fails"""
        with app.app_context():
            task_id = sample_tasks[2].id  # Completed task

        response = client.get(f'/api/tasks/pending/{task_id}')
        assert response.status_code == 400

    def test_edit_pending_task(self, client, app, sample_tasks):
        """Test editing pending task name and config"""
        with app.app_context():
            task_id = sample_tasks[0].id

        response = client.put(
            f'/api/tasks/pending/{task_id}',
            json={
                'name': 'Updated Task Name',
                'config': {'scope': 'recent', 'auto_parse': False}
            }
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True

        # Verify update
        with app.app_context():
            task = db.session.query(ImportTask).get(task_id)
            assert task.name == 'Updated Task Name'
            assert task.config['scope'] == 'recent'
            assert task.config['auto_parse'] is False

    def test_edit_task_name_only(self, client, app, sample_tasks):
        """Test editing only task name"""
        with app.app_context():
            task_id = sample_tasks[0].id
            original_config = sample_tasks[0].config.copy()

        response = client.put(
            f'/api/tasks/pending/{task_id}',
            json={'name': 'New Name Only'}
        )
        assert response.status_code == 200

        # Config should remain unchanged
        with app.app_context():
            task = db.session.query(ImportTask).get(task_id)
            assert task.name == 'New Name Only'
            assert task.config == original_config

    def test_cannot_edit_non_pending_task(self, client, app, sample_tasks):
        """Test that completed/running tasks cannot be edited"""
        with app.app_context():
            completed_task_id = sample_tasks[2].id

        response = client.put(
            f'/api/tasks/pending/{completed_task_id}',
            json={'name': 'Should Fail'}
        )
        assert response.status_code == 400

    def test_start_pending_task(self, client, app, sample_tasks):
        """Test starting a pending task"""
        with app.app_context():
            task_id = sample_tasks[0].id

        response = client.post(f'/api/tasks/pending/{task_id}/start')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True

        # Verify task is now running
        with app.app_context():
            task = db.session.query(ImportTask).get(task_id)
            assert task.status == 'running'
            assert task.started_at is not None

    def test_delete_pending_task(self, client, app, sample_tasks):
        """Test deleting a pending task"""
        with app.app_context():
            task_id = sample_tasks[0].id

        response = client.delete(f'/api/tasks/pending/{task_id}')
        assert response.status_code == 200

        # Verify task is deleted
        with app.app_context():
            task = db.session.query(ImportTask).get(task_id)
            assert task is None

    def test_get_nonexistent_task(self, client, app):
        """Test getting nonexistent task returns 404"""
        response = client.get('/api/tasks/pending/99999')
        assert response.status_code == 404


class TestHistoricalTasksAPI:
    """Test historical tasks endpoints"""

    def test_get_historical_tasks(self, client, app, sample_tasks):
        """Test listing historical tasks (completed/failed)"""
        response = client.get('/api/tasks/history')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert 'tasks' in data['data']

        tasks = data['data']['tasks']
        # Should include completed and failed tasks
        statuses = [t['status'] for t in tasks]
        assert 'completed' in statuses or 'failed' in statuses

    def test_get_historical_tasks_filter_completed(self, client, app, sample_tasks):
        """Test filtering historical tasks by completed status"""
        response = client.get('/api/tasks/history?status=completed')
        assert response.status_code == 200

        data = response.get_json()
        tasks = data['data']['tasks']

        # All tasks should be completed
        for task in tasks:
            assert task['status'] == 'completed'

    def test_get_historical_tasks_filter_failed(self, client, app, sample_tasks):
        """Test filtering historical tasks by failed status"""
        response = client.get('/api/tasks/history?status=failed')
        assert response.status_code == 200

        data = response.get_json()
        tasks = data['data']['tasks']

        # All tasks should be failed
        for task in tasks:
            assert task['status'] == 'failed'

    def test_get_historical_task_details(self, client, app, sample_tasks):
        """Test getting historical task details"""
        with app.app_context():
            task_id = sample_tasks[2].id  # Completed task

        response = client.get(f'/api/tasks/history/{task_id}')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert data['id'] == task_id
        assert data['status'] == 'completed'

    def test_clone_completed_task(self, client, app, sample_tasks):
        """Test cloning a completed task"""
        with app.app_context():
            task_id = sample_tasks[2].id  # Completed task
            original_name = sample_tasks[2].name

        response = client.post(
            f'/api/tasks/history/{task_id}/rerun',
            json={'name': 'Cloned Task Test'}
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert 'task_id' in data['data']

        new_task_id = data['data']['task_id']

        # Verify new task exists with correct properties
        with app.app_context():
            new_task = db.session.query(ImportTask).get(new_task_id)
            assert new_task is not None
            assert new_task.status == 'pending'
            assert new_task.name == 'Cloned Task Test'
            assert new_task.config['scope'] == 'all'  # Inherited from original
            assert new_task.total_links == 0  # Reset for new task
            assert new_task.processed_links == 0

    def test_clone_task_with_config_overrides(self, client, app, sample_tasks):
        """Test cloning task with modified config"""
        with app.app_context():
            task_id = sample_tasks[2].id

        response = client.post(
            f'/api/tasks/history/{task_id}/rerun',
            json={
                'name': 'Modified Clone',
                'modify_config': {'scope': 'recent', 'new_option': True}
            }
        )
        assert response.status_code == 200

        new_task_id = response.get_json()['data']['task_id']

        # Verify config was overridden
        with app.app_context():
            new_task = db.session.query(ImportTask).get(new_task_id)
            assert new_task.config['scope'] == 'recent'  # Overridden
            assert new_task.config['new_option'] is True  # Added
            assert new_task.config['auto_parse'] is True  # Preserved from original

    def test_clone_task_auto_name_generation(self, client, app, sample_tasks):
        """Test that cloning without name generates automatic name"""
        with app.app_context():
            task_id = sample_tasks[2].id
            original_name = sample_tasks[2].name

        response = client.post(f'/api/tasks/history/{task_id}/rerun')
        assert response.status_code == 200

        new_task_id = response.get_json()['data']['task_id']

        # Verify name contains original name and clone timestamp
        with app.app_context():
            new_task = db.session.query(ImportTask).get(new_task_id)
            assert 'Clone' in new_task.name
            assert original_name in new_task.name

    def test_cannot_clone_nonexistent_task(self, client, app):
        """Test that cloning nonexistent task fails"""
        response = client.post('/api/tasks/history/99999/rerun')
        assert response.status_code == 400


class TestTaskReportService:
    """Test task report generation"""

    def test_generate_excel_report(self, app, sample_tasks):
        """Test Excel report generation"""
        with app.app_context():
            task_id = sample_tasks[2].id  # Completed task with links

            service = get_task_report_service()
            result = service.generate_report(task_id, 'excel')

            assert result['success'] is True
            assert 'filepath' in result
            assert result['filepath'].endswith('.xlsx')
            assert result['format'] == 'excel'

            # Verify file exists
            filepath = Path(result['filepath'])
            assert filepath.exists()
            assert filepath.stat().st_size > 0

    def test_generate_json_report(self, app, sample_tasks):
        """Test JSON report generation"""
        with app.app_context():
            task_id = sample_tasks[2].id

            service = get_task_report_service()
            result = service.generate_report(task_id, 'json')

            assert result['success'] is True
            assert result['filepath'].endswith('.json')
            assert result['format'] == 'json'

            # Verify JSON file content
            filepath = Path(result['filepath'])
            assert filepath.exists()

            import json
            with open(filepath, 'r') as f:
                report_data = json.load(f)

            assert 'task' in report_data
            assert 'links' in report_data
            assert report_data['task']['id'] == task_id
            assert len(report_data['links']) == 5  # From sample_tasks fixture

    def test_generate_pdf_report_fallback(self, app, sample_tasks):
        """Test PDF generation falls back to JSON"""
        with app.app_context():
            task_id = sample_tasks[2].id

            service = get_task_report_service()
            result = service.generate_report(task_id, 'pdf')

            # Currently falls back to JSON
            assert result['success'] is True
            assert result['filepath'].endswith('.json')

    def test_report_nonexistent_task_fails(self, app):
        """Test that generating report for nonexistent task fails"""
        with app.app_context():
            service = get_task_report_service()
            result = service.generate_report(99999, 'excel')

            assert result['success'] is False
            assert 'not found' in result['error'].lower()

    def test_invalid_format_fails(self, app, sample_tasks):
        """Test that invalid format type fails"""
        with app.app_context():
            task_id = sample_tasks[2].id

            service = get_task_report_service()
            result = service.generate_report(task_id, 'invalid_format')

            assert result['success'] is False
            assert 'Unsupported format' in result['error']

    def test_cleanup_old_reports(self, app, sample_tasks):
        """Test cleanup of old report files"""
        with app.app_context():
            service = get_task_report_service()
            task_id = sample_tasks[2].id

            # Generate a report
            result1 = service.generate_report(task_id, 'json')
            assert result1['success'] is True

            # Manually set file modification time to old date
            filepath = Path(result1['filepath'])
            old_timestamp = datetime(2020, 1, 1).timestamp()
            os.utime(filepath, (old_timestamp, old_timestamp))

            # Run cleanup
            deleted_count = service.cleanup_old_reports(days=30)

            assert deleted_count == 1
            assert not filepath.exists()


class TestTaskReportExport:
    """Test task report export endpoint"""

    def test_export_excel_report_endpoint(self, client, app, sample_tasks):
        """Test Excel report export via API endpoint"""
        with app.app_context():
            task_id = sample_tasks[2].id

        response = client.post(
            f'/api/tasks/history/{task_id}/export',
            json={'format': 'excel'}
        )

        assert response.status_code == 200
        assert response.content_type.startswith('application/')
        assert len(response.data) > 0

    def test_export_json_report_endpoint(self, client, app, sample_tasks):
        """Test JSON report export via API endpoint"""
        with app.app_context():
            task_id = sample_tasks[2].id

        response = client.post(
            f'/api/tasks/history/{task_id}/export',
            json={'format': 'json'}
        )

        assert response.status_code == 200
        assert len(response.data) > 0

    def test_export_invalid_format_fails(self, client, app, sample_tasks):
        """Test that invalid format fails"""
        with app.app_context():
            task_id = sample_tasks[2].id

        response = client.post(
            f'/api/tasks/history/{task_id}/export',
            json={'format': 'xml'}
        )

        assert response.status_code == 400


class TestTaskServiceMethods:
    """Test new TaskService methods"""

    def test_update_task_method(self, app, sample_tasks):
        """Test TaskService.update_task() method"""
        with app.app_context():
            service = get_task_service()
            task_id = sample_tasks[0].id

            success = service.update_task(
                task_id,
                name='Service Updated Name',
                config={'new_key': 'new_value'}
            )

            assert success is True

            task = db.session.query(ImportTask).get(task_id)
            assert task.name == 'Service Updated Name'
            assert task.config['new_key'] == 'new_value'

    def test_clone_task_method(self, app, sample_tasks):
        """Test TaskService.clone_task() method"""
        with app.app_context():
            service = get_task_service()
            task_id = sample_tasks[2].id

            new_task = service.clone_task(
                task_id,
                new_name='Service Cloned Task',
                config_overrides={'override_key': 'override_value'}
            )

            assert new_task is not None
            assert new_task.status == 'pending'
            assert new_task.name == 'Service Cloned Task'
            assert new_task.config['override_key'] == 'override_value'

    def test_get_tasks_by_status_list_method(self, app, sample_tasks):
        """Test TaskService.get_tasks_by_status_list() method"""
        with app.app_context():
            service = get_task_service()

            tasks = service.get_tasks_by_status_list(['completed', 'failed'], limit=10)

            assert len(tasks) >= 2
            for task in tasks:
                assert task.status in ['completed', 'failed']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
