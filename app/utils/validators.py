"""
Input validation utilities
"""
import re
from typing import Any, List
from app.utils.exceptions import ValidationError


def validate_required(data: dict, required_fields: List[str]):
    """
    Validate required fields are present

    Args:
        data: Input data dictionary
        required_fields: List of required field names

    Raises:
        ValidationError: If any required field is missing
    """
    missing = [field for field in required_fields if field not in data or data[field] is None]

    if missing:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing)}",
            {'missing_fields': missing}
        )


def validate_url(url: str) -> bool:
    """
    Validate URL format

    Args:
        url: URL string to validate

    Returns:
        True if valid URL

    Raises:
        ValidationError: If URL is invalid
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    if not url_pattern.match(url):
        raise ValidationError(f"Invalid URL format: {url}")

    return True


def validate_email(email: str) -> bool:
    """
    Validate email format

    Args:
        email: Email string to validate

    Returns:
        True if valid email

    Raises:
        ValidationError: If email is invalid
    """
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    if not email_pattern.match(email):
        raise ValidationError(f"Invalid email format: {email}")

    return True


def validate_choice(value: str, choices: List[str], field_name: str = 'field'):
    """
    Validate value is in allowed choices

    Args:
        value: Value to validate
        choices: List of allowed values
        field_name: Name of field being validated

    Raises:
        ValidationError: If value not in choices
    """
    if value not in choices:
        raise ValidationError(
            f"{field_name} must be one of: {', '.join(choices)}. Got: {value}",
            {'allowed_values': choices, 'provided_value': value}
        )


def validate_range(value: int, min_val: int, max_val: int, field_name: str = 'field'):
    """
    Validate numeric value is within range

    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Name of field being validated

    Raises:
        ValidationError: If value out of range
    """
    if not (min_val <= value <= max_val):
        raise ValidationError(
            f"{field_name} must be between {min_val} and {max_val}. Got: {value}"
        )
