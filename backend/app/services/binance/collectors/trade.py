from typing import Dict, Any, List, Set
from datetime import datetime
from decimal import Decimal
from sqlalchemy import text

from .base import BaseCollector
from app.services.binance.client import BinanceAPIError, BinanceErrorType
from app.models.binance_reconciliation import (
    BinanceReconciliationTrade,
    BinanceTradedSymbols,
    TransactionType, 
    TransactionSubtype,
    WalletType
)


class TradeCollector(BaseCollector):
    """Collector for trades with intelligent symbol discovery"""
    
    def collect(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Collect trades for all relevant symbols for the specified date range.
        
        Args:
            start_date: Start of date range (UTC)
            end_date: End of date range (UTC)
            
        Returns:
            Dictionary containing collected data and statistics
        """
        db = self.get_db()
        try:
            results = {
                "symbols_discovered": 0,
                "symbols_processed": 0,
                "trades_collected": 0,
                "trades_saved": 0,
                "fees_saved": 0,
                "errors": [],
                "csv_file": None
            }
            
            # Discover trading symbols
            symbols = self._discover_symbols(db)
            results["symbols_discovered"] = len(symbols)
            
            # Process each symbol
            csv_data = []
            for symbol in symbols:
                try:
                    # Fetch trades for this symbol
                    trades = self._fetch_trades_for_symbol(symbol, start_date, end_date)
                    if trades:
                        results["symbols_processed"] += 1
                        results["trades_collected"] += len(trades)
                        
                        # Save symbol to traded symbols cache
                        self._save_traded_symbol(db, symbol)
                        
                        # Process each trade
                        for trade in trades:
                            # Save raw data
                            self.save_raw_data(db, "binance_raw_trades", {
                                "symbol": symbol,
                                "trades": [trade]
                            })
                            
                            # Process trade and fee
                            trade_records = self._process_trade(trade, symbol)
                            for record in trade_records:
                                self._save_trade(db, record)
                                
                                if record["txn_subtype"] in [TransactionSubtype.SPOT_BUY.value, 
                                                            TransactionSubtype.SPOT_SELL.value]:
                                    results["trades_saved"] += 1
                                else:
                                    results["fees_saved"] += 1
                                
                                csv_data.append(self._trade_to_csv_row(record))
                                
                except BinanceAPIError as e:
                    if e.error_type == BinanceErrorType.INVALID_SYMBOL:
                        # Remove invalid symbol from cache
                        self._remove_invalid_symbol(db, symbol)
                    else:
                        self.log_error(f"trade_fetch_error_{symbol}", str(e))
            
            # Export to CSV
            if csv_data:
                results["csv_file"] = self.export_to_csv(
                    csv_data,
                    f"trades_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
                    ["datetime", "email", "txn_type", "txn_subtype", "symbol", 
                     "asset", "amount", "price", "order_id", "trade_id"]
                )
            
            results["errors"] = self.errors
            return results
            
        finally:
            self.close_db(db)
    
    def _discover_symbols(self, db) -> List[str]:
        """Discover trading symbols based on user assets and exchange info"""
        if db is None:
            return []
            
        symbols = set()
        
        # 1. Get previously traded symbols from cache
        cached_symbols = db.query(BinanceTradedSymbols.symbol).filter_by(
            email=self.email,
            active=True
        ).all()
        symbols.update([s[0] for s in cached_symbols])
        
        # 2. Get user assets from view
        user_assets_query = text("""
            SELECT DISTINCT asset 
            FROM v_binance_user_assets 
            WHERE email = :email
        """)
        user_assets = db.execute(user_assets_query, {"email": self.email}).fetchall()
        user_assets = {asset[0] for asset in user_assets}
        
        # 3. Get trading pairs from exchange info
        exchange_info_query = text("""
            SELECT symbol 
            FROM binance_exchange_info 
            WHERE status = 'TRADING'
            AND (base_asset IN :assets OR quote_asset IN :assets)
        """)
        
        if user_assets:
            trading_pairs = db.execute(
                exchange_info_query, 
                {"assets": tuple(user_assets)}
            ).fetchall()
            symbols.update([pair[0] for pair in trading_pairs])
        
        # 4. Prioritize symbols (stablecoins first)
        stablecoin_symbols = [s for s in symbols if any(stable in s for stable in ["USDT", "USDC", "BUSD"])]
        other_symbols = [s for s in symbols if s not in stablecoin_symbols]
        
        return stablecoin_symbols + other_symbols
    
    def _fetch_trades_for_symbol(self, symbol: str, start_date: datetime, 
                                     end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch trades for a specific symbol"""
        all_trades = []
        
        start_ms = self.timestamp_to_ms(start_date)
        end_ms = self.timestamp_to_ms(end_date)
        
        # Use time chunking for large date ranges - trades API requires max 24 hours
        time_chunks = self.client.chunk_time_range(start_ms, end_ms, days=1)
        
        for chunk_start, chunk_end in time_chunks:
            from_id = None
            while True:
                trades = self.client.get_my_trades(
                    symbol=symbol,
                    start_time=chunk_start,
                    end_time=chunk_end,
                    from_id=from_id,
                    limit=1000
                )
                
                if not trades:
                    break
                    
                all_trades.extend(trades)
                
                # Check if we got less than limit (last page)
                if len(trades) < 1000:
                    break
                    
                # Update from_id for next page
                from_id = trades[-1]["id"] + 1
                
        return all_trades
    
    def _process_trade(self, trade: Dict[str, Any], symbol: str) -> List[Dict[str, Any]]:
        """Process raw trade data into trade records (buy/sell + fee)"""
        records = []
        trade_time = self.ms_to_datetime(trade.get("time", 0))
        
        # Determine trade side
        is_buyer = trade.get("isBuyer", False)
        
        # 1. Main trade record
        trade_record = {
            "source": "binance_api",
            "fid": 1,
            "external_id": f"trade_{trade.get('id', '')}",
            "datetime": trade_time,
            "txn_type": TransactionType.TRADE.value,
            "txn_subtype": TransactionSubtype.SPOT_BUY.value if is_buyer else TransactionSubtype.SPOT_SELL.value,
            "email": self.email,
            "wallet": WalletType.SPOT.value,
            "symbol": symbol,
            "asset": trade.get("commissionAsset", ""),  # Will be corrected below
            "amount": Decimal(str(trade.get("qty", "0"))),
            "price": Decimal(str(trade.get("price", "0"))),
            "order_id": trade.get("orderId", ""),
            "trade_id": trade.get("id", ""),
            "match_id": None,
            "reconciled": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Correct asset based on buy/sell
        if is_buyer:
            # Buying base asset
            trade_record["asset"] = symbol.replace("USDT", "").replace("USDC", "").replace("BUSD", "")
        else:
            # Selling base asset for quote asset
            trade_record["asset"] = "USDT" if "USDT" in symbol else "USDC" if "USDC" in symbol else "BUSD"
            trade_record["amount"] = Decimal(str(trade.get("quoteQty", "0")))
            
        records.append(trade_record)
        
        # 2. Commission/fee record
        commission = Decimal(str(trade.get("commission", "0")))
        if commission > 0:
            fee_record = trade_record.copy()
            fee_record["external_id"] = f"trade_fee_{trade.get('id', '')}"
            fee_record["txn_type"] = TransactionType.TXN_FEE.value
            fee_record["txn_subtype"] = TransactionSubtype.MAKER_FEE.value if trade.get("isMaker", False) else TransactionSubtype.TAKER_FEE.value
            fee_record["asset"] = trade.get("commissionAsset", "")
            fee_record["amount"] = commission
            records.append(fee_record)
            
        return records
    
    def _save_trade(self, db, trade: Dict[str, Any]):
        """Save trade to reconciliation table"""
        if db is None:
            return
            
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
    
    def _save_traded_symbol(self, db, symbol: str):
        """Save symbol to traded symbols cache"""
        if db is None:
            return
            
        existing = db.query(BinanceTradedSymbols).filter_by(
            email=self.email,
            symbol=symbol
        ).first()
        
        if not existing:
            new_symbol = BinanceTradedSymbols(
                email=self.email,
                symbol=symbol,
                last_traded=datetime.utcnow(),
                active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_symbol)
        else:
            existing.last_traded = datetime.utcnow()
            existing.active = True
            existing.updated_at = datetime.utcnow()
            
        db.commit()
    
    def _remove_invalid_symbol(self, db, symbol: str):
        """Mark symbol as inactive in cache"""
        if db is None:
            return
            
        existing = db.query(BinanceTradedSymbols).filter_by(
            email=self.email,
            symbol=symbol
        ).first()
        
        if existing:
            existing.active = False
            existing.updated_at = datetime.utcnow()
            db.commit()
    
    def _trade_to_csv_row(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Convert trade to CSV row format"""
        return {
            "datetime": trade["datetime"],
            "email": trade["email"],
            "txn_type": trade["txn_type"],
            "txn_subtype": trade["txn_subtype"],
            "symbol": trade["symbol"],
            "asset": trade["asset"],
            "amount": trade["amount"],
            "price": trade.get("price", ""),
            "order_id": trade.get("order_id", ""),
            "trade_id": trade.get("trade_id", "")
        }
    
    def validate_data(self, data: Any) -> bool:
        """Validate trade data"""
        return True  # Basic validation