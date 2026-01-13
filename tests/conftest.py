"""
PyTest configuration and fixtures
"""
import pytest
import os
import tempfile
from cryptography.fernet import Fernet
from app import create_app, db
from app.models.base import Base
# Import all models to ensure they're registered with SQLAlchemy
from app.models import (
    ModelConfiguration, NotionConfiguration, ToolParameters, UserPreferences,
    ImportTask, Link, ParsedContent, AIProcessedContent, ProcessingTask,
    NotionMapping, NotionImport, ImportNotionTask,
    Backup, BackupFiles, OperationLog, Feedback
)


@pytest.fixture(scope='session')
def encryption_key():
    """Generate a test encryption key"""
    return Fernet.generate_key().decode('utf-8')


@pytest.fixture(scope='session')
def app(encryption_key):
    """Create and configure a test Flask application"""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()

    # Set test environment variables
    os.environ['ENCRYPTION_KEY'] = encryption_key
    os.environ['TESTING'] = 'True'

    # Create app with testing configuration
    app = create_app('testing')

    # Override database path to use temporary file
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True

    # Create database tables
    with app.app_context():
        # Use Base.metadata instead of db.create_all() because we use custom Base
        Base.metadata.create_all(bind=db.engine)

        # Create default configurations only if they don't exist
        if not db.session.get(ToolParameters, 1):
            tool_params = ToolParameters(id=1)
            db.session.add(tool_params)

        if not db.session.get(UserPreferences, 1):
            user_prefs = UserPreferences(id=1)
            db.session.add(user_prefs)

        db.session.commit()

    yield app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the Flask application"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a new database session for a test"""
    with app.app_context():
        yield db.session

        # Rollback any changes after the test
        db.session.rollback()


@pytest.fixture
def sample_model_config(app):
    """Create a sample model configuration"""
    with app.app_context():
        from app.services.config_service import ConfigurationService
        service = ConfigurationService()

        model = service.create_model_config(
            name='Test-GPT-4',
            api_url='https://api.openai.com/v1/chat/completions',
            api_token='test_api_token_12345',
            max_tokens=4096,
            timeout=30,
            rate_limit=60,
            is_default=True
        )

        yield model

        # Cleanup
        try:
            db.session.delete(model)
            db.session.commit()
        except:
            db.session.rollback()


@pytest.fixture
def sample_notion_config(app):
    """Create a sample Notion configuration"""
    with app.app_context():
        from app.services.config_service import ConfigurationService
        service = ConfigurationService()

        notion = service.create_or_update_notion_config(
            api_token='test_notion_token_12345',
            workspace_id='test_workspace_id',
            workspace_name='Test Workspace'
        )

        yield notion

        # Cleanup
        try:
            db.session.delete(notion)
            db.session.commit()
        except:
            db.session.rollback()


@pytest.fixture
def multiple_model_configs(app):
    """Create multiple model configurations for testing"""
    with app.app_context():
        from app.services.config_service import ConfigurationService
        service = ConfigurationService()

        models = []

        # Create 3 test models
        for i in range(1, 4):
            model = service.create_model_config(
                name=f'Test-Model-{i}',
                api_url=f'https://api.test{i}.com/v1',
                api_token=f'test_token_{i}',
                max_tokens=2048 * i,
                timeout=30,
                rate_limit=60,
                is_default=(i == 1)
            )
            models.append(model)

        yield models

        # Cleanup
        for model in models:
            try:
                db.session.delete(model)
                db.session.commit()
            except:
                db.session.rollback()
