from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging


class BaseIngestionService(ABC):
    """
    Abstract base class for data ingestion services.
    Defines the standard interface for fetching data from exchanges.
    """
    
    def __init__(self, data_source_id: int):
        self.data_source_id = data_source_id
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def fetch_transactions(
        self, 
        start_time: datetime, 
        end_time: datetime,
        account_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch transaction data for the specified time range.
        
        Args:
            start_time: Start of the time range
            end_time: End of the time range
            account_type: Optional account type filter (spot, margin, futures)
            
        Returns:
            List of raw transaction records
        """
        pass
    
    @abstractmethod
    async def fetch_current_positions(
        self,
        account_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch current position/balance snapshot.
        
        Args:
            account_type: Optional account type filter
            
        Returns:
            Dictionary of current positions/balances
        """
        pass
    
    @abstractmethod
    async def store_raw_data(self, raw_data: List[Dict[str, Any]], data_type: str):
        """
        Store raw data in the staging layer.
        
        Args:
            raw_data: List of raw records from the exchange
            data_type: Type of data (transactions, positions, etc.)
        """
        pass
    
    def _should_retry_error(self, error: Exception) -> bool:
        """Determine if an error should trigger a retry."""
        # Common logic for retryable errors
        retryable_errors = [
            "rate limit",
            "timeout",
            "connection error",
            "temporary failure"
        ]
        error_msg = str(error).lower()
        return any(err in error_msg for err in retryable_errors)