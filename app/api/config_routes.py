"""
Configuration API routes
Handles model configuration, Notion configuration, tool parameters, and user preferences
"""
from flask import Blueprint, request, jsonify
from app.services.config_service import ConfigurationService
from app.services.model_service import get_model_service
from app.services.notion_service import get_notion_service
from app.utils.response import success_response, error_response, paginated_response
from app.utils.exceptions import NotFoundError, ValidationError, DatabaseError, ExternalAPIError
from app.utils.validators import validate_required, validate_url, validate_range, validate_choice
import logging

logger = logging.getLogger(__name__)

config_bp = Blueprint('config', __name__, url_prefix='/config')


# ========== Model Configuration Endpoints ==========

@config_bp.route('/models', methods=['GET'])
def list_model_configs():
    """Get all model configurations"""
    try:
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        service = ConfigurationService()
        models = service.get_all_model_configs(active_only=active_only)

        # Don't return encrypted tokens
        models_data = [
            {
                'id': m.id,
                'name': m.name,
                'api_url': m.api_url,
                'max_tokens': m.max_tokens,
                'timeout': m.timeout,
                'rate_limit': m.rate_limit,
                'is_default': m.is_default,
                'is_active': m.is_active,
                'status': m.status,
                'created_at': m.created_at.isoformat() if m.created_at else None,
                'updated_at': m.updated_at.isoformat() if m.updated_at else None
            }
            for m in models
        ]

        return success_response(models_data)

    except Exception as e:
        logger.error(f"Error listing model configs: {e}", exc_info=True)
        return error_response(str(e), 500)


@config_bp.route('/models/<int:model_id>', methods=['GET'])
def get_model_config(model_id):
    """Get specific model configuration"""
    try:
        service = ConfigurationService()
        model = service.get_model_config(model_id)

        model_data = {
            'id': model.id,
            'name': model.name,
            'api_url': model.api_url,
            'max_tokens': model.max_tokens,
            'timeout': model.timeout,
            'rate_limit': model.rate_limit,
            'is_default': model.is_default,
            'is_active': model.is_active,
            'status': model.status,
            'created_at': model.created_at.isoformat() if model.created_at else None,
            'updated_at': model.updated_at.isoformat() if model.updated_at else None
        }

        return success_response(model_data)

    except NotFoundError as e:
        return error_response(str(e), 404, 'RES_001')
    except Exception as e:
        logger.error(f"Error getting model config: {e}", exc_info=True)
        return error_response(str(e), 500)


@config_bp.route('/models', methods=['POST'])
def create_model_config():
    """Create new model configuration"""
    try:
        data = request.get_json()

        # Validate required fields
        validate_required(data, ['name', 'api_url', 'api_token', 'max_tokens'])

        # Validate URL format
        validate_url(data['api_url'])

        # Validate ranges
        validate_range(data['max_tokens'], 1, 1000000, 'max_tokens')

        if 'timeout' in data:
            validate_range(data['timeout'], 1, 300, 'timeout')

        if 'rate_limit' in data:
            validate_range(data['rate_limit'], 1, 10000, 'rate_limit')

        # Create model config
        service = ConfigurationService()
        model = service.create_model_config(
            name=data['name'],
            api_url=data['api_url'],
            api_token=data['api_token'],
            max_tokens=data['max_tokens'],
            timeout=data.get('timeout', 30),
            rate_limit=data.get('rate_limit', 60),
            is_default=data.get('is_default', False)
        )

        model_data = {
            'id': model.id,
            'name': model.name,
            'api_url': model.api_url,
            'max_tokens': model.max_tokens,
            'timeout': model.timeout,
            'rate_limit': model.rate_limit,
            'is_default': model.is_default,
            'is_active': model.is_active,
            'status': model.status
        }

        return success_response(model_data, 'Model configuration created successfully', 201)

    except ValidationError as e:
        return error_response(str(e), 400, 'VAL_001')
    except DatabaseError as e:
        return error_response(str(e), 500, 'SYS_002')
    except Exception as e:
        logger.error(f"Error creating model config: {e}", exc_info=True)
        return error_response(str(e), 500)


@config_bp.route('/models/<int:model_id>', methods=['PUT'])
def update_model_config(model_id):
    """Update model configuration"""
    try:
        data = request.get_json()

        # Validate if present
        if 'api_url' in data:
            validate_url(data['api_url'])

        if 'max_tokens' in data:
            validate_range(data['max_tokens'], 1, 1000000, 'max_tokens')

        if 'timeout' in data:
            validate_range(data['timeout'], 1, 300, 'timeout')

        if 'rate_limit' in data:
            validate_range(data['rate_limit'], 1, 10000, 'rate_limit')

        service = ConfigurationService()
        model = service.update_model_config(model_id, **data)

        model_data = {
            'id': model.id,
            'name': model.name,
            'api_url': model.api_url,
            'max_tokens': model.max_tokens,
            'timeout': model.timeout,
            'rate_limit': model.rate_limit,
            'is_default': model.is_default,
            'is_active': model.is_active,
            'status': model.status
        }

        return success_response(model_data, 'Model configuration updated successfully')

    except NotFoundError as e:
        return error_response(str(e), 404, 'RES_001')
    except ValidationError as e:
        return error_response(str(e), 400, 'VAL_001')
    except DatabaseError as e:
        return error_response(str(e), 500, 'SYS_002')
    except Exception as e:
        logger.error(f"Error updating model config: {e}", exc_info=True)
        return error_response(str(e), 500)


@config_bp.route('/models/<int:model_id>', methods=['DELETE'])
def delete_model_config(model_id):
    """Delete model configuration"""
    try:
        service = ConfigurationService()
        service.delete_model_config(model_id)

        return success_response(None, 'Model configuration deleted successfully')

    except NotFoundError as e:
        return error_response(str(e), 404, 'RES_001')
    except ValidationError as e:
        return error_response(str(e), 400, 'VAL_001')
    except DatabaseError as e:
        return error_response(str(e), 500, 'SYS_002')
    except Exception as e:
        logger.error(f"Error deleting model config: {e}", exc_info=True)
        return error_response(str(e), 500)


@config_bp.route('/models/<int:model_id>/set-default', methods=['PUT'])
def set_default_model(model_id):
    """Set model as default"""
    try:
        service = ConfigurationService()
        model = service.update_model_config(model_id, is_default=True)

        return success_response(
            {'id': model.id, 'name': model.name, 'is_default': model.is_default},
            'Model set as default successfully'
        )

    except NotFoundError as e:
        return error_response(str(e), 404, 'RES_001')
    except Exception as e:
        logger.error(f"Error setting default model: {e}", exc_info=True)
        return error_response(str(e), 500)


@config_bp.route('/models/<int:model_id>/test', methods=['POST'])
def test_model_connection(model_id):
    """Test model API connection"""
    try:
        service = ConfigurationService()
        model = service.get_model_config(model_id, decrypt_token=True)

        # Test connection using model service
        model_service = get_model_service()
        result = model_service.test_connection(
            api_url=model.api_url,
            api_token=model.api_token,
            model_name=model.name,
            timeout=model.timeout
        )

        # Update model status based on test result
        if result['success']:
            service.update_model_config(model_id, status='active', is_active=True)
        else:
            service.update_model_config(model_id, status='failed', is_active=False)

        return success_response(result)

    except NotFoundError as e:
        return error_response(str(e), 404, 'RES_001')
    except Exception as e:
        logger.error(f"Error testing model connection: {e}", exc_info=True)
        return error_response(str(e), 500)


# ========== Notion Configuration Endpoints ==========

@config_bp.route('/notion', methods=['GET'])
def get_notion_config():
    """Get Notion configuration"""
    try:
        service = ConfigurationService()
        notion = service.get_notion_config()

        if not notion:
            return success_response(None, 'No Notion configuration found')

        notion_data = {
            'id': notion.id,
            'workspace_id': notion.workspace_id,
            'workspace_name': notion.workspace_name,
            'status': notion.status,
            'created_at': notion.created_at.isoformat() if notion.created_at else None,
            'updated_at': notion.updated_at.isoformat() if notion.updated_at else None
        }

        return success_response(notion_data)

    except Exception as e:
        logger.error(f"Error getting Notion config: {e}", exc_info=True)
        return error_response(str(e), 500)


@config_bp.route('/notion', methods=['POST'])
def create_or_update_notion_config():
    """Create or update Notion configuration"""
    try:
        data = request.get_json()

        # Validate required fields
        validate_required(data, ['api_token'])

        service = ConfigurationService()
        notion = service.create_or_update_notion_config(
            api_token=data['api_token'],
            workspace_id=data.get('workspace_id'),
            workspace_name=data.get('workspace_name')
        )

        notion_data = {
            'id': notion.id,
            'workspace_id': notion.workspace_id,
            'workspace_name': notion.workspace_name,
            'status': notion.status
        }

        return success_response(notion_data, 'Notion configuration saved successfully', 201)

    except ValidationError as e:
        return error_response(str(e), 400, 'VAL_001')
    except DatabaseError as e:
        return error_response(str(e), 500, 'SYS_002')
    except Exception as e:
        logger.error(f"Error saving Notion config: {e}", exc_info=True)
        return error_response(str(e), 500)


@config_bp.route('/notion/test', methods=['POST'])
def test_notion_connection():
    """Test Notion API connection"""
    try:
        service = ConfigurationService()
        notion = service.get_notion_config(decrypt_token=True)

        if not notion:
            return error_response('No Notion configuration found', 404, 'RES_001')

        # Test connection using Notion service
        notion_service = get_notion_service()
        result = notion_service.test_connection(api_token=notion.api_token)

        # Update Notion configuration based on test result
        if result['success']:
            workspace_info = result.get('workspace_info', {})
            service.create_or_update_notion_config(
                api_token=notion.api_token,
                workspace_id=workspace_info.get('bot_id'),
                workspace_name=workspace_info.get('workspace_name')
            )
            # Update status separately (after create_or_update)
            from app import db
            notion.status = 'active'
            db.session.commit()
        else:
            notion.status = 'failed'
            from app import db
            db.session.commit()

        return success_response(result)

    except NotFoundError as e:
        return error_response(str(e), 404, 'RES_001')
    except Exception as e:
        logger.error(f"Error testing Notion connection: {e}", exc_info=True)
        return error_response(str(e), 500)


# ========== Tool Parameters Endpoints ==========

@config_bp.route('/parameters', methods=['GET'])
def get_tool_parameters():
    """Get tool parameters"""
    try:
        service = ConfigurationService()
        params = service.get_tool_parameters()

        params_data = {
            'id': params.id,
            'quality_threshold': params.quality_threshold,
            'render_timeout': params.render_timeout,
            'ocr_language': params.ocr_language,
            'batch_size': params.batch_size,
            'retain_cache': params.retain_cache,
            'export_format': params.export_format,
            'cache_retention_days': params.cache_retention_days,
            'cache_auto_clean': params.cache_auto_clean,
            'enable_notifications': params.enable_notifications,
            'notification_frequency': params.notification_frequency,
            'updated_at': params.updated_at.isoformat() if params.updated_at else None
        }

        return success_response(params_data)

    except Exception as e:
        logger.error(f"Error getting tool parameters: {e}", exc_info=True)
        return error_response(str(e), 500)


@config_bp.route('/parameters', methods=['PUT'])
def update_tool_parameters():
    """Update tool parameters"""
    try:
        data = request.get_json()

        # Validate ranges if present
        if 'quality_threshold' in data:
            validate_range(data['quality_threshold'], 0, 100, 'quality_threshold')

        if 'render_timeout' in data:
            validate_range(data['render_timeout'], 1, 300, 'render_timeout')

        if 'batch_size' in data:
            validate_range(data['batch_size'], 1, 1000, 'batch_size')

        if 'cache_retention_days' in data:
            validate_range(data['cache_retention_days'], 1, 365, 'cache_retention_days')

        if 'export_format' in data:
            validate_choice(data['export_format'], ['excel', 'csv', 'json'], 'export_format')

        if 'notification_frequency' in data:
            validate_choice(data['notification_frequency'], ['all', 'errors', 'none'], 'notification_frequency')

        service = ConfigurationService()
        params = service.update_tool_parameters(**data)

        params_data = {
            'id': params.id,
            'quality_threshold': params.quality_threshold,
            'render_timeout': params.render_timeout,
            'ocr_language': params.ocr_language,
            'batch_size': params.batch_size,
            'retain_cache': params.retain_cache,
            'export_format': params.export_format,
            'cache_retention_days': params.cache_retention_days,
            'cache_auto_clean': params.cache_auto_clean,
            'enable_notifications': params.enable_notifications,
            'notification_frequency': params.notification_frequency
        }

        return success_response(params_data, 'Tool parameters updated successfully')

    except ValidationError as e:
        return error_response(str(e), 400, 'VAL_001')
    except DatabaseError as e:
        return error_response(str(e), 500, 'SYS_002')
    except Exception as e:
        logger.error(f"Error updating tool parameters: {e}", exc_info=True)
        return error_response(str(e), 500)


@config_bp.route('/parameters/reset', methods=['POST'])
def reset_tool_parameters():
    """Reset tool parameters to defaults"""
    try:
        service = ConfigurationService()
        params = service.reset_tool_parameters()

        params_data = {
            'id': params.id,
            'quality_threshold': params.quality_threshold,
            'render_timeout': params.render_timeout,
            'ocr_language': params.ocr_language,
            'batch_size': params.batch_size,
            'retain_cache': params.retain_cache,
            'export_format': params.export_format,
            'cache_retention_days': params.cache_retention_days,
            'cache_auto_clean': params.cache_auto_clean,
            'enable_notifications': params.enable_notifications,
            'notification_frequency': params.notification_frequency
        }

        return success_response(params_data, 'Tool parameters reset to defaults')

    except Exception as e:
        logger.error(f"Error resetting tool parameters: {e}", exc_info=True)
        return error_response(str(e), 500)


# ========== User Preferences Endpoints ==========

@config_bp.route('/preferences', methods=['GET'])
def get_user_preferences():
    """Get user preferences"""
    try:
        service = ConfigurationService()
        prefs = service.get_user_preferences()

        prefs_data = {
            'id': prefs.id,
            'theme': prefs.theme,
            'font_size': prefs.font_size,
            'panel_layout': prefs.panel_layout,
            'shortcuts': prefs.shortcuts,
            'updated_at': prefs.updated_at.isoformat() if prefs.updated_at else None
        }

        return success_response(prefs_data)

    except Exception as e:
        logger.error(f"Error getting user preferences: {e}", exc_info=True)
        return error_response(str(e), 500)


@config_bp.route('/preferences', methods=['PUT'])
def update_user_preferences():
    """Update user preferences"""
    try:
        data = request.get_json()

        # Validate choices if present
        if 'theme' in data:
            validate_choice(data['theme'], ['light', 'dark', 'system'], 'theme')

        if 'panel_layout' in data:
            validate_choice(data['panel_layout'], ['vertical', 'horizontal', 'grid'], 'panel_layout')

        service = ConfigurationService()
        prefs = service.update_user_preferences(**data)

        prefs_data = {
            'id': prefs.id,
            'theme': prefs.theme,
            'font_size': prefs.font_size,
            'panel_layout': prefs.panel_layout,
            'shortcuts': prefs.shortcuts
        }

        return success_response(prefs_data, 'User preferences updated successfully')

    except ValidationError as e:
        return error_response(str(e), 400, 'VAL_001')
    except DatabaseError as e:
        return error_response(str(e), 500, 'SYS_002')
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}", exc_info=True)
        return error_response(str(e), 500)
