from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal

from .base import BaseCollector
from app.services.binance.client import BinanceAPIError, BinanceErrorType
from app.models.binance_reconciliation import (
    BinanceReconciliationTransfer, 
    TransactionType, 
    TransactionSubtype,
    WalletType
)


class TransferCollector(BaseCollector):
    """Collector for all types of transfers between accounts and wallets"""
    
    def collect(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Collect all transfer types for the specified date range.
        
        Args:
            start_date: Start of date range (UTC)
            end_date: End of date range (UTC)
            
        Returns:
            Dictionary containing collected data and statistics
        """
        db = self.get_db()
        try:
            results = {
                "transfers_collected": 0,
                "transfers_saved": 0,
                "transfer_types": {
                    "main_spot": 0,
                    "sub_account": 0,
                    "wallet_to_wallet": 0
                },
                "errors": [],
                "csv_file": None
            }
            
            csv_data = []
            
            # 1. Collect transfers between main account and trading accounts
            main_transfers = self._fetch_main_transfers(start_date, end_date)
            results["transfer_types"]["main_spot"] = len(main_transfers)
            results["transfers_collected"] += len(main_transfers)
            
            for transfer in main_transfers:
                self.save_raw_data(db, "binance_raw_transfer_between_account_main_spot", transfer)
                processed = self._process_main_transfer(transfer)
                if processed:
                    self._save_transfer(db, processed)
                    results["transfers_saved"] += 1
                    csv_data.append(self._transfer_to_csv_row(processed))
            
            # 2. Collect sub-account transfers (if master account)
            if self.account_type == "main":
                sub_transfers = self._fetch_sub_transfers(start_date, end_date)
                results["transfer_types"]["sub_account"] = len(sub_transfers)
                results["transfers_collected"] += len(sub_transfers)
                
                for transfer in sub_transfers:
                    self.save_raw_data(db, "binance_raw_transfer_between_account_sub", transfer)
                    processed = self._process_sub_transfer(transfer)
                    if processed:
                        self._save_transfer(db, processed)
                        results["transfers_saved"] += 1
                        csv_data.append(self._transfer_to_csv_row(processed))
            
            # 3. Collect universal wallet transfers
            wallet_transfers = self._fetch_wallet_transfers(start_date, end_date)
            results["transfer_types"]["wallet_to_wallet"] = len(wallet_transfers)
            results["transfers_collected"] += len(wallet_transfers)
            
            for transfer in wallet_transfers:
                self.save_raw_data(db, "binance_raw_transfer_between_wallets", transfer)
                processed = self._process_wallet_transfer(transfer)
                if processed:
                    self._save_transfer(db, processed)
                    results["transfers_saved"] += 1
                    csv_data.append(self._transfer_to_csv_row(processed))
            
            # Export to CSV
            if csv_data:
                results["csv_file"] = self.export_to_csv(
                    csv_data,
                    f"transfers_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
                    ["datetime", "email", "txn_type", "txn_subtype", "wallet", "asset", 
                     "amount", "counter_party", "network", "txn_hash"]
                )
            
            results["errors"] = self.errors
            return results
            
        finally:
            self.close_db(db)
    
    def _fetch_main_transfers(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch transfers between main and trading accounts"""
        transfers = []
        
        try:
            start_ms = self.timestamp_to_ms(start_date)
            end_ms = self.timestamp_to_ms(end_date)
            
            # Fetch all transfer types
            for transfer_type in ["MAIN_UMFUTURE", "MAIN_CMFUTURE", "MAIN_MARGIN", "MAIN_FUNDING"]:
                response = self.client.get_transfer_between_accounts_main(
                    start_time=start_ms,
                    end_time=end_ms,
                    type_val=transfer_type,
                    size=100
                )
                
                if response and isinstance(response, list):
                    transfers.extend(response)
                    
        except BinanceAPIError as e:
            self.handle_api_error(e)
            self.log_error("main_transfer_fetch_error", str(e))
            
        return transfers
    
    def _fetch_sub_transfers(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch sub-account transfers"""
        transfers = []
        
        try:
            start_ms = self.timestamp_to_ms(start_date)
            end_ms = self.timestamp_to_ms(end_date)
            
            response = self.client.get_transfer_between_accounts_sub(
                start_time=start_ms,
                end_time=end_ms,
                limit=500
            )
            
            if response and isinstance(response, list):
                transfers = response
                
        except BinanceAPIError as e:
            if e.error_type != BinanceErrorType.API_KEY_INVALID:
                self.handle_api_error(e)
            self.log_error("sub_transfer_fetch_error", str(e))
            
        return transfers
    
    def _fetch_wallet_transfers(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch universal wallet transfers"""
        transfers = []
        
        try:
            start_ms = self.timestamp_to_ms(start_date)
            end_ms = self.timestamp_to_ms(end_date)
            
            # Paginate through results
            current = 1
            while True:
                response = self.client.get_transfer_between_wallets(
                    start_time=start_ms,
                    end_time=end_ms,
                    current=current,
                    size=100
                )
                
                if response and "rows" in response:
                    transfers.extend(response["rows"])
                    
                    # Check if more pages
                    if len(response["rows"]) < 100:
                        break
                    current += 1
                else:
                    break
                    
        except BinanceAPIError as e:
            self.handle_api_error(e)
            self.log_error("wallet_transfer_fetch_error", str(e))
            
        return transfers
    
    def _process_main_transfer(self, transfer: Dict[str, Any]) -> Dict[str, Any]:
        """Process main account transfer"""
        # Determine direction based on type
        transfer_type = transfer.get("type", "")
        if "MAIN_" in transfer_type:
            # Transfer from main to other account
            txn_type = TransactionType.TRANSFER_OUT.value
        else:
            # Transfer to main from other account
            txn_type = TransactionType.TRANSFER_IN.value
            
        return {
            "source": "binance_api",
            "fid": 1,
            "external_id": f"main_transfer_{transfer.get('tranId', '')}",
            "datetime": self.ms_to_datetime(transfer.get("timestamp", 0)),
            "txn_type": txn_type,
            "txn_subtype": TransactionSubtype.TRANSFER_BETWEEN_ACCOUNT_MAIN_SPOT.value,
            "email": self.email,
            "wallet": WalletType.SPOT.value,
            "asset": transfer.get("asset", ""),
            "amount": Decimal(str(transfer.get("amount", "0"))),
            "counter_party": transfer_type.replace("MAIN_", ""),
            "network": None,
            "txn_hash": None,
            "match_id": None,
            "reconciled": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    def _process_sub_transfer(self, transfer: Dict[str, Any]) -> Dict[str, Any]:
        """Process sub-account transfer"""
        # Determine direction
        if transfer.get("fromEmail") == self.email:
            txn_type = TransactionType.TRANSFER_OUT.value
            counter_party = transfer.get("toEmail", "")
        else:
            txn_type = TransactionType.TRANSFER_IN.value
            counter_party = transfer.get("fromEmail", "")
            
        return {
            "source": "binance_api",
            "fid": 1,
            "external_id": f"sub_transfer_{transfer.get('tranId', '')}",
            "datetime": self.ms_to_datetime(transfer.get("time", 0)),
            "txn_type": txn_type,
            "txn_subtype": TransactionSubtype.TRANSFER_BETWEEN_ACCOUNT_SUB.value,
            "email": self.email,
            "wallet": WalletType.SPOT.value,
            "asset": transfer.get("asset", ""),
            "amount": Decimal(str(transfer.get("qty", "0"))),
            "counter_party": counter_party,
            "network": None,
            "txn_hash": None,
            "match_id": None,
            "reconciled": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    def _process_wallet_transfer(self, transfer: Dict[str, Any]) -> Dict[str, Any]:
        """Process universal wallet transfer"""
        # Determine direction based on fromAccountType
        from_type = transfer.get("fromAccountType", "")
        to_type = transfer.get("toAccountType", "")
        
        if from_type == "SPOT":
            txn_type = TransactionType.TRANSFER_OUT.value
            counter_party = to_type
        else:
            txn_type = TransactionType.TRANSFER_IN.value
            counter_party = from_type
            
        return {
            "source": "binance_api",
            "fid": 1,
            "external_id": f"wallet_transfer_{transfer.get('tranId', '')}",
            "datetime": self.ms_to_datetime(transfer.get("timestamp", 0)),
            "txn_type": txn_type,
            "txn_subtype": TransactionSubtype.TRANSFER_BETWEEN_WALLETS.value,
            "email": self.email,
            "wallet": WalletType.SPOT.value,
            "asset": transfer.get("asset", ""),
            "amount": Decimal(str(transfer.get("amount", "0"))),
            "counter_party": counter_party,
            "network": None,
            "txn_hash": None,
            "match_id": None,
            "reconciled": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    def _transfer_to_csv_row(self, transfer: Dict[str, Any]) -> Dict[str, Any]:
        """Convert transfer to CSV row format"""
        return {
            "datetime": transfer["datetime"],
            "email": transfer["email"],
            "txn_type": transfer["txn_type"],
            "txn_subtype": transfer["txn_subtype"],
            "wallet": transfer["wallet"],
            "asset": transfer["asset"],
            "amount": transfer["amount"],
            "counter_party": transfer["counter_party"],
            "network": transfer["network"],
            "txn_hash": transfer["txn_hash"]
        }
    
    def _save_transfer(self, db, transfer: Dict[str, Any]):
        """Save transfer to reconciliation table"""
        if db is None:
            return
            
        # Check if transfer already exists
        existing = db.query(BinanceReconciliationTransfer).filter_by(
            source=transfer["source"],
            external_id=transfer["external_id"]
        ).first()
        
        if existing:
            # Update existing record
            for key, value in transfer.items():
                if key not in ["created_at"]:
                    setattr(existing, key, value)
        else:
            # Create new record
            new_transfer = BinanceReconciliationTransfer(**transfer)
            db.add(new_transfer)
            
        db.commit()
    
    def validate_data(self, data: Any) -> bool:
        """Validate transfer data"""
        return True  # Basic validation, can be enhanced