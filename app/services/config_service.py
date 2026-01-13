"""
Configuration service for managing application settings
"""
import logging
from typing import Optional, List
from app import db
from app.models.configuration import (
    ModelConfiguration, NotionConfiguration,
    ToolParameters, UserPreferences
)
from app.services.encryption_service import get_encryption_service
from app.utils.exceptions import NotFoundError, ValidationError, DatabaseError

logger = logging.getLogger(__name__)


class ConfigurationService:
    """Service for managing configuration settings"""

    def __init__(self):
        self.encryption_service = get_encryption_service()

    # Model Configuration Methods

    def create_model_config(self, name: str, api_url: str, api_token: str,
                           max_tokens: int, timeout: int = 30, rate_limit: int = 60,
                           is_default: bool = False) -> ModelConfiguration:
        """
        Create new model configuration

        Args:
            name: Model name
            api_url: API endpoint URL
            api_token: API token (will be encrypted)
            max_tokens: Maximum tokens per request
            timeout: Request timeout in seconds
            rate_limit: Rate limit per minute
            is_default: Whether this is the default model

        Returns:
            Created ModelConfiguration instance

        Raises:
            DatabaseError: If creation fails
        """
        try:
            # Encrypt API token
            encrypted_token = self.encryption_service.encrypt(api_token)

            # If setting as default, unset other defaults
            if is_default:
                db.session.query(ModelConfiguration).update({'is_default': False})

            model_config = ModelConfiguration(
                name=name,
                api_url=api_url,
                api_token_encrypted=encrypted_token,
                timeout=timeout,
                max_tokens=max_tokens,
                rate_limit=rate_limit,
                is_default=is_default,
                is_active=True,
                status='pending'
            )

            db.session.add(model_config)
            db.session.commit()

            logger.info(f"Created model configuration: {name}")
            return model_config

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create model configuration: {e}")
            raise DatabaseError(f"Failed to create model configuration: {e}")

    def get_model_config(self, model_id: int, decrypt_token: bool = False) -> ModelConfiguration:
        """
        Get model configuration by ID

        Args:
            model_id: Model configuration ID
            decrypt_token: Whether to decrypt and return API token

        Returns:
            ModelConfiguration instance

        Raises:
            NotFoundError: If model not found
        """
        model_config = db.session.get(ModelConfiguration, model_id)

        if not model_config:
            raise NotFoundError('ModelConfiguration', model_id)

        if decrypt_token:
            model_config.api_token = self.encryption_service.decrypt(
                model_config.api_token_encrypted
            )

        return model_config

    def get_all_model_configs(self, active_only: bool = False) -> List[ModelConfiguration]:
        """
        Get all model configurations

        Args:
            active_only: If True, return only active models

        Returns:
            List of ModelConfiguration instances
        """
        query = db.session.query(ModelConfiguration)

        if active_only:
            query = query.filter_by(is_active=True)

        return query.all()

    def get_default_model_config(self) -> Optional[ModelConfiguration]:
        """
        Get the default model configuration

        Returns:
            Default ModelConfiguration or None
        """
        return db.session.query(ModelConfiguration).filter_by(
            is_default=True,
            is_active=True
        ).first()

    def update_model_config(self, model_id: int, **kwargs) -> ModelConfiguration:
        """
        Update model configuration

        Args:
            model_id: Model configuration ID
            **kwargs: Fields to update

        Returns:
            Updated ModelConfiguration

        Raises:
            NotFoundError: If model not found
        """
        model_config = self.get_model_config(model_id)

        try:
            # Encrypt API token if provided
            if 'api_token' in kwargs:
                kwargs['api_token_encrypted'] = self.encryption_service.encrypt(
                    kwargs.pop('api_token')
                )

            # Handle default setting
            if kwargs.get('is_default', False):
                db.session.query(ModelConfiguration).filter(
                    ModelConfiguration.id != model_id
                ).update({'is_default': False})

            for key, value in kwargs.items():
                if hasattr(model_config, key):
                    setattr(model_config, key, value)

            db.session.commit()
            logger.info(f"Updated model configuration: {model_id}")

            return model_config

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update model configuration: {e}")
            raise DatabaseError(f"Failed to update model configuration: {e}")

    def delete_model_config(self, model_id: int):
        """
        Delete model configuration

        Args:
            model_id: Model configuration ID

        Raises:
            NotFoundError: If model not found
            ValidationError: If trying to delete the default model
        """
        model_config = self.get_model_config(model_id)

        if model_config.is_default:
            raise ValidationError("Cannot delete the default model configuration")

        try:
            db.session.delete(model_config)
            db.session.commit()
            logger.info(f"Deleted model configuration: {model_id}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete model configuration: {e}")
            raise DatabaseError(f"Failed to delete model configuration: {e}")

    # Notion Configuration Methods

    def create_or_update_notion_config(self, api_token: str,
                                      workspace_id: Optional[str] = None,
                                      workspace_name: Optional[str] = None) -> NotionConfiguration:
        """
        Create or update Notion configuration (singleton)

        Args:
            api_token: Notion API token (will be encrypted)
            workspace_id: Workspace ID
            workspace_name: Workspace name

        Returns:
            NotionConfiguration instance
        """
        try:
            encrypted_token = self.encryption_service.encrypt(api_token)

            # Check if configuration exists
            notion_config = db.session.query(NotionConfiguration).first()

            if notion_config:
                notion_config.api_token_encrypted = encrypted_token
                if workspace_id:
                    notion_config.workspace_id = workspace_id
                if workspace_name:
                    notion_config.workspace_name = workspace_name
                notion_config.status = 'pending'
            else:
                notion_config = NotionConfiguration(
                    api_token_encrypted=encrypted_token,
                    workspace_id=workspace_id,
                    workspace_name=workspace_name,
                    status='pending'
                )
                db.session.add(notion_config)

            db.session.commit()
            logger.info("Created/updated Notion configuration")

            return notion_config

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save Notion configuration: {e}")
            raise DatabaseError(f"Failed to save Notion configuration: {e}")

    def get_notion_config(self, decrypt_token: bool = False) -> Optional[NotionConfiguration]:
        """
        Get Notion configuration

        Args:
            decrypt_token: Whether to decrypt and return API token

        Returns:
            NotionConfiguration instance or None
        """
        notion_config = db.session.query(NotionConfiguration).first()

        if notion_config and decrypt_token:
            notion_config.api_token = self.encryption_service.decrypt(
                notion_config.api_token_encrypted
            )

        return notion_config

    # Tool Parameters Methods

    def get_tool_parameters(self) -> ToolParameters:
        """
        Get tool parameters (creates default if not exists)

        Returns:
            ToolParameters instance
        """
        params = db.session.get(ToolParameters, 1)

        if not params:
            params = ToolParameters(id=1)
            db.session.add(params)
            db.session.commit()
            logger.info("Created default tool parameters")

        return params

    def update_tool_parameters(self, **kwargs) -> ToolParameters:
        """
        Update tool parameters

        Args:
            **kwargs: Parameters to update

        Returns:
            Updated ToolParameters instance
        """
        params = self.get_tool_parameters()

        try:
            for key, value in kwargs.items():
                if hasattr(params, key):
                    setattr(params, key, value)

            db.session.commit()
            logger.info("Updated tool parameters")

            return params

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update tool parameters: {e}")
            raise DatabaseError(f"Failed to update tool parameters: {e}")

    def reset_tool_parameters(self) -> ToolParameters:
        """
        Reset tool parameters to defaults

        Returns:
            Reset ToolParameters instance
        """
        params = self.get_tool_parameters()

        try:
            # Reset to default values
            params.quality_threshold = 60
            params.render_timeout = 30
            params.ocr_language = 'auto'
            params.batch_size = 10
            params.retain_cache = True
            params.export_format = 'excel'
            params.cache_retention_days = 7
            params.cache_auto_clean = True
            params.enable_notifications = True
            params.notification_frequency = 'all'

            db.session.commit()
            logger.info("Reset tool parameters to defaults")

            return params

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to reset tool parameters: {e}")
            raise DatabaseError(f"Failed to reset tool parameters: {e}")

    # User Preferences Methods

    def get_user_preferences(self) -> UserPreferences:
        """
        Get user preferences (creates default if not exists)

        Returns:
            UserPreferences instance
        """
        prefs = db.session.get(UserPreferences, 1)

        if not prefs:
            prefs = UserPreferences(id=1)
            db.session.add(prefs)
            db.session.commit()
            logger.info("Created default user preferences")

        return prefs

    def update_user_preferences(self, **kwargs) -> UserPreferences:
        """
        Update user preferences

        Args:
            **kwargs: Preferences to update

        Returns:
            Updated UserPreferences instance
        """
        prefs = self.get_user_preferences()

        try:
            for key, value in kwargs.items():
                if hasattr(prefs, key):
                    setattr(prefs, key, value)

            db.session.commit()
            logger.info("Updated user preferences")

            return prefs

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update user preferences: {e}")
            raise DatabaseError(f"Failed to update user preferences: {e}")
