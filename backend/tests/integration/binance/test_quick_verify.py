"""
Quick verification test - just checks if collectors can connect and start working
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.services.binance.collectors.exchange_info import ExchangeInfoCollector
from app.services.binance.client import BinanceAPIClient


def main():
    """Quick test to verify API connection works"""
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(env_path)
    
    # Test main account
    api_key = os.getenv("BINANCE_MAIN_API_KEY")
    api_secret = os.getenv("BINANCE_MAIN_API_SECRET")
    email = os.getenv("BINANCE_MAIN_EMAIL", "main@example.com")
    
    if not api_key or not api_secret:
        print("ERROR: BINANCE_MAIN_API_KEY and BINANCE_MAIN_API_SECRET not found in .env")
        return False
    
    print("Testing Binance API connection...")
    print(f"Account: {email}")
    
    try:
        # Create client and test with ExchangeInfoCollector
        client = BinanceAPIClient(api_key, api_secret)
        collector = ExchangeInfoCollector(client, email)
        
        # Just test with current date (exchange info doesn't need date range)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)
        
        print("\nFetching exchange info...")
        result = collector.collect(start_date, end_date)
        
        if isinstance(result, dict) and result.get("symbols_collected", 0) > 0:
            print(f"✓ SUCCESS: Connected to Binance API")
            print(f"  - Symbols collected: {result['symbols_collected']}")
            print(f"  - SPOT symbols: {result.get('spot_symbols', 0)}")
            print(f"  - CSV file: {result.get('csv_file', 'None')}")
            
            if result.get("csv_file"):
                csv_path = Path(__file__).parent.parent.parent / "output" / "exports" / "binance" / email
                print(f"\nCSV saved to: {csv_path}")
            
            return True
        else:
            print("✗ FAILED: No data collected")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    print("\nIf successful, you can run the full test with:")
    print("  python tests/integration/binance/test_full_reconciliation_flow.py")
    sys.exit(0 if success else 1)