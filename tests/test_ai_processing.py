"""Tests for AI processing and Notion export services"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.ai_processing_service import AIProcessingService, get_ai_processing_service
from app.services.notion_export_service import NotionExportService, get_notion_export_service


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


class TestNotionExportService:
    """Tests for NotionExportService"""

    def test_get_service_singleton(self, app):
        """Test service singleton"""
        with app.app_context():
            service1 = get_notion_export_service()
            service2 = get_notion_export_service()
            assert isinstance(service1, NotionExportService)
            assert isinstance(service2, NotionExportService)

    def test_get_export_statistics(self, app):
        """Test getting export statistics"""
        with app.app_context():
            service = NotionExportService()
            stats = service.get_export_statistics()

            assert 'total_exports' in stats
            assert 'completed' in stats
            assert 'failed' in stats
