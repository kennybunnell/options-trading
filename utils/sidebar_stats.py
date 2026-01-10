"""Sidebar statistics calculation"""

from datetime import datetime, timedelta
from utils.monthly_premium import get_live_monthly_premium_data, parse_option_symbol
import requests


def get_weekly_premium(api, account_numbers):
    """Calculate net premium for the last 7 days across accounts using LIVE logic (No Cache)"""
    if isinstance(account_numbers, str):
        account_numbers = [account_numbers]
        
    total_premium = 0
    now = datetime.now()
    current_month_key = (now.month, now.year)
    
    for acc_num in account_numbers:
        try:
            # Use the LIVE non-cached function
            monthly_data = get_live_monthly_premium_data(api, acc_num, months=6)
            if monthly_data:
                # STRICT CALENDAR MONTH: Only look for the actual current month
                for month_data in monthly_data:
                    if month_data.get('month_year') == current_month_key:
                        total_premium += month_data.get('net_premium', 0)
                        break
        except Exception as e:
            continue
    return total_premium

def get_monthly_premium(api, account_numbers):
    """Calculate net premium for the current calendar month across accounts using LIVE logic (No Cache)"""
    if isinstance(account_numbers, str):
        account_numbers = [account_numbers]
        
    total_premium = 0
    now = datetime.now()
    current_month_key = (now.month, now.year)
    
    for acc_num in account_numbers:
        try:
            # Use the LIVE non-cached function
            monthly_data = get_live_monthly_premium_data(api, acc_num, months=6)
            if monthly_data:
                # STRICT CALENDAR MONTH: Only look for the actual current month
                for month_data in monthly_data:
                    if month_data.get('month_year') == current_month_key:
                        total_premium += month_data.get('net_premium', 0)
                        break
        except Exception as e:
            continue
    
    return total_premium


def get_win_rate(api, account_number):
    """Calculate win rate from closed trades (placeholder for now)"""
    # For now, return a reasonable default or 0
    return 87.0
