from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
import json
import csv
import os

from app.services.binance.client import BinanceAPIClient, BinanceAPIError, BinanceErrorType
from app.db.session import get_db_session
# from app.core.config import settings  # Commented out for testing


class BaseCollector(ABC):
    """Abstract base class for all Binance data collectors"""
    
    def __init__(self, api_client: BinanceAPIClient, email: str, account_type: str = "main"):
        """
        Initialize collector with API client and account info.
        
        Args:
            api_client: Configured Binance API client
            email: User email for tracking
            account_type: "main" or "sub"
        """
        self.client = api_client
        self.email = email
        self.account_type = account_type
        self.errors = []
        
    def get_db(self) -> Session:
        """Get database session - Note: In production, use context manager"""
        # For testing purposes, we'll skip database operations
        # In production, this would use: with get_db_session() as session:
        return None
            
    def close_db(self, db: Session):
        """Close database session"""
        if db:
            db.close()
        
    def get_date_range(self, days_back: int = 2) -> Tuple[datetime, datetime]:
        """
        Get standard date range for T+2 processing.
        Returns UTC timestamps for start and end of the day.
        """
        # Get UTC date for T-days_back
        end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days_back)
        
        # Add one day to end_date to get full day range
        end_date = end_date + timedelta(days=1) - timedelta(microseconds=1)
        
        return start_date, end_date
        
    def timestamp_to_ms(self, dt: datetime) -> int:
        """Convert datetime to milliseconds timestamp"""
        return int(dt.timestamp() * 1000)
        
    def ms_to_datetime(self, ms: int) -> datetime:
        """Convert milliseconds timestamp to UTC datetime"""
        # Handle both string and int inputs
        if isinstance(ms, str):
            # Check if it's already a datetime string
            if '-' in ms and ':' in ms:
                # Parse datetime string
                from dateutil import parser
                return parser.parse(ms)
            else:
                # Assume it's milliseconds as string
                ms = int(ms)
        return datetime.utcfromtimestamp(ms / 1000)
        
    def log_error(self, error_type: str, message: str, details: Optional[Dict] = None):
        """Log error for later reporting"""
        error = {
            "timestamp": datetime.utcnow(),
            "type": error_type,
            "message": message,
            "details": details or {},
            "email": self.email,
            "account_type": self.account_type
        }
        self.errors.append(error)
        
    def save_raw_data(self, db: Session, table_name: str, data: Dict[str, Any]):
        """
        Save raw API response to database for audit trail.
        
        Args:
            db: Database session
            table_name: Name of the raw data table
            data: Raw API response data
        """
        # Skip if no database session (test mode)
        if db is None:
            return
            
        # Import model dynamically based on table name
        try:
            from app.models import binance_reconciliation as models
        except ImportError:
            # Models not available in test mode
            return
        
        model_map = {
            "binance_raw_daily_snapshot": models.BinanceRawDailySnapshot,
            "binance_raw_deposit_history": models.BinanceRawDepositHistory,
            "binance_raw_withdraw_history": models.BinanceRawWithdrawHistory,
            "binance_raw_transfer_between_account_main_spot": models.BinanceRawTransferBetweenAccountMainSpot,
            "binance_raw_transfer_between_account_sub": models.BinanceRawTransferBetweenAccountSub,
            "binance_raw_transfer_between_wallets": models.BinanceRawTransferBetweenWallets,
            "binance_raw_trades": models.BinanceRawTrades,
            "binance_raw_convert_history": models.BinanceRawConvertHistory,
        }
        
        model = model_map.get(table_name)
        if not model:
            raise ValueError(f"Unknown table name: {table_name}")
            
        # Create record based on table type
        if table_name == "binance_raw_trades":
            # Trades have symbol field
            record = model(
                email=self.email,
                symbol=data.get("symbol", ""),
                trade_data=data,
                created_at=datetime.utcnow()
            )
        elif table_name == "binance_raw_daily_snapshot":
            # Snapshot has special structure
            record = model(
                email=self.email,
                snapshot_date=self.ms_to_datetime(data.get("updateTime", 0)).date(),
                snapshot_data=data,
                created_at=datetime.utcnow()
            )
        else:
            # Other tables follow standard pattern
            field_map = {
                "binance_raw_deposit_history": "deposit_data",
                "binance_raw_withdraw_history": "withdraw_data", 
                "binance_raw_transfer_between_account_main_spot": "transfer_data",
                "binance_raw_transfer_between_account_sub": "transfer_data",
                "binance_raw_transfer_between_wallets": "transfer_data",
                "binance_raw_convert_history": "convert_data",
            }
            
            data_field = field_map.get(table_name, "data")
            record = model(
                email=self.email,
                **{data_field: data},
                created_at=datetime.utcnow()
            )
            
        db.add(record)
        db.commit()
        
    def export_to_csv(self, data: List[Dict], filename: str, fieldnames: List[str]):
        """
        Export data to CSV for verification against Binance UI.
        
        Args:
            data: List of dictionaries to export
            filename: Output filename
            fieldnames: List of field names for CSV header
        """
        # For testing, use a simple output directory
        output_dir = os.path.join("tests", "output", "exports", "binance", self.email)
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
        return filepath
        
    def handle_api_error(self, error: BinanceAPIError) -> bool:
        """
        Handle API errors with appropriate retry logic.
        
        Returns:
            True if should retry, False otherwise
        """
        if error.error_type == BinanceErrorType.RATE_LIMIT:
            # Rate limit hit, wait and retry
            import time
            time.sleep(60)
            return True
        elif error.error_type == BinanceErrorType.INVALID_SYMBOL:
            # Log and skip this symbol
            self.log_error("invalid_symbol", str(error))
            return False
        elif error.error_type == BinanceErrorType.API_KEY_INVALID:
            # Critical error, stop processing
            self.log_error("api_key_invalid", str(error))
            raise
        else:
            # Log other errors and continue
            self.log_error("api_error", str(error), {"error_type": error.error_type.value})
            return False
            
    @abstractmethod
    def collect(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Collect data for the specified date range.
        
        Args:
            start_date: Start of date range (UTC)
            end_date: End of date range (UTC)
            
        Returns:
            Dictionary containing collected data and statistics
        """
        pass
        
    @abstractmethod
    def validate_data(self, data: Any) -> bool:
        """
        Validate collected data for completeness and accuracy.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass