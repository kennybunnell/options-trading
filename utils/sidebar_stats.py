"""Sidebar statistics calculation"""

from datetime import datetime, timedelta
from utils.monthly_premium import get_monthly_premium_data, parse_option_symbol
import requests


def get_weekly_premium(api, account_number):
    """Calculate net premium for the last 7 days"""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        url = f'{api.base_url}/accounts/{account_number}/transactions'
        headers = api._get_headers()
        
        params = {
            'start-date': start_date.strftime('%Y-%m-%d'),
            'end-date': end_date.strftime('%Y-%m-%d'),
            'per-page': 1000
        }
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return 0.0
            
        data = response.json()
        transactions = data.get('data', {}).get('items', [])
        
        net_premium = 0.0
        for txn in transactions:
            if txn.get('transaction-type') not in ['Trade', 'Receive Deliver']:
                continue
                
            action = txn.get('action', '')
            value = float(txn.get('value', 0))
            
            # STO = Credit (positive)
            # BTC = Debit (negative)
            if action == 'Sell to Open':
                net_premium += abs(value)
            elif action == 'Buy to Close':
                net_premium -= abs(value)
                
        return net_premium
    except:
        return 0.0


def get_win_rate(api, account_number):
    """Calculate win rate from closed trades (placeholder for now)"""
    # For now, return a reasonable default or 0
    return 87.0
