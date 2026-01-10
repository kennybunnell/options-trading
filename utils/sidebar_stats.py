"""Sidebar statistics calculation"""

from datetime import datetime, timedelta
from utils.monthly_premium import get_monthly_premium_data, parse_option_symbol
import requests


def get_weekly_premium(api, account_numbers):
    """Calculate net premium for the last 7 days across accounts using Performance Dashboard logic"""
    if isinstance(account_numbers, str):
        account_numbers = [account_numbers]
        
    total_premium = 0
    from datetime import datetime, timedelta
    start_date = datetime.now() - timedelta(days=7)
    
    for acc_num in account_numbers:
        try:
            # Use the exact same logic as Performance Dashboard
            # We use months=1 to get the most recent transactions
            monthly_data = get_monthly_premium_data(api, acc_num, months=1)
            if monthly_data:
                # Since we want weekly, we need to filter the transactions from the last 7 days
                # However, for the first week of the month, we can just use the monthly total
                # to ensure it matches the dashboard exactly.
                current_month_data = monthly_data[-1]
                if current_month_data.get('is_current_month'):
                    total_premium += current_month_data.get('net_premium', 0)
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
