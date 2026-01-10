"""
Monthly Premium Calculator
Calculates net premium earnings (credits - debits) grouped by month
for both CSPs and Covered Calls
"""

import requests
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
import re


def parse_option_symbol(symbol: str) -> Dict:
    """Parse OCC option symbol to extract components"""
    try:
        clean_symbol = symbol.replace(' ', '')
        match = re.match(r'([A-Z]+)(\d{6})([CP])(\d+)', clean_symbol)
        if match:
            underlying = match.group(1)
            date_str = match.group(2)
            option_type = 'PUT' if match.group(3) == 'P' else 'CALL'
            strike = int(match.group(4)) / 1000
            return {
                'underlying': underlying,
                'option_type': option_type,
                'strike': strike
            }
    except Exception as e:
        pass
    return None


import streamlit as st

def get_live_monthly_premium_data(api, account_number: str, months: int = 6) -> List[Dict]:
    """
    NON-CACHED version of premium data retrieval for sidebar accuracy.
    """
    # Calculate date range - Align to the 1st of the month for strict calendar tracking
    now = datetime.now()
    # Go back to the 1st of the current month, then subtract N months
    first_of_current = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate start date by going back N months
    start_month = now.month - months + 1
    start_year = now.year
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = datetime(start_year, start_month, 1)
    end_date = now
    
    # Get transactions from Tastytrade API
    try:
        url = f'{api.base_url}/accounts/{account_number}/transactions'
        headers = api._get_headers()
        
        params = {
            'start-date': start_date.strftime('%Y-%m-%d'),
            'end-date': end_date.strftime('%Y-%m-%d'),
            'per-page': 1000  # Get all transactions
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        transactions = data.get('data', {}).get('items', [])
        
    except Exception as e:
        return []
    
    # Group transactions by month and calculate net premium
    monthly_data = defaultdict(lambda: {
        'csp_credits': 0.0,
        'csp_debits': 0.0,
        'cc_credits': 0.0,
        'cc_debits': 0.0
    })
    
    total_processed = 0
    for txn in transactions:
        # DEBUG: Log every transaction to find the missing $2,172
        t_type = txn.get('transaction-type')
        symbol = txn.get('symbol', '')
        action = txn.get('action', '')
        value = float(txn.get('value', 0))
        executed_at = txn.get('executed-at', '')
        
        if t_type not in ['Trade', 'Receive Deliver']:
            continue
        
        if not executed_at:
            continue
        
        try:
            txn_date = datetime.fromisoformat(executed_at.replace('Z', '+00:00'))
            month_key = (txn_date.month, txn_date.year)
        except:
            continue
        
        option_info = parse_option_symbol(symbol)
        if not option_info:
            continue
        
        option_type = option_info['option_type']
        
        if action == 'Sell to Open':
            if option_type == 'PUT':
                monthly_data[month_key]['csp_credits'] += abs(value)

            elif option_type == 'CALL':
                monthly_data[month_key]['cc_credits'] += abs(value)

        elif action == 'Buy to Close':
            if option_type == 'PUT':
                monthly_data[month_key]['csp_debits'] += abs(value)

            elif option_type == 'CALL':
                monthly_data[month_key]['cc_debits'] += abs(value)

    
    # Generate list of last N months using proper calendar math
    now = datetime.now()
    month_list = []
    
    for i in range(months - 1, -1, -1):
        # Calculate the year and month correctly
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        month_key = (m, y)
        month_list.append(month_key)
    
    # Build result list
    results = []
    for month_key in month_list:
        month, year = month_key
        data = monthly_data[month_key]
        csp_net = data['csp_credits'] - data['csp_debits']
        cc_net = data['cc_credits'] - data['cc_debits']
        total_net = csp_net + cc_net
        is_current = (month == now.month and year == now.year)
        month_name = datetime(year, month, 1).strftime('%b %Y')
        
        results.append({
            'month_name': month_name,
            'month_year': month_key,
            'is_current_month': is_current,
            'net_premium': total_net,
            'csp_net': csp_net,
            'cc_net': cc_net
        })
    return results

def get_monthly_premium_data(api, account_number: str, months: int = 6) -> List[Dict]:
    """
    Get monthly premium data for the last N months
    
    Args:
        api: TastytradeAPI instance
        account_number: Account number to query
        months: Number of months to retrieve (default 6)
    
    Returns:
        List of dicts with monthly premium data, ordered from oldest to newest
        Each dict contains:
        - month_name: "Aug 2025"
        - month_year: (8, 2025)
        - is_current_month: bool
        - net_premium: float (total CSP + CC net)
        - csp_net: float
        - cc_net: float
        - csp_percentage: float
        - cc_percentage: float
        - pct_change: float (vs previous month)
    """
    
    # Calculate date range - Align to the 1st of the month for strict calendar tracking
    now = datetime.now()
    # Go back to the 1st of the current month, then subtract N months
    first_of_current = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate start date by going back N months
    start_month = now.month - months + 1
    start_year = now.year
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = datetime(start_year, start_month, 1)
    end_date = now
    
    # Get transactions from Tastytrade API
    try:
        url = f'{api.base_url}/accounts/{account_number}/transactions'
        headers = api._get_headers()
        
        params = {
            'start-date': start_date.strftime('%Y-%m-%d'),
            'end-date': end_date.strftime('%Y-%m-%d'),
            'per-page': 1000  # Get all transactions
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Failed to get transactions: {response.status_code}")
            return []
        
        data = response.json()
        transactions = data.get('data', {}).get('items', [])
        
    except Exception as e:
        print(f"Error fetching transactions: {str(e)}")
        return []
    
    # Group transactions by month and calculate net premium
    monthly_data = defaultdict(lambda: {
        'csp_credits': 0.0,
        'csp_debits': 0.0,
        'cc_credits': 0.0,
        'cc_debits': 0.0
    })
    
    for txn in transactions:
        # Only process option trades
        if txn.get('transaction-type') not in ['Trade', 'Receive Deliver']:
            continue
        
        # Get transaction details
        symbol = txn.get('symbol', '')
        action = txn.get('action', '')
        value = float(txn.get('value', 0))
        executed_at = txn.get('executed-at', '')
        
        if not executed_at:
            continue
        
        # Parse date
        try:
            txn_date = datetime.fromisoformat(executed_at.replace('Z', '+00:00'))
            month_key = (txn_date.month, txn_date.year)
        except:
            continue
        
        # Parse option symbol to determine type
        option_info = parse_option_symbol(symbol)
        if not option_info:
            continue
        
        option_type = option_info['option_type']
        
        # Determine if CSP or CC and credit/debit
        # Sell to Open (STO) = Credit
        # Buy to Close (BTC) = Debit
        
        if action == 'Sell to Open':
            # Opening credit
            if option_type == 'PUT':
                monthly_data[month_key]['csp_credits'] += abs(value)
            elif option_type == 'CALL':
                monthly_data[month_key]['cc_credits'] += abs(value)
        
        elif action == 'Buy to Close':
            # Closing debit
            if option_type == 'PUT':
                monthly_data[month_key]['csp_debits'] += abs(value)
            elif option_type == 'CALL':
                monthly_data[month_key]['cc_debits'] += abs(value)
    
    # Generate list of last N months using proper calendar math
    now = datetime.now()
    month_list = []
    
    for i in range(months - 1, -1, -1):
        # Calculate the year and month correctly
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        month_key = (m, y)
        month_list.append(month_key)
    
    # Build result list
    results = []
    prev_net = None
    
    for idx, month_key in enumerate(month_list):
        month, year = month_key
        data = monthly_data[month_key]
        
        # Calculate net premiums
        csp_net = data['csp_credits'] - data['csp_debits']
        cc_net = data['cc_credits'] - data['cc_debits']
        total_net = csp_net + cc_net
        
        # Calculate percentages
        if total_net > 0:
            csp_pct = (csp_net / total_net) * 100
            cc_pct = (cc_net / total_net) * 100
        else:
            csp_pct = 0
            cc_pct = 0
        
        # Calculate month-over-month change
        if prev_net is not None and prev_net > 0:
            pct_change = ((total_net - prev_net) / prev_net) * 100
        else:
            pct_change = 0
        
        # Check if current month - STRICT CALENDAR CHECK
        is_current = (month == now.month and year == now.year)
        
        # Month name
        month_name = datetime(year, month, 1).strftime('%b %Y')
        
        results.append({
            'month_name': month_name,
            'month_year': month_key,
            'is_current_month': is_current,
            'net_premium': total_net,
            'csp_net': csp_net,
            'cc_net': cc_net,
            'csp_percentage': csp_pct,
            'cc_percentage': cc_pct,
            'pct_change': pct_change
        })
        
        prev_net = total_net
    
    return results


def render_monthly_premium_summary(api, account_number: str = None, all_accounts: bool = False):
    """
    Render the Monthly Premium Summary component in Streamlit
    
    Args:
        api: TastytradeAPI instance
        account_number: Account number to query (if all_accounts=False)
        all_accounts: If True, aggregate data from all accounts
    """
    import streamlit as st
    from collections import defaultdict
    
    # Premium section header
    if all_accounts:
        st.markdown('<div class="section-header">💰 MONTHLY PREMIUM PERFORMANCE (ALL ACCOUNTS)</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-header">💰 MONTHLY PREMIUM PERFORMANCE</div>', unsafe_allow_html=True)
    
    # Get data
    if all_accounts:
        # Get all accounts
        accounts = api.get_accounts()
        if not accounts:
            st.warning("⚠️ No accounts found.")
            return
        
        # Aggregate data from all accounts
        aggregated_data = defaultdict(lambda: {
            'net_premium': 0,
            'csp_net': 0,
            'cc_net': 0,
            'pct_change': 0
        })
        
        # Get current month/year for strict filtering
        now = datetime.now()
        current_month_key = (now.month, now.year)
        print(f"DEBUG DASHBOARD: Current month key = {current_month_key}")
        
        for account in accounts:
            account_num = account.get('account', {}).get('account-number')
            if account_num:
                # Get the raw 6-month data for this account
                account_months = get_monthly_premium_data(api, account_num, months=6)
                for month_data in account_months:
                    # Use the month_year tuple (month, year) as the unique key for aggregation
                    # This prevents December data from being mixed into January
                    m_year_key = month_data['month_year']
                    month_name = month_data['month_name']
                    
                    # Initialize if not exists
                    if month_name not in aggregated_data:
                        aggregated_data[month_name] = {
                            'net_premium': 0,
                            'csp_net': 0,
                            'cc_net': 0,
                            'month_year': m_year_key,
                            'is_current_month': (m_year_key == current_month_key)
                        }
                    
                    # Aggregate data into the correct calendar month bucket
                    aggregated_data[month_name]['net_premium'] += month_data['net_premium']
                    aggregated_data[month_name]['csp_net'] += month_data['csp_net']
                    aggregated_data[month_name]['cc_net'] += month_data['cc_net']
                    print(f"DEBUG DASHBOARD: Account {account_num} | Month {month_name} | m_year_key={m_year_key} | Premium={month_data['net_premium']}")
        
        # Convert to list format
        months_data = []
        prev_net = None
        
        # Get current month/year for strict display labeling
        now = datetime.now()
        current_month_key = (now.month, now.year)
        
        # Sort by month_year to ensure chronological order
        sorted_months = sorted(aggregated_data.keys(), key=lambda x: aggregated_data[x]['month_year'])
        
        for month_name in sorted_months:
            data = aggregated_data[month_name]
            m_year_key = data['month_year']
            total_net = data['net_premium']
            csp_net = data['csp_net']
            cc_net = data['cc_net']
            
            # Calculate percentages
            if total_net > 0:
                csp_pct = (csp_net / total_net) * 100
                cc_pct = (cc_net / total_net) * 100
            else:
                csp_pct = 0
                cc_pct = 0
            
            # Calculate month-over-month change
            if prev_net is not None and prev_net > 0:
                pct_change = ((total_net - prev_net) / prev_net) * 100
            else:
                pct_change = 0
            
            # STRICT CALENDAR MONTH CHECK FOR DISPLAY
            is_current = (m_year_key == current_month_key)
            
            months_data.append({
                'month_name': month_name,
                'month_year': m_year_key,
                'is_current_month': is_current,
                'net_premium': total_net,
                'csp_net': csp_net,
                'cc_net': cc_net,
                'csp_percentage': csp_pct,
                'cc_percentage': cc_pct,
                'pct_change': pct_change
            })
            print(f"DEBUG DASHBOARD FINAL: {month_name} | is_current={is_current} | total={total_net}")
            prev_net = total_net
    else:
        months_data = get_monthly_premium_data(api, account_number, months=6)
    
    if not months_data:
        st.warning("⚠️ No premium data available. Please upload your activity file in the 'Import Data' tab.")
        return
    
    # Display cards in columns
    cols = st.columns(6)
    
    for idx, month_data in enumerate(months_data):
        with cols[idx]:
            # Month name
            month_name = month_data['month_name']
            is_current = month_data['is_current_month']
            
            if is_current:
                st.markdown(f"**{month_name}**")
                st.caption("(MTD)")
            else:
                st.markdown(f"**{month_name}**")
            
            # Net premium
            net_premium = month_data['net_premium']
            pct_change = month_data['pct_change']
            
            # DEBUG: Print what's being rendered
            print(f"DEBUG UI RENDER: {month_name} | is_current={is_current} | net_premium={net_premium}")
            
            # Show metric with delta
            if is_current:
                st.metric(
                    label="Net Premium",
                    value=f"${net_premium:,.0f}",
                    label_visibility="collapsed"
                )
            else:
                st.metric(
                    label="Net Premium",
                    value=f"${net_premium:,.0f}",
                    delta=f"{pct_change:+.0f}%" if idx > 0 else None,
                    label_visibility="collapsed"
                )
            
            # Breakdown
            csp_pct = month_data['csp_percentage']
            cc_pct = month_data['cc_percentage']
            st.caption(f"CSP: {csp_pct:.0f}%")
            st.caption(f"CC: {cc_pct:.0f}%")
    
    # Summary row
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_6mo = sum([m['net_premium'] for m in months_data])
        st.metric("6-Month Total", f"${total_6mo:,.0f}")
    
    with col2:
        avg_monthly = total_6mo / 6 if len(months_data) == 6 else 0
        st.metric("Avg/Month", f"${avg_monthly:,.0f}")
    
    with col3:
        if months_data:
            best_month = max(months_data, key=lambda x: x['net_premium'])
            st.metric(
                "Best Month", 
                best_month['month_name'],
                delta=f"${best_month['net_premium']:,.0f}",
                delta_color="off"
            )
    
    with col4:
        avg_csp_pct = sum([m['csp_percentage'] for m in months_data]) / len(months_data) if months_data else 0
        avg_cc_pct = 100 - avg_csp_pct
        st.metric("Avg CSP/CC", f"{avg_csp_pct:.0f}% / {avg_cc_pct:.0f}%")
    
    st.divider()
