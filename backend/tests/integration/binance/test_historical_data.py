"""
Test historical data collectors - deposits, withdrawals, transfers, trades, etc.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.services.binance.collectors.snapshot import SnapshotCollector
from app.services.binance.collectors.deposit import DepositCollector
from app.services.binance.collectors.withdraw import WithdrawCollector
from app.services.binance.collectors.transfer import TransferCollector
from app.services.binance.collectors.trade import TradeCollector
from app.services.binance.collectors.convert import ConvertCollector
from app.services.binance.client import BinanceAPIClient


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def test_historical_collectors():
    """Test all historical data collectors"""
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(env_path)
    
    # Use main account
    api_key = os.getenv("BINANCE_MAIN_API_KEY")
    api_secret = os.getenv("BINANCE_MAIN_API_SECRET")
    email = os.getenv("BINANCE_MAIN_EMAIL", "main@example.com")
    
    if not api_key or not api_secret:
        print("ERROR: BINANCE_MAIN_API_KEY and BINANCE_MAIN_API_SECRET not found in .env")
        return False
    
    print_section("Testing Historical Data Collection")
    print(f"Account: {email}")
    
    # Date range - last 90 days to ensure we capture some data
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)
    
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    csv_files = []
    
    # 1. Daily Snapshots
    print_section("1. Daily Balance Snapshots")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = SnapshotCollector(client, email)
        result = collector.collect(start_date, end_date)
        
        print(f"Snapshots collected: {result.get('snapshots_collected', 0)}")
        print(f"Assets found: {result.get('unique_assets', 0)}")
        if result.get('csv_file'):
            csv_files.append(result['csv_file'])
            print(f"CSV file: {result['csv_file']}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
    
    # 2. Deposit History
    print_section("2. Deposit History")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = DepositCollector(client, email)
        result = collector.collect(start_date, end_date)
        
        print(f"Deposits collected: {result.get('deposits_collected', 0)}")
        if result.get('deposits_collected', 0) > 0:
            print("Sample deposits:")
            # The collector might have deposit details we can show
        if result.get('csv_file'):
            csv_files.append(result['csv_file'])
            print(f"CSV file: {result['csv_file']}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
    
    # 3. Withdrawal History
    print_section("3. Withdrawal History")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = WithdrawCollector(client, email)
        result = collector.collect(start_date, end_date)
        
        print(f"Withdrawals collected: {result.get('withdrawals_collected', 0)}")
        if result.get('csv_file'):
            csv_files.append(result['csv_file'])
            print(f"CSV file: {result['csv_file']}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
    
    # 4. Transfer History (all types)
    print_section("4. Transfer History")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = TransferCollector(client, email)
        result = collector.collect(start_date, end_date)
        
        print(f"Total transfers collected: {result.get('transfers_collected', 0)}")
        if 'transfer_types' in result:
            print("Transfer breakdown:")
            for transfer_type, count in result['transfer_types'].items():
                if count > 0:
                    print(f"  - {transfer_type}: {count}")
        if result.get('csv_file'):
            csv_files.append(result['csv_file'])
            print(f"CSV file: {result['csv_file']}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
    
    # 5. Trade History
    print_section("5. Trade History")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = TradeCollector(client, email)
        result = collector.collect(start_date, end_date)
        
        print(f"Symbols discovered: {result.get('symbols_discovered', 0)}")
        print(f"Symbols processed: {result.get('symbols_processed', 0)}")
        print(f"Total trades collected: {result.get('trades_collected', 0)}")
        print(f"Total fees collected: {result.get('fees_saved', 0)}")
        if result.get('csv_file'):
            csv_files.append(result['csv_file'])
            print(f"CSV file: {result['csv_file']}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
    
    # 6. Convert History
    print_section("6. Convert History")
    try:
        client = BinanceAPIClient(api_key, api_secret)
        collector = ConvertCollector(client, email)
        result = collector.collect(start_date, end_date)
        
        print(f"Converts collected: {result.get('converts_collected', 0)}")
        if result.get('csv_file'):
            csv_files.append(result['csv_file'])
            print(f"CSV file: {result['csv_file']}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
    
    # Summary
    print_section("Summary")
    print(f"Total CSV files generated: {len(csv_files)}")
    
    if csv_files:
        print("\nGenerated CSV files:")
        for csv_file in csv_files:
            print(f"  - {csv_file}")
    
    output_dir = Path(__file__).parent.parent.parent / "output" / "exports" / "binance" / email
    print(f"\nAll files saved to: {output_dir}")
    
    # List all CSV files in the directory
    if output_dir.exists():
        print("\nAll CSV files in output directory:")
        for csv_file in sorted(output_dir.glob("*.csv")):
            size = csv_file.stat().st_size
            print(f"  - {csv_file.name} ({size:,} bytes)")
    
    return True


if __name__ == "__main__":
    success = test_historical_collectors()
    sys.exit(0 if success else 1)