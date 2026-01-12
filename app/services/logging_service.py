"""
Logging service for centralized application logging
Provides structured logging with file rotation and database persistence
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional
from flask import request, has_request_context


def setup_logging(app):
    """
    Configure application-wide logging

    Sets up:
    - Console logging (always enabled)
    - File logging with rotation
    - Structured log format

    Args:
        app: Flask application instance
    """
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_dir = app.config.get('LOG_DIR', 'logs')
    log_format = app.config.get('LOG_FORMAT')

    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler with rotation (10MB per file, keep 5 backup files)
    log_file = os.path.join(log_dir, 'app.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Error log file (errors only)
    error_file = os.path.join(log_dir, 'error.log')
    error_handler = RotatingFileHandler(
        error_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)

    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    app.logger.info(f"Logging configured successfully at {log_level} level")


class DatabaseLogHandler(logging.Handler):
    """
    Custom logging handler that persists logs to database
    Used for operation logging that needs to be queryable
    """

    def __init__(self, db_session):
        """
        Initialize database log handler

        Args:
            db_session: SQLAlchemy database session
        """
        super().__init__()
        self.db_session = db_session

    def emit(self, record: logging.LogRecord):
        """
        Persist log record to database

        Args:
            record: Log record to persist
        """
        try:
            from app.models.system import OperationLog

            # Extract request context if available
            ip_address = None
            user_id = None

            if has_request_context():
                ip_address = request.remote_addr
                # user_id = getattr(g, 'user_id', None)  # For future authentication

            log_entry = OperationLog(
                level=record.levelname.lower(),
                module=record.module,
                action=record.funcName,
                message=record.getMessage(),
                user_id=user_id,
                ip_address=ip_address,
                created_at=datetime.utcnow()
            )

            self.db_session.add(log_entry)
            self.db_session.commit()
        except Exception as e:
            # Fallback to standard error logging if database logging fails
            self.handleError(record)
            print(f"Failed to log to database: {e}")


def log_operation(level: str, module: str, action: str, message: str,
                  user_id: Optional[str] = None, ip_address: Optional[str] = None):
    """
    Log an operation to database

    Convenience function for explicit operation logging

    Args:
        level: Log level (info, warning, error)
        module: Module name
        action: Action performed
        message: Log message
        user_id: User ID (optional)
        ip_address: IP address (optional)
    """
    from app.models.system import OperationLog
    from app import db

    try:
        log_entry = OperationLog(
            level=level,
            module=module,
            action=action,
            message=message,
            user_id=user_id,
            ip_address=ip_address,
            created_at=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        logging.error(f"Failed to log operation to database: {e}")
