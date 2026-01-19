"""Sidebar statistics calculation"""

from datetime import datetime, timedelta
from utils.monthly_premium import get_live_monthly_premium_data, parse_option_symbol
import requests


def get_weekly_premium(api, account_numbers):
    """Calculate net premium for the CURRENT WEEK (Monday-Sunday) across accounts"""
    if isinstance(account_numbers, str):
        account_numbers = [account_numbers]
        
    total_premium = 0
    now = datetime.now()
    
    # Calculate start of current week (Monday)
    days_since_monday = now.weekday()  # Monday=0, Sunday=6
    week_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    for acc_num in account_numbers:
        try:
            # Get transaction history for the account
            transactions = api.get_transactions(acc_num)
            
            if transactions:
                for txn in transactions:
                    # Parse transaction date
                    txn_date_str = txn.get('executed-at') or txn.get('transaction-date')
                    if not txn_date_str:
                        continue
                    
                    # Parse the date (handle ISO format)
                    try:
                        if 'T' in txn_date_str:
                            txn_date = datetime.fromisoformat(txn_date_str.replace('Z', '+00:00'))
                        else:
                            txn_date = datetime.strptime(txn_date_str, '%Y-%m-%d')
                    except:
                        continue
                    
                    # Check if transaction is in current week
                    if txn_date >= week_start:
                        # Get transaction value (premium collected/paid)
                        value = txn.get('value', 0)
                        action = txn.get('action', '')
                        
                        # For options: STO (Sell to Open) = credit, BTC (Buy to Close) = debit
                        if action in ['Sell to Open', 'STO']:
                            total_premium += abs(value)
                        elif action in ['Buy to Close', 'BTC']:
                            total_premium -= abs(value)
                            
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
