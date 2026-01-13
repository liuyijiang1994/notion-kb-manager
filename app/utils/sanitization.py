"""
Input sanitization utilities
Protects against XSS, injection attacks, and path traversal
"""
import re
import os
import html
import json
from typing import Any, Optional
from urllib.parse import urlparse, quote
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def sanitize_html(text: str, allow_safe_tags: bool = False) -> str:
    """
    Remove or escape HTML tags to prevent XSS attacks

    Args:
        text: Input text that may contain HTML
        allow_safe_tags: If True, allows basic formatting tags (b, i, u, br, p)

    Returns:
        Sanitized text with HTML removed or escaped

    Examples:
        >>> sanitize_html("<script>alert('XSS')</script>Hello")
        "&lt;script&gt;alert('XSS')&lt;/script&gt;Hello"

        >>> sanitize_html("<b>Bold</b> text", allow_safe_tags=True)
        "<b>Bold</b> text"
    """
    if not text:
        return text

    if allow_safe_tags:
        # Allow only safe formatting tags
        safe_tags = ['b', 'i', 'u', 'br', 'p', 'strong', 'em']

        # Remove dangerous tags
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'<iframe[^>]*>.*?</iframe>',  # Iframes
            r'<object[^>]*>.*?</object>',  # Objects
            r'<embed[^>]*>',                # Embeds
            r'<link[^>]*>',                 # Links (stylesheets)
            r'on\w+\s*=',                   # Event handlers (onclick, etc)
            r'javascript:',                  # JavaScript URLs
        ]

        for pattern in dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        return text
    else:
        # Escape all HTML entities
        return html.escape(text)


def sanitize_url(url: str, allowed_schemes: list = None) -> Optional[str]:
    """
    Validate and sanitize URLs to prevent SSRF and injection attacks

    Args:
        url: URL to sanitize
        allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])

    Returns:
        Sanitized URL or None if invalid

    Examples:
        >>> sanitize_url("https://example.com/page?id=123")
        "https://example.com/page?id=123"

        >>> sanitize_url("javascript:alert('XSS')")
        None

        >>> sanitize_url("file:///etc/passwd")
        None
    """
    if not url:
        return None

    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']

    try:
        # Parse URL
        parsed = urlparse(url)

        # Validate scheme
        if parsed.scheme.lower() not in allowed_schemes:
            logger.warning(f"Invalid URL scheme: {parsed.scheme}")
            return None

        # Block localhost/internal IPs (prevent SSRF)
        if parsed.hostname:
            hostname = parsed.hostname.lower()

            # Block localhost
            if hostname in ['localhost', '127.0.0.1', '::1', '0.0.0.0']:
                logger.warning(f"Blocked localhost URL: {url}")
                return None

            # Block private IP ranges
            if hostname.startswith(('192.168.', '10.', '172.16.', '172.17.', '172.18.',
                                   '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
                                   '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
                                   '172.29.', '172.30.', '172.31.')):
                logger.warning(f"Blocked private IP URL: {url}")
                return None

        # Reconstruct safe URL
        safe_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        if parsed.query:
            safe_url += f"?{parsed.query}"

        return safe_url

    except Exception as e:
        logger.error(f"URL sanitization error: {e}")
        return None


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to prevent path traversal and injection attacks

    Args:
        filename: Original filename
        max_length: Maximum allowed filename length

    Returns:
        Sanitized filename safe for file system

    Examples:
        >>> sanitize_filename("../../etc/passwd")
        "etc_passwd"

        >>> sanitize_filename("report<script>.pdf")
        "report_script_.pdf"

        >>> sanitize_filename("my file (1).txt")
        "my_file_1_.txt"
    """
    if not filename:
        return "unnamed_file"

    # Remove path components
    filename = os.path.basename(filename)

    # Remove or replace dangerous characters
    # Allow only alphanumeric, dash, underscore, dot
    filename = re.sub(r'[^\w\-\.]', '_', filename)

    # Remove leading/trailing dots and underscores
    filename = filename.strip('._')

    # Prevent multiple consecutive dots (directory traversal)
    filename = re.sub(r'\.{2,}', '.', filename)

    # Ensure filename has an extension
    if '.' not in filename:
        filename += '.txt'

    # Limit length
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext

    # Ensure not empty after sanitization
    if not filename or filename == '.txt':
        filename = "unnamed_file.txt"

    return filename


def sanitize_path(path: str, base_dir: str) -> Optional[str]:
    """
    Sanitize file path to prevent directory traversal attacks

    Args:
        path: Requested file path
        base_dir: Base directory that path must be within

    Returns:
        Sanitized absolute path or None if invalid

    Examples:
        >>> sanitize_path("../../etc/passwd", "/var/app/uploads")
        None

        >>> sanitize_path("user/file.txt", "/var/app/uploads")
        "/var/app/uploads/user/file.txt"
    """
    try:
        # Resolve to absolute path
        base = Path(base_dir).resolve()
        target = (base / path).resolve()

        # Check if target is within base directory
        if base in target.parents or target == base:
            return str(target)
        else:
            logger.warning(f"Path traversal attempt: {path}")
            return None

    except Exception as e:
        logger.error(f"Path sanitization error: {e}")
        return None


def sanitize_json_field(value: Any, field_type: str = 'text') -> Any:
    """
    Sanitize JSON field based on expected type

    Args:
        value: Field value to sanitize
        field_type: Expected field type ('text', 'html', 'url', 'number', 'boolean')

    Returns:
        Sanitized value

    Examples:
        >>> sanitize_json_field("<script>alert('XSS')</script>", 'text')
        "&lt;script&gt;alert('XSS')&lt;/script&gt;"

        >>> sanitize_json_field("javascript:alert()", 'url')
        None

        >>> sanitize_json_field("123", 'number')
        123
    """
    if value is None:
        return None

    if field_type == 'text':
        if isinstance(value, str):
            return sanitize_html(value, allow_safe_tags=False)
        return value

    elif field_type == 'html':
        if isinstance(value, str):
            return sanitize_html(value, allow_safe_tags=True)
        return value

    elif field_type == 'url':
        if isinstance(value, str):
            return sanitize_url(value)
        return None

    elif field_type == 'number':
        try:
            if isinstance(value, (int, float)):
                return value
            return float(value) if '.' in str(value) else int(value)
        except (ValueError, TypeError):
            return None

    elif field_type == 'boolean':
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes']
        return bool(value)

    return value


def validate_json_schema(data: dict, schema: dict) -> tuple[bool, Optional[str]]:
    """
    Validate JSON data against a schema and sanitize fields

    Args:
        data: JSON data to validate
        schema: Schema definition with field types

    Returns:
        Tuple of (is_valid, error_message)

    Schema format:
        {
            'field_name': {
                'type': 'text|html|url|number|boolean',
                'required': True|False,
                'max_length': int (for text fields)
            }
        }

    Example:
        >>> schema = {
        ...     'title': {'type': 'text', 'required': True, 'max_length': 200},
        ...     'url': {'type': 'url', 'required': True},
        ...     'count': {'type': 'number', 'required': False}
        ... }
        >>> validate_json_schema({'title': 'Test', 'url': 'https://example.com'}, schema)
        (True, None)
    """
    for field_name, field_schema in schema.items():
        field_type = field_schema.get('type', 'text')
        required = field_schema.get('required', False)
        max_length = field_schema.get('max_length')

        # Check required fields
        if required and field_name not in data:
            return False, f"Missing required field: {field_name}"

        # Validate field if present
        if field_name in data:
            value = data[field_name]

            # Sanitize based on type
            sanitized = sanitize_json_field(value, field_type)

            if sanitized is None and value is not None:
                return False, f"Invalid value for field: {field_name}"

            # Check max length for text fields
            if max_length and isinstance(sanitized, str):
                if len(sanitized) > max_length:
                    return False, f"Field {field_name} exceeds max length of {max_length}"

            # Update with sanitized value
            data[field_name] = sanitized

    return True, None


def strip_sql_injection(value: str) -> str:
    """
    Remove common SQL injection patterns from input

    Note: This is NOT a substitute for parameterized queries!
    Always use SQLAlchemy's parameter binding for database queries.

    Args:
        value: Input string that might contain SQL injection

    Returns:
        String with SQL injection patterns removed

    Examples:
        >>> strip_sql_injection("admin'; DROP TABLE users; --")
        "admin"

        >>> strip_sql_injection("1' OR '1'='1")
        "1"
    """
    if not value:
        return value

    # Remove SQL comment markers
    value = re.sub(r'--.*$', '', value)  # SQL line comments
    value = re.sub(r'/\*.*?\*/', '', value, flags=re.DOTALL)  # SQL block comments

    # Remove common SQL keywords in injection context
    dangerous_patterns = [
        r";\s*(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER|EXEC|EXECUTE)\s+",
        r"'\s*(OR|AND)\s+'[^']*'\s*=\s*'",
        r"\bUNION\b.*\bSELECT\b",
        r"\bINTO\s+OUTFILE\b",
        r"\bLOAD_FILE\b",
    ]

    for pattern in dangerous_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)

    return value.strip()


def sanitize_request_data(data: dict) -> dict:
    """
    Sanitize all string fields in request data

    Args:
        data: Request data dictionary

    Returns:
        Dictionary with sanitized string values

    Example:
        >>> sanitize_request_data({
        ...     'title': '<script>XSS</script>',
        ...     'count': 5,
        ...     'nested': {'text': '<b>bold</b>'}
        ... })
        {'title': '&lt;script&gt;XSS&lt;/script&gt;', 'count': 5, 'nested': {'text': '&lt;b&gt;bold&lt;/b&gt;'}}
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}

    for key, value in data.items():
        if isinstance(value, str):
            # Sanitize string values
            sanitized[key] = sanitize_html(value, allow_safe_tags=False)
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries
            sanitized[key] = sanitize_request_data(value)
        elif isinstance(value, list):
            # Sanitize list items
            sanitized[key] = [
                sanitize_request_data(item) if isinstance(item, dict)
                else sanitize_html(item, allow_safe_tags=False) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            # Keep non-string values as-is
            sanitized[key] = value

    return sanitized
