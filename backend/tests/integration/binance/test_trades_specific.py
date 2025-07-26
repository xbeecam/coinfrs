"""
Test trade collection with specific symbols
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.services.binance.collectors.trade import TradeCollector
from app.services.binance.client import BinanceAPIClient


def test_specific_trades():
    """Test trade collection for specific symbols"""
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(env_path)
    
    # Use main account
    api_key = os.getenv("BINANCE_MAIN_API_KEY")
    api_secret = os.getenv("BINANCE_MAIN_API_SECRET")
    email = os.getenv("BINANCE_MAIN_EMAIL", "main@example.com")
    
    if not api_key or not api_secret:
        print("ERROR: API credentials not found")
        return False
    
    print(f"Testing Trade Collection for {email}")
    print("="*50)
    
    # Date range - last 365 days to ensure we find some trades
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)
    
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Popular trading pairs to test
    test_symbols = [
        "BTCUSDT",   # Bitcoin/USDT
        "ETHUSDT",   # Ethereum/USDT
        "BNBUSDT",   # BNB/USDT
        "ADAUSDT",   # Cardano/USDT (we saw ADA in deposits)
        "SOLUSDT",   # Solana/USDT (we saw SOL in deposits)
        "BTCBUSD",   # Bitcoin/BUSD
        "ETHBUSD",   # Ethereum/BUSD
        "USDCUSDT",  # USDC/USDT (we saw USDC in deposits)
    ]
    
    client = BinanceAPIClient(api_key, api_secret)
    
    # First, let's check account status
    print("\nChecking account info...")
    try:
        account_info = client.get_account()
        print(f"Account type: {'SPOT' if account_info.get('canTrade') else 'Unknown'}")
        print(f"Can trade: {account_info.get('canTrade', False)}")
        
        # Show non-zero balances
        balances = [b for b in account_info.get('balances', []) if float(b.get('free', '0')) > 0 or float(b.get('locked', '0')) > 0]
        if balances:
            print("\nNon-zero balances:")
            for balance in balances[:10]:  # Show first 10
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                if free > 0 or locked > 0:
                    print(f"  {asset}: free={free}, locked={locked}")
    except Exception as e:
        print(f"Error getting account info: {e}")
    
    # Test each symbol
    print(f"\nTesting {len(test_symbols)} trading pairs...")
    total_trades = 0
    symbols_with_trades = []
    
    for symbol in test_symbols:
        print(f"\n{symbol}:")
        try:
            # Get trades for this symbol
            trades = client.get_my_trades(symbol=symbol, limit=10)
            
            if trades:
                symbols_with_trades.append(symbol)
                print(f"  Found {len(trades)} recent trades")
                total_trades += len(trades)
                
                # Show first trade details
                if trades:
                    first_trade = trades[0]
                    trade_time = datetime.utcfromtimestamp(first_trade['time'] / 1000)
                    print(f"  Latest trade: {trade_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"    - Side: {first_trade.get('isBuyer', False) and 'BUY' or 'SELL'}")
                    print(f"    - Price: {first_trade.get('price')}")
                    print(f"    - Qty: {first_trade.get('qty')}")
            else:
                print("  No trades found")
                
        except Exception as e:
            error_msg = str(e)
            if "Invalid symbol" in error_msg:
                print("  Symbol not available")
            else:
                print(f"  Error: {error_msg[:100]}")
    
    # Now test the TradeCollector with full date range
    print(f"\n{'='*50}")
    print("Testing TradeCollector with auto-discovery...")
    
    try:
        collector = TradeCollector(client, email)
        
        # For testing, let's manually set some symbols if we found trades
        if symbols_with_trades:
            # Monkey patch the discover method to return our symbols
            original_discover = collector._discover_symbols
            collector._discover_symbols = lambda db: symbols_with_trades
        
        result = collector.collect(start_date, end_date)
        
        print(f"\nTradeCollector Results:")
        print(f"  Symbols discovered: {result.get('symbols_discovered', 0)}")
        print(f"  Symbols processed: {result.get('symbols_processed', 0)}")
        print(f"  Total trades collected: {result.get('trades_collected', 0)}")
        print(f"  Total fees collected: {result.get('fees_saved', 0)}")
        
        if result.get('csv_file'):
            print(f"  CSV file: {result['csv_file']}")
            
    except Exception as e:
        print(f"TradeCollector error: {e}")
    
    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Total symbols with trades: {len(symbols_with_trades)}")
    print(f"  Total trades found: {total_trades}")
    
    if symbols_with_trades:
        print(f"  Symbols with trades: {', '.join(symbols_with_trades)}")
    
    return True


if __name__ == "__main__":
    test_specific_trades()