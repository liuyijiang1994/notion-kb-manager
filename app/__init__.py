"""
Notion Knowledge Base Management Tool
Main application package with Flask factory pattern
"""
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
logger = logging.getLogger(__name__)


def create_app(config_name='development'):
    """
    Application factory pattern

    Args:
        config_name: Configuration environment ('development', 'testing', 'production')

    Returns:
        Flask application instance
    """
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # Load configuration
    from config.settings import config
    app.config.from_object(config[config_name])

    # Ensure required directories exist
    _create_directories(app)

    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])

    # Initialize rate limiter
    from app.middleware.rate_limiter import init_rate_limiter
    init_rate_limiter(app)

    # Initialize security headers
    from app.middleware.security_headers import init_security_headers
    init_security_headers(app)

    # Initialize JWT authentication
    from app.middleware.auth import init_auth
    init_auth(app)

    # Setup logging
    from app.services.logging_service import setup_logging
    setup_logging(app)

    # Initialize encryption service
    from app.services import encryption_service
    encryption_service.init_app(app)

    # Register error handlers
    _register_error_handlers(app)

    # Register blueprints
    _register_blueprints(app)

    # Initialize API documentation
    from app.api.docs_routes import init_api_docs
    init_api_docs(app)

    # Initialize performance monitoring
    from app.utils.monitoring import init_monitoring, start_metrics_collector
    init_monitoring(app)

    # Start background metrics collection (every 15 seconds)
    if config_name == 'production':
        start_metrics_collector(interval=15)

    # Create database tables (development only)
    with app.app_context():
        if config_name == 'development':
            db.create_all()
            _initialize_defaults()

    logger.info(f"Application created with {config_name} configuration")

    return app


def _create_directories(app):
    """Create necessary directories if they don't exist"""
    directories = [
        app.config['DATABASE_DIR'],
        app.config['LOG_DIR'],
        app.config['UPLOAD_FOLDER'],
        app.config['CACHE_FOLDER'],
        app.config['BACKUP_FOLDER']
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")


def _register_error_handlers(app):
    """Register global error handlers"""

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'RES_001',
                'message': 'Resource not found'
            }
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'REQ_001',
                'message': 'Method not allowed'
            }
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYS_001',
                'message': 'Internal server error'
            }
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        return jsonify({
            'success': False,
            'error': {
                'code': 'SYS_001',
                'message': str(error)
            }
        }), 500


def _register_blueprints(app):
    """Register API blueprints"""
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Health check endpoint
    @app.route('/')
    def index():
        return jsonify({
            'name': 'Notion KB Manager',
            'version': app.config['API_VERSION'],
            'status': 'running'
        })

    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})


def _initialize_defaults():
    """Initialize default database values"""
    from app.models.configuration import ToolParameters, UserPreferences

    # Create default tool parameters if not exist
    tool_params = db.session.query(ToolParameters).first()
    if not tool_params:
        tool_params = ToolParameters(id=1)
        db.session.add(tool_params)
        logger.info("Created default tool parameters")

    # Create default user preferences if not exist
    user_prefs = db.session.query(UserPreferences).first()
    if not user_prefs:
        user_prefs = UserPreferences(id=1)
        db.session.add(user_prefs)
        logger.info("Created default user preferences")

    db.session.commit()
