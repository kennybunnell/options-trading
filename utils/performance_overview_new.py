"""
Performance Overview Dashboard - REAL DATA ONLY
No fake data, no hardcoded values, no artificial distributions
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from collections import defaultdict
import requests


def get_real_monthly_data(api, account_numbers):
    """
    Get REAL monthly premium data from transaction history.
    Returns only months that have actual data.
    """
    if isinstance(account_numbers, str):
        account_numbers = [account_numbers]
    
    # Aggregate data across all accounts
    monthly_totals = defaultdict(lambda: {
        'csp_credits': 0.0,
        'csp_debits': 0.0,
        'cc_credits': 0.0,
        'cc_debits': 0.0,
        'csp_trades': 0,
        'cc_trades': 0,
        'assignments': 0,
        'called_away': 0
    })
    
    # Go back 12 months to capture all data
    now = datetime.now()
    start_month = now.month - 11
    start_year = now.year
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = datetime(start_year, start_month, 1)
    
    for account_number in account_numbers:
        try:
            url = f'{api.base_url}/accounts/{account_number}/transactions'
            headers = api._get_headers()
            
            params = {
                'start-date': start_date.strftime('%Y-%m-%d'),
                'end-date': now.strftime('%Y-%m-%d'),
                'per-page': 1000
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                continue
            
            data = response.json()
            transactions = data.get('data', {}).get('items', [])
            
            for txn in transactions:
                txn_type = txn.get('transaction-type', '')
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
                
                # Determine option type from symbol
                option_type = None
                if symbol and len(symbol) > 10:
                    # OCC format: SYMBOL + 6 digit date + C/P + 8 digit strike
                    # Find the C or P
                    for i, char in enumerate(symbol):
                        if char in ['C', 'P'] and i > 5:
                            option_type = 'CALL' if char == 'C' else 'PUT'
                            break
                
                if not option_type:
                    continue
                
                # Track trades
                if txn_type == 'Trade':
                    if action == 'Sell to Open':
                        if option_type == 'PUT':
                            monthly_totals[month_key]['csp_credits'] += abs(value)
                            monthly_totals[month_key]['csp_trades'] += 1
                        elif option_type == 'CALL':
                            monthly_totals[month_key]['cc_credits'] += abs(value)
                            monthly_totals[month_key]['cc_trades'] += 1
                    
                    elif action == 'Buy to Close':
                        if option_type == 'PUT':
                            monthly_totals[month_key]['csp_debits'] += abs(value)
                        elif option_type == 'CALL':
                            monthly_totals[month_key]['cc_debits'] += abs(value)
                
                # Track assignments and called away
                elif txn_type == 'Receive Deliver':
                    if option_type == 'PUT' and action in ['Buy', 'Receive']:
                        monthly_totals[month_key]['assignments'] += 1
                    elif option_type == 'CALL' and action in ['Sell', 'Deliver']:
                        monthly_totals[month_key]['called_away'] += 1
                        
        except Exception as e:
            print(f"Error fetching transactions for {account_number}: {str(e)}")
            continue
    
    # Convert to sorted list (newest to oldest to match Dashboard)
    results = []
    for month_key in sorted(monthly_totals.keys(), key=lambda x: (x[1], x[0]), reverse=True):
        month, year = month_key
        data = monthly_totals[month_key]
        
        csp_net = data['csp_credits'] - data['csp_debits']
        cc_net = data['cc_credits'] - data['cc_debits']
        total_net = csp_net + cc_net
        
        # Only include months with actual data
        if data['csp_credits'] > 0 or data['cc_credits'] > 0:
            results.append({
                'month_name': datetime(year, month, 1).strftime('%b %Y'),
                'month_key': month_key,
                'csp_credits': data['csp_credits'],
                'csp_debits': data['csp_debits'],
                'cc_credits': data['cc_credits'],
                'cc_debits': data['cc_debits'],
                'csp_net': csp_net,
                'cc_net': cc_net,
                'total_net': total_net,
                'csp_trades': data['csp_trades'],
                'cc_trades': data['cc_trades'],
                'assignments': data['assignments'],
                'called_away': data['called_away']
            })
    
    return results


def render_performance_overview_real(api, account_numbers):
    """
    Render Performance Overview with REAL DATA ONLY.
    No fake data, no hardcoded values.
    """
    
    st.header("Wheel Strategy Performance Dashboard")
    st.caption("📊 All data sourced from actual transaction history")
    
    # Get real monthly data
    with st.spinner("Loading real transaction data..."):
        monthly_data = get_real_monthly_data(api, account_numbers)
    
    if not monthly_data:
        st.warning("⚠️ No transaction data found. Please ensure you have trading history in your account.")
        return
    
    # Calculate totals from real data
    total_csp_credits = sum(m['csp_credits'] for m in monthly_data)
    total_csp_debits = sum(m['csp_debits'] for m in monthly_data)
    total_cc_credits = sum(m['cc_credits'] for m in monthly_data)
    total_cc_debits = sum(m['cc_debits'] for m in monthly_data)
    
    total_credits = total_csp_credits + total_cc_credits
    total_debits = total_csp_debits + total_cc_debits
    total_net = total_credits - total_debits
    
    total_csp_net = total_csp_credits - total_csp_debits
    total_cc_net = total_cc_credits - total_cc_debits
    
    total_csp_trades = sum(m['csp_trades'] for m in monthly_data)
    total_cc_trades = sum(m['cc_trades'] for m in monthly_data)
    total_assignments = sum(m['assignments'] for m in monthly_data)
    total_called_away = sum(m['called_away'] for m in monthly_data)
    
    # Date range
    first_month = monthly_data[0]['month_name']
    last_month = monthly_data[-1]['month_name']
    
    st.info(f"📅 Data range: **{first_month}** to **{last_month}** ({len(monthly_data)} months with activity)")
    
    # Top metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="💰 Total Credits",
            value=f"${total_credits:,.0f}",
            delta=f"{total_csp_trades + total_cc_trades} trades opened"
        )
    
    with col2:
        st.metric(
            label="💸 Total Debits",
            value=f"${total_debits:,.0f}",
            delta="Closing costs",
            delta_color="inverse"
        )
    
    with col3:
        retention_pct = (total_net / total_credits * 100) if total_credits > 0 else 0
        st.metric(
            label="✅ NET Premium",
            value=f"${total_net:,.0f}",
            delta=f"{retention_pct:.1f}% retained"
        )
    
    with col4:
        csp_pct = (total_csp_net / total_net * 100) if total_net > 0 else 0
        st.metric(
            label="📈 CSP Premium",
            value=f"${total_csp_net:,.0f}",
            delta=f"{csp_pct:.0f}% of total"
        )
    
    with col5:
        cc_pct = (total_cc_net / total_net * 100) if total_net > 0 else 0
        st.metric(
            label="📉 CC Premium",
            value=f"${total_cc_net:,.0f}",
            delta=f"{cc_pct:.0f}% of total"
        )
    
    st.divider()
    
    # ==========================================
    # PREMIUM EARNINGS OVER TIME - REAL DATA
    # ==========================================
    st.subheader("Premium Earnings Over Time")
    
    # Prepare data for chart
    month_labels = [m['month_name'] for m in monthly_data]
    monthly_net_values = [m['total_net'] for m in monthly_data]
    
    # Calculate cumulative
    cumulative_values = []
    running_total = 0
    for v in monthly_net_values:
        running_total += v
        cumulative_values.append(running_total)
    
    # Create combined bar + line chart
    fig = go.Figure()
    
    # Add bars for monthly premium
    fig.add_trace(go.Bar(
        x=month_labels,
        y=monthly_net_values,
        name='Monthly Net Premium',
        marker_color='#28a745',
        opacity=0.8,
        text=[f"${v:,.0f}" for v in monthly_net_values],
        textposition='outside'
    ))
    
    # Add line for cumulative premium
    fig.add_trace(go.Scatter(
        x=month_labels,
        y=cumulative_values,
        name='Cumulative Premium',
        line=dict(color='#17a2b8', width=3),
        mode='lines+markers',
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, color='#888'),
        yaxis=dict(
            showgrid=True, 
            gridcolor='rgba(255,255,255,0.1)', 
            color='#888',
            title='Monthly Net Premium ($)',
            tickprefix='$',
            tickformat=',.'
        ),
        yaxis2=dict(
            title='Cumulative Premium ($)',
            overlaying='y',
            side='right',
            showgrid=False,
            color='#17a2b8',
            tickprefix='$',
            tickformat=',.'
        ),
        margin=dict(l=60, r=60, t=30, b=50),
        height=400,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig)
    
    st.divider()
    
    # ==========================================
    # CSP AND CC PERFORMANCE - REAL DATA
    # ==========================================
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CSP Performance by Month")
        
        # Monthly CSP data
        csp_values = [m['csp_net'] for m in monthly_data]
        
        fig_csp = go.Figure()
        fig_csp.add_trace(go.Bar(
            x=month_labels,
            y=csp_values,
            marker_color='#28a745',
            name='CSP Net Premium',
            text=[f"${v:,.0f}" for v in csp_values],
            textposition='outside'
        ))
        
        fig_csp.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#888', tickangle=-45),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='#888',
                      tickprefix='$', tickformat=',.0f'),
            margin=dict(l=60, r=20, t=10, b=80),
            height=250,
            showlegend=False
        )
        
        st.plotly_chart(fig_csp)
        
        # CSP Stats - REAL DATA
        avg_csp_per_trade = total_csp_net / total_csp_trades if total_csp_trades > 0 else 0
        assignment_rate = (total_assignments / total_csp_trades * 100) if total_csp_trades > 0 else 0
        
        st.markdown(f"""
        | Metric | Value |
        |--------|-------|
        | 📄 Total CSP Trades | **{total_csp_trades}** |
        | 💵 Total CSP Premium | **${total_csp_net:,.2f}** |
        | 📊 Avg Premium/Trade | **${avg_csp_per_trade:,.2f}** |
        | 🔄 Assignments | **{total_assignments}** ({assignment_rate:.1f}%) |
        """)
    
    with col2:
        st.subheader("CC Performance by Month")
        
        # Monthly CC data
        cc_values = [m['cc_net'] for m in monthly_data]
        
        fig_cc = go.Figure()
        fig_cc.add_trace(go.Bar(
            x=month_labels,
            y=cc_values,
            marker_color='#17a2b8',
            name='CC Net Premium',
            text=[f"${v:,.0f}" for v in cc_values],
            textposition='outside'
        ))
        
        fig_cc.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#888', tickangle=-45),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='#888',
                      tickprefix='$', tickformat=',.0f'),
            margin=dict(l=60, r=20, t=10, b=80),
            height=250,
            showlegend=False
        )
        
        st.plotly_chart(fig_cc)
        
        # CC Stats - REAL DATA
        avg_cc_per_trade = total_cc_net / total_cc_trades if total_cc_trades > 0 else 0
        called_away_rate = (total_called_away / total_cc_trades * 100) if total_cc_trades > 0 else 0
        
        st.markdown(f"""
        | Metric | Value |
        |--------|-------|
        | 📄 Total CC Trades | **{total_cc_trades}** |
        | 💵 Total CC Premium | **${total_cc_net:,.2f}** |
        | 📊 Avg Premium/Trade | **${avg_cc_per_trade:,.2f}** |
        | 📤 Called Away | **{total_called_away}** ({called_away_rate:.1f}%) |
        """)
    
    st.divider()
    
    # ==========================================
    # MONTHLY BREAKDOWN TABLE
    # ==========================================
    st.subheader("📋 Monthly Breakdown (Detailed)")
    
    # Create a detailed table
    table_data = []
    for m in monthly_data:
        table_data.append({
            'Month': m['month_name'],
            'CSP Credits': f"${m['csp_credits']:,.0f}",
            'CSP Debits': f"${m['csp_debits']:,.0f}",
            'CSP Net': f"${m['csp_net']:,.0f}",
            'CC Credits': f"${m['cc_credits']:,.0f}",
            'CC Debits': f"${m['cc_debits']:,.0f}",
            'CC Net': f"${m['cc_net']:,.0f}",
            'Total Net': f"${m['total_net']:,.0f}",
            'CSP Trades': m['csp_trades'],
            'CC Trades': m['cc_trades']
        })
    
    import pandas as pd
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True)
