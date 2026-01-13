"""Tests for AI processing and Notion import services"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.ai_processing_service import AIProcessingService, get_ai_processing_service
from app.services.notion_import_service import NotionImportService, get_notion_import_service


class TestAIProcessingService:
    """Tests for AIProcessingService"""

    def test_get_service_singleton(self, app):
        """Test service singleton"""
        with app.app_context():
            service1 = get_ai_processing_service()
            service2 = get_ai_processing_service()
            assert isinstance(service1, AIProcessingService)
            assert isinstance(service2, AIProcessingService)

    def test_get_processing_statistics(self, app):
        """Test getting processing statistics"""
        with app.app_context():
            service = AIProcessingService()
            stats = service.get_processing_statistics()

            assert 'total_processed' in stats
            assert 'total_tokens_used' in stats
            assert 'total_cost' in stats
            assert 'by_model' in stats


class TestNotionImportService:
    """Tests for NotionImportService"""

    def test_get_service_singleton(self, app):
        """Test service singleton"""
        with app.app_context():
            service1 = get_notion_import_service()
            service2 = get_notion_import_service()
            assert isinstance(service1, NotionImportService)
            assert isinstance(service2, NotionImportService)

    def test_get_import_statistics(self, app):
        """Test getting import statistics"""
        with app.app_context():
            service = NotionImportService()
            stats = service.get_import_statistics()

            assert 'total_imports' in stats
            assert 'completed' in stats
            assert 'failed' in stats
