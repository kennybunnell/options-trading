"""
Debug Script: January 2026 Premium Analysis
Queries Tastytrade API directly to show all January transactions
"""

import os
import sys
from datetime import datetime
from utils.tastytrade_api import TastytradeAPI
from utils.monthly_premium import parse_option_symbol

def main():
    print("=" * 80)
    print("🔍 JANUARY 2026 PREMIUM DEBUG SCRIPT")
    print("=" * 80)
    
    # Initialize API
    api = TastytradeAPI()
    
    # Get accounts
    accounts = api.get_accounts_with_names()
    
    if not accounts:
        print("❌ No accounts found")
        return
    
    # Use first account or let user select
    if len(accounts) == 1:
        account = accounts[0]
    else:
        print("\n📋 Available Accounts:")
        for idx, acc in enumerate(accounts, 1):
            print(f"  {idx}. {acc['display']}")
        
        choice = input("\nSelect account (1-{}): ".format(len(accounts)))
        try:
            account = accounts[int(choice) - 1]
        except:
            print("❌ Invalid selection")
            return
    
    account_number = account['account_number']
    print(f"\n✅ Using account: {account['display']}")
    print(f"   Account Number: {account_number}")
    
    # Query January 2026 transactions
    print("\n" + "=" * 80)
    print("📅 QUERYING JANUARY 2026 TRANSACTIONS")
    print("=" * 80)
    
    url = f'{api.base_url}/accounts/{account_number}/transactions'
    headers = api._get_headers()
    
    params = {
        'start-date': '2026-01-01',
        'end-date': '2026-01-31',
        'per-page': 1000
    }
    
    import requests
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"❌ Failed to get transactions: {response.status_code}")
        return
    
    data = response.json()
    transactions = data.get('data', {}).get('items', [])
    
    print(f"\n✅ Total transactions in January 2026: {len(transactions)}")
    
    # Filter for option trades
    option_trades = []
    
    for txn in transactions:
        txn_type = txn.get('transaction-type', '')
        if txn_type not in ['Trade', 'Receive Deliver']:
            continue
        
        symbol = txn.get('symbol', '')
        action = txn.get('action', '')
        value = float(txn.get('value', 0))
        executed_at = txn.get('executed-at', '')
        
        # Check if it's an option
        option_info = parse_option_symbol(symbol)
        if option_info:
            option_trades.append({
                'symbol': symbol,
                'action': action,
                'value': value,
                'executed_at': executed_at,
                'option_type': option_info['option_type'],
                'underlying': option_info['underlying'],
                'strike': option_info['strike']
            })
    
    print(f"✅ Option trades found: {len(option_trades)}")
    
    # Categorize trades
    csp_credits = []
    csp_debits = []
    cc_credits = []
    cc_debits = []
    
    for trade in option_trades:
        if trade['action'] == 'Sell to Open':
            if trade['option_type'] == 'PUT':
                csp_credits.append(trade)
            elif trade['option_type'] == 'CALL':
                cc_credits.append(trade)
        elif trade['action'] == 'Buy to Close':
            if trade['option_type'] == 'PUT':
                csp_debits.append(trade)
            elif trade['option_type'] == 'CALL':
                cc_debits.append(trade)
    
    # Display results
    print("\n" + "=" * 80)
    print("💰 CSP TRANSACTIONS (Cash-Secured Puts)")
    print("=" * 80)
    
    print(f"\n✅ CSP Credits (Sell to Open) - {len(csp_credits)} transactions:")
    csp_credit_total = 0
    for trade in csp_credits:
        print(f"   • {trade['underlying']:6s} ${trade['strike']:7.2f}P  ${abs(trade['value']):8,.2f}  {trade['executed_at'][:10]}")
        csp_credit_total += abs(trade['value'])
    print(f"   {'':20s} TOTAL: ${csp_credit_total:,.2f}")
    
    print(f"\n❌ CSP Debits (Buy to Close) - {len(csp_debits)} transactions:")
    csp_debit_total = 0
    for trade in csp_debits:
        print(f"   • {trade['underlying']:6s} ${trade['strike']:7.2f}P  ${abs(trade['value']):8,.2f}  {trade['executed_at'][:10]}")
        csp_debit_total += abs(trade['value'])
    print(f"   {'':20s} TOTAL: ${csp_debit_total:,.2f}")
    
    csp_net = csp_credit_total - csp_debit_total
    print(f"\n💵 CSP NET PREMIUM: ${csp_net:,.2f}")
    
    print("\n" + "=" * 80)
    print("💰 CC TRANSACTIONS (Covered Calls)")
    print("=" * 80)
    
    print(f"\n✅ CC Credits (Sell to Open) - {len(cc_credits)} transactions:")
    cc_credit_total = 0
    for trade in cc_credits:
        print(f"   • {trade['underlying']:6s} ${trade['strike']:7.2f}C  ${abs(trade['value']):8,.2f}  {trade['executed_at'][:10]}")
        cc_credit_total += abs(trade['value'])
    print(f"   {'':20s} TOTAL: ${cc_credit_total:,.2f}")
    
    print(f"\n❌ CC Debits (Buy to Close) - {len(cc_debits)} transactions:")
    cc_debit_total = 0
    for trade in cc_debits:
        print(f"   • {trade['underlying']:6s} ${trade['strike']:7.2f}C  ${abs(trade['value']):8,.2f}  {trade['executed_at'][:10]}")
        cc_debit_total += abs(trade['value'])
    print(f"   {'':20s} TOTAL: ${cc_debit_total:,.2f}")
    
    cc_net = cc_credit_total - cc_debit_total
    print(f"\n💵 CC NET PREMIUM: ${cc_net:,.2f}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 JANUARY 2026 SUMMARY")
    print("=" * 80)
    
    total_net = csp_net + cc_net
    
    print(f"\n  CSP Net:   ${csp_net:>12,.2f}")
    print(f"  CC Net:    ${cc_net:>12,.2f}")
    print(f"  " + "-" * 30)
    print(f"  TOTAL NET: ${total_net:>12,.2f}")
    
    if total_net < 0:
        print(f"\n⚠️  NEGATIVE NET: You paid more in buybacks than you collected in new premium")
        print(f"    This could mean:")
        print(f"    • More positions closed than opened in January")
        print(f"    • Buybacks cost more than new premium collected")
        print(f"    • Defensive management (closing losing positions)")
    
    print("\n" + "=" * 80)
    print("✅ DEBUG COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
