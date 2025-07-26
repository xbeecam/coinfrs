"""
Comprehensive test for all Binance reconciliation endpoints and collectors.
Tests the full flow of data collection needed for the reconciliation process.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

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
from app.core.config import settings


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def print_results(collector_name: str, results: Dict[str, Any]):
    """Print collector results"""
    print(f"\n{collector_name} Results:")
    print(f"-" * (len(collector_name) + 9))
    
    for key, value in results.items():
        if key == "errors" and value:
            print(f"  {key}:")
            for error in value:
                print(f"    - {error}")
        else:
            print(f"  {key}: {value}")


def test_all_collectors():
    """Test all collectors with actual API calls"""
    
    # Initialize API client
    print_section("Testing Full Binance Reconciliation Flow")
    
    # Get API credentials from environment
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        print("ERROR: Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
        sys.exit(1)
    
    # Test account email
    test_email = "test@example.com"
    
    # Date range for historical data (last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    print(f"Using date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Test account: {test_email}")
    
    # Create output directory
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    # Test results summary
    summary = {
        "total_collectors": 0,
        "successful": 0,
        "failed": 0,
        "csv_files_generated": []
    }
    
    # 1. Test Exchange Info Collector
    print_section("1. Exchange Info Collector")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = ExchangeInfoCollector(client, test_email)
        results = collector.collect(start_date, end_date)
        print_results("ExchangeInfoCollector", results)
        
        summary["total_collectors"] += 1
        if results.get("symbols_collected", 0) > 0:
            summary["successful"] += 1
            if results.get("csv_file"):
                summary["csv_files_generated"].append(results["csv_file"])
        else:
            summary["failed"] += 1
    except Exception as e:
        print(f"ERROR: {str(e)}")
        summary["total_collectors"] += 1
        summary["failed"] += 1
    
    # 2. Test Snapshot Collector
    print_section("2. Daily Snapshot Collector")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = SnapshotCollector(client, test_email)
        results = collector.collect(start_date, end_date)
        print_results("SnapshotCollector", results)
        
        summary["total_collectors"] += 1
        if results.get("snapshots_collected", 0) > 0:
            summary["successful"] += 1
            if results.get("csv_file"):
                summary["csv_files_generated"].append(results["csv_file"])
        else:
            summary["failed"] += 1
    except Exception as e:
        print(f"ERROR: {str(e)}")
        summary["total_collectors"] += 1
        summary["failed"] += 1
    
    # 3. Test Deposit Collector
    print_section("3. Deposit History Collector")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = DepositCollector(client, test_email)
        results = collector.collect(start_date, end_date)
        print_results("DepositCollector", results)
        
        summary["total_collectors"] += 1
        if "deposits_collected" in results:
            summary["successful"] += 1
            if results.get("csv_file"):
                summary["csv_files_generated"].append(results["csv_file"])
        else:
            summary["failed"] += 1
    except Exception as e:
        print(f"ERROR: {str(e)}")
        summary["total_collectors"] += 1
        summary["failed"] += 1
    
    # 4. Test Withdraw Collector
    print_section("4. Withdrawal History Collector")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = WithdrawCollector(client, test_email)
        results = collector.collect(start_date, end_date)
        print_results("WithdrawCollector", results)
        
        summary["total_collectors"] += 1
        if "withdrawals_collected" in results:
            summary["successful"] += 1
            if results.get("csv_file"):
                summary["csv_files_generated"].append(results["csv_file"])
        else:
            summary["failed"] += 1
    except Exception as e:
        print(f"ERROR: {str(e)}")
        summary["total_collectors"] += 1
        summary["failed"] += 1
    
    # 5. Test Transfer Collector (handles all transfer types)
    print_section("5. Transfer Collector (All Types)")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = TransferCollector(client, test_email)
        results = collector.collect(start_date, end_date)
        print_results("TransferCollector", results)
        
        summary["total_collectors"] += 1
        if "transfers_collected" in results:
            summary["successful"] += 1
            if results.get("csv_file"):
                summary["csv_files_generated"].append(results["csv_file"])
        else:
            summary["failed"] += 1
    except Exception as e:
        print(f"ERROR: {str(e)}")
        summary["total_collectors"] += 1
        summary["failed"] += 1
    
    # 6. Test Trade Collector
    print_section("6. Trade History Collector")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = TradeCollector(client, test_email)
        # TradeCollector will auto-discover symbols based on user assets
        results = collector.collect(start_date, end_date)
        print_results("TradeCollector", results)
        
        summary["total_collectors"] += 1
        if results.get("symbols_discovered", 0) > 0 or results.get("trades_collected", 0) > 0:
            summary["successful"] += 1
            if results.get("csv_file"):
                summary["csv_files_generated"].append(results["csv_file"])
        else:
            summary["failed"] += 1
    except Exception as e:
        print(f"ERROR: {str(e)}")
        summary["total_collectors"] += 1
        summary["failed"] += 1
    
    # 7. Test Convert Collector
    print_section("7. Convert History Collector")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = ConvertCollector(client, test_email)
        results = collector.collect(start_date, end_date)
        print_results("ConvertCollector", results)
        
        summary["total_collectors"] += 1
        if "converts_collected" in results:
            summary["successful"] += 1
            if results.get("csv_file"):
                summary["csv_files_generated"].append(results["csv_file"])
        else:
            summary["failed"] += 1
    except Exception as e:
        print(f"ERROR: {str(e)}")
        summary["total_collectors"] += 1
        summary["failed"] += 1
    
    # Print final summary
    print_section("Test Summary")
    print(f"Total collectors tested: {summary['total_collectors']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"\nCSV files generated: {len(summary['csv_files_generated'])}")
    
    if summary['csv_files_generated']:
        print("\nGenerated CSV files:")
        for csv_file in summary['csv_files_generated']:
            print(f"  - {csv_file}")
    
    print(f"\nCSV output directory: {Path(__file__).parent.parent.parent / 'output' / 'exports' / 'binance' / test_email}")
    
    # Return success status
    return summary['failed'] == 0


if __name__ == "__main__":
    success = test_all_collectors()
    sys.exit(0 if success else 1)