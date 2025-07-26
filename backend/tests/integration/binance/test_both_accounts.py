"""
Test both main and sub accounts to verify the reconciliation system works
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

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


def test_account(account_type: str, api_key: str, api_secret: str, email: str):
    """Test collectors for a specific account"""
    print(f"\n{'='*60}")
    print(f" Testing {account_type} Account: {email}")
    print(f"{'='*60}\n")
    
    # Date range - just 1 day for quick test
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=1)
    
    collectors = [
        ("ExchangeInfoCollector", ExchangeInfoCollector),
        ("SnapshotCollector", SnapshotCollector),
        ("DepositCollector", DepositCollector),
        ("WithdrawCollector", WithdrawCollector),
        ("TransferCollector", TransferCollector),
        ("TradeCollector", TradeCollector),
        ("ConvertCollector", ConvertCollector),
    ]
    
    results = []
    
    for collector_name, collector_class in collectors:
        print(f"{collector_name}... ", end="", flush=True)
        try:
            client = BinanceAPIClient(api_key, api_secret)
            collector = collector_class(client, email)
            
            # Special handling for TradeCollector - it auto-discovers symbols
            result = collector.collect(start_date, end_date)
            
            if isinstance(result, dict):
                # Extract key metric for display
                key_metric = None
                if "symbols_collected" in result:
                    key_metric = f"{result['symbols_collected']} symbols"
                elif "snapshots_collected" in result:
                    key_metric = f"{result['snapshots_collected']} snapshots"
                elif "deposits_collected" in result:
                    key_metric = f"{result['deposits_collected']} deposits"
                elif "withdrawals_collected" in result:
                    key_metric = f"{result['withdrawals_collected']} withdrawals"
                elif "transfers_collected" in result:
                    key_metric = f"{result['transfers_collected']} transfers"
                elif "trades_collected" in result:
                    key_metric = f"{result['trades_collected']} trades"
                elif "converts_collected" in result:
                    key_metric = f"{result['converts_collected']} converts"
                
                print(f"✓ ({key_metric or 'success'})")
                results.append((collector_name, True, key_metric))
            else:
                print("✗ (unexpected result)")
                results.append((collector_name, False, "unexpected result"))
                
        except Exception as e:
            print(f"✗ ({str(e)[:50]}...)")
            results.append((collector_name, False, str(e)))
    
    return results


def main():
    """Test both main and sub accounts"""
    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(env_path)
    
    # Get credentials for both accounts
    accounts = []
    
    # Main account
    main_key = os.getenv("BINANCE_MAIN_API_KEY")
    main_secret = os.getenv("BINANCE_MAIN_API_SECRET")
    main_email = os.getenv("BINANCE_MAIN_EMAIL", "main@example.com")
    
    if main_key and main_secret:
        accounts.append(("Main", main_key, main_secret, main_email))
    
    # Sub account
    sub_key = os.getenv("BINANCE_SUB_API_KEY")
    sub_secret = os.getenv("BINANCE_SUB_API_SECRET")
    sub_email = os.getenv("BINANCE_SUB_EMAIL", "sub@example.com")
    
    if sub_key and sub_secret:
        accounts.append(("Sub", sub_key, sub_secret, sub_email))
    
    # Also check legacy format
    if not accounts:
        legacy_key = os.getenv("BINANCE_API_KEY")
        legacy_secret = os.getenv("BINANCE_API_SECRET")
        if legacy_key and legacy_secret:
            accounts.append(("Legacy", legacy_key, legacy_secret, "test@example.com"))
    
    if not accounts:
        print("ERROR: No Binance API credentials found in .env file")
        print(f"Checked .env path: {env_path}")
        print("\nPlease ensure one of these sets is configured:")
        print("  - BINANCE_MAIN_API_KEY and BINANCE_MAIN_API_SECRET")
        print("  - BINANCE_SUB_API_KEY and BINANCE_SUB_API_SECRET")
        print("  - BINANCE_API_KEY and BINANCE_API_SECRET (legacy)")
        return False
    
    print(f"Found {len(accounts)} account(s) to test")
    
    all_results = []
    
    # Test each account
    for account_type, api_key, api_secret, email in accounts:
        results = test_account(account_type, api_key, api_secret, email)
        all_results.append((account_type, email, results))
    
    # Summary
    print(f"\n{'='*60}")
    print(" SUMMARY")
    print(f"{'='*60}\n")
    
    for account_type, email, results in all_results:
        passed = sum(1 for _, success, _ in results if success)
        failed = sum(1 for _, success, _ in results if not success)
        
        print(f"{account_type} Account ({email}):")
        print(f"  Passed: {passed}/{len(results)}")
        print(f"  Failed: {failed}/{len(results)}")
        
        if failed > 0:
            print("  Failed collectors:")
            for name, success, error in results:
                if not success:
                    print(f"    - {name}: {error}")
        print()
    
    # CSV output location
    print(f"CSV files are saved to:")
    print(f"  /backend/tests/output/exports/binance/{{email}}/")
    
    # Return True if all tests passed
    return all(all(success for _, success, _ in results) for _, _, results in all_results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)