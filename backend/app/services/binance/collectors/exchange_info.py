from typing import Dict, Any
from datetime import datetime

from .base import BaseCollector
from app.services.binance.client import BinanceAPIError
from app.models.binance_reconciliation import BinanceExchangeInfo


class ExchangeInfoCollector(BaseCollector):
    """Collector for exchange info (trading pairs and symbols)"""
    
    async def collect(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        Collect current exchange info. Date parameters are ignored as this is always current data.
        
        Returns:
            Dictionary containing collected data and statistics
        """
        db = self.get_db()
        try:
            results = {
                "symbols_collected": 0,
                "symbols_saved": 0,
                "spot_symbols": 0,
                "errors": [],
                "csv_file": None
            }
            
            # Fetch exchange info
            exchange_info = await self._fetch_exchange_info()
            
            if exchange_info:
                symbols = exchange_info.get("symbols", [])
                results["symbols_collected"] = len(symbols)
                
                # Process each symbol
                csv_data = []
                for symbol_info in symbols:
                    # Only process SPOT trading symbols
                    if symbol_info.get("status") == "TRADING" and "SPOT" in symbol_info.get("permissions", []):
                        results["spot_symbols"] += 1
                        
                        # Save or update symbol
                        self._save_symbol(db, symbol_info)
                        results["symbols_saved"] += 1
                        
                        csv_data.append({
                            "symbol": symbol_info.get("symbol", ""),
                            "base_asset": symbol_info.get("baseAsset", ""),
                            "quote_asset": symbol_info.get("quoteAsset", ""),
                            "status": symbol_info.get("status", ""),
                            "base_precision": symbol_info.get("baseAssetPrecision", 0),
                            "quote_precision": symbol_info.get("quoteAssetPrecision", 0)
                        })
                
                # Export to CSV
                if csv_data:
                    results["csv_file"] = self.export_to_csv(
                        csv_data,
                        f"exchange_info_{datetime.utcnow().strftime('%Y%m%d')}.csv",
                        ["symbol", "base_asset", "quote_asset", "status", 
                         "base_precision", "quote_precision"]
                    )
            
            results["errors"] = self.errors
            return results
            
        finally:
            self.close_db(db)
    
    async def _fetch_exchange_info(self) -> Dict[str, Any]:
        """Fetch exchange info from Binance API"""
        try:
            return self.client.get_exchange_info()
        except BinanceAPIError as e:
            self.handle_api_error(e)
            self.log_error("exchange_info_fetch_error", str(e))
            return None
    
    def _save_symbol(self, db, symbol_info: Dict[str, Any]):
        """Save or update symbol in exchange info table"""
        symbol = symbol_info.get("symbol", "")
        
        # Check if symbol already exists
        existing = db.query(BinanceExchangeInfo).filter_by(symbol=symbol).first()
        
        if existing:
            # Update existing record
            existing.base_asset = symbol_info.get("baseAsset", "")
            existing.quote_asset = symbol_info.get("quoteAsset", "")
            existing.status = symbol_info.get("status", "")
            existing.base_precision = symbol_info.get("baseAssetPrecision", 0)
            existing.quote_precision = symbol_info.get("quoteAssetPrecision", 0)
            existing.tick_size = self._extract_tick_size(symbol_info)
            existing.lot_size = self._extract_lot_size(symbol_info)
            existing.min_notional = self._extract_min_notional(symbol_info)
            existing.updated_at = datetime.utcnow()
        else:
            # Create new record
            new_symbol = BinanceExchangeInfo(
                symbol=symbol,
                base_asset=symbol_info.get("baseAsset", ""),
                quote_asset=symbol_info.get("quoteAsset", ""),
                status=symbol_info.get("status", ""),
                base_precision=symbol_info.get("baseAssetPrecision", 0),
                quote_precision=symbol_info.get("quoteAssetPrecision", 0),
                tick_size=self._extract_tick_size(symbol_info),
                lot_size=self._extract_lot_size(symbol_info),
                min_notional=self._extract_min_notional(symbol_info),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_symbol)
            
        db.commit()
    
    def _extract_tick_size(self, symbol_info: Dict[str, Any]) -> str:
        """Extract tick size from filters"""
        for filter_info in symbol_info.get("filters", []):
            if filter_info.get("filterType") == "PRICE_FILTER":
                return filter_info.get("tickSize", "0")
        return "0"
    
    def _extract_lot_size(self, symbol_info: Dict[str, Any]) -> str:
        """Extract lot size from filters"""
        for filter_info in symbol_info.get("filters", []):
            if filter_info.get("filterType") == "LOT_SIZE":
                return filter_info.get("stepSize", "0")
        return "0"
    
    def _extract_min_notional(self, symbol_info: Dict[str, Any]) -> str:
        """Extract minimum notional from filters"""
        for filter_info in symbol_info.get("filters", []):
            if filter_info.get("filterType") == "MIN_NOTIONAL":
                return filter_info.get("minNotional", "0")
        return "0"
    
    def validate_data(self, data: Any) -> bool:
        """Validate exchange info data"""
        if not isinstance(data, dict):
            return False
            
        if "symbols" not in data:
            return False
            
        return True