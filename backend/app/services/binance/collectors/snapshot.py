from typing import Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

from .base import BaseCollector
from app.services.binance.client import BinanceAPIError
from app.models.binance_reconciliation import BinanceReconciliationBalance, WalletType


class SnapshotCollector(BaseCollector):
    """Collector for daily account balance snapshots"""
    
    def collect(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Collect daily balance snapshots for the specified date range.
        
        Args:
            start_date: Start of date range (UTC)
            end_date: End of date range (UTC)
            
        Returns:
            Dictionary containing collected data and statistics
        """
        db = self.get_db()
        try:
            results = {
                "snapshots_collected": 0,
                "balances_saved": 0,
                "errors": [],
                "csv_file": None
            }
            
            # Get snapshots for date range
            snapshots = self._fetch_snapshots(start_date, end_date)
            results["snapshots_collected"] = len(snapshots)
            
            # Process each snapshot
            csv_data = []
            for snapshot in snapshots:
                # Save raw data
                self.save_raw_data(db, "binance_raw_daily_snapshot", snapshot)
                
                # Process balances
                balances = self._process_snapshot(snapshot)
                for balance in balances:
                    # Save to reconciliation table
                    self._save_balance(db, balance)
                    results["balances_saved"] += 1
                    
                    # Add to CSV data
                    csv_data.append({
                        "date": balance["date"],
                        "email": balance["email"],
                        "wallet": balance["wallet"],
                        "asset": balance["asset"],
                        "raw_balance": balance["raw_balance"],
                        "raw_loan": balance["raw_loan"],
                        "raw_interest": balance["raw_interest"],
                        "raw_unrealised_pnl": balance["raw_unrealised_pnl"]
                    })
            
            # Export to CSV
            if csv_data:
                results["csv_file"] = self.export_to_csv(
                    csv_data,
                    f"daily_snapshots_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
                    ["date", "email", "wallet", "asset", "raw_balance", "raw_loan", "raw_interest", "raw_unrealised_pnl"]
                )
            
            results["errors"] = self.errors
            return results
            
        finally:
            self.close_db(db)
    
    def _fetch_snapshots(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch account snapshots from Binance API"""
        snapshots = []
        
        # Account types to fetch - all accounts can have SPOT, MARGIN, and FUTURES
        account_types = ["SPOT", "MARGIN", "FUTURES"]
        
        for account_type in account_types:
            try:
                # Binance snapshot API returns last 30 days max
                # Default is 7 days if no time range specified
                start_ms = self.timestamp_to_ms(start_date)
                end_ms = self.timestamp_to_ms(end_date)
                
                # Fetch snapshots for this account type
                response = self.client.get_account_snapshot(
                    account_type=account_type,
                    start_time=start_ms,
                    end_time=end_ms,
                    limit=30  # Max days per request
                )
                
                if response.get("code") == 200 and "snapshotVos" in response:
                    for snapshot in response["snapshotVos"]:
                        # Add account type to snapshot data
                        snapshot["_account_type"] = account_type
                        snapshots.append(snapshot)
                        
            except BinanceAPIError as e:
                # Log error and continue with next account type
                self.log_error("snapshot_fetch_error", str(e), {
                    "account_type": account_type,
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": end_date.strftime('%Y-%m-%d'),
                    "error_type": e.error_type.value if hasattr(e, 'error_type') else 'unknown'
                })
                    
        return snapshots
    
    def _process_snapshot(self, snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process raw snapshot data into balance records"""
        balances = []
        
        # Extract snapshot info
        update_time = snapshot.get("updateTime", 0)
        snapshot_date = self.ms_to_datetime(update_time).date()
        
        # Get balance data
        data = snapshot.get("data", {})
        if not data:
            return balances
            
        # Process each asset balance
        for balance_info in data.get("balances", []):
            asset = balance_info.get("asset", "")
            free = Decimal(balance_info.get("free", "0"))
            locked = Decimal(balance_info.get("locked", "0"))
            
            # Only save non-zero balances
            total_balance = free + locked
            if total_balance > 0:
                balance = {
                    "source": "binance_api",
                    "fid": 1,  # Default facility ID
                    "external_id": f"{self.email}_{snapshot_date}_{asset}",
                    "date": snapshot_date,
                    "email": self.email,
                    "wallet": self._get_wallet_type(snapshot.get("_account_type", "SPOT")),
                    "asset": asset,
                    "raw_balance": total_balance,
                    "raw_loan": Decimal("0"),
                    "raw_interest": Decimal("0"),
                    "raw_unrealised_pnl": Decimal("0"),
                    "cal_balance": total_balance,  # Will be recalculated during reconciliation
                    "cal_loan": Decimal("0"),
                    "cal_interest": Decimal("0"),
                    "cal_unrealised_pnl": Decimal("0"),
                    "matched": False,
                    "variance": Decimal("0"),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                balances.append(balance)
                
        return balances
    
    def _save_balance(self, db, balance: Dict[str, Any]):
        """Save balance to reconciliation table"""
        if db is None:
            return
            
        # Check if balance already exists
        existing = db.query(BinanceReconciliationBalance).filter_by(
            email=balance["email"],
            date=balance["date"],
            wallet=balance["wallet"],
            asset=balance["asset"]
        ).first()
        
        if existing:
            # Update existing record
            for key, value in balance.items():
                if key not in ["created_at"]:  # Don't update created_at
                    setattr(existing, key, value)
        else:
            # Create new record
            new_balance = BinanceReconciliationBalance(**balance)
            db.add(new_balance)
            
        db.commit()
    
    def _get_wallet_type(self, account_type: str) -> str:
        """Map account type to wallet type"""
        mapping = {
            "SPOT": WalletType.SPOT.value,
            "MARGIN": WalletType.MARGIN.value,
            "FUTURES": WalletType.FUTURES.value
        }
        return mapping.get(account_type, WalletType.SPOT.value)
    
    def validate_data(self, data: Any) -> bool:
        """
        Validate snapshot data for completeness and accuracy.
        
        Args:
            data: Snapshot data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, dict):
            return False
            
        # Check required fields
        if "snapshotVos" not in data:
            return False
            
        # Validate each snapshot
        for snapshot in data.get("snapshotVos", []):
            if "updateTime" not in snapshot or "data" not in snapshot:
                return False
                
            # Validate balance data
            balance_data = snapshot.get("data", {})
            if "balances" not in balance_data:
                return False
                
        return True