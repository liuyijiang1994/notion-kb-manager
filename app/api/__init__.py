"""
API Blueprint
Centralizes all API routes
"""
from flask import Blueprint
from app.utils.response import success_response

# Create main API blueprint
api_bp = Blueprint('api', __name__)


@api_bp.route('/ping')
def ping():
    """Health check endpoint for API"""
    return success_response({'message': 'pong'})


# Import and register route modules
from app.api.config_routes import config_bp
from app.api.link_routes import link_bp, task_bp
from app.api.parsing_routes import parsing_bp
from app.api.ai_routes import ai_bp, notion_import_bp

api_bp.register_blueprint(config_bp)
api_bp.register_blueprint(link_bp)
api_bp.register_blueprint(task_bp)
api_bp.register_blueprint(parsing_bp)
api_bp.register_blueprint(ai_bp)
api_bp.register_blueprint(notion_import_bp)
