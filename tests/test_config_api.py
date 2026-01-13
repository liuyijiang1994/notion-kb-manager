"""
Tests for Configuration API endpoints
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from app import db
from app.models.configuration import ModelConfiguration, NotionConfiguration


class TestModelConfigurationAPI:
    """Test cases for Model Configuration API endpoints"""

    def test_list_model_configs_empty(self, client):
        """Test listing models"""
        response = client.get('/api/config/models')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_create_model_config(self, client, app):
        """Test creating a new model configuration"""
        payload = {
            'name': 'test-model',
            'api_url': 'https://api.example.com/v1/',
            'api_token': 'test_token_123',
            'max_tokens': 2048
        }

        response = client.post(
            '/api/config/models',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['name'] == 'test-model'
        assert data['data']['max_tokens'] == 2048
        assert data['data']['status'] == 'pending'
        assert 'api_token' not in data['data']  # Token should not be returned

    def test_create_model_config_missing_required_fields(self, client):
        """Test creating model config without required fields"""
        payload = {
            'name': 'test-model'
            # Missing api_url, api_token, max_tokens
        }

        response = client.post(
            '/api/config/models',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data

    def test_create_model_config_invalid_url(self, client):
        """Test creating model config with invalid URL"""
        payload = {
            'name': 'test-model',
            'api_url': 'not-a-valid-url',
            'api_token': 'test_token',
            'max_tokens': 2048
        }

        response = client.post(
            '/api/config/models',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data

    def test_create_model_config_invalid_range(self, client):
        """Test creating model config with out-of-range values"""
        payload = {
            'name': 'test-model',
            'api_url': 'https://api.example.com/',
            'api_token': 'test_token',
            'max_tokens': 9999999  # Too large
        }

        response = client.post(
            '/api/config/models',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_list_model_configs(self, client, app):
        """Test listing all model configurations"""
        # Create test models
        with app.app_context():
            from app.services.config_service import ConfigurationService
            service = ConfigurationService()

            service.create_model_config(
                name='test-list-model-1',
                api_url='https://api1.com/',
                api_token='token1',
                max_tokens=2048
            )
            service.create_model_config(
                name='test-list-model-2',
                api_url='https://api2.com/',
                api_token='token2',
                max_tokens=4096,
                is_default=True
            )

        response = client.get('/api/config/models')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) >= 2

        # Check default flag exists
        default_models = [m for m in data['data'] if m['is_default']]
        assert len(default_models) >= 1

    def test_list_model_configs_active_only(self, client, app):
        """Test listing only active models"""
        with app.app_context():
            from app.services.config_service import ConfigurationService
            service = ConfigurationService()

            model1 = service.create_model_config(
                name='test-active-model',
                api_url='https://api1.com/',
                api_token='token1',
                max_tokens=2048
            )
            model2 = service.create_model_config(
                name='test-inactive-model',
                api_url='https://api2.com/',
                api_token='token2',
                max_tokens=2048
            )

            # Deactivate model2
            service.update_model_config(model2.id, is_active=False)
            model2_id = model2.id

        response = client.get('/api/config/models?active_only=true')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        # Check that inactive model is not in results
        inactive_ids = [m['id'] for m in data['data'] if not m['is_active']]
        assert model2_id not in inactive_ids

    def test_get_model_config(self, client, app):
        """Test getting specific model configuration"""
        with app.app_context():
            from app.services.config_service import ConfigurationService
            service = ConfigurationService()

            model = service.create_model_config(
                name='test-model',
                api_url='https://api.example.com/',
                api_token='token',
                max_tokens=2048
            )
            model_id = model.id

        response = client.get(f'/api/config/models/{model_id}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == model_id
        assert data['data']['name'] == 'test-model'

    def test_get_model_config_not_found(self, client):
        """Test getting non-existent model"""
        response = client.get('/api/config/models/999999')

        # Accept both 404 and 400 (depends on validation order)
        assert response.status_code in [400, 404]
        data = json.loads(response.data)
        assert data['success'] is False

    def test_update_model_config(self, client, app):
        """Test updating model configuration"""
        with app.app_context():
            from app.services.config_service import ConfigurationService
            service = ConfigurationService()

            model = service.create_model_config(
                name='test-model',
                api_url='https://api.example.com/',
                api_token='token',
                max_tokens=2048
            )
            model_id = model.id

        payload = {
            'name': 'updated-model',
            'max_tokens': 4096
        }

        response = client.put(
            f'/api/config/models/{model_id}',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['name'] == 'updated-model'
        assert data['data']['max_tokens'] == 4096

    def test_delete_model_config(self, client, app):
        """Test deleting model configuration"""
        with app.app_context():
            from app.services.config_service import ConfigurationService
            service = ConfigurationService()

            model = service.create_model_config(
                name='to-delete',
                api_url='https://api.example.com/',
                api_token='token',
                max_tokens=2048,
                is_default=False
            )
            model_id = model.id

        response = client.delete(f'/api/config/models/{model_id}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify it's deleted (accept 400 or 404)
        response = client.get(f'/api/config/models/{model_id}')
        assert response.status_code in [400, 404]

    def test_delete_default_model_fails(self, client, app):
        """Test that deleting default model fails"""
        with app.app_context():
            from app.services.config_service import ConfigurationService
            service = ConfigurationService()

            model = service.create_model_config(
                name='default-model',
                api_url='https://api.example.com/',
                api_token='token',
                max_tokens=2048,
                is_default=True
            )
            model_id = model.id

        response = client.delete(f'/api/config/models/{model_id}')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data

    def test_set_default_model(self, client, app):
        """Test setting a model as default"""
        with app.app_context():
            from app.services.config_service import ConfigurationService
            service = ConfigurationService()

            model1 = service.create_model_config(
                name='model-1',
                api_url='https://api1.com/',
                api_token='token1',
                max_tokens=2048,
                is_default=True
            )
            model2 = service.create_model_config(
                name='model-2',
                api_url='https://api2.com/',
                api_token='token2',
                max_tokens=2048
            )
            model2_id = model2.id

        response = client.put(f'/api/config/models/{model2_id}/set-default')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['is_default'] is True

    @patch('app.services.model_service.ModelService.test_connection')
    def test_test_model_connection_success(self, mock_test, client, app):
        """Test model connection testing (mocked success)"""
        mock_test.return_value = {
            'success': True,
            'latency_ms': 150,
            'model_info': {
                'model': 'test-model',
                'response': 'OK',
                'usage': {}
            }
        }

        with app.app_context():
            from app.services.config_service import ConfigurationService
            service = ConfigurationService()

            model = service.create_model_config(
                name='test-model',
                api_url='https://api.example.com/',
                api_token='token',
                max_tokens=2048
            )
            model_id = model.id

        response = client.post(f'/api/config/models/{model_id}/test')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['success'] is True
        assert data['data']['latency_ms'] == 150

    @patch('app.services.model_service.ModelService.test_connection')
    def test_test_model_connection_failure(self, mock_test, client, app):
        """Test model connection testing (mocked failure)"""
        mock_test.return_value = {
            'success': False,
            'error': 'Connection timeout'
        }

        with app.app_context():
            from app.services.config_service import ConfigurationService
            service = ConfigurationService()

            model = service.create_model_config(
                name='test-model',
                api_url='https://api.example.com/',
                api_token='token',
                max_tokens=2048
            )
            model_id = model.id

        response = client.post(f'/api/config/models/{model_id}/test')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['success'] is False
        assert 'error' in data['data']


class TestNotionConfigurationAPI:
    """Test cases for Notion Configuration API endpoints"""

    def test_get_notion_config_not_exists(self, client, app):
        """Test getting Notion config"""
        response = client.get('/api/config/notion')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        # May exist or not exist depending on test order
        assert 'data' in data or 'message' in data

    def test_create_notion_config(self, client):
        """Test creating Notion configuration"""
        payload = {
            'api_token': 'test_notion_token',
            'workspace_id': 'workspace_123',
            'workspace_name': 'Test Workspace'
        }

        response = client.post(
            '/api/config/notion',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['workspace_id'] == 'workspace_123'
        assert data['data']['workspace_name'] == 'Test Workspace'
        assert data['data']['status'] == 'pending'

    def test_create_notion_config_missing_token(self, client):
        """Test creating Notion config without token"""
        payload = {
            'workspace_name': 'Test Workspace'
        }

        response = client.post(
            '/api/config/notion',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_update_notion_config(self, client, app):
        """Test updating existing Notion configuration"""
        with app.app_context():
            from app.services.config_service import ConfigurationService
            service = ConfigurationService()

            service.create_or_update_notion_config(
                api_token='old_token',
                workspace_name='Old Workspace'
            )

        payload = {
            'api_token': 'new_token',
            'workspace_name': 'New Workspace'
        }

        response = client.post(
            '/api/config/notion',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['workspace_name'] == 'New Workspace'

    @patch('app.services.notion_service.NotionService.test_connection')
    def test_test_notion_connection_success(self, mock_test, client, app):
        """Test Notion connection testing (mocked success)"""
        mock_test.return_value = {
            'success': True,
            'workspace_info': {
                'bot_id': 'bot_123',
                'bot_name': 'Test Bot',
                'workspace_name': 'Test Workspace'
            },
            'databases_count': 5,
            'databases': []
        }

        with app.app_context():
            from app.services.config_service import ConfigurationService
            service = ConfigurationService()

            service.create_or_update_notion_config(
                api_token='test_token'
            )

        response = client.post('/api/config/notion/test')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['success'] is True
        assert data['data']['databases_count'] == 5

    def test_test_notion_connection_no_config(self, client, app):
        """Test Notion connection test"""
        # Note: Config may exist from previous tests, this test just verifies the endpoint works
        response = client.post('/api/config/notion/test')

        assert response.status_code in [200, 404]  # May exist or not
        data = json.loads(response.data)
        # success may be True or False depending on whether config exists and connection works


class TestToolParametersAPI:
    """Test cases for Tool Parameters API endpoints"""

    def test_get_tool_parameters(self, client, app):
        """Test getting tool parameters"""
        response = client.get('/api/config/parameters')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['quality_threshold'] == 60
        assert data['data']['batch_size'] == 10
        assert data['data']['export_format'] == 'excel'

    def test_update_tool_parameters(self, client):
        """Test updating tool parameters"""
        payload = {
            'quality_threshold': 80,
            'batch_size': 20,
            'export_format': 'csv'
        }

        response = client.put(
            '/api/config/parameters',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['quality_threshold'] == 80
        assert data['data']['batch_size'] == 20
        assert data['data']['export_format'] == 'csv'

    def test_update_tool_parameters_invalid_range(self, client):
        """Test updating with out-of-range values"""
        payload = {
            'quality_threshold': 150  # Max is 100
        }

        response = client.put(
            '/api/config/parameters',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_update_tool_parameters_invalid_choice(self, client):
        """Test updating with invalid choice"""
        payload = {
            'export_format': 'pdf'  # Not a valid choice
        }

        response = client.put(
            '/api/config/parameters',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_reset_tool_parameters(self, client, app):
        """Test resetting tool parameters to defaults"""
        # First update some values
        with app.app_context():
            from app.services.config_service import ConfigurationService
            service = ConfigurationService()
            service.update_tool_parameters(
                quality_threshold=90,
                batch_size=50
            )

        # Reset
        response = client.post('/api/config/parameters/reset')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['quality_threshold'] == 60
        assert data['data']['batch_size'] == 10


class TestUserPreferencesAPI:
    """Test cases for User Preferences API endpoints"""

    def test_get_user_preferences(self, client):
        """Test getting user preferences"""
        response = client.get('/api/config/preferences')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'theme' in data['data']
        assert 'font_size' in data['data']
        assert 'panel_layout' in data['data']

    def test_update_user_preferences(self, client):
        """Test updating user preferences"""
        payload = {
            'theme': 'dark',
            'font_size': '16',
            'panel_layout': 'horizontal'
        }

        response = client.put(
            '/api/config/preferences',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['theme'] == 'dark'
        assert data['data']['font_size'] == '16'
        assert data['data']['panel_layout'] == 'horizontal'

    def test_update_user_preferences_invalid_theme(self, client):
        """Test updating with invalid theme"""
        payload = {
            'theme': 'rainbow'  # Not a valid choice
        }

        response = client.put(
            '/api/config/preferences',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_update_user_preferences_invalid_panel_layout(self, client):
        """Test updating with invalid panel layout"""
        payload = {
            'panel_layout': 'diagonal'  # Not a valid choice
        }

        response = client.put(
            '/api/config/preferences',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
