"""
Enhanced trade collection test with comprehensive symbol discovery
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.services.binance.collectors.enhanced_trade_collector import EnhancedTradeCollector
from app.services.binance.collectors.exchange_info import ExchangeInfoCollector
from app.services.binance.collectors.deposit import DepositCollector
from app.services.binance.collectors.withdraw import WithdrawCollector
from app.services.binance.collectors.transfer import TransferCollector
from app.services.binance.collectors.convert import ConvertCollector
from app.services.binance.client import BinanceAPIClient


def collect_all_assets(api_key: str, api_secret: str, email: str, days: int = 365):
    """
    Collect all assets from various sources
    
    Returns:
        Dictionary containing all collected data
    """
    client = BinanceAPIClient(api_key, api_secret)
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    print(f"Collecting data for asset discovery...")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    collected_data = {
        'deposits': [],
        'withdrawals': [],
        'transfers': [],
        'converts': [],
        'exchange_info': {}
    }
    
    # 1. Collect exchange info first
    print("\n1. Collecting exchange info...")
    try:
        collector = ExchangeInfoCollector(client, email)
        result = collector.collect(start_date, end_date)
        print(f"   Symbols collected: {result.get('symbols_collected', 0)}")
        
        # Get the raw exchange info
        exchange_info = client.get_exchange_info()
        collected_data['exchange_info'] = exchange_info
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Collect deposits
    print("\n2. Collecting deposits...")
    try:
        collector = DepositCollector(client, email)
        # Use shorter date range for deposits to avoid timeout
        deposit_start = end_date - timedelta(days=90)
        deposits = collector._fetch_deposits(deposit_start, end_date)
        collected_data['deposits'] = deposits
        print(f"   Deposits found: {len(deposits)}")
        
        # Show deposit assets
        deposit_assets = set(d.get('coin', '') for d in deposits)
        if deposit_assets:
            print(f"   Assets: {', '.join(sorted(deposit_assets))}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Collect withdrawals
    print("\n3. Collecting withdrawals...")
    try:
        collector = WithdrawCollector(client, email)
        withdraw_start = end_date - timedelta(days=90)
        withdrawals = collector._fetch_withdrawals(withdraw_start, end_date)
        collected_data['withdrawals'] = withdrawals
        print(f"   Withdrawals found: {len(withdrawals)}")
        
        # Show withdrawal assets
        withdraw_assets = set(w.get('coin', '') for w in withdrawals)
        if withdraw_assets:
            print(f"   Assets: {', '.join(sorted(withdraw_assets))}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Collect transfers
    print("\n4. Collecting transfers...")
    try:
        collector = TransferCollector(client, email)
        # Get different types of transfers
        transfer_start = end_date - timedelta(days=90)
        
        # Sub-account transfers
        sub_transfers = collector._fetch_sub_transfers(transfer_start, end_date)
        collected_data['transfers'].extend(sub_transfers)
        
        # Main account transfers (if available)
        try:
            main_transfers = collector._fetch_main_transfers(transfer_start, end_date)
            collected_data['transfers'].extend(main_transfers)
        except:
            pass
            
        print(f"   Transfers found: {len(collected_data['transfers'])}")
        
        # Show transfer assets
        transfer_assets = set(t.get('asset', '') for t in collected_data['transfers'])
        if transfer_assets:
            print(f"   Assets: {', '.join(sorted(transfer_assets))}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. Try to get convert history
    print("\n5. Collecting convert history...")
    try:
        collector = ConvertCollector(client, email)
        convert_start = end_date - timedelta(days=90)
        converts = collector._fetch_converts(convert_start, end_date)
        collected_data['converts'] = converts
        print(f"   Converts found: {len(converts)}")
        
        # Show convert assets
        convert_assets = set()
        for c in converts:
            if 'fromAsset' in c:
                convert_assets.add(c['fromAsset'])
            if 'toAsset' in c:
                convert_assets.add(c['toAsset'])
        if convert_assets:
            print(f"   Assets: {', '.join(sorted(convert_assets))}")
    except Exception as e:
        print(f"   Error: {e}")
    
    return collected_data


def test_enhanced_trade_collection():
    """Test trade collection with enhanced symbol discovery"""
    
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
    
    print("="*70)
    print(" ENHANCED TRADE COLLECTION TEST")
    print("="*70)
    print(f"Account: {email}\n")
    
    # Step 1: Collect all asset data
    collected_data = collect_all_assets(api_key, api_secret, email, days=365)
    
    # Step 2: Create enhanced trade collector
    print("\n" + "="*70)
    print(" SYMBOL DISCOVERY")
    print("="*70)
    
    client = BinanceAPIClient(api_key, api_secret)
    trade_collector = EnhancedTradeCollector(
        client, 
        email, 
        exchange_info=collected_data['exchange_info']
    )
    
    # Discover symbols from collected data
    discovered_symbols = trade_collector.discover_symbols_from_data(
        deposits=collected_data['deposits'],
        withdrawals=collected_data['withdrawals'],
        transfers=collected_data['transfers'],
        converts=collected_data['converts']
    )
    
    if not discovered_symbols:
        print("\nNo trading symbols discovered!")
        return False
    
    # Step 3: Collect trades for discovered symbols
    print("\n" + "="*70)
    print(" TRADE COLLECTION")
    print("="*70)
    
    # Use shorter date range for trades (last 30 days to avoid too many API calls)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    print(f"\nCollecting trades from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Processing {len(discovered_symbols)} symbols with rate limiting...\n")
    
    # Limit symbols to avoid rate limits in testing
    max_symbols = 20
    if len(discovered_symbols) > max_symbols:
        print(f"Limiting to first {max_symbols} symbols for testing")
        test_symbols = discovered_symbols[:max_symbols]
    else:
        test_symbols = discovered_symbols
    
    # Collect trades with rate limiting
    results = trade_collector.collect_with_rate_limiting(
        test_symbols,
        start_date,
        end_date
    )
    
    # Step 4: Show results
    print("\n" + "="*70)
    print(" RESULTS")
    print("="*70)
    
    print(f"\nAsset Discovery Summary:")
    all_assets = set()
    for source, data in [
        ("Deposits", collected_data['deposits']),
        ("Withdrawals", collected_data['withdrawals']),
        ("Transfers", collected_data['transfers']),
        ("Converts", collected_data['converts'])
    ]:
        if data:
            if source == "Converts":
                assets = set()
                for item in data:
                    if 'fromAsset' in item:
                        assets.add(item['fromAsset'])
                    if 'toAsset' in item:
                        assets.add(item['toAsset'])
            else:
                assets = set(item.get('asset', item.get('coin', '')) for item in data if item.get('asset') or item.get('coin'))
            
            all_assets.update(assets)
            if assets:
                print(f"  {source}: {', '.join(sorted(assets))}")
    
    print(f"\nTotal unique assets: {len(all_assets)}")
    print(f"Trading symbols discovered: {len(discovered_symbols)}")
    print(f"Symbols processed: {results['symbols_processed']}")
    print(f"Total trades collected: {results['trades_collected']}")
    print(f"Total fees collected: {results['fees_saved']}")
    
    if results.get('csv_file'):
        print(f"\nCSV file: {results['csv_file']}")
        
        # Show file location
        csv_path = Path(__file__).parent.parent.parent / "output" / "exports" / "binance" / email
        print(f"Location: {csv_path}")
    
    if results.get('errors'):
        print(f"\nErrors encountered: {len(results['errors'])}")
        for error in results['errors'][:5]:  # Show first 5 errors
            print(f"  - {error.get('type', 'unknown')}: {error.get('message', '')[:100]}")
    
    return results['trades_collected'] > 0


if __name__ == "__main__":
    success = test_enhanced_trade_collection()
    sys.exit(0 if success else 1)