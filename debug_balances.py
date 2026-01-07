"""
Debug script to see ALL available balance fields from Tastytrade API
"""

import sys
sys.path.append('/home/ubuntu/options-trading-github')

from utils.tastytrade_api import TastytradeAPI
import json

def debug_balances():
    """Check what balance fields are actually available"""
    
    api = TastytradeAPI()
    
    # Get all accounts
    accounts = api.get_accounts_with_names()
    
    print("=" * 80)
    print("TASTYTRADE API BALANCE FIELDS DEBUG")
    print("=" * 80)
    print()
    
    if not accounts:
        print("❌ No accounts found or authentication failed")
        return
    
    print(f"Found {len(accounts)} accounts:")
    for acc in accounts:
        print(f"  - {acc['display']}")
    print()
    
    # Check balance fields for each account
    for acc in accounts:
        account_number = acc['account_number']
        nickname = acc['nickname']
        
        print("=" * 80)
        print(f"ACCOUNT: {nickname} ({account_number})")
        print("=" * 80)
        print()
        
        balances = api.get_account_balances(account_number)
        
        if balances:
            print("📊 RAW API RESPONSE:")
            print(json.dumps(balances, indent=2))
            print()
            
            print("=" * 80)
            print("ALL FIELDS (sorted):")
            print("=" * 80)
            for key in sorted(balances.keys()):
                value = balances[key]
                if isinstance(value, (int, float)):
                    print(f"  {key:50s} = ${value:>15,.2f}")
                else:
                    print(f"  {key:50s} = {value}")
            print()
            
            # Look for buying power fields
            print("=" * 80)
            print("BUYING POWER RELATED FIELDS:")
            print("=" * 80)
            for key in balances.keys():
                if 'buying' in key.lower() or 'power' in key.lower():
                    value = balances[key]
                    if isinstance(value, (int, float)):
                        print(f"  ✅ {key:50s} = ${value:>15,.2f}")
                    else:
                        print(f"  ✅ {key:50s} = {value}")
            print()
            
        else:
            print("  ❌ Could not fetch balances for this account")
            print()

if __name__ == "__main__":
    try:
        debug_balances()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
