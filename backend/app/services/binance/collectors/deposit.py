from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal

from .base import BaseCollector
from app.services.binance.client import BinanceAPIError
from app.models.binance_reconciliation import (
    BinanceReconciliationTransfer, 
    TransactionType, 
    TransactionSubtype,
    WalletType
)


class DepositCollector(BaseCollector):
    """Collector for deposit history"""
    
    async def collect(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Collect deposit history for the specified date range.
        
        Args:
            start_date: Start of date range (UTC)
            end_date: End of date range (UTC)
            
        Returns:
            Dictionary containing collected data and statistics
        """
        db = self.get_db()
        try:
            results = {
                "deposits_collected": 0,
                "deposits_saved": 0,
                "errors": [],
                "csv_file": None
            }
            
            # Fetch deposits using pagination
            deposits = await self._fetch_deposits(start_date, end_date)
            results["deposits_collected"] = len(deposits)
            
            # Process each deposit
            csv_data = []
            for deposit in deposits:
                # Save raw data
                self.save_raw_data(db, "binance_raw_deposit_history", deposit)
                
                # Process deposit
                transfer_record = self._process_deposit(deposit)
                if transfer_record:
                    # Save to reconciliation table
                    self._save_transfer(db, transfer_record)
                    results["deposits_saved"] += 1
                    
                    # Add to CSV data
                    csv_data.append({
                        "datetime": transfer_record["datetime"],
                        "email": transfer_record["email"],
                        "txn_type": transfer_record["txn_type"],
                        "txn_subtype": transfer_record["txn_subtype"],
                        "wallet": transfer_record["wallet"],
                        "asset": transfer_record["asset"],
                        "amount": transfer_record["amount"],
                        "counter_party": transfer_record["counter_party"],
                        "network": transfer_record["network"],
                        "txn_hash": transfer_record["txn_hash"],
                        "status": deposit.get("status", 0)
                    })
            
            # Export to CSV
            if csv_data:
                results["csv_file"] = self.export_to_csv(
                    csv_data,
                    f"deposits_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
                    ["datetime", "email", "txn_type", "txn_subtype", "wallet", "asset", 
                     "amount", "counter_party", "network", "txn_hash", "status"]
                )
            
            results["errors"] = self.errors
            return results
            
        finally:
            self.close_db(db)
    
    async def _fetch_deposits(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch deposit history from Binance API with pagination"""
        all_deposits = []
        
        # Convert to milliseconds
        start_ms = self.timestamp_to_ms(start_date)
        end_ms = self.timestamp_to_ms(end_date)
        
        # Use time chunking for large date ranges
        time_chunks = self.client.chunk_time_range(start_ms, end_ms, days=90)
        
        for chunk_start, chunk_end in time_chunks:
            try:
                # Paginate through results
                offset = 0
                while True:
                    response = self.client.get_deposit_history(
                        start_time=chunk_start,
                        end_time=chunk_end,
                        limit=1000
                    )
                    
                    if not response:
                        break
                        
                    all_deposits.extend(response)
                    
                    # Check if we got less than limit (last page)
                    if len(response) < 1000:
                        break
                        
                    offset += 1000
                    
            except BinanceAPIError as e:
                if self.handle_api_error(e):
                    # Retry this chunk
                    continue
                else:
                    # Skip this chunk
                    self.log_error("deposit_fetch_error", str(e), {
                        "start_time": chunk_start,
                        "end_time": chunk_end
                    })
                    
        return all_deposits
    
    def _process_deposit(self, deposit: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw deposit data into transfer record"""
        # Only process successful deposits (status = 1)
        if deposit.get("status") != 1:
            return None
            
        # Extract deposit info
        insert_time = deposit.get("insertTime", 0)
        
        transfer = {
            "source": "binance_api",
            "fid": 1,  # Default facility ID
            "external_id": f"deposit_{deposit.get('id', '')}",
            "datetime": self.ms_to_datetime(insert_time),
            "txn_type": TransactionType.TRANSFER_IN.value,
            "txn_subtype": TransactionSubtype.DEPOSIT.value,
            "email": self.email,
            "wallet": WalletType.SPOT.value,
            "asset": deposit.get("coin", ""),
            "amount": Decimal(str(deposit.get("amount", "0"))),
            "counter_party": deposit.get("address", ""),
            "network": deposit.get("network", ""),
            "txn_hash": deposit.get("txId", ""),
            "match_id": None,
            "reconciled": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        return transfer
    
    def _save_transfer(self, db, transfer: Dict[str, Any]):
        """Save transfer to reconciliation table"""
        # Check if transfer already exists
        existing = db.query(BinanceReconciliationTransfer).filter_by(
            source=transfer["source"],
            external_id=transfer["external_id"]
        ).first()
        
        if existing:
            # Update existing record
            for key, value in transfer.items():
                if key not in ["created_at"]:  # Don't update created_at
                    setattr(existing, key, value)
        else:
            # Create new record
            new_transfer = BinanceReconciliationTransfer(**transfer)
            db.add(new_transfer)
            
        db.commit()
    
    def validate_data(self, data: Any) -> bool:
        """
        Validate deposit data for completeness and accuracy.
        
        Args:
            data: Deposit data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, list):
            return False
            
        # Validate each deposit
        for deposit in data:
            # Check required fields
            required_fields = ["id", "amount", "coin", "status", "insertTime"]
            for field in required_fields:
                if field not in deposit:
                    return False
                    
            # Validate amount is numeric
            try:
                Decimal(str(deposit.get("amount", "0")))
            except:
                return False
                
        return True