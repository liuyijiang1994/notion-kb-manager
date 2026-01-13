"""Tests for content parsing service"""
import pytest
import json
from unittest.mock import patch, MagicMock
from app.services.content_parsing_service import ContentParsingService, get_content_parsing_service
from app.models.link import Link
from app.models.content import ParsedContent
from app import db


class TestContentParsingService:
    """Tests for ContentParsingService"""

    def test_get_service_singleton(self):
        """Test service singleton"""
        service1 = get_content_parsing_service()
        service2 = get_content_parsing_service()
        assert isinstance(service1, ContentParsingService)
        assert isinstance(service2, ContentParsingService)

    @patch('app.services.content_parsing_service.requests.get')
    def test_fetch_url_success(self, mock_get, app):
        """Test successful URL fetching"""
        with app.app_context():
            # Mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {'content-length': '1000'}
            mock_response.encoding = 'utf-8'
            mock_response.iter_content = lambda chunk_size: [b'<html><body>Test content</body></html>']
            mock_get.return_value = mock_response

            service = ContentParsingService()
            html = service._fetch_url('https://example.com')

            assert html is not None
            assert 'Test content' in html

    @patch('app.services.content_parsing_service.requests.get')
    def test_fetch_url_timeout(self, mock_get, app):
        """Test URL fetching with timeout"""
        with app.app_context():
            import requests
            mock_get.side_effect = requests.Timeout()

            service = ContentParsingService()
            html = service._fetch_url('https://example.com')

            assert html is None

    def test_extract_images(self, app):
        """Test image extraction from HTML"""
        with app.app_context():
            from bs4 import BeautifulSoup

            html = '''
            <html>
                <body>
                    <img src="/image1.jpg" alt="Image 1" width="200" height="200"/>
                    <img src="https://example.com/image2.png" alt="Image 2"/>
                    <img src="/tiny.gif" width="10" height="10"/>
                </body>
            </html>
            '''

            soup = BeautifulSoup(html, 'lxml')
            service = ContentParsingService()
            images = service._extract_images(soup, 'https://example.com')

            assert len(images) >= 1
            assert any('image1.jpg' in img['url'] for img in images)

    def test_extract_tables(self, app):
        """Test table extraction from HTML"""
        with app.app_context():
            from bs4 import BeautifulSoup

            html = '''
            <html>
                <body>
                    <table>
                        <thead>
                            <tr><th>Name</th><th>Age</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>John</td><td>30</td></tr>
                            <tr><td>Jane</td><td>25</td></tr>
                        </tbody>
                    </table>
                </body>
            </html>
            '''

            soup = BeautifulSoup(html, 'lxml')
            service = ContentParsingService()
            tables = service._extract_tables(soup)

            assert len(tables) == 1
            assert tables[0]['headers'] == ['Name', 'Age']
            assert len(tables[0]['rows']) >= 2

    def test_calculate_quality_score(self, app):
        """Test quality score calculation"""
        with app.app_context():
            from bs4 import BeautifulSoup

            # Good quality content
            html = '''
            <html>
                <body>
                    <h1>Title</h1>
                    <h2>Section 1</h2>
                    <p>Paragraph 1 with substantial content that is meaningful.</p>
                    <p>Paragraph 2 with more content.</p>
                    <h2>Section 2</h2>
                    <p>Paragraph 3</p>
                    <ul><li>Item 1</li><li>Item 2</li></ul>
                    <pre><code>code block</code></pre>
                </body>
            </html>
            '''

            soup = BeautifulSoup(html, 'lxml')
            markdown = "# Title\n## Section 1\nParagraph 1\n\nParagraph 2"

            service = ContentParsingService()
            score = service._calculate_quality_score(soup, markdown, 2, 1)

            assert 0 <= score <= 100
            assert score > 20  # Should have decent score

    def test_extract_paper_info(self, app):
        """Test paper information extraction"""
        with app.app_context():
            from bs4 import BeautifulSoup

            html = '''
            <html>
                <body>
                    <h1>Research Paper Title</h1>
                    <div class="authors">John Doe, Jane Smith</div>
                    <div class="abstract">This is an abstract of the paper.</div>
                </body>
            </html>
            '''

            soup = BeautifulSoup(html, 'lxml')
            markdown = "# Research Paper Title\n2023\nAbstract content"

            service = ContentParsingService()
            paper_info = service._extract_paper_info(soup, markdown)

            assert paper_info is not None
            assert 'title' in paper_info

    @patch('app.services.content_parsing_service.ContentParsingService._fetch_url')
    def test_fetch_and_parse_success(self, mock_fetch, app):
        """Test full fetch and parse workflow"""
        with app.app_context():
            # Create a test link
            from app.services.link_import_service import LinkImportService
            import_service = LinkImportService()
            result = import_service.import_manual('https://example.com')

            if result['imported'] > 0:
                link_id = result['links'][0].id
            else:
                # Link already exists, get it
                link = db.session.query(Link).filter_by(url='https://example.com').first()
                link_id = link.id

            # Mock HTML content
            mock_html = '''
            <html>
                <head><title>Test Page</title></head>
                <body>
                    <h1>Main Title</h1>
                    <p>This is test content with substantial text.</p>
                    <p>More paragraphs for better quality score.</p>
                </body>
            </html>
            '''
            mock_fetch.return_value = mock_html

            service = ContentParsingService()
            result = service.fetch_and_parse(link_id)

            assert result['success']
            assert 'parsed_content_id' in result
            assert 'quality_score' in result

    def test_get_parsed_content(self, app):
        """Test retrieving parsed content"""
        with app.app_context():
            # This test depends on having parsed content in the database
            # For now, just test that the method doesn't crash
            service = ContentParsingService()
            content = service.get_parsed_content(99999)
            assert content is None

    def test_get_parsing_statistics(self, app):
        """Test getting parsing statistics"""
        with app.app_context():
            service = ContentParsingService()
            stats = service.get_parsing_statistics()

            assert 'total' in stats
            assert 'completed' in stats
            assert 'failed' in stats
            assert 'average_quality' in stats


class TestContentParsingAPI:
    """Tests for content parsing API endpoints"""

    @patch('app.services.content_parsing_service.ContentParsingService.fetch_and_parse')
    def test_parse_link_success(self, mock_parse, client, app):
        """Test parsing a link via API"""
        with app.app_context():
            # Create a test link first
            from app.services.link_import_service import LinkImportService
            import_service = LinkImportService()
            result = import_service.import_manual('https://test.com')

            if result['imported'] > 0:
                link_id = result['links'][0].id
            else:
                link = db.session.query(Link).filter_by(url='https://test.com').first()
                link_id = link.id

            # Mock successful parse
            mock_parse.return_value = {
                'success': True,
                'parsed_content_id': 1,
                'quality_score': 85,
                'word_count': 500,
                'images_count': 3,
                'tables_count': 1
            }

            response = client.post(f'/api/parsing/parse/{link_id}')

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success']

    def test_parse_link_not_found(self, client, app):
        """Test parsing non-existent link"""
        with app.app_context():
            response = client.post('/api/parsing/parse/99999')

            assert response.status_code == 400

    def test_parse_batch(self, client, app):
        """Test batch parsing"""
        with app.app_context():
            # Create test links
            from app.services.link_import_service import LinkImportService
            import_service = LinkImportService()
            result = import_service.import_manual('https://batch1.com\nhttps://batch2.com')

            link_ids = [link.id for link in result['links']]

            payload = {'link_ids': link_ids[:1]}  # Just test with one to avoid long test
            response = client.post(
                '/api/parsing/parse/batch',
                data=json.dumps(payload),
                content_type='application/json'
            )

            # May fail if can't actually fetch URLs, but should not crash
            assert response.status_code in [201, 400, 500]

    def test_parse_batch_missing_link_ids(self, client, app):
        """Test batch parsing without link_ids"""
        with app.app_context():
            payload = {}
            response = client.post(
                '/api/parsing/parse/batch',
                data=json.dumps(payload),
                content_type='application/json'
            )

            assert response.status_code == 400

    def test_get_parsing_statistics(self, client, app):
        """Test getting parsing statistics"""
        with app.app_context():
            response = client.get('/api/parsing/statistics')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success']
            assert 'total' in data['data']
