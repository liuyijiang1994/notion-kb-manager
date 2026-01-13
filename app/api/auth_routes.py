"""
Authentication API endpoints
Handles user login, token refresh, and API key management
"""
import logging
import secrets
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.middleware.auth import create_tokens, get_current_user
from app.utils.response import success_response, error_response
from app.utils.validators import validate_required
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint

    Request:
        {
            "username": "admin",
            "password": "password123"
        }

    Response:
        {
            "success": true,
            "data": {
                "access_token": "eyJ...",
                "refresh_token": "eyJ...",
                "token_type": "Bearer",
                "expires_in": 3600,
                "user": {
                    "user_id": "admin",
                    "roles": ["admin", "user"]
                }
            }
        }

    Status Codes:
        200: Login successful
        400: Missing required fields
        401: Invalid credentials
    """
    try:
        data = request.get_json()

        # Validate required fields
        try:
            validate_required(data, ['username', 'password'])
        except ValidationError as e:
            return error_response(
                code='REQ_002',
                message='Missing required fields',
                details={'error': str(e)},
                status=400
            )

        username = data.get('username')
        password = data.get('password')

        # TODO: Replace with actual user authentication from database
        # For now, use simple hardcoded credentials (CHANGE IN PRODUCTION!)
        valid_users = {
            'admin': {
                'password': 'admin123',
                'roles': ['admin', 'user']
            },
            'user': {
                'password': 'user123',
                'roles': ['user']
            }
        }

        user = valid_users.get(username)
        if not user or user['password'] != password:
            logger.warning(f"Failed login attempt for username: {username}")
            return error_response(
                code='AUTH_006',
                message='Invalid credentials',
                details={'error': 'Username or password is incorrect'},
                status=401
            )

        # Create tokens
        tokens = create_tokens(user_id=username, roles=user['roles'])

        logger.info(f"User logged in: {username}")

        return success_response(
            data={
                **tokens,
                'user': {
                    'id': username,
                    'username': username,
                    'roles': user['roles'],
                    'is_admin': 'admin' in user['roles']
                }
            },
            message='Login successful'
        )

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return error_response(
            code='SYS_001',
            message=str(e),
            details={'error': 'Login failed'},
            status=500
        )


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token

    Request Headers:
        Authorization: Bearer <refresh_token>

    Response:
        {
            "success": true,
            "data": {
                "access_token": "eyJ...",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }

    Status Codes:
        200: Token refreshed successfully
        401: Invalid or expired refresh token
    """
    try:
        current_user = get_current_user()
        user_id = current_user['user_id']
        roles = current_user['roles']

        # Create new access token
        tokens = create_tokens(user_id=user_id, roles=roles)

        logger.info(f"Token refreshed for user: {user_id}")

        return success_response(
            data={
                'access_token': tokens['access_token'],
                'token_type': tokens['token_type'],
                'expires_in': tokens['expires_in']
            },
            message='Token refreshed successfully'
        )

    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        return error_response(
            code='SYS_001',
            message='Token refresh failed',
            details=str(e),
            status=500
        )


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    """
    Get current authenticated user information

    Request Headers:
        Authorization: Bearer <access_token>

    Response:
        {
            "success": true,
            "data": {
                "user_id": "admin",
                "roles": ["admin", "user"],
                "is_admin": true
            }
        }

    Status Codes:
        200: User info retrieved successfully
        401: Unauthorized
    """
    try:
        user = get_current_user()

        return success_response(
            data=user,
            message='User information retrieved'
        )

    except Exception as e:
        logger.error(f"Get user info error: {e}", exc_info=True)
        return error_response(
            code='SYS_001',
            message='Failed to get user info',
            details=str(e),
            status=500
        )


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User logout endpoint

    Note: JWT tokens are stateless, so we can't truly invalidate them
    on the server side without a token blacklist (Redis).
    This endpoint is provided for client-side cleanup.

    Request Headers:
        Authorization: Bearer <access_token>

    Response:
        {
            "success": true,
            "message": "Logout successful"
        }

    Status Codes:
        200: Logout successful
        401: Unauthorized
    """
    try:
        user = get_current_user()
        user_id = user['user_id']

        # TODO: Add token to blacklist in Redis for true revocation
        # For now, just log the logout

        logger.info(f"User logged out: {user_id}")

        return success_response(
            message='Logout successful. Please discard your tokens.'
        )

    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        return error_response(
            code='SYS_001',
            message='Logout failed',
            details=str(e),
            status=500
        )


@auth_bp.route('/generate-api-key', methods=['POST'])
@jwt_required()
def generate_api_key():
    """
    Generate a new API key for programmatic access

    Request Headers:
        Authorization: Bearer <access_token>

    Request:
        {
            "name": "My API Key",
            "description": "For CI/CD automation"
        }

    Response:
        {
            "success": true,
            "data": {
                "api_key": "sk_live_abc123...",
                "name": "My API Key",
                "description": "For CI/CD automation",
                "created_at": "2026-01-13T10:00:00Z"
            }
        }

    Status Codes:
        200: API key generated successfully
        401: Unauthorized
    """
    try:
        user = get_current_user()
        data = request.get_json() or {}

        # Generate secure API key
        api_key = f"sk_live_{secrets.token_urlsafe(32)}"

        # TODO: Store API key in database with user_id
        # For now, just return it

        logger.info(f"API key generated for user: {user['user_id']}")

        return success_response(
            data={
                'api_key': api_key,
                'name': data.get('name', 'Unnamed API Key'),
                'description': data.get('description', ''),
                'created_at': '2026-01-13T10:00:00Z'  # TODO: Use actual timestamp
            },
            message='API key generated successfully'
        )

    except Exception as e:
        logger.error(f"API key generation error: {e}", exc_info=True)
        return error_response(
            code='SYS_001',
            message='Failed to generate API key',
            details=str(e),
            status=500
        )
