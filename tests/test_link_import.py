"""Tests for link import and task management services"""
import pytest
import json
from datetime import datetime
from app.services.link_import_service import LinkImportService, get_link_import_service
from app.services.link_validation_service import LinkValidationService, get_link_validation_service
from app.services.task_service import TaskService, get_task_service
from app.models.link import Link, ImportTask
from app import db


class TestLinkImportService:
    """Tests for LinkImportService"""

    def test_get_service_singleton(self):
        """Test service singleton"""
        service1 = get_link_import_service()
        service2 = get_link_import_service()
        assert isinstance(service1, LinkImportService)
        assert isinstance(service2, LinkImportService)

    def test_extract_urls_from_text_single_line(self, app):
        """Test extracting URLs from single line text"""
        with app.app_context():
            service = LinkImportService()
            text = "https://example.com"
            urls = service._extract_urls_from_text(text)
            assert len(urls) == 1
            assert "https://example.com" in urls

    def test_extract_urls_from_text_multiple(self, app):
        """Test extracting multiple URLs"""
        with app.app_context():
            service = LinkImportService()
            text = """https://example.com
            https://google.com
            https://github.com"""
            urls = service._extract_urls_from_text(text)
            assert len(urls) == 3

    def test_extract_urls_with_mixed_text(self, app):
        """Test extracting URLs from mixed text"""
        with app.app_context():
            service = LinkImportService()
            text = "Check out https://example.com and https://google.com for more info"
            urls = service._extract_urls_from_text(text)
            assert len(urls) == 2

    def test_is_valid_url(self, app):
        """Test URL validation"""
        with app.app_context():
            service = LinkImportService()
            assert service._is_valid_url("https://example.com")
            assert service._is_valid_url("http://example.com")
            assert not service._is_valid_url("ftp://example.com")
            assert not service._is_valid_url("not-a-url")
            assert not service._is_valid_url("")

    def test_extract_title_from_url(self, app):
        """Test title extraction from URL"""
        with app.app_context():
            service = LinkImportService()
            title = service._extract_title_from_url("https://example.com/page")
            assert title == "example.com"

    def test_import_manual_single_url(self, app):
        """Test manual import with single URL"""
        with app.app_context():
            service = LinkImportService()
            result = service.import_manual("https://example.com")

            assert result['success']
            assert result['imported'] == 1
            assert result['total'] == 1

            # Check database
            link = Link.query.filter_by(url="https://example.com").first()
            assert link is not None
            assert link.source == 'manual'

    def test_import_manual_multiple_urls(self, app):
        """Test manual import with multiple URLs"""
        with app.app_context():
            service = LinkImportService()
            text = """https://example.com
            https://google.com
            https://github.com"""
            result = service.import_manual(text)

            assert result['success']
            assert result['imported'] == 3
            assert result['total'] == 3

    def test_import_manual_duplicate_detection(self, app):
        """Test duplicate detection in manual import"""
        with app.app_context():
            service = LinkImportService()

            # First import
            result1 = service.import_manual("https://example.com")
            assert result1['imported'] == 1

            # Second import - should detect duplicate
            result2 = service.import_manual("https://example.com")
            assert result2['duplicates'] == 1
            assert result2['imported'] == 0

    def test_import_manual_no_urls(self, app):
        """Test manual import with no valid URLs"""
        with app.app_context():
            service = LinkImportService()
            result = service.import_manual("no urls here")

            assert not result['success']
            assert 'No valid URLs' in result['error']

    def test_parse_html_bookmarks(self, app):
        """Test parsing HTML bookmarks"""
        with app.app_context():
            service = LinkImportService()
            html = '''
            <!DOCTYPE NETSCAPE-Bookmark-file-1>
            <HTML>
            <DL>
                <DT><A HREF="https://example.com" ADD_DATE="1234567890">Example Site</A>
                <DT><A HREF="https://google.com" ADD_DATE="1234567891">Google</A>
            </DL>
            </HTML>
            '''
            links = service._parse_html_bookmarks(html)

            assert len(links) == 2
            assert links[0]['url'] == "https://example.com"
            assert links[0]['title'] == "Example Site"
            assert links[1]['url'] == "https://google.com"

    def test_parse_json_bookmarks(self, app):
        """Test parsing JSON bookmarks (Chrome format)"""
        with app.app_context():
            service = LinkImportService()
            bookmark_data = {
                "roots": {
                    "bookmark_bar": {
                        "children": [
                            {
                                "type": "url",
                                "url": "https://example.com",
                                "name": "Example Site"
                            },
                            {
                                "type": "url",
                                "url": "https://google.com",
                                "name": "Google"
                            }
                        ]
                    }
                }
            }
            json_str = json.dumps(bookmark_data)
            links = service._parse_json_bookmarks(json_str)

            assert len(links) == 2
            assert any(link['url'] == "https://example.com" for link in links)

    def test_import_from_favorites_html(self, app):
        """Test importing from HTML favorites file"""
        with app.app_context():
            service = LinkImportService()
            html = '''
            <HTML>
            <DL>
                <DT><A HREF="https://example.com">Example</A>
            </DL>
            </HTML>
            '''
            result = service.import_from_favorites(html, file_type='html')

            assert result['success']
            assert result['imported'] == 1

    def test_check_duplicate(self, app):
        """Test duplicate checking"""
        with app.app_context():
            service = LinkImportService()

            # No duplicate initially
            is_dup, existing = service.check_duplicate("https://example.com")
            assert not is_dup
            assert existing is None

            # Create a link
            service.import_manual("https://example.com")

            # Now should be duplicate
            is_dup, existing = service.check_duplicate("https://example.com")
            assert is_dup
            assert existing is not None

    def test_get_import_statistics(self, app):
        """Test getting import statistics"""
        with app.app_context():
            service = LinkImportService()

            # Import some links
            service.import_manual("https://example.com")
            service.import_manual("https://google.com")

            stats = service.get_import_statistics()
            assert stats['total_links'] >= 2
            assert 'manual' in stats['by_source']


class TestLinkValidationService:
    """Tests for LinkValidationService"""

    def test_get_service_singleton(self):
        """Test service singleton"""
        service1 = get_link_validation_service()
        service2 = get_link_validation_service()
        assert isinstance(service1, LinkValidationService)
        assert isinstance(service2, LinkValidationService)

    def test_validate_single_valid_url(self, app):
        """Test validating a single valid URL"""
        with app.app_context():
            service = LinkValidationService()
            result = service.validate_single("https://www.google.com")

            assert 'status_code' in result
            assert 'is_valid' in result
            assert result['url'] == "https://www.google.com"

    def test_validate_single_invalid_url(self, app):
        """Test validating an invalid URL"""
        with app.app_context():
            service = LinkValidationService()
            result = service.validate_single("https://this-domain-definitely-does-not-exist-12345.com")

            assert result['is_valid'] == False
            assert result['status'] in ['error', 'connection_error', 'timeout']

    def test_validate_batch(self, app):
        """Test batch validation"""
        with app.app_context():
            # Create some links
            import_service = LinkImportService()
            import_service.import_manual("https://www.google.com")

            links = Link.query.all()
            link_ids = [link.id for link in links]

            service = LinkValidationService()
            result = service.validate_batch(link_ids, update_db=False)

            assert result['success']
            assert result['total'] == len(link_ids)
            assert 'results' in result

    def test_get_validation_statistics(self, app):
        """Test getting validation statistics"""
        with app.app_context():
            # Create a link
            import_service = LinkImportService()
            import_service.import_manual("https://example.com")

            service = LinkValidationService()
            stats = service.get_validation_statistics()

            assert 'total' in stats
            assert 'valid' in stats
            assert 'invalid' in stats
            assert 'pending' in stats


class TestTaskService:
    """Tests for TaskService"""

    def test_get_service_singleton(self):
        """Test service singleton"""
        service1 = get_task_service()
        service2 = get_task_service()
        assert isinstance(service1, TaskService)
        assert isinstance(service2, TaskService)

    def test_create_import_task(self, app):
        """Test creating an import task"""
        with app.app_context():
            service = TaskService()
            task = service.create_import_task(
                name="Test Task",
                config={'test': 'config'}
            )

            assert task.id is not None
            assert task.name == "Test Task"
            assert task.status == 'pending'
            assert task.config['test'] == 'config'

    def test_get_task(self, app):
        """Test getting a task by ID"""
        with app.app_context():
            service = TaskService()
            task = service.create_import_task(name="Test Task")

            retrieved = service.get_task(task.id)
            assert retrieved is not None
            assert retrieved.id == task.id
            assert retrieved.name == "Test Task"

    def test_get_all_tasks(self, app):
        """Test getting all tasks"""
        with app.app_context():
            service = TaskService()
            service.create_import_task(name="Task 1")
            service.create_import_task(name="Task 2")

            tasks = service.get_all_tasks()
            assert len(tasks) >= 2

    def test_update_task_status(self, app):
        """Test updating task status"""
        with app.app_context():
            service = TaskService()
            task = service.create_import_task(name="Test Task")

            updated = service.update_task_status(
                task.id,
                status='running',
                total_links=10,
                processed_links=5
            )

            assert updated.status == 'running'
            assert updated.total_links == 10
            assert updated.processed_links == 5
            assert updated.started_at is not None

    def test_start_task(self, app):
        """Test starting a task"""
        with app.app_context():
            service = TaskService()
            task = service.create_import_task(name="Test Task")

            started = service.start_task(task.id)
            assert started.status == 'running'
            assert started.started_at is not None

    def test_complete_task(self, app):
        """Test completing a task"""
        with app.app_context():
            service = TaskService()
            task = service.create_import_task(name="Test Task")
            service.start_task(task.id)

            completed = service.complete_task(task.id)
            assert completed.status == 'completed'
            assert completed.completed_at is not None

    def test_fail_task(self, app):
        """Test failing a task"""
        with app.app_context():
            service = TaskService()
            task = service.create_import_task(name="Test Task")

            failed = service.fail_task(task.id, "Test error")
            assert failed.status == 'failed'
            assert failed.config['error'] == "Test error"

    def test_update_progress(self, app):
        """Test updating task progress"""
        with app.app_context():
            service = TaskService()
            task = service.create_import_task(name="Test Task")

            updated = service.update_progress(task.id, 50)
            assert updated.processed_links == 50

    def test_delete_task(self, app):
        """Test deleting a task"""
        with app.app_context():
            service = TaskService()
            task = service.create_import_task(name="Test Task")
            task_id = task.id

            success = service.delete_task(task_id)
            assert success

            # Task should be gone
            deleted = service.get_task(task_id)
            assert deleted is None

    def test_get_task_statistics(self, app):
        """Test getting task statistics"""
        with app.app_context():
            service = TaskService()
            service.create_import_task(name="Task 1")
            service.create_import_task(name="Task 2")

            stats = service.get_task_statistics()
            assert stats['total'] >= 2
            assert stats['pending'] >= 2

    def test_get_task_links(self, app):
        """Test getting task links"""
        with app.app_context():
            task_service = TaskService()
            task = task_service.create_import_task(name="Test Task")

            # Import links with task ID
            import_service = LinkImportService()
            import_service.import_manual(
                "https://example.com\nhttps://google.com",
                task_id=task.id
            )

            links = task_service.get_task_links(task.id)
            assert len(links) == 2

    def test_get_task_summary(self, app):
        """Test getting task summary"""
        with app.app_context():
            task_service = TaskService()
            task = task_service.create_import_task(name="Test Task")

            summary = task_service.get_task_summary(task.id)
            assert summary is not None
            assert summary['name'] == "Test Task"
            assert 'link_statistics' in summary
