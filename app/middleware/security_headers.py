"""
Security headers middleware using Flask-Talisman
Adds security headers to protect against XSS, clickjacking, and other attacks
"""
import logging
from flask_talisman import Talisman

logger = logging.getLogger(__name__)

# Content Security Policy configuration
CSP_POLICY = {
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'"],  # Allow inline scripts for API responses
    'style-src': ["'self'", "'unsafe-inline'"],   # Allow inline styles
    'img-src': ["'self'", "data:", "https:"],     # Allow images from self and data URIs
    'connect-src': "'self'",                       # Restrict AJAX/WebSocket connections
    'font-src': "'self'",
    'object-src': "'none'",                        # Disable plugins
    'frame-ancestors': "'self'",                   # Clickjacking protection
}


def init_security_headers(app):
    """
    Initialize security headers with Flask-Talisman

    Headers added:
    - Content-Security-Policy: Prevents XSS and code injection
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Browser XSS protection
    - Strict-Transport-Security: Enforces HTTPS
    - Referrer-Policy: Controls referrer information

    Args:
        app: Flask application instance
    """
    env = app.config.get('ENV', 'development')

    # Only enforce HTTPS in production
    force_https = (env == 'production')

    # Initialize Talisman with security headers
    talisman_config = {
        'force_https': force_https,
        'strict_transport_security': True,
        'strict_transport_security_max_age': 31536000,  # 1 year
        'strict_transport_security_include_subdomains': True,
        'content_security_policy': CSP_POLICY,
        'content_security_policy_report_only': False,
        'session_cookie_secure': force_https,
        'session_cookie_samesite': 'Lax',
        'frame_options': 'SAMEORIGIN',
        'frame_options_allow_from': None,
        'content_security_policy_nonce_in': [],
    }

    Talisman(app, **talisman_config)

    # Add custom headers
    @app.after_request
    def add_security_headers(response):
        """Add additional security headers to every response"""
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Enable browser XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Control referrer information
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Prevent browser from caching sensitive data
        if env == 'production' and '/api/' in response.location or '/api/' in str(response):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

        return response

    logger.info(f"Security headers initialized (HTTPS enforced: {force_https})")
