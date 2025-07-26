"""
Basic test to verify all collectors are working properly.
This test checks that each collector can be instantiated and called without errors.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.services.binance.collectors.exchange_info import ExchangeInfoCollector
from app.services.binance.collectors.snapshot import SnapshotCollector
from app.services.binance.collectors.deposit import DepositCollector
from app.services.binance.collectors.withdraw import WithdrawCollector
from app.services.binance.collectors.transfer import TransferCollector
from app.services.binance.collectors.trade import TradeCollector
from app.services.binance.collectors.convert import ConvertCollector
from app.services.binance.client import BinanceAPIClient


def test_collectors():
    """Test that all collectors can be instantiated and called"""
    
    # Get API credentials
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        print("ERROR: Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
        return False
    
    # Test parameters
    test_email = "test@example.com"
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=1)  # Just 1 day for quick test
    
    # List of all collectors to test
    collectors = [
        ("ExchangeInfoCollector", ExchangeInfoCollector),
        ("SnapshotCollector", SnapshotCollector),
        ("DepositCollector", DepositCollector),
        ("WithdrawCollector", WithdrawCollector),
        ("TransferCollector", TransferCollector),
        ("TradeCollector", TradeCollector),
        ("ConvertCollector", ConvertCollector),
    ]
    
    print("Testing all Binance collectors...\n")
    
    passed = 0
    failed = 0
    
    for collector_name, collector_class in collectors:
        print(f"Testing {collector_name}... ", end="")
        try:
            # Create client and collector
            client = BinanceAPIClient(api_key, api_secret)
            collector = collector_class(client, test_email)
            
            # Call collect method - TradeCollector will auto-discover symbols
            results = collector.collect(start_date, end_date)
            
            # Check if we got results
            if isinstance(results, dict):
                print("✓ PASSED")
                passed += 1
                
                # Print key metrics
                for key, value in results.items():
                    if key != "errors" and key != "csv_file":
                        print(f"    - {key}: {value}")
            else:
                print("✗ FAILED (unexpected result type)")
                failed += 1
                
        except Exception as e:
            print(f"✗ FAILED ({str(e)})")
            failed += 1
        
        print()
    
    # Summary
    print(f"\nSummary:")
    print(f"  Total collectors: {len(collectors)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    return failed == 0


if __name__ == "__main__":
    success = test_collectors()
    sys.exit(0 if success else 1)