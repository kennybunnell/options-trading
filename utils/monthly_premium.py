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


def get_monthly_premium_data(api, account_number: str, months: int = 6, debug: bool = False) -> List[Dict]:
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
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 31)  # Approximate
    
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
    
    if debug:
        print(f"\n=== MONTHLY PREMIUM DEBUG ===")
        print(f"Total transactions fetched: {len(transactions)}")
        print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"\n=== PROCESSING TRANSACTIONS ===")
    
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
            if debug and symbol:  # Only log if there's a symbol
                print(f"  ⚠️  Could not parse symbol: {symbol}")
            continue
        
        option_type = option_info['option_type']
        
        # Debug logging for January 2026 transactions
        if debug and month_key == (1, 2026):
            print(f"\n  📅 Jan 2026 Transaction:")
            print(f"     Symbol: {symbol}")
            print(f"     Type: {option_type}")
            print(f"     Action: {action}")
            print(f"     Value: ${abs(value):,.2f}")
            print(f"     Date: {executed_at}")
        
        # Determine if CSP or CC and credit/debit
        # Sell to Open (STO) = Credit
        # Buy to Close (BTC) = Debit
        
        if action == 'Sell to Open':
            # Opening credit
            if option_type == 'PUT':
                monthly_data[month_key]['csp_credits'] += abs(value)
                if debug and month_key == (1, 2026):
                    print(f"     ✅ Added to CSP Credits")
            elif option_type == 'CALL':
                monthly_data[month_key]['cc_credits'] += abs(value)
                if debug and month_key == (1, 2026):
                    print(f"     ✅ Added to CC Credits")
        
        elif action == 'Buy to Close':
            # Closing debit
            if option_type == 'PUT':
                monthly_data[month_key]['csp_debits'] += abs(value)
                if debug and month_key == (1, 2026):
                    print(f"     ❌ Added to CSP Debits")
            elif option_type == 'CALL':
                monthly_data[month_key]['cc_debits'] += abs(value)
                if debug and month_key == (1, 2026):
                    print(f"     ❌ Added to CC Debits")
    
    # Generate list of last N months
    current_date = datetime.now()
    month_list = []
    
    for i in range(months - 1, -1, -1):
        target_date = current_date - timedelta(days=i * 31)
        month_key = (target_date.month, target_date.year)
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
        
        # Check if current month
        is_current = (month == current_date.month and year == current_date.year)
        
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


def render_monthly_premium_summary(api, account_number: str):
    """
    Render the Monthly Premium Summary component in Streamlit
    
    Args:
        api: TastytradeAPI instance
        account_number: Account number to query
    """
    import streamlit as st
    
    st.subheader("💰 Monthly Premium Summary (Net of Buybacks)")
    
    # Get data
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
    
    # Show January 2026 breakdown if debug mode is on
    if debug_mode:
        jan_2026_data = next((m for m in months_data if m['month_year'] == (1, 2026)), None)
        if jan_2026_data:
            st.divider()
            with st.expander("🔍 January 2026 Debug Details", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**CSP Breakdown:**")
                    st.write(f"Net: ${jan_2026_data['csp_net']:,.2f}")
                with col2:
                    st.write("**CC Breakdown:**")
                    st.write(f"Net: ${jan_2026_data['cc_net']:,.2f}")
                with col3:
                    st.write("**Total:**")
                    st.write(f"Net: ${jan_2026_data['net_premium']:,.2f}")
                st.info("📝 Check the terminal/console output for detailed transaction logs")
    
    st.divider()
