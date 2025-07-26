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


class WithdrawCollector(BaseCollector):
    """Collector for withdrawal history"""
    
    async def collect(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Collect withdrawal history for the specified date range.
        
        Args:
            start_date: Start of date range (UTC)
            end_date: End of date range (UTC)
            
        Returns:
            Dictionary containing collected data and statistics
        """
        db = self.get_db()
        try:
            results = {
                "withdrawals_collected": 0,
                "withdrawals_saved": 0,
                "fees_saved": 0,
                "errors": [],
                "csv_file": None
            }
            
            # Fetch withdrawals using pagination
            withdrawals = await self._fetch_withdrawals(start_date, end_date)
            results["withdrawals_collected"] = len(withdrawals)
            
            # Process each withdrawal
            csv_data = []
            for withdrawal in withdrawals:
                # Save raw data
                self.save_raw_data(db, "binance_raw_withdraw_history", withdrawal)
                
                # Process withdrawal and fee as separate transfers
                transfers = self._process_withdrawal(withdrawal)
                for transfer_record in transfers:
                    # Save to reconciliation table
                    self._save_transfer(db, transfer_record)
                    
                    if transfer_record["txn_subtype"] == TransactionSubtype.WITHDRAW.value:
                        results["withdrawals_saved"] += 1
                    else:
                        results["fees_saved"] += 1
                    
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
                        "status": withdrawal.get("status", 0)
                    })
            
            # Export to CSV
            if csv_data:
                results["csv_file"] = self.export_to_csv(
                    csv_data,
                    f"withdrawals_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
                    ["datetime", "email", "txn_type", "txn_subtype", "wallet", "asset", 
                     "amount", "counter_party", "network", "txn_hash", "status"]
                )
            
            results["errors"] = self.errors
            return results
            
        finally:
            self.close_db(db)
    
    async def _fetch_withdrawals(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch withdrawal history from Binance API with pagination"""
        all_withdrawals = []
        
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
                    response = self.client.get_withdrawal_history(
                        start_time=chunk_start,
                        end_time=chunk_end,
                        limit=1000
                    )
                    
                    if not response:
                        break
                        
                    all_withdrawals.extend(response)
                    
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
                    self.log_error("withdrawal_fetch_error", str(e), {
                        "start_time": chunk_start,
                        "end_time": chunk_end
                    })
                    
        return all_withdrawals
    
    def _process_withdrawal(self, withdrawal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process raw withdrawal data into transfer records (withdrawal + fee)"""
        transfers = []
        
        # Only process successful withdrawals (status = 6)
        if withdrawal.get("status") != 6:
            return transfers
            
        # Extract withdrawal info
        apply_time = withdrawal.get("applyTime", 0)
        withdrawal_id = withdrawal.get("id", "")
        
        # 1. Main withdrawal transfer
        withdrawal_transfer = {
            "source": "binance_api",
            "fid": 1,  # Default facility ID
            "external_id": f"withdrawal_{withdrawal_id}",
            "datetime": self.ms_to_datetime(apply_time),
            "txn_type": TransactionType.TRANSFER_OUT.value,
            "txn_subtype": TransactionSubtype.WITHDRAW.value,
            "email": self.email,
            "wallet": WalletType.SPOT.value,
            "asset": withdrawal.get("coin", ""),
            "amount": Decimal(str(withdrawal.get("amount", "0"))),
            "counter_party": withdrawal.get("address", ""),
            "network": withdrawal.get("network", ""),
            "txn_hash": withdrawal.get("txId", ""),
            "match_id": None,
            "reconciled": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        transfers.append(withdrawal_transfer)
        
        # 2. Withdrawal fee (if any)
        fee = Decimal(str(withdrawal.get("transactionFee", "0")))
        if fee > 0:
            fee_transfer = {
                "source": "binance_api",
                "fid": 1,  # Default facility ID
                "external_id": f"withdrawal_fee_{withdrawal_id}",
                "datetime": self.ms_to_datetime(apply_time),
                "txn_type": TransactionType.TXN_FEE.value,
                "txn_subtype": TransactionSubtype.WITHDRAWAL_FEE.value,
                "email": self.email,
                "wallet": WalletType.SPOT.value,
                "asset": withdrawal.get("coin", ""),  # Fee is in same asset
                "amount": fee,
                "counter_party": "binance",
                "network": withdrawal.get("network", ""),
                "txn_hash": withdrawal.get("txId", ""),
                "match_id": None,
                "reconciled": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            transfers.append(fee_transfer)
            
        return transfers
    
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
        Validate withdrawal data for completeness and accuracy.
        
        Args:
            data: Withdrawal data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, list):
            return False
            
        # Validate each withdrawal
        for withdrawal in data:
            # Check required fields
            required_fields = ["id", "amount", "coin", "status", "applyTime"]
            for field in required_fields:
                if field not in withdrawal:
                    return False
                    
            # Validate amounts are numeric
            try:
                Decimal(str(withdrawal.get("amount", "0")))
                Decimal(str(withdrawal.get("transactionFee", "0")))
            except:
                return False
                
        return True