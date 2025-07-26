#!/usr/bin/env python3
"""
Integration test for Binance API client and collectors.
This script allows testing with real API keys to verify data collection works properly.

Usage:
    cd backend
    python -m tests.integration.binance.test_collectors
    
Environment variables needed in .env:
    BINANCE_TEST_API_KEY=your-api-key
    BINANCE_TEST_API_SECRET=your-api-secret
    BINANCE_TEST_EMAIL=your-email (optional)
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Optional, Dict, Any

# Add backend to path if needed
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
from app.services.binance.client import BinanceAPIClient, BinanceAPIError, BinanceErrorType
from app.services.binance.collectors import (
    ExchangeInfoCollector,
    SnapshotCollector,
    DepositCollector,
    WithdrawCollector,
    TransferCollector,
    TradeCollector,
    ConvertCollector,
)


def print_section(title: str):
    """Print a section header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_result(label: str, value: any):
    """Print a result line"""
    print(f"{label:<25}: {value}")


async def test_api_connection(client: BinanceAPIClient) -> bool:
    """Test basic API connection and permissions"""
    print_section("Testing API Connection")
    
    try:
        # Test basic connection
        print("Testing exchange info endpoint...")
        exchange_info = client.get_exchange_info()
        
        if exchange_info:
            print_result("Connection", "✅ Success")
            print_result("Server Time", datetime.utcfromtimestamp(exchange_info.get('serverTime', 0) / 1000))
            print_result("Symbols Available", len(exchange_info.get('symbols', [])))
            return True
        else:
            print_result("Connection", "❌ Failed - No response")
            return False
            
    except BinanceAPIError as e:
        print_result("Connection", f"❌ Failed - {e.error_type.value}")
        print_result("Error Message", str(e))
        if e.error_type == BinanceErrorType.API_KEY_INVALID:
            print("\n⚠️  Please check your API key and secret are correct.")
            print("⚠️  Also ensure your API key has read permissions enabled.")
        return False
    except Exception as e:
        print_result("Connection", f"❌ Failed - Unexpected error")
        print_result("Error", str(e))
        return False


async def test_account_snapshot(client: BinanceAPIClient, email: str) -> bool:
    """Test account snapshot endpoint"""
    print_section("Testing Account Snapshot")
    
    try:
        # Get snapshot for yesterday
        yesterday = datetime.utcnow() - timedelta(days=1)
        start_ms = int(yesterday.timestamp() * 1000)
        
        print(f"Fetching SPOT wallet snapshot for {yesterday.strftime('%Y-%m-%d')}...")
        response = client.get_account_snapshot(
            account_type="SPOT",
            limit=1
        )
        
        if response and response.get('code') == 200:
            snapshots = response.get('snapshotVos', [])
            print_result("Snapshots Found", len(snapshots))
            
            if snapshots:
                latest = snapshots[-1]
                update_time = datetime.utcfromtimestamp(latest.get('updateTime', 0) / 1000)
                balances = latest.get('data', {}).get('balances', [])
                non_zero = [b for b in balances if float(b.get('free', 0)) + float(b.get('locked', 0)) > 0]
                
                print_result("Latest Snapshot Date", update_time.strftime('%Y-%m-%d %H:%M:%S UTC'))
                print_result("Total Assets", len(balances))
                print_result("Non-Zero Balances", len(non_zero))
                
                # Show top 5 balances
                if non_zero:
                    print("\nTop balances:")
                    for i, balance in enumerate(non_zero[:5]):
                        asset = balance.get('asset', '')
                        free = float(balance.get('free', 0))
                        locked = float(balance.get('locked', 0))
                        total = free + locked
                        print(f"  {asset:<6}: {total:,.8f} (free: {free:,.8f}, locked: {locked:,.8f})")
            
            return True
        else:
            print_result("Snapshot Fetch", "❌ Failed")
            return False
            
    except BinanceAPIError as e:
        print_result("Snapshot Fetch", f"❌ Failed - {e.error_type.value}")
        print_result("Error Message", str(e))
        return False


async def test_collectors_dry_run(client: BinanceAPIClient, email: str, days_back: int = 7, account_type: str = "main") -> Dict[str, Any]:
    """Test collectors without database (dry run)"""
    print_section(f"Testing Collectors - DRY RUN (last {days_back} days)")
    print("Note: This will fetch data but NOT save to database\n")
    
    # Set date range
    end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=days_back)
    
    print_result("Start Date", start_date.strftime('%Y-%m-%d %H:%M:%S UTC'))
    print_result("End Date", end_date.strftime('%Y-%m-%d %H:%M:%S UTC'))
    
    results = {}
    
    # Create mock collectors that don't use database
    class MockCollector:
        def __init__(self, real_collector):
            self.real_collector = real_collector
            self.client = real_collector.client
            self.email = real_collector.email
            
        async def collect(self, start_date, end_date):
            """Collect data without saving to database"""
            # Call the private fetch methods directly
            collector_name = self.real_collector.__class__.__name__
            
            if collector_name == "ExchangeInfoCollector":
                data = await self.real_collector._fetch_exchange_info()
                return {
                    "symbols_collected": len(data.get('symbols', [])) if data else 0,
                    "data_sample": data.get('symbols', [])[:5] if data else []
                }
            elif collector_name == "SnapshotCollector":
                snapshots = await self.real_collector._fetch_snapshots(start_date, end_date)
                return {
                    "snapshots_collected": len(snapshots),
                    "data_sample": snapshots[:2] if snapshots else []
                }
            elif collector_name == "DepositCollector":
                deposits = await self.real_collector._fetch_deposits(start_date, end_date)
                return {
                    "deposits_collected": len(deposits),
                    "data_sample": deposits[:5] if deposits else []
                }
            elif collector_name == "WithdrawCollector":
                withdrawals = await self.real_collector._fetch_withdrawals(start_date, end_date)
                return {
                    "withdrawals_collected": len(withdrawals),
                    "data_sample": withdrawals[:5] if withdrawals else []
                }
            elif collector_name == "TransferCollector":
                main = await self.real_collector._fetch_main_transfers(start_date, end_date)
                sub = await self.real_collector._fetch_sub_transfers(start_date, end_date)
                wallet = await self.real_collector._fetch_wallet_transfers(start_date, end_date)
                return {
                    "transfers_collected": len(main) + len(sub) + len(wallet),
                    "transfer_types": {
                        "main_spot": len(main),
                        "sub_account": len(sub),
                        "wallet_to_wallet": len(wallet)
                    },
                    "data_sample": {
                        "main": main[:2] if main else [],
                        "sub": sub[:2] if sub else [],
                        "wallet": wallet[:2] if wallet else []
                    }
                }
            elif collector_name == "TradeCollector":
                # Just test with a few common symbols
                test_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
                all_trades = []
                for symbol in test_symbols:
                    try:
                        trades = await self.real_collector._fetch_trades_for_symbol(symbol, start_date, end_date)
                        if trades:
                            all_trades.extend(trades)
                    except:
                        pass
                return {
                    "symbols_tested": len(test_symbols),
                    "trades_collected": len(all_trades),
                    "data_sample": all_trades[:5] if all_trades else []
                }
            elif collector_name == "ConvertCollector":
                converts = await self.real_collector._fetch_converts(start_date, end_date)
                return {
                    "converts_collected": len(converts),
                    "data_sample": converts[:5] if converts else []
                }
            else:
                return {"error": f"Unknown collector: {collector_name}"}
    
    # Test each collector
    collectors = [
        ("Exchange Info", MockCollector(ExchangeInfoCollector(client, email))),
        ("Snapshots", MockCollector(SnapshotCollector(client, email, account_type))),
        ("Deposits", MockCollector(DepositCollector(client, email, account_type))),
        ("Withdrawals", MockCollector(WithdrawCollector(client, email, account_type))),
        ("Transfers", MockCollector(TransferCollector(client, email, account_type))),
        ("Trades", MockCollector(TradeCollector(client, email, account_type))),
        ("Converts", MockCollector(ConvertCollector(client, email, account_type))),
    ]
    
    for name, collector in collectors:
        print(f"\n{'Testing ' + name + '...':<30}", end='', flush=True)
        try:
            result = await collector.collect(start_date, end_date)
            results[name] = result
            
            # Print summary
            if name == "Exchange Info":
                print(f"✅ {result.get('symbols_collected', 0)} symbols")
            elif name == "Snapshots":
                print(f"✅ {result.get('snapshots_collected', 0)} snapshots")
            elif name == "Deposits":
                print(f"✅ {result.get('deposits_collected', 0)} deposits")
            elif name == "Withdrawals":
                print(f"✅ {result.get('withdrawals_collected', 0)} withdrawals")
            elif name == "Transfers":
                types = result.get('transfer_types', {})
                print(f"✅ {result.get('transfers_collected', 0)} total ({types.get('main_spot', 0)} main, {types.get('sub_account', 0)} sub, {types.get('wallet_to_wallet', 0)} wallet)")
            elif name == "Trades":
                print(f"✅ {result.get('symbols_tested', 0)} symbols tested, {result.get('trades_collected', 0)} trades found")
            elif name == "Converts":
                print(f"✅ {result.get('converts_collected', 0)} converts")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results[name] = {"error": str(e)}
    
    return results


async def test_specific_endpoints(client: BinanceAPIClient):
    """Test specific endpoints that might need special handling"""
    print_section("Testing Specific Endpoints")
    
    # Test deposit history
    try:
        print("Testing deposit history...")
        deposits = client.get_deposit_history(limit=10)
        print_result("Recent Deposits", len(deposits) if deposits else 0)
    except Exception as e:
        print_result("Deposit History", f"Error: {str(e)}")
    
    # Test withdrawal history
    try:
        print("Testing withdrawal history...")
        withdrawals = client.get_withdrawal_history(limit=10)
        print_result("Recent Withdrawals", len(withdrawals) if withdrawals else 0)
    except Exception as e:
        print_result("Withdrawal History", f"Error: {str(e)}")
    
    # Test convert history
    try:
        print("Testing convert history...")
        # Last 30 days
        end_time = int(datetime.utcnow().timestamp() * 1000)
        start_time = int((datetime.utcnow() - timedelta(days=30)).timestamp() * 1000)
        converts = client.get_convert_history(start_time=start_time, end_time=end_time, limit=10)
        print_result("Recent Converts", len(converts.get('list', [])) if converts else 0)
    except Exception as e:
        print_result("Convert History", f"Error: {str(e)}")
    
    # Test a trade endpoint with a common symbol
    try:
        print("\nTesting trade history (BTCUSDT)...")
        # Last 7 days
        end_time = int(datetime.utcnow().timestamp() * 1000)
        start_time = int((datetime.utcnow() - timedelta(days=7)).timestamp() * 1000)
        trades = client.get_my_trades(symbol="BTCUSDT", start_time=start_time, end_time=end_time, limit=10)
        print_result("Recent BTCUSDT Trades", len(trades) if trades else 0)
    except Exception as e:
        print_result("Trade History", f"Error: {str(e)}")


def save_test_results(results: Dict[str, Any], output_dir: Path):
    """Save test results to JSON file"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save detailed results
    detailed_file = output_dir / f"test_results_detailed_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(detailed_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Save summary without data samples
    summary = {}
    for name, result in results.items():
        if isinstance(result, dict):
            summary[name] = {k: v for k, v in result.items() if k != 'data_sample'}
        else:
            summary[name] = result
    
    summary_file = output_dir / f"test_results_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    return detailed_file, summary_file


def main():
    """Main test function"""
    print("="*60)
    print(" Binance API Client and Collectors Test Script")
    print("="*60)
    
    # Load environment variables
    env_path = backend_path / '.env'
    load_dotenv(env_path)
    
    # Get configuration for main and sub accounts
    main_api_key = os.getenv('BINANCE_MAIN_API_KEY') or os.getenv('BINANCE_TEST_API_KEY') or os.getenv('BINANCE_API_KEY')
    main_api_secret = os.getenv('BINANCE_MAIN_API_SECRET') or os.getenv('BINANCE_TEST_API_SECRET') or os.getenv('BINANCE_API_SECRET')
    main_email = os.getenv('BINANCE_MAIN_EMAIL', 'main@example.com')
    
    sub_api_key = os.getenv('BINANCE_SUB_API_KEY')
    sub_api_secret = os.getenv('BINANCE_SUB_API_SECRET')
    sub_email = os.getenv('BINANCE_SUB_EMAIL', 'sub@example.com')
    
    if not main_api_key or not main_api_secret:
        print("\n❌ ERROR: Main account API credentials not found!")
        print(f"\nPlease add the following to your .env file at: {env_path}")
        print("\n  # Main Account")
        print("  BINANCE_MAIN_API_KEY=your-main-api-key")
        print("  BINANCE_MAIN_API_SECRET=your-main-api-secret")
        print("  BINANCE_MAIN_EMAIL=main@example.com")
        print("\n  # Sub Account (optional)")
        print("  BINANCE_SUB_API_KEY=your-sub-api-key")
        print("  BINANCE_SUB_API_SECRET=your-sub-api-secret")
        print("  BINANCE_SUB_EMAIL=sub@example.com")
        return
    
    # Determine which accounts to test
    accounts_to_test = []
    
    # Always test main account
    accounts_to_test.append({
        'type': 'main',
        'api_key': main_api_key,
        'api_secret': main_api_secret,
        'email': main_email
    })
    
    # Test sub account if credentials provided
    if sub_api_key and sub_api_secret:
        accounts_to_test.append({
            'type': 'sub',
            'api_key': sub_api_key,
            'api_secret': sub_api_secret,
            'email': sub_email
        })
    
    print_result("Accounts to Test", f"{len(accounts_to_test)} ({', '.join([a['type'] for a in accounts_to_test])})")
    
    # Run tests for each account
    loop = asyncio.get_event_loop()
    all_results = {}
    
    try:
        for account in accounts_to_test:
            print("\n" + "="*60)
            print(f" Testing {account['type'].upper()} Account")
            print("="*60)
            print_result("Email", account['email'])
            print_result("API Key", f"{account['api_key'][:8]}...{account['api_key'][-4:]}")
            
            # Create API client for this account
            client = BinanceAPIClient(account['api_key'], account['api_secret'])
            
            # Test API connection
            if not loop.run_until_complete(test_api_connection(client)):
                print(f"\n❌ API connection failed for {account['type']} account. Skipping...")
                continue
            
            # Test account snapshot
            loop.run_until_complete(test_account_snapshot(client, account['email']))
            
            # Test specific endpoints
            loop.run_until_complete(test_specific_endpoints(client))
            
            # Store results for this account
            all_results[account['type']] = {
                'email': account['email'],
                'connection': 'success'
            }
        
        # Ask user if they want to test collectors
        print("\n" + "="*60)
        response = input("\nDo you want to test data collectors for all accounts? (y/n): ").lower()
        
        if response == 'y':
            # Ask for date range
            days = input("How many days back to test? (default: 7): ").strip()
            days_back = int(days) if days else 7
            
            # Test collectors for each account
            for account in accounts_to_test:
                print("\n" + "="*60)
                print(f" Testing Collectors for {account['type'].upper()} Account")
                print("="*60)
                
                client = BinanceAPIClient(account['api_key'], account['api_secret'])
                
                # Test collectors (dry run - no database)
                # Pass account type to collectors
                results = loop.run_until_complete(test_collectors_dry_run(
                    client, 
                    account['email'], 
                    days_back,
                    account_type=account['type']
                ))
                
                # Store results
                all_results[account['type']]['collectors'] = results
                
                # Save results for this account
                output_dir = backend_path / 'tests' / 'integration' / 'binance' / 'results'
                account_dir = output_dir / account['type']
                detailed_file, summary_file = save_test_results(results, account_dir)
                
                print(f"\n✅ {account['type'].upper()} account test results saved to:")
                print(f"   - Summary: {summary_file}")
                print(f"   - Detailed: {detailed_file}")
            
            # Save combined results
            combined_file = output_dir / f"combined_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(combined_file, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
            print(f"\n✅ Combined results saved to: {combined_file}")
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()