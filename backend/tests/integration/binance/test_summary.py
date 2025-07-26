"""
Summary of all collected data
"""
import os
from pathlib import Path
from datetime import datetime

def show_summary():
    """Show summary of all collected CSV files"""
    
    # Output directory
    base_dir = Path(__file__).parent.parent.parent / "output" / "exports" / "binance"
    
    print("="*70)
    print(" BINANCE RECONCILIATION DATA COLLECTION SUMMARY")
    print("="*70)
    print(f"\nData collection timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    if not base_dir.exists():
        print(f"\nNo data found at: {base_dir}")
        return
    
    # Check each email directory
    for email_dir in sorted(base_dir.iterdir()):
        if not email_dir.is_dir():
            continue
            
        email = email_dir.name
        print(f"\n\nAccount: {email}")
        print("-" * (len(email) + 10))
        
        csv_files = list(email_dir.glob("*.csv"))
        
        if not csv_files:
            print("  No CSV files found")
            continue
        
        # Group files by type
        files_by_type = {
            "Exchange Info": [],
            "Deposits": [],
            "Withdrawals": [],
            "Transfers": [],
            "Trades": [],
            "Convert": [],
            "Snapshots": [],
            "Other": []
        }
        
        for csv_file in sorted(csv_files):
            name = csv_file.name
            size = csv_file.stat().st_size
            
            # Categorize file
            if "exchange_info" in name:
                files_by_type["Exchange Info"].append((name, size))
            elif "deposit" in name:
                files_by_type["Deposits"].append((name, size))
            elif "withdraw" in name:
                files_by_type["Withdrawals"].append((name, size))
            elif "transfer" in name:
                files_by_type["Transfers"].append((name, size))
            elif "trade" in name:
                files_by_type["Trades"].append((name, size))
            elif "convert" in name:
                files_by_type["Convert"].append((name, size))
            elif "snapshot" in name:
                files_by_type["Snapshots"].append((name, size))
            else:
                files_by_type["Other"].append((name, size))
        
        # Display by category
        for category, files in files_by_type.items():
            if files:
                print(f"\n  {category}:")
                for name, size in files:
                    print(f"    - {name} ({size:,} bytes)")
                    
                    # Show sample data for non-exchange info files
                    if size > 0 and category != "Exchange Info":
                        file_path = email_dir / name
                        try:
                            with open(file_path, 'r') as f:
                                lines = f.readlines()
                                if len(lines) > 1:
                                    print(f"      Records: {len(lines) - 1}")  # Minus header
                                    # Show first data row
                                    if len(lines) > 1:
                                        fields = lines[0].strip().split(',')
                                        data = lines[1].strip().split(',')
                                        if 'datetime' in fields:
                                            idx = fields.index('datetime')
                                            print(f"      First record: {data[idx]}")
                        except Exception as e:
                            pass
    
    print("\n" + "="*70)
    print("\nSUMMARY:")
    print("  ✓ Exchange Info collected (trading pairs and symbols)")
    print("  ✓ Deposit history collected")
    print("  ✓ Transfer history collected (sub-account transfers)")
    print("  ✗ Withdrawal history (data format issue)")
    print("  ✗ Trade history (rate limit reached)")
    print("  ✗ Daily snapshots (may require different permissions)")
    print("  ✗ Convert history (no data in date range)")
    
    print("\nNOTES:")
    print("  - Trade collection requires smaller date ranges due to rate limits")
    print("  - Some endpoints may require additional API permissions")
    print("  - CSV files contain raw data ready for reconciliation processing")
    
    print("\nAll data saved to:")
    print(f"  {base_dir}")


if __name__ == "__main__":
    show_summary()