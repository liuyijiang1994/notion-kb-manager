"""
Rate limiting middleware using Flask-Limiter
Protects API endpoints from abuse with Redis-based rate limiting
"""
import logging
import os
from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.utils.response import error_response

logger = logging.getLogger(__name__)

# Get Redis URL from environment with fallback
REDIS_RATE_LIMIT_URL = os.getenv('REDIS_RATE_LIMIT_URL', 'redis://localhost:6379/1')

# Initialize Flask-Limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=REDIS_RATE_LIMIT_URL,
    default_limits=[
        "1000 per hour",  # Max 1000 requests per hour
        "100 per minute"   # Max 100 requests per minute
    ],
    headers_enabled=True,  # Add rate limit headers to responses
    swallow_errors=True   # Don't crash if Redis is unavailable
)


def init_rate_limiter(app):
    """
    Initialize rate limiter with Flask app

    Args:
        app: Flask application instance
    """
    limiter.init_app(app)

    # Custom error handler for rate limit exceeded
    @app.errorhandler(429)
    def ratelimit_handler(e):
        """Handle rate limit exceeded errors"""
        logger.warning(f"Rate limit exceeded: {request.remote_addr} - {request.endpoint}")

        return jsonify(error_response(
            error_code='RATE_001',
            message='Rate limit exceeded',
            details='Too many requests. Please try again later.',
            status_code=429
        )), 429

    logger.info(f"Rate limiter initialized with storage: {REDIS_RATE_LIMIT_URL}")


# Predefined rate limit decorators for specific use cases

def config_rate_limit():
    """
    Rate limit for configuration endpoints
    100 requests per hour - configuration changes are infrequent
    """
    return limiter.limit("100 per hour")


def parsing_rate_limit():
    """
    Rate limit for synchronous parsing endpoint
    10 requests per minute - resource intensive operation
    """
    return limiter.limit("10 per minute")


def ai_processing_rate_limit():
    """
    Rate limit for AI processing endpoints
    20 requests per minute - external API calls with costs
    """
    return limiter.limit("20 per minute")


def backup_rate_limit():
    """
    Rate limit for backup creation
    5 requests per hour - expensive disk/database operation
    """
    return limiter.limit("5 per hour")


def batch_operation_rate_limit():
    """
    Rate limit for batch operations
    30 requests per hour - can be resource intensive
    """
    return limiter.limit("30 per hour")


def report_generation_rate_limit():
    """
    Rate limit for report generation
    20 requests per hour - can be resource intensive
    """
    return limiter.limit("20 per hour")


def exempt_from_rate_limit():
    """
    Exempt endpoint from rate limiting
    Use for health checks and internal endpoints
    """
    return limiter.exempt
