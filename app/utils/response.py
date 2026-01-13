"""
API response utilities
Standardized response formatting
"""
from flask import jsonify
from datetime import datetime
from typing import Any, Optional, Dict


def success_response(data: Any = None, message: Optional[str] = None, status: int = 200):
    """
    Create standardized success response

    Args:
        data: Response data
        message: Success message
        status: HTTP status code

    Returns:
        Flask JSON response
    """
    response = {
        'success': True,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    if data is not None:
        response['data'] = data

    if message:
        response['message'] = message

    return jsonify(response), status


def error_response(code: str, message: str, details: Optional[Dict] = None, status: int = 400):
    """
    Create standardized error response

    Args:
        code: Error code (e.g., 'VAL_001')
        message: Error message
        details: Additional error details
        status: HTTP status code

    Returns:
        Flask JSON response
    """
    response = {
        'success': False,
        'error': {
            'code': code,
            'message': message
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    if details:
        response['error']['details'] = details

    return jsonify(response), status


def paginated_response(items: list, total: int, page: int, limit: int, status: int = 200):
    """
    Create paginated response

    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        limit: Items per page
        status: HTTP status code

    Returns:
        Flask JSON response
    """
    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    response = {
        'success': True,
        'data': {
            'items': items,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': total_pages
            }
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    return jsonify(response), status
