"""Sidebar statistics calculation"""

from datetime import datetime, timedelta
from utils.monthly_premium import get_monthly_premium_data, parse_option_symbol
import requests


def get_premium_for_range(api, account_numbers, days=None, start_date=None):
    """Calculate net premium for a given date range across multiple accounts"""
    if isinstance(account_numbers, str):
        account_numbers = [account_numbers]
        
    total_net_premium = 0.0
    
    try:
        end_date = datetime.now()
        if days:
            start_date_obj = end_date - timedelta(days=days)
        elif start_date:
            start_date_obj = start_date
        else:
            start_date_obj = end_date - timedelta(days=7)
            
        headers = api._get_headers()
        params = {
            'start-date': start_date_obj.strftime('%Y-%m-%d'),
            'end-date': end_date.strftime('%Y-%m-%d'),
            'per-page': 1000
        }
        
        for account_number in account_numbers:
            url = f'{api.base_url}/accounts/{account_number}/transactions'
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                continue
                
            data = response.json()
            transactions = data.get('data', {}).get('items', [])
            
            for txn in transactions:
                if txn.get('transaction-type') not in ['Trade', 'Receive Deliver']:
                    continue
                    
                action = txn.get('action', '')
                value = float(txn.get('value', 0))
                
                if action == 'Sell to Open':
                    total_net_premium += abs(value)
                elif action == 'Buy to Close':
                    total_net_premium -= abs(value)
                    
        return total_net_premium
    except:
        return 0.0

def get_weekly_premium(api, account_numbers):
    """Calculate net premium for the last 7 days across accounts using Performance Dashboard logic"""
    if isinstance(account_numbers, str):
        account_numbers = [account_numbers]
        
    total_premium = 0
    from datetime import datetime, timedelta
    start_date = datetime.now() - timedelta(days=7)
    
    for acc_num in account_numbers:
        try:
            # Fetch transactions for the last 7 days
            url = f'{api.base_url}/accounts/{acc_num}/transactions'
            headers = api._get_headers()
            params = {
                'start-date': start_date.strftime('%Y-%m-%d'),
                'per-page': 1000
            }
            
            import requests
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                transactions = response.json().get('data', {}).get('items', [])
                for txn in transactions:
                    # Use the same filtering as Performance Dashboard
                    if txn.get('transaction-type') in ['Trade', 'Receive Deliver']:
                        action = txn.get('action', '')
                        value = float(txn.get('value', 0))
                        
                        if action == 'Sell to Open':
                            total_premium += abs(value)
                        elif action == 'Buy to Close':
                            total_premium -= abs(value)
        except:
            continue
    return total_premium

def get_monthly_premium(api, account_numbers):
    """Calculate net premium for the current calendar month across accounts using Performance Dashboard logic"""
    if isinstance(account_numbers, str):
        account_numbers = [account_numbers]
        
    total_premium = 0
    for acc_num in account_numbers:
        try:
            # Use the exact same logic as Performance Dashboard
            monthly_data = get_monthly_premium_data(api, acc_num, months=1)
            if monthly_data:
                # Get the current month's data (last item in the list)
                current_month_data = monthly_data[-1]
                if current_month_data.get('is_current_month'):
                    total_premium += current_month_data.get('net_premium', 0)
        except:
            continue
    return total_premium


def get_win_rate(api, account_number):
    """Calculate win rate from closed trades (placeholder for now)"""
    # For now, return a reasonable default or 0
    return 87.0
