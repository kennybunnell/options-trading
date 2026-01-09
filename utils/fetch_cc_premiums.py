"""Fetch and calculate CC premiums from Tastytrade transaction history"""

import json
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict


def parse_option_symbol(symbol: str):
    """Parse OCC option symbol to extract underlying"""
    try:
        clean_symbol = symbol.replace(' ', '')
        match = re.match(r'([A-Z]+)(\d{6})([CP])(\d+)', clean_symbol)
        if match:
            return match.group(1)  # Return underlying symbol
    except:
        pass
    return None


def fetch_and_save_cc_premiums(api, lookback_days=365):
    """
    Fetch CC premiums from Tastytrade transaction history
    
    Args:
        api: TastytradeAPI instance
        lookback_days: Number of days to look back (default 365)
        
    Returns:
        dict: Premium data by symbol
    """
    print(f"\n=== Fetching CC Premium Data (last {lookback_days} days) ===")
    
    # Get all accounts
    accounts = api.get_accounts_with_names()
    if not accounts:
        print("No accounts found")
        return None
    
    # Track premiums by underlying symbol
    cc_premiums = defaultdict(float)
    csp_premiums = defaultdict(float)
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print(f"Date range: {start_str} to {end_str}")
    
    # Fetch transactions from all accounts
    for acc in accounts:
        account_number = acc['account_number']
        account_name = acc.get('nickname', account_number)
        
        print(f"\nFetching transactions for account: {account_name}")
        
        transactions = api.get_transactions(account_number, start_str, end_str)
        
        if not transactions:
            print(f"  No transactions found")
            continue
        
        print(f"  Found {len(transactions)} transactions")
        
        # Debug: Show first transaction structure
        if transactions and len(transactions) > 0:
            print(f"\n  DEBUG: First transaction structure:")
            first_txn = transactions[0]
            for key in ['transaction-type', 'transaction-sub-type', 'action', 'symbol', 'underlying-symbol', 'instrument-type', 'value', 'quantity']:
                print(f"    {key}: {first_txn.get(key, 'NOT FOUND')}")
        
        # Process transactions
        for txn in transactions:
            # Look for option trades
            txn_type = txn.get('transaction-type', '')
            txn_sub_type = txn.get('transaction-sub-type', '')
            
            # We want "Trade" transactions with "Sell to Open" sub-type
            if txn_type == 'Trade' and txn_sub_type == 'Sell to Open':
                # Get transaction details
                symbol = txn.get('symbol', '')
                underlying = txn.get('underlying-symbol', '')
                
                # Parse underlying from option symbol if not provided
                if not underlying and symbol:
                    underlying = parse_option_symbol(symbol)
                
                if not underlying:
                    continue
                
                # Get option type (PUT or CALL)
                option_type = txn.get('option-type', '').upper()
                
                # Get premium (value should be positive for credit received)
                value = float(txn.get('value', 0))
                quantity = abs(int(float(txn.get('quantity', 0))))
                
                # Premium is the credit received (positive value)
                premium = abs(value)
                
                if premium > 0:
                    if option_type == 'CALL':
                        cc_premiums[underlying] += premium
                        print(f"    ✅ CC: {underlying} - ${premium:.2f}")
                    elif option_type == 'PUT':
                        csp_premiums[underlying] += premium
                        print(f"    ✅ CSP: {underlying} - ${premium:.2f}")
    
    # Calculate totals
    total_cc = sum(cc_premiums.values())
    total_csp = sum(csp_premiums.values())
    
    print(f"\n=== Summary ===")
    print(f"Total CC Premium: ${total_cc:,.2f}")
    print(f"Total CSP Premium: ${total_csp:,.2f}")
    print(f"CC Symbols: {len(cc_premiums)}")
    print(f"CSP Symbols: {len(csp_premiums)}")
    
    # Save to JSON
    premium_data = {
        'cc_premiums': dict(cc_premiums),
        'csp_premiums': dict(csp_premiums),
        'total_cc': total_cc,
        'total_csp': total_csp,
        'last_updated': datetime.now().isoformat(),
        'lookback_days': lookback_days
    }
    
    premium_file = '/home/ubuntu/premium_summary.json'
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(premium_file), exist_ok=True)
        
        with open(premium_file, 'w') as f:
            json.dump(premium_data, f, indent=2)
        print(f"\n✅ Saved premium data to {premium_file}")
    except Exception as e:
        print(f"\n❌ Error saving premium data: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    return premium_data
