"""
Test script to check what balance fields are available from Tastytrade API
"""

import sys
sys.path.append('/home/ubuntu/options-trading-github')

from utils.tastytrade_api import TastytradeAPI
import json

def test_balance_fields():
    """Check what balance fields are available for different account types"""
    
    print("=" * 80)
    print("TASTYTRADE BALANCE FIELDS TEST")
    print("=" * 80)
    print()
    
    api = TastytradeAPI()
    
    # Get all accounts
    accounts = api.get_accounts_with_names()
    
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
        
        balances = api.get_account_balances(account_number)
        
        if balances:
            print("\n📊 ALL AVAILABLE BALANCE FIELDS:\n")
            
            # Sort keys for easier reading
            for key in sorted(balances.keys()):
                value = balances[key]
                
                # Format numeric values as currency
                if isinstance(value, (int, float)):
                    print(f"  {key:40s} = ${value:>15,.2f}")
                else:
                    print(f"  {key:40s} = {value}")
            
            print("\n" + "=" * 80)
            print("KEY FIELDS FOR CSP TRADING:")
            print("=" * 80)
            
            # Extract key fields
            cash_balance = float(balances.get('cash-balance', 0))
            derivative_bp = float(balances.get('derivative-buying-power', 0))
            equity_bp = float(balances.get('equity-buying-power', 0))
            maintenance_excess = float(balances.get('maintenance-excess', 0))
            
            print(f"\n  Cash Balance:              ${cash_balance:>15,.2f}")
            print(f"  Derivative Buying Power:   ${derivative_bp:>15,.2f}")
            print(f"  Equity Buying Power:       ${equity_bp:>15,.2f}")
            print(f"  Maintenance Excess:        ${maintenance_excess:>15,.2f}")
            
            print("\n" + "-" * 80)
            print("ANALYSIS:")
            print("-" * 80)
            
            # Determine account type
            if 'IRA' in nickname.upper() or 'RETIREMENT' in nickname.upper():
                print("\n  🔍 Account Type: LIKELY IRA (Retirement)")
                print("\n  ⚠️  FOR CSP IN IRA:")
                print("      - Should use: cash-balance (cash-only, no margin)")
                print("      - Must have actual cash to cover strike × 100 × contracts")
                print(f"      - Available for CSP: ${cash_balance:,.2f}")
            else:
                print("\n  🔍 Account Type: LIKELY MARGIN ACCOUNT")
                print("\n  💡 FOR CSP IN MARGIN ACCOUNT:")
                print("      - Can use: derivative-buying-power (includes margin)")
                print("      - OR use: cash-balance if you want to avoid margin")
                print(f"      - Available (with margin): ${derivative_bp:,.2f}")
                print(f"      - Available (cash-only): ${cash_balance:,.2f}")
            
            # Check if derivative BP > cash (indicates margin)
            if derivative_bp > cash_balance * 1.1:  # 10% buffer for rounding
                margin_amount = derivative_bp - cash_balance
                print(f"\n  ⚠️  MARGIN DETECTED: ${margin_amount:,.2f} of buying power is from margin")
                print("      Using derivative-buying-power WILL allow margin usage!")
            else:
                print("\n  ✅ No significant margin detected")
            
            print()
        else:
            print("  ❌ Could not fetch balances for this account")
            print()

if __name__ == "__main__":
    try:
        test_balance_fields()
        
        print("\n" + "=" * 80)
        print("RECOMMENDATION FOR CSP DASHBOARD:")
        print("=" * 80)
        print("""
For Cash-Secured Puts, you should:

1. IRA Accounts (Traditional IRA, Roth IRA):
   ✅ Use: cash-balance
   ❌ Never use: derivative-buying-power (not applicable in IRA anyway)
   
2. Margin Accounts (if you want to AVOID margin):
   ✅ Use: cash-balance
   ❌ Avoid: derivative-buying-power (includes margin)
   
3. Margin Accounts (if you're OK with margin):
   ✅ Use: derivative-buying-power
   ⚠️  Warning: This allows margin usage!

CURRENT CSP DASHBOARD ISSUE:
❌ Currently uses: derivative-buying-power for ALL accounts
✅ Should use: cash-balance (to avoid margin) OR make it configurable

SUGGESTED FIX:
- Add user preference: "Avoid Margin for CSP" (default: ON)
- When ON: use cash-balance
- When OFF: use derivative-buying-power
- Show clear warning when margin would be used
        """)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
