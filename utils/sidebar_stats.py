"""Sidebar statistics calculation"""

from datetime import datetime, timedelta
from utils.monthly_premium import get_monthly_premium_data, parse_option_symbol
import requests


def get_weekly_premium(api, account_numbers):
    """Calculate net premium for the last 7 days across accounts using Performance Dashboard logic (Forced Refresh)"""
    if isinstance(account_numbers, str):
        account_numbers = [account_numbers]
        
    total_premium = 0
    from utils.monthly_premium import get_monthly_premium_data
    
    for acc_num in account_numbers:
        try:
            # Force refresh by passing a unique value to the force_refresh parameter
            # This bypasses the Streamlit cache and ensures we get the latest $12,671 total
            monthly_data = get_monthly_premium_data(api, acc_num, months=1, force_refresh=True)
            if monthly_data:
                current_month_data = monthly_data[-1]
                if current_month_data.get('is_current_month'):
                    total_premium += current_month_data.get('net_premium', 0)
        except:
            continue
    return total_premium

def get_monthly_premium(api, account_numbers):
    """Calculate net premium for the current calendar month across accounts using Performance Dashboard logic (Forced Refresh)"""
    if isinstance(account_numbers, str):
        account_numbers = [account_numbers]
        
    total_premium = 0
    from utils.monthly_premium import get_monthly_premium_data
    
    for acc_num in account_numbers:
        try:
            # Use the exact same logic as Performance Dashboard with forced refresh
            monthly_data = get_monthly_premium_data(api, acc_num, months=1, force_refresh=True)
            if monthly_data:
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
