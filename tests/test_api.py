"""
Tests for API endpoints
"""
import pytest
import json


class TestHealthEndpoints:
    """Test cases for health check endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns application info"""
        response = client.get('/')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Notion KB Manager'
        assert 'version' in data
        assert data['status'] == 'running'

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

    def test_api_ping_endpoint(self, client):
        """Test API ping endpoint"""
        response = client.get('/api/ping')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['message'] == 'pong'
        assert 'timestamp' in data


class TestErrorHandlers:
    """Test cases for error handlers"""

    def test_404_error_handler(self, client):
        """Test 404 error handler returns proper format"""
        response = client.get('/nonexistent-endpoint')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
        assert data['error']['code'] == 'RES_001'
        assert 'not found' in data['error']['message'].lower()

    def test_method_not_allowed(self, client):
        """Test 405 method not allowed"""
        response = client.post('/health')

        assert response.status_code == 405


class TestResponseFormats:
    """Test cases for response format consistency"""

    def test_success_response_format(self, client):
        """Test success response has consistent format"""
        response = client.get('/api/ping')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Check required fields
        assert 'success' in data
        assert 'timestamp' in data
        assert data['success'] is True

        # Check timestamp format (ISO 8601)
        assert 'T' in data['timestamp']
        assert 'Z' in data['timestamp']

    def test_error_response_format(self, client):
        """Test error response has consistent format"""
        response = client.get('/nonexistent')

        assert response.status_code == 404
        data = json.loads(response.data)

        # Check required fields
        assert 'success' in data
        assert 'error' in data
        assert data['success'] is False

        # Check error structure
        assert 'code' in data['error']
        assert 'message' in data['error']


class TestCORS:
    """Test cases for CORS configuration"""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present in responses"""
        response = client.get('/api/ping')

        # CORS headers should be present
        assert 'Access-Control-Allow-Origin' in response.headers

    def test_options_request(self, client):
        """Test OPTIONS preflight request"""
        response = client.options('/api/ping')

        # Should allow OPTIONS
        assert response.status_code in [200, 204]


class TestDatabaseIntegration:
    """Test cases for database integration in API"""

    def test_app_has_database_connection(self, app):
        """Test application has active database connection"""
        with app.app_context():
            from app import db
            assert db is not None
            assert db.engine is not None

    def test_default_configurations_created(self, app):
        """Test default configurations are created on app startup"""
        with app.app_context():
            from app import db
            from app.models.configuration import ToolParameters, UserPreferences

            tool_params = db.session.query(ToolParameters).first()
            user_prefs = db.session.query(UserPreferences).first()

            assert tool_params is not None
            assert user_prefs is not None


class TestContentTypeHeaders:
    """Test cases for content type headers"""

    def test_json_content_type(self, client):
        """Test responses have JSON content type"""
        response = client.get('/api/ping')

        assert response.status_code == 200
        assert 'application/json' in response.content_type

    def test_health_check_json_content_type(self, client):
        """Test health check returns JSON"""
        response = client.get('/health')

        assert response.status_code == 200
        assert 'application/json' in response.content_type
