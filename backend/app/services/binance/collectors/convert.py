from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal

from .base import BaseCollector
from app.services.binance.client import BinanceAPIError
from app.models.binance_reconciliation import (
    BinanceReconciliationTrade,
    TransactionType, 
    TransactionSubtype,
    WalletType
)


class ConvertCollector(BaseCollector):
    """Collector for convert transactions"""
    
    async def collect(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Collect convert transactions for the specified date range.
        
        Args:
            start_date: Start of date range (UTC)
            end_date: End of date range (UTC)
            
        Returns:
            Dictionary containing collected data and statistics
        """
        db = self.get_db()
        try:
            results = {
                "converts_collected": 0,
                "converts_saved": 0,
                "errors": [],
                "csv_file": None
            }
            
            # Fetch convert history
            converts = await self._fetch_converts(start_date, end_date)
            results["converts_collected"] = len(converts)
            
            # Process each convert
            csv_data = []
            for convert in converts:
                # Save raw data
                self.save_raw_data(db, "binance_raw_convert_history", convert)
                
                # Process convert (creates buy and sell records)
                trade_records = self._process_convert(convert)
                for record in trade_records:
                    self._save_trade(db, record)
                    results["converts_saved"] += 1
                    
                    csv_data.append({
                        "datetime": record["datetime"],
                        "email": record["email"],
                        "txn_type": record["txn_type"],
                        "txn_subtype": record["txn_subtype"],
                        "symbol": record["symbol"],
                        "asset": record["asset"],
                        "amount": record["amount"],
                        "price": record.get("price", ""),
                        "order_id": record.get("order_id", "")
                    })
            
            # Export to CSV
            if csv_data:
                results["csv_file"] = self.export_to_csv(
                    csv_data,
                    f"converts_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
                    ["datetime", "email", "txn_type", "txn_subtype", "symbol", 
                     "asset", "amount", "price", "order_id"]
                )
            
            results["errors"] = self.errors
            return results
            
        finally:
            self.close_db(db)
    
    async def _fetch_converts(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch convert history from Binance API"""
        converts = []
        
        try:
            start_ms = self.timestamp_to_ms(start_date)
            end_ms = self.timestamp_to_ms(end_date)
            
            response = self.client.get_convert_history(
                start_time=start_ms,
                end_time=end_ms,
                limit=1000
            )
            
            if response and "list" in response:
                converts = response["list"]
                
        except BinanceAPIError as e:
            self.handle_api_error(e)
            self.log_error("convert_fetch_error", str(e))
            
        return converts
    
    def _process_convert(self, convert: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process convert transaction into buy and sell records"""
        records = []
        
        # Extract convert info
        order_id = convert.get("orderId", "")
        create_time = self.ms_to_datetime(convert.get("createTime", 0))
        from_asset = convert.get("fromAsset", "")
        to_asset = convert.get("toAsset", "")
        from_amount = Decimal(str(convert.get("fromAmount", "0")))
        to_amount = Decimal(str(convert.get("toAmount", "0")))
        
        # Calculate price
        price = to_amount / from_amount if from_amount > 0 else Decimal("0")
        symbol = f"{from_asset}{to_asset}"
        
        # 1. Sell record (from asset)
        sell_record = {
            "source": "binance_api",
            "fid": 1,
            "external_id": f"convert_sell_{order_id}",
            "datetime": create_time,
            "txn_type": TransactionType.TRADE.value,
            "txn_subtype": TransactionSubtype.CONVERT_SELL.value,
            "email": self.email,
            "wallet": WalletType.SPOT.value,
            "symbol": symbol,
            "asset": from_asset,
            "amount": -from_amount,  # Negative for sell
            "price": price,
            "order_id": order_id,
            "trade_id": order_id,
            "match_id": None,
            "reconciled": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        records.append(sell_record)
        
        # 2. Buy record (to asset)
        buy_record = sell_record.copy()
        buy_record["external_id"] = f"convert_buy_{order_id}"
        buy_record["txn_subtype"] = TransactionSubtype.CONVERT_BUY.value
        buy_record["asset"] = to_asset
        buy_record["amount"] = to_amount  # Positive for buy
        records.append(buy_record)
        
        return records
    
    def _save_trade(self, db, trade: Dict[str, Any]):
        """Save trade to reconciliation table"""
        # Check if trade already exists
        existing = db.query(BinanceReconciliationTrade).filter_by(
            source=trade["source"],
            external_id=trade["external_id"]
        ).first()
        
        if existing:
            # Update existing record
            for key, value in trade.items():
                if key not in ["created_at"]:
                    setattr(existing, key, value)
        else:
            # Create new record
            new_trade = BinanceReconciliationTrade(**trade)
            db.add(new_trade)
            
        db.commit()
    
    def validate_data(self, data: Any) -> bool:
        """Validate convert data"""
        return True  # Basic validation