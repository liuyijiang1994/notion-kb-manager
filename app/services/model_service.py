"""
Model service for AI model integration and testing
Supports OpenAI-compatible APIs (OpenAI, VolcEngine, etc.)
"""
import logging
import requests
import time
from typing import Dict, Any, Optional
from app.utils.exceptions import ExternalAPIError, ValidationError

logger = logging.getLogger(__name__)


class ModelService:
    """Service for interacting with AI models"""

    def __init__(self):
        self.timeout = 30  # Default timeout in seconds

    def test_connection(self, api_url: str, api_token: str, model_name: str,
                       timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Test connection to AI model API

        Args:
            api_url: Base URL of the API endpoint
            api_token: API authentication token
            model_name: Model identifier
            timeout: Request timeout in seconds

        Returns:
            Dictionary with connection test results:
            {
                'success': bool,
                'latency_ms': int,
                'model_info': dict,
                'error': str (if failed)
            }
        """
        timeout = timeout or self.timeout

        try:
            # Prepare OpenAI-compatible chat completion request
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }

            # Simple test message
            payload = {
                'model': model_name,
                'messages': [
                    {
                        'role': 'user',
                        'content': 'Hello, this is a connection test. Please respond with OK.'
                    }
                ],
                'max_tokens': 10,
                'temperature': 0.1
            }

            # Measure latency
            start_time = time.time()

            # Make request to chat completions endpoint
            endpoint = self._build_endpoint(api_url, 'chat/completions')
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=timeout
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Check response
            if response.status_code == 200:
                data = response.json()

                return {
                    'success': True,
                    'latency_ms': latency_ms,
                    'model_info': {
                        'model': data.get('model', model_name),
                        'response': data.get('choices', [{}])[0].get('message', {}).get('content', ''),
                        'usage': data.get('usage', {}),
                        'finish_reason': data.get('choices', [{}])[0].get('finish_reason', 'unknown')
                    },
                    'message': f'Connection successful. Response time: {latency_ms}ms'
                }
            else:
                error_msg = self._parse_error_response(response)
                logger.error(f"Model API connection failed: {error_msg}")

                return {
                    'success': False,
                    'latency_ms': latency_ms,
                    'error': error_msg,
                    'status_code': response.status_code
                }

        except requests.exceptions.Timeout:
            logger.error(f"Model API connection timeout after {timeout}s")
            return {
                'success': False,
                'error': f'Connection timeout after {timeout} seconds',
                'latency_ms': timeout * 1000
            }

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Model API connection error: {e}")
            return {
                'success': False,
                'error': f'Connection error: Unable to reach API endpoint',
                'details': str(e)
            }

        except Exception as e:
            logger.error(f"Unexpected error testing model connection: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }

    def chat_completion(self, api_url: str, api_token: str, model_name: str,
                       messages: list, max_tokens: int = 1000,
                       temperature: float = 0.7, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Make a chat completion request to the model

        Args:
            api_url: Base URL of the API endpoint
            api_token: API authentication token
            model_name: Model identifier
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            timeout: Request timeout in seconds

        Returns:
            Dictionary with response data or error
        """
        timeout = timeout or self.timeout

        try:
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': model_name,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature
            }

            endpoint = self._build_endpoint(api_url, 'chat/completions')
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = self._parse_error_response(response)
                raise ExternalAPIError('Model API', error_msg)

        except requests.exceptions.Timeout:
            raise ExternalAPIError('Model API', f'Request timeout after {timeout} seconds')

        except requests.exceptions.ConnectionError as e:
            raise ExternalAPIError('Model API', f'Connection error: {str(e)}')

    def _build_endpoint(self, base_url: str, path: str) -> str:
        """Build full API endpoint URL"""
        # Remove trailing slash from base_url
        base_url = base_url.rstrip('/')
        # Remove leading slash from path
        path = path.lstrip('/')
        return f"{base_url}/{path}"

    def _parse_error_response(self, response: requests.Response) -> str:
        """Parse error message from API response"""
        try:
            error_data = response.json()

            # OpenAI-compatible error format
            if 'error' in error_data:
                error_obj = error_data['error']
                if isinstance(error_obj, dict):
                    return error_obj.get('message', str(error_obj))
                return str(error_obj)

            return error_data.get('message', f'API error: {response.status_code}')

        except Exception:
            return f'HTTP {response.status_code}: {response.text[:200]}'


# Global instance
_model_service: Optional[ModelService] = None


def get_model_service() -> ModelService:
    """Get or create global ModelService instance"""
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
    return _model_service
