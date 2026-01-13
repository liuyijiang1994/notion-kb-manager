"""
Custom exception classes
"""
from typing import Any


class ApplicationError(Exception):
    """Base exception for application errors"""
    def __init__(self, message: str, code: str = 'APP_ERROR', status: int = 500):
        self.message = message
        self.code = code
        self.status = status
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """Raised when input validation fails"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code='VAL_001', status=400)
        self.details = details


class NotFoundError(ApplicationError):
    """Raised when resource not found"""
    def __init__(self, resource: str, identifier: Any):
        message = f"{resource} with id {identifier} not found"
        super().__init__(message, code='RES_001', status=404)


class AlreadyExistsError(ApplicationError):
    """Raised when resource already exists"""
    def __init__(self, resource: str, identifier: Any):
        message = f"{resource} with {identifier} already exists"
        super().__init__(message, code='RES_002', status=409)


class ExternalAPIError(ApplicationError):
    """Raised when external API call fails"""
    def __init__(self, service: str, message: str):
        full_message = f"{service} API error: {message}"
        super().__init__(full_message, code='EXT_001', status=502)


class DatabaseError(ApplicationError):
    """Raised when database operation fails"""
    def __init__(self, message: str):
        super().__init__(message, code='SYS_002', status=500)
