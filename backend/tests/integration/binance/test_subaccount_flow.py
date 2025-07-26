#!/usr/bin/env python3
"""
Test script for sub-account discovery workflow.
This tests the API client's ability to fetch sub-accounts.

Usage:
    cd backend
    python -m tests.integration.binance.test_subaccount_flow
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
from app.services.binance.client import BinanceAPIClient, BinanceAPIError, BinanceErrorType


def test_subaccount_discovery():
    """Test sub-account discovery with main account credentials"""
    # Load environment variables
    load_dotenv(backend_path / '.env')
    
    # Get main account credentials
    api_key = os.getenv('BINANCE_MAIN_API_KEY')
    api_secret = os.getenv('BINANCE_MAIN_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Main account credentials not found in .env")
        print("Please set BINANCE_MAIN_API_KEY and BINANCE_MAIN_API_SECRET")
        return
    
    print("Testing Sub-Account Discovery")
    print("=" * 50)
    
    try:
        # Create client
        client = BinanceAPIClient(api_key, api_secret)
        
        # Test API connection first
        print("1. Testing API connection...")
        exchange_info = client.get_exchange_info()
        print("   ✅ API connection successful")
        
        # Try to fetch sub-accounts
        print("\n2. Fetching sub-accounts...")
        try:
            response = client.get_sub_account_list(limit=200)
            
            sub_accounts = response.get("subAccounts", [])
            print(f"   ✅ Found {len(sub_accounts)} sub-accounts")
            
            if sub_accounts:
                print("\n   Sub-Account List:")
                print("   " + "-" * 60)
                print(f"   {'Email':<40} {'Created':<20} {'Frozen'}")
                print("   " + "-" * 60)
                
                for sub in sub_accounts:
                    email = sub.get("email", "")
                    create_time = datetime.utcfromtimestamp(sub.get("createTime", 0) / 1000)
                    is_freeze = "Yes" if sub.get("isFreeze", False) else "No"
                    print(f"   {email:<40} {create_time.strftime('%Y-%m-%d %H:%M'):<20} {is_freeze}")
            else:
                print("   ℹ️  No sub-accounts found (this account may not have any sub-accounts)")
                
        except BinanceAPIError as e:
            if e.error_type == BinanceErrorType.API_KEY_INVALID:
                print("   ❌ This is not a master account or API key lacks permission")
                print("      Sub-account list is only available for master accounts")
            else:
                print(f"   ❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def test_workflow_simulation():
    """Simulate the complete onboarding workflow"""
    print("\n\nOnboarding Workflow Simulation")
    print("=" * 50)
    print("\n📋 Step 1: User enters main account API credentials")
    print("   - API Key: ****...****")
    print("   - API Secret: ****...****")
    
    print("\n📋 Step 2: System fetches sub-accounts")
    print("   - Calls /sapi/v1/sub-account/list")
    print("   - Displays list of sub-accounts with emails")
    
    print("\n📋 Step 3: User selects sub-accounts to include")
    print("   - Shows checkbox list of discovered sub-accounts")
    print("   - User enters API credentials for each selected sub-account")
    
    print("\n📋 Step 4: System stores encrypted credentials")
    print("   - Main account marked with is_main_account=True")
    print("   - Sub-accounts linked via parent_id")
    print("   - All credentials encrypted before storage")
    
    print("\n📋 Step 5: Daily monitoring")
    print("   - Celery task checks for new sub-accounts")
    print("   - Alerts sent if new sub-accounts found")


if __name__ == "__main__":
    print("Binance Sub-Account Discovery Test")
    print("=" * 70)
    
    # Run tests
    test_subaccount_discovery()
    test_workflow_simulation()
    
    print("\n✅ Test completed!")
    print("\nNote: If you see 'not a master account' error, it means:")
    print("- The API key belongs to a sub-account (not main/master)")
    print("- Only master accounts can list their sub-accounts")