# /Users/cameronwong/coinfrs_v2/backend/app/services/ingestion/binance_client.py
import time
import hmac
import hashlib
from urllib.parse import urlencode
import requests

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

    def _make_request(self, method: str, url: str, params: dict = None, signed: bool = False):
        """
        Makes a request to the Binance API.
        """
        if params is None:
            params = {}

        if signed:
            params["timestamp"] = self._get_timestamp()
            params["signature"] = self._sign_request(params)

        try:
            response = self.session.request(method, url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # In a real app, log this error
            print(f"Error making request to {url}: {e}")
            # You might want to raise a custom exception here
            raise

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
        except requests.exceptions.RequestException:
            return False

