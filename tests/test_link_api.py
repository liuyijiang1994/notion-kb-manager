"""Tests for link import and task management API endpoints"""
import pytest
import json
from app.models.link import Link, ImportTask
from app import db


class TestLinkImportAPI:
    """Tests for link import API endpoints"""

    def test_import_manual_success(self, client, app):
        """Test manual link import"""
        with app.app_context():
            payload = {
                'text': 'https://example.com\nhttps://google.com'
            }
            response = client.post(
                '/api/links/import/manual',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success']
            assert data['data']['imported'] >= 2

    def test_import_manual_with_task_name(self, client, app):
        """Test manual import with task creation"""
        with app.app_context():
            payload = {
                'text': 'https://example.com',
                'task_name': 'Test Import Task'
            }
            response = client.post(
                '/api/links/import/manual',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success']
            assert data['data']['task_id'] is not None

    def test_import_manual_missing_text(self, client, app):
        """Test manual import with missing text"""
        with app.app_context():
            payload = {}
            response = client.post(
                '/api/links/import/manual',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert not data['success']

    def test_import_from_favorites_html(self, client, app):
        """Test importing from HTML favorites"""
        with app.app_context():
            html = '''<HTML>
            <DL>
                <DT><A HREF="https://example.com">Example</A>
            </DL>
            </HTML>'''

            payload = {
                'file_content': html,
                'file_type': 'html'
            }
            response = client.post(
                '/api/links/import/favorites',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success']
            assert data['data']['imported'] >= 1

    def test_import_from_favorites_json(self, client, app):
        """Test importing from JSON favorites"""
        with app.app_context():
            bookmark_data = {
                "roots": {
                    "bookmark_bar": {
                        "children": [
                            {
                                "type": "url",
                                "url": "https://example.com",
                                "name": "Example"
                            }
                        ]
                    }
                }
            }

            payload = {
                'file_content': json.dumps(bookmark_data),
                'file_type': 'json'
            }
            response = client.post(
                '/api/links/import/favorites',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success']

    def test_import_favorites_invalid_file_type(self, client, app):
        """Test importing with invalid file type"""
        with app.app_context():
            payload = {
                'file_content': 'content',
                'file_type': 'invalid'
            }
            response = client.post(
                '/api/links/import/favorites',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 400


class TestLinkManagementAPI:
    """Tests for link management API endpoints"""

    def test_get_links(self, client, app):
        """Test getting all links"""
        with app.app_context():
            response = client.get('/api/links')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']
            assert 'links' in data['data']

    def test_get_links_with_filters(self, client, app):
        """Test getting links with filters"""
        with app.app_context():
            # Create a link first
            from app.services.link_import_service import get_link_import_service
            service = get_link_import_service()
            service.import_manual('https://example.com')

            response = client.get('/api/links?source=manual&limit=10')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']

    def test_get_single_link(self, client, app):
        """Test getting a single link"""
        with app.app_context():
            # Create a link first
            from app.services.link_import_service import get_link_import_service
            service = get_link_import_service()
            result = service.import_manual('https://example.com')
            link_id = result['links'][0].id

            response = client.get(f'/api/links/{link_id}')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']
            assert data['data']['id'] == link_id

    def test_get_nonexistent_link(self, client, app):
        """Test getting a nonexistent link"""
        with app.app_context():
            response = client.get('/api/links/99999')

            assert response.status_code == 404

    def test_update_link(self, client, app):
        """Test updating a link"""
        with app.app_context():
            # Create a link first
            from app.services.link_import_service import get_link_import_service
            service = get_link_import_service()
            result = service.import_manual('https://example.com')
            link_id = result['links'][0].id

            payload = {
                'title': 'Updated Title',
                'priority': 'high',
                'tags': ['test', 'updated']
            }
            response = client.put(
                f'/api/links/{link_id}',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']

    def test_delete_link(self, client, app):
        """Test deleting a link"""
        with app.app_context():
            # Create a link first
            from app.services.link_import_service import get_link_import_service
            service = get_link_import_service()
            result = service.import_manual('https://example.com')
            link_id = result['links'][0].id

            response = client.delete(f'/api/links/{link_id}')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']

            # Verify deletion
            link = Link.query.get(link_id)
            assert link is None

    def test_batch_delete_links(self, client, app):
        """Test batch deleting links"""
        with app.app_context():
            # Create some links first
            from app.services.link_import_service import get_link_import_service
            service = get_link_import_service()
            result = service.import_manual('https://example.com\nhttps://google.com')
            link_ids = [link.id for link in result['links']]

            payload = {'link_ids': link_ids}
            response = client.delete(
                '/api/links/batch',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']
            assert data['data']['deleted'] == len(link_ids)


class TestLinkValidationAPI:
    """Tests for link validation API endpoints"""

    def test_validate_links(self, client, app):
        """Test batch link validation"""
        with app.app_context():
            # Create some links first
            from app.services.link_import_service import get_link_import_service
            service = get_link_import_service()
            result = service.import_manual('https://www.google.com')
            link_ids = [link.id for link in result['links']]

            payload = {'link_ids': link_ids}
            response = client.post(
                '/api/links/validate',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']

    def test_validate_links_missing_ids(self, client, app):
        """Test validation with missing link_ids"""
        with app.app_context():
            payload = {}
            response = client.post(
                '/api/links/validate',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 400

    def test_validate_pending_links(self, client, app):
        """Test validating all pending links"""
        with app.app_context():
            # Create some links first
            from app.services.link_import_service import get_link_import_service
            service = get_link_import_service()
            service.import_manual('https://example.com')

            payload = {'limit': 10}
            response = client.post(
                '/api/links/validate/pending',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']

    def test_get_link_statistics(self, client, app):
        """Test getting link statistics"""
        with app.app_context():
            response = client.get('/api/links/statistics')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']
            assert 'import' in data['data']
            assert 'validation' in data['data']


class TestTaskManagementAPI:
    """Tests for task management API endpoints"""

    def test_create_import_task(self, client, app):
        """Test creating an import task"""
        with app.app_context():
            payload = {
                'name': 'Test Task',
                'config': {'test': 'value'}
            }
            response = client.post(
                '/api/tasks/import',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success']
            assert data['data']['name'] == 'Test Task'

    def test_create_task_missing_name(self, client, app):
        """Test creating task with missing name"""
        with app.app_context():
            payload = {}
            response = client.post(
                '/api/tasks/import',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 400

    def test_get_import_tasks(self, client, app):
        """Test getting all import tasks"""
        with app.app_context():
            # Create a task first
            from app.services.task_service import get_task_service
            service = get_task_service()
            service.create_import_task('Test Task')

            response = client.get('/api/tasks/import')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']
            assert len(data['data']['tasks']) >= 1

    def test_get_tasks_with_status_filter(self, client, app):
        """Test getting tasks with status filter"""
        with app.app_context():
            response = client.get('/api/tasks/import?status=pending')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']

    def test_get_single_task(self, client, app):
        """Test getting a single task"""
        with app.app_context():
            # Create a task first
            from app.services.task_service import get_task_service
            service = get_task_service()
            task = service.create_import_task('Test Task')

            response = client.get(f'/api/tasks/import/{task.id}')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']
            assert data['data']['id'] == task.id

    def test_get_nonexistent_task(self, client, app):
        """Test getting a nonexistent task"""
        with app.app_context():
            response = client.get('/api/tasks/import/99999')

            assert response.status_code == 404

    def test_start_task(self, client, app):
        """Test starting a task"""
        with app.app_context():
            # Create a task first
            from app.services.task_service import get_task_service
            service = get_task_service()
            task = service.create_import_task('Test Task')

            response = client.post(f'/api/tasks/import/{task.id}/start')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']
            assert data['data']['status'] == 'running'

    def test_delete_task(self, client, app):
        """Test deleting a task"""
        with app.app_context():
            # Create a task first
            from app.services.task_service import get_task_service
            service = get_task_service()
            task = service.create_import_task('Test Task')

            response = client.delete(f'/api/tasks/import/{task.id}')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']

            # Verify deletion
            deleted_task = ImportTask.query.get(task.id)
            assert deleted_task is None

    def test_get_task_statistics(self, client, app):
        """Test getting task statistics"""
        with app.app_context():
            response = client.get('/api/tasks/statistics')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']
            assert 'total' in data['data']
