#!/usr/bin/env python3
"""
Simple test script for Binance data collection.
Tests basic connectivity and data retrieval for main and sub accounts.

Usage:
    cd backend
    python -m tests.integration.binance.test_simple_collection
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import asyncio

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
from app.services.binance.client import BinanceAPIClient, BinanceAPIError


def test_basic_api_calls():
    """Test basic API connectivity and snapshot retrieval"""
    # Load environment variables
    load_dotenv(backend_path / '.env')
    
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
    
    print("Binance API Simple Test")
    print("="*60)
    
    for account_type, creds in accounts.items():
        if not creds['api_key'] or not creds['api_secret']:
            print(f"\n❌ {account_type} account credentials missing")
            continue
            
        print(f"\n{account_type} Account Test")
        print("-"*40)
        
        try:
            # Create client
            client = BinanceAPIClient(creds['api_key'], creds['api_secret'])
            
            # Test 1: Basic connectivity
            print("1. Testing basic connectivity...")
            exchange_info = client.get_exchange_info()
            print(f"   ✅ Connected to Binance")
            print(f"   Server time: {datetime.utcfromtimestamp(exchange_info['serverTime']/1000)}")
            
            # Test 2: Account snapshot (default 7 days)
            print("\n2. Testing account snapshot (SPOT)...")
            try:
                # Just test SPOT wallet with default parameters (last 7 days)
                response = client.get_account_snapshot(account_type="SPOT")
                
                if response.get("code") == 200:
                    snapshots = response.get("snapshotVos", [])
                    print(f"   ✅ Retrieved {len(snapshots)} daily snapshots")
                    
                    if snapshots:
                        # Show first snapshot info
                        first = snapshots[0]
                        update_time = datetime.utcfromtimestamp(first['updateTime']/1000)
                        print(f"   First snapshot: {update_time}")
                        
                        # Count non-zero balances
                        balances = first.get('data', {}).get('balances', [])
                        non_zero = [b for b in balances if float(b.get('free', 0)) + float(b.get('locked', 0)) > 0]
                        print(f"   Non-zero balances: {len(non_zero)} assets")
                else:
                    print(f"   ❌ API returned code: {response.get('code')}")
                    print(f"   Message: {response.get('msg')}")
                    
            except BinanceAPIError as e:
                print(f"   ❌ Error: {e}")
                
            # Test 3: Recent deposits (last 7 days)
            print("\n3. Testing deposit history...")
            try:
                deposits = client.get_deposit_history()
                print(f"   ✅ Retrieved {len(deposits)} deposits")
            except BinanceAPIError as e:
                print(f"   ❌ Error: {e}")
                
            # Test 4: Recent withdrawals (last 7 days)  
            print("\n4. Testing withdrawal history...")
            try:
                withdrawals = client.get_withdrawal_history()
                successful = [w for w in withdrawals if w.get('status') == 6]
                print(f"   ✅ Retrieved {len(withdrawals)} withdrawals ({len(successful)} completed)")
            except BinanceAPIError as e:
                print(f"   ❌ Error: {e}")
                
        except Exception as e:
            print(f"\n❌ Critical error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("Test completed!")
    print("\nNotes:")
    print("- Account snapshot returns last 7 days by default")
    print("- Can specify up to 30 days with startTime/endTime")
    print("- Historical data only available for last month")


if __name__ == "__main__":
    test_basic_api_calls()