"""
Notion Knowledge Base Management Tool
Main application package
"""
from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


def create_app():
    """Application factory pattern"""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # Load configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['NOTION_API_KEY'] = os.getenv('NOTION_API_KEY')
    app.config['NOTION_DATABASE_ID'] = os.getenv('NOTION_DATABASE_ID')

    # Register blueprints here when ready
    # from app.api import api_bp
    # app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        return "Notion Knowledge Base Management Tool"

    return app
