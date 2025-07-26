"""
Enhanced Trade Collector with comprehensive symbol discovery
"""
from typing import Dict, Any, List, Set
from datetime import datetime
import time
from decimal import Decimal

from .trade import TradeCollector
from app.services.binance.client import BinanceAPIError, BinanceErrorType


class EnhancedTradeCollector(TradeCollector):
    """Trade collector with enhanced symbol discovery that works without database"""
    
    def __init__(self, client, email, exchange_info=None):
        super().__init__(client, email)
        self.exchange_info = exchange_info or {}
        self.rate_limit_delay = 0.5  # Delay between API calls to avoid rate limits
        
    def discover_symbols_from_data(self, 
                                  deposits: List[Dict] = None,
                                  withdrawals: List[Dict] = None,
                                  transfers: List[Dict] = None,
                                  converts: List[Dict] = None,
                                  snapshots: List[Dict] = None) -> List[str]:
        """
        Discover trading symbols from collected data without database dependency
        
        Args:
            deposits: List of deposit records
            withdrawals: List of withdrawal records
            transfers: List of transfer records
            converts: List of convert records
            snapshots: List of snapshot/balance records
            
        Returns:
            List of valid trading symbols sorted by priority
        """
        # Step 1: Collect all unique assets
        all_assets = set()
        
        # From deposits
        if deposits:
            for deposit in deposits:
                asset = deposit.get('asset', deposit.get('coin', ''))
                if asset:
                    all_assets.add(asset)
        
        # From withdrawals
        if withdrawals:
            for withdrawal in withdrawals:
                asset = withdrawal.get('asset', withdrawal.get('coin', ''))
                if asset:
                    all_assets.add(asset)
                    
        # From transfers
        if transfers:
            for transfer in transfers:
                asset = transfer.get('asset', '')
                if asset:
                    all_assets.add(asset)
                    
        # From converts
        if converts:
            for convert in converts:
                # Converts have fromAsset and toAsset
                from_asset = convert.get('fromAsset', '')
                to_asset = convert.get('toAsset', '')
                if from_asset:
                    all_assets.add(from_asset)
                if to_asset:
                    all_assets.add(to_asset)
                    
        # From snapshots/balances
        if snapshots:
            for snapshot in snapshots:
                # Could be nested in data.balances
                balances = snapshot.get('data', {}).get('balances', [])
                if not balances and 'balances' in snapshot:
                    balances = snapshot['balances']
                    
                for balance in balances:
                    asset = balance.get('asset', '')
                    if asset:
                        all_assets.add(asset)
        
        print(f"Discovered {len(all_assets)} unique assets: {sorted(all_assets)}")
        
        # Step 2: Identify quote assets (stablecoins and common pairs)
        quote_assets = {'USDT', 'USDC', 'BUSD', 'BTC', 'ETH', 'BNB'}
        user_quote_assets = all_assets.intersection(quote_assets)
        
        # Step 3: Get valid trading symbols from exchange info
        valid_symbols = set()
        if self.exchange_info and 'symbols' in self.exchange_info:
            for symbol_info in self.exchange_info['symbols']:
                if symbol_info.get('status') == 'TRADING':
                    symbol = symbol_info.get('symbol', '')
                    base_asset = symbol_info.get('baseAsset', '')
                    quote_asset = symbol_info.get('quoteAsset', '')
                    
                    # Include if user has either base or quote asset
                    if base_asset in all_assets or quote_asset in all_assets:
                        valid_symbols.add(symbol)
        
        # Step 4: Form potential trading pairs
        potential_symbols = set()
        
        # For each user asset, try pairing with common quote assets
        for asset in all_assets:
            if asset not in quote_assets:  # Don't pair quote assets with themselves
                for quote in quote_assets:
                    if asset != quote:
                        # Try both directions
                        potential_symbols.add(f"{asset}{quote}")
                        potential_symbols.add(f"{quote}{asset}")
        
        # Also add pairs between user's assets
        asset_list = list(all_assets)
        for i, asset1 in enumerate(asset_list):
            for asset2 in asset_list[i+1:]:
                potential_symbols.add(f"{asset1}{asset2}")
                potential_symbols.add(f"{asset2}{asset1}")
        
        # Step 5: Filter to only valid exchange symbols
        discovered_symbols = valid_symbols.intersection(potential_symbols)
        
        # Step 6: Prioritize symbols
        # Priority 1: Stablecoin pairs (USDT, USDC, BUSD)
        stablecoin_symbols = [s for s in discovered_symbols 
                             if any(stable in s for stable in ['USDT', 'USDC', 'BUSD'])]
        
        # Priority 2: Major crypto pairs (BTC, ETH, BNB)
        major_symbols = [s for s in discovered_symbols 
                        if any(major in s for major in ['BTC', 'ETH', 'BNB'])
                        and s not in stablecoin_symbols]
        
        # Priority 3: Other symbols
        other_symbols = [s for s in discovered_symbols 
                        if s not in stablecoin_symbols and s not in major_symbols]
        
        # Combine in priority order
        final_symbols = stablecoin_symbols + major_symbols + other_symbols
        
        print(f"Discovered {len(final_symbols)} valid trading symbols")
        if final_symbols:
            print(f"Sample symbols: {final_symbols[:10]}")
            
        return final_symbols
    
    def collect_with_rate_limiting(self, symbols: List[str], start_date: datetime, 
                                  end_date: datetime) -> Dict[str, Any]:
        """
        Collect trades for specified symbols with rate limit handling
        
        Args:
            symbols: List of symbols to collect trades for
            start_date: Start date for collection
            end_date: End date for collection
            
        Returns:
            Dictionary with collection results
        """
        results = {
            "symbols_discovered": len(symbols),
            "symbols_processed": 0,
            "trades_collected": 0,
            "trades_saved": 0,
            "fees_saved": 0,
            "errors": [],
            "csv_file": None
        }
        
        csv_data = []
        
        for i, symbol in enumerate(symbols):
            try:
                print(f"Processing {symbol} ({i+1}/{len(symbols)})...", end='', flush=True)
                
                # Add delay to avoid rate limits
                if i > 0:
                    time.sleep(self.rate_limit_delay)
                
                # Fetch trades for this symbol
                trades = self._fetch_trades_for_symbol(symbol, start_date, end_date)
                
                if trades:
                    results["symbols_processed"] += 1
                    results["trades_collected"] += len(trades)
                    print(f" found {len(trades)} trades")
                    
                    # Process each trade
                    for trade in trades:
                        # Process trade and fee
                        trade_records = self._process_trade(trade, symbol)
                        for record in trade_records:
                            if record["txn_subtype"] in ["spot_buy", "spot_sell"]:
                                results["trades_saved"] += 1
                            else:
                                results["fees_saved"] += 1
                            
                            csv_data.append(self._trade_to_csv_row(record))
                else:
                    print(" no trades")
                    
            except BinanceAPIError as e:
                if e.error_type == BinanceErrorType.RATE_LIMIT:
                    print(f" rate limit hit, waiting 60s...")
                    time.sleep(60)  # Wait 1 minute for rate limit reset
                    # Retry this symbol
                    try:
                        trades = self._fetch_trades_for_symbol(symbol, start_date, end_date)
                        if trades:
                            results["symbols_processed"] += 1
                            results["trades_collected"] += len(trades)
                            print(f" retry successful, found {len(trades)} trades")
                    except Exception as retry_error:
                        print(f" retry failed: {str(retry_error)}")
                        self.log_error(f"trade_fetch_error_{symbol}", str(retry_error))
                elif e.error_type == BinanceErrorType.INVALID_SYMBOL:
                    print(" invalid symbol")
                else:
                    print(f" error: {str(e)}")
                    self.log_error(f"trade_fetch_error_{symbol}", str(e))
            except Exception as e:
                print(f" unexpected error: {str(e)}")
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
    
    def _trade_to_csv_row(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert trade record to CSV row format"""
        return {
            "datetime": record["datetime"],
            "email": record["email"],
            "txn_type": record["txn_type"],
            "txn_subtype": record["txn_subtype"],
            "symbol": record["symbol"],
            "asset": record["asset"],
            "amount": str(record["amount"]),
            "price": str(record.get("price", "")),
            "order_id": record.get("external_id", "").replace("trade_", "").replace("fee_", ""),
            "trade_id": record.get("agg_id", "")
        }