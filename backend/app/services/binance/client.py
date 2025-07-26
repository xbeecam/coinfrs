# /Users/cameronwong/coinfrs_v2/backend/app/services/ingestion/binance_client.py
import time
import hmac
import hashlib
from urllib.parse import urlencode
import requests
from enum import Enum
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime


class BinanceErrorType(Enum):
    """Binance API error types for proper error handling and recovery"""
    API_KEY_INVALID = "API_KEY_INVALID"
    RATE_LIMIT = "RATE_LIMIT"
    PARAMETER_ERROR = "PARAMETER_ERROR"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    NETWORK_ERROR = "NETWORK_ERROR"
    INVALID_SYMBOL = "INVALID_SYMBOL"
    UNKNOWN = "UNKNOWN"


class BinanceAPIError(Exception):
    """Custom exception for Binance API errors with error type categorization"""
    def __init__(self, message: str, error_type: BinanceErrorType, code: Optional[int] = None):
        super().__init__(message)
        self.error_type = error_type
        self.code = code
        self.timestamp = datetime.utcnow()
        
    def __str__(self):
        return f"BinanceAPIError({self.error_type.value}): {super().__str__()} [Code: {self.code}]"


class RateLimiter:
    """Conservative rate limiter for Binance API requests"""
    def __init__(self):
        # Conservative limits (50% of actual)
        self.weight_limit = 3000  # per minute (actual is 6000)
        self.weight_used = 0
        self.weight_window_start = time.time()
        self.lock = asyncio.Lock()
        
    async def acquire(self, weight: int):
        """Acquire permission to use specified weight, waiting if necessary"""
        async with self.lock:
            current_time = time.time()
            # Reset window if minute has passed
            if current_time - self.weight_window_start >= 60:
                self.weight_used = 0
                self.weight_window_start = current_time
            
            # Check if we would exceed limit
            if self.weight_used + weight > self.weight_limit:
                # Calculate wait time
                wait_time = 60 - (current_time - self.weight_window_start)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Reset after waiting
                    self.weight_used = 0
                    self.weight_window_start = time.time()
            
            self.weight_used += weight
            
    def reset(self):
        """Manually reset the rate limiter"""
        self.weight_used = 0
        self.weight_window_start = time.time()


class BinanceAPIClient:
    """
    A client for interacting with the Binance API.
    Handles request signing as required by USER_DATA and SAPI endpoints.
    """
    BASE_API_URL = "https://api.binance.com"
    BASE_SAPI_URL = "https://api.binance.com/sapi/v1"

    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise ValueError("API key and secret cannot be empty.")
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        self.rate_limiter = RateLimiter()

    def _get_timestamp(self) -> int:
        """Returns the current time in milliseconds."""
        return int(time.time() * 1000)

    def _sign_request(self, params: dict) -> str:
        """
        Generates an HMAC-SHA256 signature for the request.
        """
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _categorize_error(self, error_code: int, error_msg: str) -> BinanceErrorType:
        """Categorize Binance API errors based on error code and message"""
        # API key related errors
        if error_code in [-2014, -2015, -1022]:
            return BinanceErrorType.API_KEY_INVALID
        # Rate limit errors
        elif error_code in [-1003, -1015]:
            return BinanceErrorType.RATE_LIMIT
        # Parameter errors
        elif error_code in [-1100, -1101, -1102, -1103, -1104, -1105, -1106, -1111, -1112, -1121, -1125, -1127, -1128]:
            return BinanceErrorType.PARAMETER_ERROR
        # Invalid symbol
        elif error_code == -1121:
            return BinanceErrorType.INVALID_SYMBOL
        # Insufficient balance
        elif error_code in [-2010, -1013]:
            return BinanceErrorType.INSUFFICIENT_BALANCE
        # Network error
        elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
            return BinanceErrorType.NETWORK_ERROR
        else:
            return BinanceErrorType.UNKNOWN

    def _make_request(self, method: str, url: str, params: dict = None, signed: bool = False, weight: int = 1):
        """
        Makes a request to the Binance API with proper error handling and categorization.
        """
        if params is None:
            params = {}

        if signed:
            params["timestamp"] = self._get_timestamp()
            params["signature"] = self._sign_request(params)

        # Apply rate limiting synchronously (blocking)
        time.sleep(weight * 0.02)  # Simple delay based on weight
        
        try:
            response = self.session.request(method, url, params=params, timeout=30)
            
            # Check for API errors in response
            if response.status_code != 200:
                error_data = response.json()
                error_code = error_data.get("code", 0)
                error_msg = error_data.get("msg", "Unknown error")
                error_type = self._categorize_error(error_code, error_msg)
                raise BinanceAPIError(error_msg, error_type, error_code)
            
            return response.json()
        except requests.exceptions.ConnectionError as e:
            raise BinanceAPIError(f"Network connection error: {str(e)}", BinanceErrorType.NETWORK_ERROR)
        except requests.exceptions.Timeout as e:
            raise BinanceAPIError(f"Request timeout: {str(e)}", BinanceErrorType.NETWORK_ERROR)
        except requests.exceptions.RequestException as e:
            raise BinanceAPIError(f"Request error: {str(e)}", BinanceErrorType.UNKNOWN)

    def get_exchange_info(self):
        """
        Fetches current exchange trading rules and symbol information.
        """
        url = f"{self.BASE_API_URL}/api/v3/exchangeInfo"
        return self._make_request("GET", url)

    # --- Methods for the required endpoints will be added here ---

    def get_my_trades(self, symbol: str, start_time: int = None, end_time: int = None, from_id: int = None, limit: int = 1000):
        """
        Get trades for a specific account and symbol.
        """
        params = {"symbol": symbol, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if from_id:
            params["fromId"] = from_id
        
        url = f"{self.BASE_API_URL}/api/v3/myTrades"
        return self._make_request("GET", url, params=params, signed=True)

    def get_deposit_history(self, start_time: int = None, end_time: int = None, limit: int = 1000):
        """
        Fetch deposit history.
        """
        params = {"limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        url = f"{self.BASE_SAPI_URL}/capital/deposit/hisrec"
        return self._make_request("GET", url, params=params, signed=True)

    def get_withdrawal_history(self, start_time: int = None, end_time: int = None, limit: int = 1000):
        """
        Fetch withdrawal history.
        """
        params = {"limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        
        url = f"{self.BASE_SAPI_URL}/capital/withdraw/history"
        return self._make_request("GET", url, params=params, signed=True)

    def validate_api_permissions(self) -> bool:
        """
        Validates API key and permissions by making a simple read-only call.
        """
        try:
            self.get_exchange_info()
            return True
        except BinanceAPIError as e:
            if e.error_type == BinanceErrorType.API_KEY_INVALID:
                return False
            raise
        except Exception:
            return False
    
    # Pagination helper methods
    def paginate_request(self, endpoint_func, start_time: int, end_time: int, 
                        limit_per_page: int = 1000, **kwargs) -> List[Dict[str, Any]]:
        """
        Helper method to paginate through API results for endpoints that support pagination.
        Handles both fromId and offset-based pagination.
        """
        all_results = []
        page = 0
        from_id = None
        
        while True:
            # Prepare params for this page
            params = {
                "startTime": start_time,
                "endTime": end_time,
                "limit": limit_per_page,
                **kwargs
            }
            
            # Add pagination param if applicable
            if from_id:
                params["fromId"] = from_id
            elif page > 0 and "offset" in kwargs:
                params["offset"] = page * limit_per_page
            
            # Make request
            results = endpoint_func(**params)
            
            # Handle different response formats
            if isinstance(results, dict) and "rows" in results:
                results = results["rows"]
            
            if not results:
                break
                
            all_results.extend(results)
            
            # Check if we got less than limit (last page)
            if len(results) < limit_per_page:
                break
                
            # Update pagination params
            if results and "id" in results[-1]:
                from_id = results[-1]["id"]
            else:
                page += 1
                
        return all_results
    
    def chunk_time_range(self, start_time: int, end_time: int, days: int = 90) -> List[tuple]:
        """
        Split a time range into chunks to avoid hitting API limits for large date ranges.
        Returns list of (start, end) timestamp tuples.
        """
        chunks = []
        chunk_ms = days * 24 * 60 * 60 * 1000  # Convert days to milliseconds
        
        current_start = start_time
        while current_start < end_time:
            current_end = min(current_start + chunk_ms, end_time)
            chunks.append((current_start, current_end))
            current_start = current_end
            
        return chunks
    
    # New endpoint methods
    def get_account_snapshot(self, account_type: str = "SPOT", start_time: int = None, 
                           end_time: int = None, limit: int = 30) -> Dict[str, Any]:
        """
        Get daily account snapshot. Weight: 2400
        account_type: "SPOT", "MARGIN", or "FUTURES"
        """
        params = {
            "type": account_type,
            "limit": limit,
            "recvWindow": 60000  # 60 seconds to handle time sync issues
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
            
        url = f"{self.BASE_SAPI_URL}/accountSnapshot"
        return self._make_request("GET", url, params=params, signed=True, weight=2400)
    
    def get_convert_history(self, start_time: int, end_time: int, limit: int = 1000) -> Dict[str, Any]:
        """
        Get convert trade history. Weight: 3000
        """
        params = {
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit
        }
        
        url = f"{self.BASE_SAPI_URL}/convert/tradeFlow"
        return self._make_request("GET", url, params=params, signed=True, weight=3000)
    
    def get_transfer_between_accounts_main(self, start_time: int = None, end_time: int = None, 
                                         type_val: str = None, size: int = 100) -> List[Dict[str, Any]]:
        """
        Get transfer history between main and trading accounts (futures, margin, etc).
        type_val: MAIN_UMFUTURE, MAIN_CMFUTURE, MAIN_MARGIN, etc.
        """
        params = {"size": size}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if type_val:
            params["type"] = type_val
            
        url = f"{self.BASE_SAPI_URL}/asset/transfer"
        return self._make_request("GET", url, params=params, signed=True)
    
    def get_transfer_between_accounts_sub(self, start_time: int = None, end_time: int = None,
                                        limit: int = 500) -> Dict[str, Any]:
        """
        Get sub-account transfer history (for master accounts).
        """
        params = {"limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
            
        url = f"{self.BASE_SAPI_URL}/sub-account/sub/transfer/history"
        return self._make_request("GET", url, params=params, signed=True)
    
    def get_transfer_between_wallets(self, start_time: int = None, end_time: int = None,
                                   current: int = 1, size: int = 100) -> Dict[str, Any]:
        """
        Get universal transfer history (wallet to wallet).
        """
        params = {
            "current": current,
            "size": size
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
            
        url = f"{self.BASE_SAPI_URL}/asset/transfer/universal"
        return self._make_request("GET", url, params=params, signed=True)
    
    def get_sub_account_list(self, email: Optional[str] = None, is_freeze: Optional[bool] = None, 
                           page: int = 1, limit: int = 200) -> Dict[str, Any]:
        """
        Get sub-account list (for master accounts only).
        
        Args:
            email: Sub-account email (optional, for filtering)
            is_freeze: Filter by freeze status (optional)
            page: Page number (default: 1)
            limit: Number of records per page (max: 200, default: 200)
            
        Returns:
            Dictionary containing sub-account list and pagination info
            
        Raises:
            BinanceAPIError: If not a master account or other API errors
        """
        params = {"page": page, "limit": limit}
        if email:
            params["email"] = email
        if is_freeze is not None:
            params["isFreeze"] = is_freeze
            
        url = f"{self.BASE_SAPI_URL}/sub-account/list"
        return self._make_request("GET", url, params=params, signed=True, weight=10)
