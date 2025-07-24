from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class BaseAPIClient(ABC):
    """
    Abstract base class for all exchange API clients.
    Provides common functionality and enforces consistent interface.
    """
    
    def __init__(self, api_key: str, api_secret: str, **kwargs):
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logging.getLogger(self.__class__.__name__)
        self._initialize(**kwargs)
    
    @abstractmethod
    def _initialize(self, **kwargs):
        """Initialize exchange-specific settings."""
        pass
    
    @abstractmethod
    def test_connectivity(self) -> bool:
        """Test if the API connection is working."""
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """Get basic account information."""
        pass
    
    @abstractmethod
    def validate_api_permissions(self) -> Dict[str, bool]:
        """
        Validate that API keys have required permissions.
        Returns dict with permission checks.
        """
        pass
    
    def _log_request(self, method: str, endpoint: str, params: Optional[Dict] = None):
        """Log API request details for debugging."""
        self.logger.debug(f"{method} {endpoint} - params: {params}")
    
    def _log_response(self, status_code: int, response_data: Any):
        """Log API response details for debugging."""
        self.logger.debug(f"Response {status_code}: {response_data}")