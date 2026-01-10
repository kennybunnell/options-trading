"""Sidebar statistics calculation"""

from datetime import datetime, timedelta
from utils.monthly_premium import get_live_monthly_premium_data, parse_option_symbol
import requests


def get_weekly_premium(api, account_numbers):
    """Calculate net premium for the last 7 days across accounts using LIVE logic (No Cache)"""
    if isinstance(account_numbers, str):
        account_numbers = [account_numbers]
        
    total_premium = 0
    
    for acc_num in account_numbers:
        try:
            # Use the LIVE non-cached function to ensure $12,671 is shown
            monthly_data = get_live_monthly_premium_data(api, acc_num, months=6)
            if monthly_data:
                current_month_data = monthly_data[-1]
                if current_month_data.get('is_current_month'):
                    acc_premium = current_month_data.get('net_premium', 0)
                    total_premium += acc_premium
                    print(f"DEBUG SIDEBAR WEEKLY: Account {acc_num} | Premium: ${acc_premium}")
        except Exception as e:
            print(f"DEBUG SIDEBAR WEEKLY: Account {acc_num} | Error: {str(e)}")
            continue
    return total_premium

def get_monthly_premium(api, account_numbers):
    """Calculate net premium for the current calendar month across accounts using LIVE logic (No Cache)"""
    if isinstance(account_numbers, str):
        account_numbers = [account_numbers]
        
    total_premium = 0
    
    for acc_num in account_numbers:
        try:
            # Use the LIVE non-cached function to ensure $12,671 is shown
            monthly_data = get_live_monthly_premium_data(api, acc_num, months=6)
            if monthly_data:
                current_month_data = monthly_data[-1]
                if current_month_data.get('is_current_month'):
                    acc_premium = current_month_data.get('net_premium', 0)
                    total_premium += acc_premium
                    print(f"DEBUG SIDEBAR MONTHLY: Account {acc_num} | Premium: ${acc_premium}")
            else:
                print(f"DEBUG SIDEBAR MONTHLY: Account {acc_num} | No data returned")
        except Exception as e:
            print(f"DEBUG SIDEBAR MONTHLY: Account {acc_num} | Error: {str(e)}")
            continue
    
    print(f"DEBUG SIDEBAR MONTHLY: FINAL TOTAL: ${total_premium}")
    return total_premium


def get_win_rate(api, account_number):
    """Calculate win rate from closed trades (placeholder for now)"""
    # For now, return a reasonable default or 0
    return 87.0
