"""
Integration tests for Phase 6 features
- Content management
- Backup and restore
- Log management
- Help and feedback
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from app import create_app, db
from app.models.link import Link
from app.models.content import ParsedContent, AIProcessedContent
from app.models.configuration import ModelConfiguration
from app.models.system import Backup, OperationLog, Feedback
from app.services.content_management_service import get_content_management_service
from app.services.backup_service import get_backup_service
from app.services.log_service import get_log_service
from app.services.feedback_service import get_feedback_service, get_help_service


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
def sample_content(app):
    """Create sample content for testing"""
    with app.app_context():
        # Create links
        links = []
        for i in range(5):
            link = Link(
                url=f'https://example.com/page{i}',
                title=f'Test Page {i}',
                source='manual'
            )
            db.session.add(link)
            links.append(link)

        db.session.flush()

        # Create parsed content
        parsed_contents = []
        for i, link in enumerate(links):
            parsed = ParsedContent(
                link_id=link.id,
                raw_content=f'<html>Test {i}</html>',
                formatted_content=f'Test content {i}',
                quality_score=85 + i,
                status='completed'
            )
            db.session.add(parsed)
            parsed_contents.append(parsed)

        db.session.commit()

        return {
            'links': links,
            'parsed_contents': parsed_contents
        }


class TestContentManagement:
    """Test content management service and API"""

    def test_get_local_content(self, app, sample_content):
        """Test getting local content with pagination"""
        with app.app_context():
            service = get_content_management_service()
            result = service.get_local_content(page=1, per_page=3)

            assert len(result['items']) == 3
            assert result['pagination']['total'] == 5
            assert result['pagination']['pages'] == 2

    def test_get_local_content_with_search(self, app, sample_content):
        """Test content search"""
        with app.app_context():
            service = get_content_management_service()
            result = service.get_local_content(search='Page 0')

            assert len(result['items']) == 1
            assert result['items'][0]['title'] == 'Test Page 0'

    def test_get_content_details(self, app, sample_content):
        """Test getting detailed content information"""
        with app.app_context():
            parsed_id = sample_content['parsed_contents'][0].id
            service = get_content_management_service()
            result = service.get_content_details(parsed_id)

            assert result is not None
            assert result['parsed_content']['id'] == parsed_id
            assert result['parsed_content']['title'] == 'Test Page 0'

    def test_update_content(self, app, sample_content):
        """Test updating content"""
        with app.app_context():
            parsed_id = sample_content['parsed_contents'][0].id
            service = get_content_management_service()

            updates = {
                'formatted_content': 'Updated content'
            }
            success = service.update_content(parsed_id, updates)

            assert success is True

            # Verify update
            parsed = db.session.query(ParsedContent).get(parsed_id)
            assert parsed.formatted_content == 'Updated content'

    def test_delete_content_batch(self, app, sample_content):
        """Test batch delete content"""
        with app.app_context():
            service = get_content_management_service()

            content_ids = [pc.id for pc in sample_content['parsed_contents'][:3]]
            deleted_count = service.delete_content_batch(content_ids)

            assert deleted_count == 3

            # Verify deletion
            remaining = db.session.query(ParsedContent).count()
            assert remaining == 2

    def test_get_content_statistics(self, app, sample_content):
        """Test content statistics"""
        with app.app_context():
            service = get_content_management_service()
            stats = service.get_content_statistics()

            assert stats['total_parsed'] == 5
            assert stats['average_quality_score'] > 0
            assert 'by_type' in stats

    def test_content_management_api(self, client, app, sample_content):
        """Test content management API endpoints"""
        with app.app_context():
            # Get local content
            response = client.get('/api/content/local?page=1&per_page=3')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert len(data['data']['items']) == 3

            # Get content details
            parsed_id = sample_content['parsed_contents'][0].id
            response = client.get(f'/api/content/local/{parsed_id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['data']['parsed_content']['id'] == parsed_id


class TestBackupService:
    """Test backup and restore service"""

    def test_create_backup(self, app):
        """Test creating a backup"""
        with app.app_context():
            service = get_backup_service()

            result = service.create_backup(
                backup_type='manual',
                include_database=True,
                include_files=False,
                retention_days=30
            )

            assert result['success'] is True
            assert 'backup_id' in result
            assert 'filename' in result

    def test_list_backups(self, app):
        """Test listing backups"""
        with app.app_context():
            service = get_backup_service()

            # Create some backups
            service.create_backup(backup_type='manual')
            service.create_backup(backup_type='auto')

            result = service.list_backups(page=1, per_page=10)

            assert result['success'] is True
            assert len(result['items']) == 2

    def test_get_backup_details(self, app):
        """Test getting backup details"""
        with app.app_context():
            service = get_backup_service()

            # Create backup
            result = service.create_backup(backup_type='manual')
            backup_id = result['backup_id']

            # Get details
            details = service.get_backup_details(backup_id)

            assert details is not None
            assert details['id'] == backup_id
            assert 'files_by_type' in details

    def test_delete_backup(self, app):
        """Test deleting backup"""
        with app.app_context():
            service = get_backup_service()

            # Create backup
            result = service.create_backup(backup_type='manual')
            backup_id = result['backup_id']

            # Delete backup
            success = service.delete_backup(backup_id, delete_file=True)

            assert success is True

            # Verify deletion
            backup = db.session.query(Backup).get(backup_id)
            assert backup is None

    def test_cleanup_expired_backups(self, app):
        """Test cleanup expired backups"""
        with app.app_context():
            # Create expired backup
            backup = Backup(
                filename='old_backup.zip',
                filepath='backups/old_backup.zip',
                size=1000,
                type='auto',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(backup)
            db.session.commit()

            service = get_backup_service()
            result = service.cleanup_expired_backups()

            assert result['success'] is True
            assert result['deleted_count'] == 1

    def test_backup_statistics(self, app):
        """Test backup statistics"""
        with app.app_context():
            service = get_backup_service()

            # Create backups
            service.create_backup(backup_type='manual')
            service.create_backup(backup_type='auto')

            stats = service.get_backup_statistics()

            assert stats['total_backups'] == 2
            assert stats['manual_backups'] == 1
            assert stats['auto_backups'] == 1

    def test_backup_api(self, client, app):
        """Test backup API endpoints"""
        with app.app_context():
            # Create backup
            response = client.post('/api/backup/', json={
                'type': 'manual',
                'include_database': True,
                'include_files': False
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

            # List backups
            response = client.get('/api/backup/')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


class TestLogService:
    """Test log management service"""

    def test_create_log(self, app):
        """Test creating a log entry"""
        with app.app_context():
            service = get_log_service()

            log_id = service.create_log(
                level='info',
                module='test',
                action='test_action',
                message='Test message',
                user_id='test_user'
            )

            assert log_id > 0

            # Verify log was created
            log = db.session.query(OperationLog).get(log_id)
            assert log is not None
            assert log.level == 'info'
            assert log.module == 'test'

    def test_get_logs(self, app):
        """Test getting logs with filtering"""
        with app.app_context():
            service = get_log_service()

            # Create some logs
            for i in range(5):
                service.create_log(
                    level='info' if i % 2 == 0 else 'error',
                    module='test_module',
                    action=f'action_{i}',
                    message=f'Test message {i}'
                )

            result = service.get_logs(page=1, per_page=10)

            assert len(result['items']) == 5
            assert result['pagination']['total'] == 5

    def test_get_logs_with_filter(self, app):
        """Test getting logs with level filter"""
        with app.app_context():
            service = get_log_service()

            # Create logs with different levels
            service.create_log(level='info', module='test', action='test', message='Info')
            service.create_log(level='error', module='test', action='test', message='Error')
            service.create_log(level='warning', module='test', action='test', message='Warning')

            result = service.get_logs(level='error', page=1, per_page=10)

            assert len(result['items']) == 1
            assert result['items'][0]['level'] == 'error'

    def test_get_log_statistics(self, app):
        """Test log statistics"""
        with app.app_context():
            service = get_log_service()

            # Create logs
            service.create_log(level='info', module='test', action='test', message='Info')
            service.create_log(level='error', module='test', action='test', message='Error')

            stats = service.get_log_statistics(days=7)

            assert stats['total_logs'] == 2
            assert 'by_level' in stats
            assert 'by_module' in stats

    def test_cleanup_old_logs(self, app):
        """Test cleanup old logs"""
        with app.app_context():
            # Create old log
            old_log = OperationLog(
                level='info',
                module='test',
                action='test',
                message='Old log',
                created_at=datetime.utcnow() - timedelta(days=100)
            )
            db.session.add(old_log)
            db.session.commit()

            service = get_log_service()
            deleted_count = service.cleanup_old_logs(days=90)

            assert deleted_count == 1

    def test_export_logs(self, app):
        """Test exporting logs"""
        with app.app_context():
            service = get_log_service()

            # Create logs
            service.create_log(level='info', module='test', action='test', message='Log 1')
            service.create_log(level='error', module='test', action='test', message='Log 2')

            exported = service.export_logs()

            assert len(exported) == 2
            assert exported[0]['level'] in ['info', 'error']

    def test_get_modules(self, app):
        """Test getting unique modules"""
        with app.app_context():
            service = get_log_service()

            # Create logs with different modules
            service.create_log(level='info', module='parsing', action='test', message='Test')
            service.create_log(level='info', module='ai_processing', action='test', message='Test')

            modules = service.get_modules()

            assert len(modules) == 2
            assert 'parsing' in modules
            assert 'ai_processing' in modules

    def test_log_api(self, client, app):
        """Test log management API endpoints"""
        with app.app_context():
            service = get_log_service()

            # Create some logs
            service.create_log(level='info', module='test', action='test', message='Test')

            # Get logs
            response = client.get('/api/logs/?page=1&per_page=10')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

            # Get statistics
            response = client.get('/api/logs/statistics?days=7')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


class TestFeedbackService:
    """Test feedback service"""

    def test_submit_feedback(self, app):
        """Test submitting feedback"""
        with app.app_context():
            service = get_feedback_service()

            result = service.submit_feedback(
                feedback_type='bug',
                content='This is a test bug report',
                user_email='test@example.com'
            )

            assert result['success'] is True
            assert 'feedback_id' in result

    def test_get_feedback_list(self, app):
        """Test getting feedback list"""
        with app.app_context():
            service = get_feedback_service()

            # Submit feedback
            service.submit_feedback(
                feedback_type='bug',
                content='Bug report',
                user_email='test@example.com'
            )
            service.submit_feedback(
                feedback_type='feature',
                content='Feature request',
                user_email='test@example.com'
            )

            result = service.get_feedback_list(page=1, per_page=10)

            assert result['success'] is True
            assert len(result['items']) == 2

    def test_get_feedback_details(self, app):
        """Test getting feedback details"""
        with app.app_context():
            service = get_feedback_service()

            # Submit feedback
            result = service.submit_feedback(
                feedback_type='bug',
                content='Bug report',
                user_email='test@example.com'
            )
            feedback_id = result['feedback_id']

            # Get details
            details = service.get_feedback_details(feedback_id)

            assert details is not None
            assert details['id'] == feedback_id
            assert details['type'] == 'bug'

    def test_update_feedback_status(self, app):
        """Test updating feedback status"""
        with app.app_context():
            service = get_feedback_service()

            # Submit feedback
            result = service.submit_feedback(
                feedback_type='bug',
                content='Bug report'
            )
            feedback_id = result['feedback_id']

            # Update status
            success = service.update_feedback_status(feedback_id, 'reviewed')

            assert success is True

            # Verify update
            feedback = db.session.query(Feedback).get(feedback_id)
            assert feedback.status == 'reviewed'

    def test_delete_feedback(self, app):
        """Test deleting feedback"""
        with app.app_context():
            service = get_feedback_service()

            # Submit feedback
            result = service.submit_feedback(
                feedback_type='bug',
                content='Bug report'
            )
            feedback_id = result['feedback_id']

            # Delete feedback
            success = service.delete_feedback(feedback_id)

            assert success is True

            # Verify deletion
            feedback = db.session.query(Feedback).get(feedback_id)
            assert feedback is None

    def test_feedback_statistics(self, app):
        """Test feedback statistics"""
        with app.app_context():
            service = get_feedback_service()

            # Submit feedback
            service.submit_feedback(feedback_type='bug', content='Bug')
            service.submit_feedback(feedback_type='feature', content='Feature')

            stats = service.get_feedback_statistics()

            assert stats['total_feedback'] == 2
            assert 'by_type' in stats
            assert 'by_status' in stats

    def test_feedback_api(self, client, app):
        """Test feedback API endpoints"""
        with app.app_context():
            # Submit feedback
            response = client.post('/api/feedback/', json={
                'type': 'bug',
                'content': 'This is a test bug report'
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

            # Get feedback list
            response = client.get('/api/feedback/')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


class TestHelpService:
    """Test help service"""

    def test_get_help_topics(self, app):
        """Test getting help topics"""
        with app.app_context():
            service = get_help_service()

            topics = service.get_help_topics()

            assert len(topics) > 0
            assert 'id' in topics[0]
            assert 'title' in topics[0]

    def test_get_help_topic(self, app):
        """Test getting specific help topic"""
        with app.app_context():
            service = get_help_service()

            topic = service.get_help_topic('getting_started')

            assert topic is not None
            assert topic['id'] == 'getting_started'
            assert 'content' in topic

    def test_search_help(self, app):
        """Test searching help topics"""
        with app.app_context():
            service = get_help_service()

            results = service.search_help('configuration')

            assert len(results) > 0

    def test_help_api(self, client, app):
        """Test help API endpoints"""
        with app.app_context():
            # Get topics
            response = client.get('/api/help/topics')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

            # Get specific topic
            response = client.get('/api/help/topics/getting_started')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

            # Search help
            response = client.get('/api/help/search?q=configuration')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
