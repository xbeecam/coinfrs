#!/usr/bin/env python3
"""
Test script to verify raw data collection from main and sub accounts.
This tests all collectors with both account types.

Usage:
    cd backend
    python -m tests.integration.binance.test_raw_data_collection
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add backend to path
print("DEBUG 1: Setting up path...")
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

print("DEBUG 2: Importing dotenv...")
from dotenv import load_dotenv
print("DEBUG 3: Importing BinanceAPIClient...")
from app.services.binance.client import BinanceAPIClient
print("DEBUG 4: Importing collectors...")
from app.services.binance.collectors import (
    SnapshotCollector,
    DepositCollector,
    WithdrawCollector,
    TransferCollector,
    TradeCollector,
    ConvertCollector,
    ExchangeInfoCollector
)
print("DEBUG 5: All imports completed")


def test_account_data_collection(account_type: str, api_key: str, api_secret: str):
    """Test data collection for a specific account"""
    print(f"\n{'='*60}")
    print(f"Testing {account_type} Account Data Collection")
    print(f"{'='*60}")
    
    try:
        # Create client
        client = BinanceAPIClient(api_key, api_secret)
        
        # Test connection
        print(f"\n1. Testing API connection...")
        exchange_info = client.get_exchange_info()
        print(f"   ✅ Connected to Binance API")
        print(f"   Server Time: {datetime.utcfromtimestamp(exchange_info['serverTime']/1000)}")
        
        # Create collectors (using test email for dry-run mode)
        test_email = f"test_{account_type.lower()}@example.com"
        collectors = {
            'Exchange Info': ExchangeInfoCollector(client, test_email, account_type.lower()),
            'Snapshot': SnapshotCollector(client, test_email, account_type.lower()),
            'Deposits': DepositCollector(client, test_email, account_type.lower()),
            'Withdrawals': WithdrawCollector(client, test_email, account_type.lower()),
            'Transfers': TransferCollector(client, test_email, account_type.lower()),
            'Trades': TradeCollector(client, test_email, account_type.lower()),
            'Converts': ConvertCollector(client, test_email, account_type.lower())
        }
        
        # Test each collector
        results = {}
        print(f"\n2. Testing data collectors...")
        
        for name, collector in collectors.items():
            print(f"\n   Testing {name} Collector:")
            try:
                # All collectors now require date range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                raw_data = collector.collect(
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Store results
                results[name] = {
                    'success': True,
                    'record_count': len(raw_data) if isinstance(raw_data, list) else 1,
                    'sample': raw_data[:3] if isinstance(raw_data, list) and len(raw_data) > 0 else raw_data
                }
                
                print(f"      ✅ Success - Found {results[name]['record_count']} records")
                
            except Exception as e:
                results[name] = {
                    'success': False,
                    'error': str(e)
                }
                print(f"      ❌ Failed: {e}")
        
        # Summary
        print(f"\n3. Collection Summary for {account_type}:")
        print(f"   {'Collector':<20} {'Status':<10} {'Records':<10}")
        print(f"   {'-'*40}")
        
        for name, result in results.items():
            if result['success']:
                status = "✅ OK"
                records = str(result['record_count'])
            else:
                status = "❌ Failed"
                records = "-"
            print(f"   {name:<20} {status:<10} {records:<10}")
        
        # Save detailed results
        output_dir = Path("tests/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{account_type.lower()}_raw_data_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n   📄 Detailed results saved to: {output_file}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main test function"""
    print("Binance Raw Data Collection Test")
    print("="*60)
    print("\nStarting test...")
    
    print("DEBUG: About to load dotenv...")
    # Load environment variables
    load_dotenv(backend_path / '.env')
    print("DEBUG: Dotenv loaded")
    
    # Test configuration
    accounts = {
        'Main': {
            'api_key': os.getenv('BINANCE_MAIN_API_KEY'),
            'api_secret': os.getenv('BINANCE_MAIN_API_SECRET')
        },
        'Sub': {
            'api_key': os.getenv('BINANCE_SUB_API_KEY'),
            'api_secret': os.getenv('BINANCE_SUB_API_SECRET')
        }
    }
    
    # Check credentials
    print("\nChecking API credentials...")
    for account_type, creds in accounts.items():
        if creds['api_key'] and creds['api_secret']:
            print(f"✅ {account_type} account credentials found")
        else:
            print(f"❌ {account_type} account credentials missing")
            accounts[account_type] = None
    
    # Test each configured account
    all_results = {}
    for account_type, creds in accounts.items():
        if creds:
            results = test_account_data_collection(
                account_type, 
                creds['api_key'], 
                creds['api_secret']
            )
            if results:
                all_results[account_type] = results
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    if all_results:
        print("\nData collection capability verified for:")
        for account_type in all_results:
            print(f"  ✅ {account_type} Account")
        
        print("\nNext steps:")
        print("1. Review the output JSON files for sample data")
        print("2. Verify the data structure matches expectations")
        print("3. Proceed to Phase 5: Data Processing (canonical.py)")
    else:
        print("\n❌ No accounts were successfully tested")
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    print("DEBUG: Starting main...")
    main()