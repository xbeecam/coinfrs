"""
Direct test of trade collection bypassing symbol discovery
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


class DirectTradeCollector(TradeCollector):
    """Modified TradeCollector that accepts symbols directly"""
    
    def __init__(self, client, email, symbols):
        super().__init__(client, email)
        self.symbols = symbols
    
    def _discover_symbols(self, db):
        """Override to return our predefined symbols"""
        return self.symbols


def test_direct_trades():
    """Test trade collection with known symbols"""
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
    
    print(f"Direct Trade Collection Test for {email}")
    print("="*60)
    
    # Date range - last 365 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)
    
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Symbols we know have trades
    symbols_with_trades = ["ETHUSDT", "ADAUSDT", "USDCUSDT"]
    
    client = BinanceAPIClient(api_key, api_secret)
    collector = DirectTradeCollector(client, email, symbols_with_trades)
    
    print(f"\nProcessing {len(symbols_with_trades)} symbols: {', '.join(symbols_with_trades)}")
    
    try:
        result = collector.collect(start_date, end_date)
        
        print(f"\nResults:")
        print(f"  Symbols discovered: {result.get('symbols_discovered', 0)}")
        print(f"  Symbols processed: {result.get('symbols_processed', 0)}")
        print(f"  Total trades collected: {result.get('trades_collected', 0)}")
        print(f"  Total trades saved: {result.get('trades_saved', 0)}")
        print(f"  Total fees saved: {result.get('fees_saved', 0)}")
        
        if result.get('errors'):
            print(f"\nErrors:")
            for error in result['errors']:
                print(f"  - {error}")
        
        if result.get('csv_file'):
            print(f"\nCSV file generated: {result['csv_file']}")
            
            # Show CSV location
            csv_path = Path(__file__).parent.parent.parent / "output" / "exports" / "binance" / email
            full_path = csv_path / Path(result['csv_file']).name
            
            if full_path.exists():
                print(f"Full path: {full_path}")
                print(f"File size: {full_path.stat().st_size:,} bytes")
                
                # Show first few lines
                print("\nFirst few lines of CSV:")
                with open(full_path, 'r') as f:
                    for i, line in enumerate(f):
                        if i < 5:
                            print(f"  {line.strip()}")
                        else:
                            break
        
        return result.get('trades_collected', 0) > 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_direct_trades()
    sys.exit(0 if success else 1)