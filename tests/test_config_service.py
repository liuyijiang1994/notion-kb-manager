"""
Tests for configuration service
"""
import pytest
from app import db
from app.services.config_service import ConfigurationService
from app.models.configuration import (
    ModelConfiguration, NotionConfiguration,
    ToolParameters, UserPreferences
)
from app.utils.exceptions import NotFoundError, ValidationError, DatabaseError


class TestModelConfiguration:
    """Test cases for Model Configuration CRUD operations"""

    def test_create_model_config(self, app):
        """Test creating a new model configuration"""
        with app.app_context():
            service = ConfigurationService()

            model = service.create_model_config(
                name='GPT-4',
                api_url='https://api.openai.com/v1',
                api_token='test_token',
                max_tokens=4096,
                timeout=30,
                rate_limit=60,
                is_default=True
            )

            assert model is not None
            assert model.id is not None
            assert model.name == 'GPT-4'
            assert model.api_url == 'https://api.openai.com/v1'
            assert model.max_tokens == 4096
            assert model.is_default is True
            assert model.is_active is True
            assert model.status == 'pending'
            assert model.api_token_encrypted is not None

    def test_create_model_config_encrypts_token(self, app):
        """Test that API token is encrypted when creating model config"""
        with app.app_context():
            service = ConfigurationService()
            plaintext_token = 'my_secret_token_12345'

            model = service.create_model_config(
                name='Test-Model',
                api_url='https://api.test.com',
                api_token=plaintext_token,
                max_tokens=2048
            )

            # Token should be encrypted (not equal to plaintext)
            assert model.api_token_encrypted != plaintext_token

            # Should be able to decrypt
            decrypted = service.encryption_service.decrypt(model.api_token_encrypted)
            assert decrypted == plaintext_token

    def test_create_model_config_sets_only_one_default(self, app):
        """Test that setting a new default unsets previous default"""
        with app.app_context():
            service = ConfigurationService()

            # Create first default model
            model1 = service.create_model_config(
                name='Model-1',
                api_url='https://api1.com',
                api_token='token1',
                max_tokens=2048,
                is_default=True
            )

            assert model1.is_default is True

            # Create second default model
            model2 = service.create_model_config(
                name='Model-2',
                api_url='https://api2.com',
                api_token='token2',
                max_tokens=2048,
                is_default=True
            )

            # Refresh model1 from database
            db.session.refresh(model1)

            assert model2.is_default is True
            assert model1.is_default is False

    def test_get_model_config(self, app, sample_model_config):
        """Test retrieving a model configuration by ID"""
        with app.app_context():
            service = ConfigurationService()

            retrieved = service.get_model_config(sample_model_config.id)

            assert retrieved is not None
            assert retrieved.id == sample_model_config.id
            assert retrieved.name == sample_model_config.name

    def test_get_model_config_with_decryption(self, app, sample_model_config):
        """Test retrieving model config with token decryption"""
        with app.app_context():
            service = ConfigurationService()

            retrieved = service.get_model_config(sample_model_config.id, decrypt_token=True)

            assert hasattr(retrieved, 'api_token')
            assert retrieved.api_token == 'test_api_token_12345'

    def test_get_model_config_not_found(self, app):
        """Test getting non-existent model config raises error"""
        with app.app_context():
            service = ConfigurationService()

            with pytest.raises(NotFoundError) as exc_info:
                service.get_model_config(99999)

            assert 'ModelConfiguration' in str(exc_info.value)
            assert '99999' in str(exc_info.value)

    def test_get_all_model_configs(self, app, multiple_model_configs):
        """Test retrieving all model configurations"""
        with app.app_context():
            service = ConfigurationService()

            all_models = service.get_all_model_configs()

            assert len(all_models) >= 3
            names = [m.name for m in all_models]
            assert 'Test-Model-1' in names
            assert 'Test-Model-2' in names
            assert 'Test-Model-3' in names

    def test_get_all_model_configs_active_only(self, app, multiple_model_configs):
        """Test retrieving only active model configurations"""
        with app.app_context():
            service = ConfigurationService()

            # Deactivate one model
            model_id = multiple_model_configs[0].id
            model = service.get_model_config(model_id)
            model.is_active = False
            db.session.commit()

            active_models = service.get_all_model_configs(active_only=True)

            assert len(active_models) >= 2
            active_ids = [m.id for m in active_models]
            assert model_id not in active_ids

    def test_get_default_model_config(self, app, sample_model_config):
        """Test retrieving the default model configuration"""
        with app.app_context():
            service = ConfigurationService()

            default_model = service.get_default_model_config()

            assert default_model is not None
            assert default_model.is_default is True
            assert default_model.is_active is True

    def test_update_model_config(self, app, sample_model_config):
        """Test updating model configuration"""
        with app.app_context():
            service = ConfigurationService()

            updated = service.update_model_config(
                sample_model_config.id,
                name='Updated-Model',
                max_tokens=8192,
                timeout=60
            )

            assert updated.name == 'Updated-Model'
            assert updated.max_tokens == 8192
            assert updated.timeout == 60

    def test_update_model_config_encrypts_new_token(self, app, sample_model_config):
        """Test updating model config with new token encrypts it"""
        with app.app_context():
            service = ConfigurationService()
            new_token = 'new_secret_token'

            updated = service.update_model_config(
                sample_model_config.id,
                api_token=new_token
            )

            # Decrypt and verify
            decrypted = service.encryption_service.decrypt(updated.api_token_encrypted)
            assert decrypted == new_token

    def test_update_model_config_to_default(self, app, multiple_model_configs):
        """Test updating a model to be default unsets other defaults"""
        with app.app_context():
            service = ConfigurationService()

            # Model 1 is currently default
            model1_id = multiple_model_configs[0].id
            model2_id = multiple_model_configs[1].id

            service.update_model_config(model2_id, is_default=True)

            # Refresh models from database
            model1 = service.get_model_config(model1_id)
            model2 = service.get_model_config(model2_id)

            assert model2.is_default is True
            assert model1.is_default is False

    def test_delete_model_config(self, app):
        """Test deleting a model configuration"""
        with app.app_context():
            service = ConfigurationService()

            # Create a non-default model
            model = service.create_model_config(
                name='To-Delete',
                api_url='https://api.test.com',
                api_token='token',
                max_tokens=2048,
                is_default=False
            )
            model_id = model.id

            service.delete_model_config(model_id)

            with pytest.raises(NotFoundError):
                service.get_model_config(model_id)

    def test_delete_default_model_raises_error(self, app, sample_model_config):
        """Test deleting default model raises validation error"""
        with app.app_context():
            service = ConfigurationService()

            # sample_model_config is default
            with pytest.raises(ValidationError) as exc_info:
                service.delete_model_config(sample_model_config.id)

            assert 'default' in str(exc_info.value).lower()


class TestNotionConfiguration:
    """Test cases for Notion Configuration operations"""

    def test_create_notion_config(self, app):
        """Test creating Notion configuration"""
        with app.app_context():
            service = ConfigurationService()

            notion = service.create_or_update_notion_config(
                api_token='notion_token_12345',
                workspace_id='workspace_123',
                workspace_name='My Workspace'
            )

            assert notion is not None
            assert notion.workspace_id == 'workspace_123'
            assert notion.workspace_name == 'My Workspace'
            assert notion.status == 'pending'
            assert notion.api_token_encrypted is not None

    def test_update_existing_notion_config(self, app, sample_notion_config):
        """Test updating existing Notion configuration (singleton)"""
        with app.app_context():
            service = ConfigurationService()

            updated = service.create_or_update_notion_config(
                api_token='new_notion_token',
                workspace_id='new_workspace_id',
                workspace_name='Updated Workspace'
            )

            # Should be same record (singleton)
            assert updated.id == sample_notion_config.id
            assert updated.workspace_id == 'new_workspace_id'
            assert updated.workspace_name == 'Updated Workspace'

            # Verify only one notion config exists
            all_configs = db.session.query(NotionConfiguration).all()
            assert len(all_configs) == 1

    def test_get_notion_config(self, app, sample_notion_config):
        """Test retrieving Notion configuration"""
        with app.app_context():
            service = ConfigurationService()

            notion = service.get_notion_config()

            assert notion is not None
            assert notion.id == sample_notion_config.id

    def test_get_notion_config_with_decryption(self, app, sample_notion_config):
        """Test retrieving Notion config with token decryption"""
        with app.app_context():
            service = ConfigurationService()

            notion = service.get_notion_config(decrypt_token=True)

            assert hasattr(notion, 'api_token')
            assert notion.api_token == 'test_notion_token_12345'

    def test_get_notion_config_returns_none_when_empty(self, app):
        """Test get_notion_config returns None when no config exists"""
        with app.app_context():
            # Delete any existing notion config
            db.session.query(NotionConfiguration).delete()
            db.session.commit()

            service = ConfigurationService()
            notion = service.get_notion_config()

            assert notion is None


class TestToolParameters:
    """Test cases for Tool Parameters operations"""

    def test_get_tool_parameters(self, app):
        """Test retrieving tool parameters"""
        with app.app_context():
            service = ConfigurationService()

            params = service.get_tool_parameters()

            assert params is not None
            assert params.id == 1
            assert params.quality_threshold == 60
            assert params.render_timeout == 30
            assert params.batch_size == 10

    def test_get_tool_parameters_creates_default(self, app):
        """Test get_tool_parameters creates default if not exists"""
        with app.app_context():
            # Delete existing
            db.session.query(ToolParameters).delete()
            db.session.commit()

            service = ConfigurationService()
            params = service.get_tool_parameters()

            assert params is not None
            assert params.id == 1

    def test_update_tool_parameters(self, app):
        """Test updating tool parameters"""
        with app.app_context():
            service = ConfigurationService()

            updated = service.update_tool_parameters(
                quality_threshold=80,
                batch_size=20,
                ocr_language='eng'
            )

            assert updated.quality_threshold == 80
            assert updated.batch_size == 20
            assert updated.ocr_language == 'eng'

    def test_reset_tool_parameters(self, app):
        """Test resetting tool parameters to defaults"""
        with app.app_context():
            service = ConfigurationService()

            # Update to non-default values
            service.update_tool_parameters(
                quality_threshold=90,
                batch_size=50
            )

            # Reset
            reset_params = service.reset_tool_parameters()

            assert reset_params.quality_threshold == 60
            assert reset_params.batch_size == 10
            assert reset_params.render_timeout == 30


class TestUserPreferences:
    """Test cases for User Preferences operations"""

    def test_get_user_preferences(self, app):
        """Test retrieving user preferences"""
        with app.app_context():
            service = ConfigurationService()

            prefs = service.get_user_preferences()

            assert prefs is not None
            assert prefs.id == 1

    def test_get_user_preferences_creates_default(self, app):
        """Test get_user_preferences creates default if not exists"""
        with app.app_context():
            # Delete existing
            db.session.query(UserPreferences).delete()
            db.session.commit()

            service = ConfigurationService()
            prefs = service.get_user_preferences()

            assert prefs is not None
            assert prefs.id == 1

    def test_update_user_preferences(self, app):
        """Test updating user preferences"""
        with app.app_context():
            service = ConfigurationService()

            updated = service.update_user_preferences(
                theme='dark',
                font_size='14',
                panel_layout='horizontal'
            )

            assert updated.theme == 'dark'
            assert updated.font_size == '14'
            assert updated.panel_layout == 'horizontal'
