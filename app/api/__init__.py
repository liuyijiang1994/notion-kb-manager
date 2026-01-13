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
api_bp.register_blueprint(config_bp)
