"""
JWT-based authentication middleware
Provides token-based authentication for protected API endpoints
"""
import logging
import os
from datetime import timedelta
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, \
    get_jwt_identity, verify_jwt_in_request, get_jwt
from app.utils.response import error_response

logger = logging.getLogger(__name__)

# JWT configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))  # 30 days
REQUIRE_AUTH = os.getenv('REQUIRE_AUTH', 'false').lower() == 'true'

# Initialize JWT manager
jwt = JWTManager()


def init_auth(app):
    """
    Initialize JWT authentication with Flask app

    Args:
        app: Flask application instance
    """
    # Configure JWT
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(seconds=JWT_REFRESH_TOKEN_EXPIRES)
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'

    # Initialize JWT manager
    jwt.init_app(app)

    # Register JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired token"""
        logger.warning(f"Expired token used: {jwt_payload.get('sub')}")
        return jsonify(error_response(
            error_code='AUTH_002',
            message='Token has expired',
            details='Please refresh your token or login again',
            status_code=401
        )), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handle invalid token"""
        logger.warning(f"Invalid token: {error}")
        return jsonify(error_response(
            error_code='AUTH_003',
            message='Invalid token',
            details='The token signature is invalid',
            status_code=401
        )), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handle missing token"""
        logger.warning(f"Missing token: {error}")
        return jsonify(error_response(
            error_code='AUTH_001',
            message='Authorization required',
            details='Please provide a valid access token',
            status_code=401
        )), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Handle revoked token"""
        logger.warning(f"Revoked token used: {jwt_payload.get('sub')}")
        return jsonify(error_response(
            error_code='AUTH_004',
            message='Token has been revoked',
            details='This token is no longer valid',
            status_code=401
        )), 401

    logger.info(f"JWT authentication initialized (Auth required: {REQUIRE_AUTH})")


def create_tokens(user_id: str, roles: list = None) -> dict:
    """
    Create access and refresh tokens for a user

    Args:
        user_id: User identifier
        roles: List of user roles (default: ['user'])

    Returns:
        dict: Access and refresh tokens
    """
    if roles is None:
        roles = ['user']

    additional_claims = {
        'roles': roles
    }

    access_token = create_access_token(
        identity=user_id,
        additional_claims=additional_claims
    )

    refresh_token = create_refresh_token(
        identity=user_id,
        additional_claims=additional_claims
    )

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': JWT_ACCESS_TOKEN_EXPIRES
    }


def require_auth(roles: list = None):
    """
    Decorator to require JWT authentication for endpoint

    Args:
        roles: Optional list of required roles

    Usage:
        @require_auth()
        def protected_route():
            user_id = get_jwt_identity()
            ...

        @require_auth(roles=['admin'])
        def admin_only_route():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Skip auth check if not required (development mode)
            if not REQUIRE_AUTH:
                return fn(*args, **kwargs)

            # Verify JWT in request
            try:
                verify_jwt_in_request()
            except Exception as e:
                logger.warning(f"JWT verification failed: {e}")
                return jsonify(error_response(
                    error_code='AUTH_001',
                    message='Authorization required',
                    details=str(e),
                    status_code=401
                )), 401

            # Check roles if specified
            if roles:
                jwt_data = get_jwt()
                user_roles = jwt_data.get('roles', [])

                if not any(role in user_roles for role in roles):
                    logger.warning(f"Insufficient permissions: required={roles}, user={user_roles}")
                    return jsonify(error_response(
                        error_code='AUTH_005',
                        message='Insufficient permissions',
                        details=f'This endpoint requires one of: {", ".join(roles)}',
                        status_code=403
                    )), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def optional_auth():
    """
    Decorator to optionally use JWT authentication if provided

    Allows endpoint to work both authenticated and unauthenticated
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request(optional=True)
            except Exception:
                pass  # Token not required, continue without auth
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user() -> dict:
    """
    Get current authenticated user from JWT

    Returns:
        dict: User information including user_id and roles
    """
    user_id = get_jwt_identity()
    jwt_data = get_jwt()
    roles = jwt_data.get('roles', [])

    return {
        'user_id': user_id,
        'roles': roles,
        'is_admin': 'admin' in roles
    }
