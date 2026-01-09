"""Sidebar statistics calculation"""

from datetime import datetime, timedelta
from utils.monthly_premium import get_monthly_premium_data, parse_option_symbol
import requests


def get_premium_for_range(api, account_number, days=None, start_date=None):
    """Calculate net premium for a given date range"""
    try:
        end_date = datetime.now()
        if days:
            start_date_obj = end_date - timedelta(days=days)
        elif start_date:
            start_date_obj = start_date
        else:
            start_date_obj = end_date - timedelta(days=7)
            
        url = f'{api.base_url}/accounts/{account_number}/transactions'
        headers = api._get_headers()
        
        params = {
            'start-date': start_date_obj.strftime('%Y-%m-%d'),
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
            
            if action == 'Sell to Open':
                net_premium += abs(value)
            elif action == 'Buy to Close':
                net_premium -= abs(value)
                
        return net_premium
    except:
        return 0.0

def get_weekly_premium(api, account_number):
    """Calculate net premium for the last 7 days"""
    return get_premium_for_range(api, account_number, days=7)

def get_monthly_premium(api, account_number):
    """Calculate net premium for the current calendar month"""
    now = datetime.now()
    first_day_of_month = datetime(now.year, now.month, 1)
    return get_premium_for_range(api, account_number, start_date=first_day_of_month)


def get_win_rate(api, account_number):
    """Calculate win rate from closed trades (placeholder for now)"""
    # For now, return a reasonable default or 0
    return 87.0
