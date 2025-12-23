"""
Amadeus API client wrapper with authentication, retry logic, and logging.
Reuses the same client wrapper pattern as mcp-flights.
"""
import os
import sys
import time
import socket
from pathlib import Path
from typing import Any, Dict, Optional
from amadeus import Client, ResponseError
from amadeus.client.errors import ServerError, ClientError, NetworkError

# Set a default socket timeout to prevent API calls from hanging indefinitely
# This is critical for the sandbox environment where network issues can cause hangs
socket.setdefaulttimeout(30)  # 30 seconds timeout

# Load .env file if it exists (from project root)
try:
    from dotenv import load_dotenv
    # Try to find .env file in project root
    # This file is at: OdyssAI/mcp-servers/mcp-hotels/amadeus_client.py
    # .env is at: OdyssAI/.env
    # So we go up 3 levels: mcp-hotels -> mcp-servers -> OdyssAI
    current_file = Path(__file__).resolve()
    env_path = current_file.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except (ImportError, NameError):
    # python-dotenv not installed or __file__ not available, skip loading .env
    pass

from logger import get_logger


class AmadeusClientWrapper:
    """Wrapper for Amadeus client with enhanced logging and error handling."""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialize Amadeus client.
        
        Args:
            client_id: Amadeus API client ID (defaults to AMADEUS_CLIENT_ID env var)
            client_secret: Amadeus API client secret (defaults to AMADEUS_CLIENT_SECRET env var)
        """
        self.logger = get_logger("AMADEUS_CLIENT")
        
        # Get credentials from parameters or environment
        # Support both naming conventions
        self.client_id = (
            client_id or 
            os.getenv('AMADEUS_CLIENT_ID') or 
            os.getenv('AMADEUS_API_KEY')
        )
        self.client_secret = (
            client_secret or 
            os.getenv('AMADEUS_CLIENT_SECRET') or 
            os.getenv('AMADEUS_API_SECRET')
        )
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Amadeus credentials not provided. "
                "Set AMADEUS_CLIENT_ID/AMADEUS_API_KEY and "
                "AMADEUS_CLIENT_SECRET/AMADEUS_API_SECRET environment variables."
            )
        
        # Initialize Amadeus client
        # Support both AMADEUS_HOSTNAME and AMADEUS_ENV
        amadeus_env = os.getenv('AMADEUS_ENV', '').lower()
        amadeus_hostname = os.getenv('AMADEUS_HOSTNAME', '').lower()
        
        if amadeus_hostname:
            hostname = amadeus_hostname
        elif amadeus_env == 'prod' or amadeus_env == 'production':
            hostname = 'production'
        elif amadeus_env == 'test':
            hostname = 'test'
        else:
            hostname = 'test'  # default
        
        self.client = Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            hostname=hostname
        )
        
        self.logger.info(f"Amadeus client initialized (hostname: {hostname})")
    
    def _log_api_call(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None
    ):
        """Log API call details."""
        self.logger.debug(f"API Call: {method} {endpoint}")
        if params:
            # Sanitize sensitive data
            sanitized_params = self._sanitize_dict(params)
            self.logger.debug(f"Parameters: {sanitized_params}")
        if body:
            sanitized_body = self._sanitize_dict(body)
            self.logger.debug(f"Request Body: {sanitized_body}")
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from dict for logging."""
        sensitive_keys = {'client_secret', 'password', 'creditCard', 'cardNumber'}
        sanitized = {}
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized
    
    def _log_api_response(self, response: Any, duration: float):
        """Log API response details."""
        if hasattr(response, 'data'):
            data_size = len(str(response.data)) if response.data else 0
            self.logger.info(
                f"API Response received in {duration:.3f}s "
                f"(data size: {data_size} chars)"
            )
            self.logger.debug(f"Response data: {response.data}")
        else:
            self.logger.info(f"API Response received in {duration:.3f}s")
    
    def _handle_error(self, error: Exception, retry_count: int = 0):
        """Handle and log API errors."""
        error_type = type(error).__name__
        
        if isinstance(error, ResponseError):
            self.logger.error(
                f"Amadeus API Error (attempt {retry_count + 1}): "
                f"{error_type} - {str(error)}"
            )
            self.logger.debug(f"Error code: {getattr(error, 'code', 'N/A')}")
        elif isinstance(error, ServerError):
            self.logger.error(f"Amadeus Server Error (attempt {retry_count + 1}): {error}")
        elif isinstance(error, ClientError):
            self.logger.error(f"Amadeus Client Error (attempt {retry_count + 1}): {error}")
        elif isinstance(error, NetworkError):
            self.logger.error(f"Amadeus Network Error (attempt {retry_count + 1}): {error}")
        else:
            self.logger.error(f"Unexpected error (attempt {retry_count + 1}): {error_type} - {error}")
    
    def _should_retry(self, error: Exception, retry_count: int, max_retries: int) -> bool:
        """Determine if request should be retried."""
        if retry_count >= max_retries:
            return False
        
        # Retry on server errors and network errors
        if isinstance(error, (ServerError, NetworkError)):
            return True
        
        # Retry on rate limit errors (429)
        if isinstance(error, ResponseError) and hasattr(error, 'code') and error.code == 429:
            return True
        
        return False
    
    def _get_retry_delay(self, retry_count: int) -> float:
        """Calculate exponential backoff delay."""
        base_delay = 1.0
        return base_delay * (2 ** retry_count)
    
    def get_client(self) -> Client:
        """Get the underlying Amadeus client instance."""
        return self.client

