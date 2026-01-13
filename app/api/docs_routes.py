"""
API Documentation Routes
Serves Swagger UI and OpenAPI specification
"""
import os
import yaml
import json
from pathlib import Path
from flask import Blueprint, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import logging

logger = logging.getLogger(__name__)

# Create blueprint for docs
docs_bp = Blueprint('docs', __name__, url_prefix='/docs')

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
OPENAPI_SPEC_PATH = PROJECT_ROOT / 'docs' / 'api' / 'openapi.yaml'


@docs_bp.route('/openapi.yaml')
def get_openapi_yaml():
    """
    Serve OpenAPI specification in YAML format

    Returns:
        YAML file with OpenAPI 3.0 specification
    """
    try:
        if not OPENAPI_SPEC_PATH.exists():
            return jsonify({
                'error': 'OpenAPI specification not found'
            }), 404

        return send_from_directory(
            OPENAPI_SPEC_PATH.parent,
            OPENAPI_SPEC_PATH.name,
            mimetype='application/x-yaml'
        )

    except Exception as e:
        logger.error(f"Error serving OpenAPI YAML: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@docs_bp.route('/openapi.json')
def get_openapi_json():
    """
    Serve OpenAPI specification in JSON format

    Converts YAML spec to JSON for clients that prefer JSON

    Returns:
        JSON representation of OpenAPI spec
    """
    try:
        if not OPENAPI_SPEC_PATH.exists():
            return jsonify({
                'error': 'OpenAPI specification not found'
            }), 404

        # Load YAML and convert to JSON
        with open(OPENAPI_SPEC_PATH, 'r') as f:
            spec = yaml.safe_load(f)

        return jsonify(spec)

    except Exception as e:
        logger.error(f"Error serving OpenAPI JSON: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# Configure Swagger UI
SWAGGER_URL = '/api/docs'  # URL for Swagger UI
API_URL = '/api/docs/openapi.json'  # URL for OpenAPI spec

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Notion KB Manager API",
        'docExpansion': 'list',  # 'none', 'list', or 'full'
        'defaultModelsExpandDepth': 3,
        'defaultModelExpandDepth': 3,
        'displayRequestDuration': True,
        'filter': True,  # Enable filtering
        'showExtensions': True,
        'showCommonExtensions': True,
        'tryItOutEnabled': True,  # Enable "Try it out" by default
        'persistAuthorization': True,  # Remember auth tokens
    }
)


def init_api_docs(app):
    """
    Initialize API documentation with Flask app

    Args:
        app: Flask application instance
    """
    # Register docs blueprint
    app.register_blueprint(docs_bp, url_prefix='/api/docs')

    # Register Swagger UI blueprint
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    logger.info(f"API documentation available at: {SWAGGER_URL}")
    logger.info(f"OpenAPI spec available at: /api/docs/openapi.json")
