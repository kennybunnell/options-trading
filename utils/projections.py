"""
Projections Module
Calculates income projections based on open positions, theta decay, and historical performance.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import re


def parse_option_symbol(symbol: str) -> Optional[Dict]:
    """Parse OCC option symbol to extract components"""
    try:
        clean_symbol = symbol.replace(' ', '')
        match = re.match(r'([A-Z]+)(\d{6})([CP])(\d+)', clean_symbol)
        if match:
            underlying = match.group(1)
            date_str = match.group(2)
            option_type = 'PUT' if match.group(3) == 'P' else 'CALL'
            strike = int(match.group(4)) / 1000
            year = 2000 + int(date_str[:2])
            month = int(date_str[2:4])
            day = int(date_str[4:6])
            expiration = f"{year}-{month:02d}-{day:02d}"
            return {
                'underlying': underlying,
                'expiration': expiration,
                'option_type': option_type,
                'strike': strike
            }
    except Exception:
        pass
    return None


def calculate_dte(expiration_str: str) -> int:
    """Calculate days to expiration"""
    try:
        exp_date = datetime.strptime(expiration_str, '%Y-%m-%d')
        return max(0, (exp_date - datetime.now()).days)
    except:
        return 0


def get_locked_in_income(api, account_numbers: List[str]) -> Dict:
    """
    Calculate locked-in income from open positions.
    Returns premium that will be realized if positions expire worthless.
    """
    now = datetime.now()
    this_week_end = now + timedelta(days=(4 - now.weekday()))  # Friday
    this_month_end = (now.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    next_month_end = (this_month_end + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    income = {
        'this_week': {'premium': 0.0, 'positions': 0},
        'this_month': {'premium': 0.0, 'positions': 0},
        'next_month': {'premium': 0.0, 'positions': 0},
        'beyond': {'premium': 0.0, 'positions': 0},
        'total_open': {'premium': 0.0, 'positions': 0}
    }
    
    for account_number in account_numbers:
        try:
            positions = api.get_positions(account_number)
            if not positions:
                continue
                
            for pos in positions:
                instrument_type = pos.get('instrument-type', '')
                if instrument_type != 'Equity Option':
                    continue
                
                # Check if it's a short position (sold option)
                quantity = int(float(pos.get('quantity', 0)))
                quantity_direction = pos.get('quantity-direction', '')
                is_short = quantity_direction.lower() == 'short' or quantity < 0
                
                if not is_short:
                    continue
                
                symbol = pos.get('symbol', '')
                parsed = parse_option_symbol(symbol)
                if not parsed:
                    continue
                
                # Calculate premium value
                open_price = float(pos.get('average-open-price', 0))
                multiplier = int(float(pos.get('multiplier', 100)))
                qty = abs(quantity)
                premium = open_price * qty * multiplier
                
                # Get expiration date
                exp_str = parsed['expiration']
                try:
                    exp_date = datetime.strptime(exp_str, '%Y-%m-%d')
                except:
                    continue
                
                income['total_open']['premium'] += premium
                income['total_open']['positions'] += 1
                
                # Categorize by expiration timeframe
                if exp_date <= this_week_end:
                    income['this_week']['premium'] += premium
                    income['this_week']['positions'] += 1
                elif exp_date <= this_month_end:
                    income['this_month']['premium'] += premium
                    income['this_month']['positions'] += 1
                elif exp_date <= next_month_end:
                    income['next_month']['premium'] += premium
                    income['next_month']['positions'] += 1
                else:
                    income['beyond']['premium'] += premium
                    income['beyond']['positions'] += 1
                    
        except Exception as e:
            continue
    
    return income


def get_portfolio_theta(api, account_numbers: List[str]) -> Dict:
    """
    Calculate portfolio-level theta (daily time decay).
    Note: This is an approximation since we don't have live greeks from the API.
    We estimate theta based on premium and DTE.
    """
    total_theta = 0.0
    position_count = 0
    
    for account_number in account_numbers:
        try:
            positions = api.get_positions(account_number)
            if not positions:
                continue
                
            for pos in positions:
                instrument_type = pos.get('instrument-type', '')
                if instrument_type != 'Equity Option':
                    continue
                
                # Check if it's a short position
                quantity = int(float(pos.get('quantity', 0)))
                quantity_direction = pos.get('quantity-direction', '')
                is_short = quantity_direction.lower() == 'short' or quantity < 0
                
                if not is_short:
                    continue
                
                symbol = pos.get('symbol', '')
                parsed = parse_option_symbol(symbol)
                if not parsed:
                    continue
                
                # Get current value and DTE
                current_price = float(pos.get('mark', 0) or pos.get('mark-price', 0) or pos.get('close-price', 0) or 0)
                multiplier = int(float(pos.get('multiplier', 100)))
                qty = abs(quantity)
                current_value = current_price * qty * multiplier
                
                dte = calculate_dte(parsed['expiration'])
                
                # Estimate daily theta as current_value / DTE (simplified)
                # This assumes linear decay, which underestimates near-term theta
                if dte > 0:
                    # Apply acceleration factor for near-term options
                    if dte <= 7:
                        acceleration = 2.0  # Theta accelerates in final week
                    elif dte <= 21:
                        acceleration = 1.5
                    else:
                        acceleration = 1.0
                    
                    daily_theta = (current_value / dte) * acceleration
                    total_theta += daily_theta
                    position_count += 1
                    
        except Exception as e:
            continue
    
    return {
        'daily_theta': total_theta,
        'weekly_theta': total_theta * 5,  # Trading days
        'monthly_theta': total_theta * 21,  # Trading days
        'position_count': position_count
    }


def get_historical_performance(api, account_numbers: List[str], months: int = 6) -> Dict:
    """
    Calculate historical performance metrics from transaction history.
    Returns average monthly yield, win rate, and capital turnover.
    """
    import requests
    
    now = datetime.now()
    
    # Calculate start date
    start_month = now.month - months + 1
    start_year = now.year
    while start_month <= 0:
        start_month += 12
        start_year -= 1
    start_date = datetime(start_year, start_month, 1)
    
    monthly_premiums = defaultdict(float)
    total_credits = 0.0
    total_debits = 0.0
    winning_trades = 0
    total_trades = 0
    
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
                t_type = txn.get('transaction-type')
                action = txn.get('action', '')
                value = float(txn.get('value', 0))
                executed_at = txn.get('executed-at', '')
                symbol = txn.get('symbol', '')
                
                if t_type not in ['Trade', 'Receive Deliver']:
                    continue
                
                # Only count option trades
                option_info = parse_option_symbol(symbol)
                if not option_info:
                    continue
                
                if not executed_at:
                    continue
                
                try:
                    txn_date = datetime.fromisoformat(executed_at.replace('Z', '+00:00'))
                    month_key = f"{txn_date.year}-{txn_date.month:02d}"
                except:
                    continue
                
                if action == 'Sell to Open':
                    total_credits += abs(value)
                    monthly_premiums[month_key] += abs(value)
                    total_trades += 1
                elif action == 'Buy to Close':
                    total_debits += abs(value)
                    # A BTC after STO is typically a winning trade if debit < original credit
                    # We'll approximate win rate based on net positive months
                    
        except Exception as e:
            continue
    
    # Calculate metrics
    net_premium = total_credits - total_debits
    months_with_data = len(monthly_premiums)
    
    if months_with_data > 0:
        avg_monthly_premium = net_premium / months_with_data
        monthly_values = list(monthly_premiums.values())
        
        # Win rate approximation: months with positive premium
        positive_months = sum(1 for v in monthly_values if v > 0)
        win_rate = (positive_months / months_with_data) * 100 if months_with_data > 0 else 0
    else:
        avg_monthly_premium = 0
        win_rate = 0
    
    return {
        'total_credits': total_credits,
        'total_debits': total_debits,
        'net_premium': net_premium,
        'avg_monthly_premium': avg_monthly_premium,
        'months_analyzed': months_with_data,
        'win_rate': win_rate,
        'monthly_breakdown': dict(monthly_premiums)
    }


def calculate_projections(portfolio_value: float, monthly_yield_pct: float, 
                          monthly_contribution: float = 0, months: int = 12) -> List[Dict]:
    """
    Calculate projected portfolio growth with compounding.
    """
    projections = []
    current_value = portfolio_value
    cumulative_income = 0
    
    for month in range(1, months + 1):
        # Add monthly contribution
        current_value += monthly_contribution
        
        # Calculate monthly income
        monthly_income = current_value * (monthly_yield_pct / 100)
        cumulative_income += monthly_income
        
        # Compound (reinvest premium)
        current_value += monthly_income
        
        projections.append({
            'month': month,
            'portfolio_value': current_value,
            'monthly_income': monthly_income,
            'cumulative_income': cumulative_income
        })
    
    return projections


def get_scenario_projections(portfolio_value: float, monthly_contribution: float = 0) -> Dict:
    """
    Generate projections for conservative, expected, and optimistic scenarios.
    """
    scenarios = {
        'conservative': {
            'yield_pct': 2.0,
            'description': 'Conservative (2%/month)',
            'projections': calculate_projections(portfolio_value, 2.0, monthly_contribution, 24)
        },
        'expected': {
            'yield_pct': 3.0,
            'description': 'Expected (3%/month)',
            'projections': calculate_projections(portfolio_value, 3.0, monthly_contribution, 24)
        },
        'optimistic': {
            'yield_pct': 4.0,
            'description': 'Optimistic (4%/month)',
            'projections': calculate_projections(portfolio_value, 4.0, monthly_contribution, 24)
        }
    }
    
    return scenarios


def render_projections_tab(api, account_numbers: List[str], portfolio_value: float):
    """
    Render the Projections tab in the Performance dashboard.
    """
    st.subheader("📊 Income Projections")
    st.markdown("*Forecast your premium income based on open positions and historical performance*")
    
    # Section 1: Locked-In Income
    st.markdown("---")
    st.markdown("### 🔒 Locked-In Income")
    st.markdown("*Premium from open positions that will be realized if they expire worthless*")
    
    with st.spinner("Calculating locked-in income..."):
        locked_in = get_locked_in_income(api, account_numbers)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "This Week",
            f"${locked_in['this_week']['premium']:,.0f}",
            f"{locked_in['this_week']['positions']} positions"
        )
    
    with col2:
        st.metric(
            "This Month",
            f"${locked_in['this_month']['premium']:,.0f}",
            f"{locked_in['this_month']['positions']} positions"
        )
    
    with col3:
        st.metric(
            "Next Month",
            f"${locked_in['next_month']['premium']:,.0f}",
            f"{locked_in['next_month']['positions']} positions"
        )
    
    with col4:
        st.metric(
            "Total Open Premium",
            f"${locked_in['total_open']['premium']:,.0f}",
            f"{locked_in['total_open']['positions']} positions"
        )
    
    # Section 2: Theta Decay Projection
    st.markdown("---")
    st.markdown("### ⏱️ Theta Decay Projection")
    st.markdown("*Estimated daily time decay working in your favor*")
    
    with st.spinner("Calculating theta..."):
        theta = get_portfolio_theta(api, account_numbers)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Daily Theta",
            f"${theta['daily_theta']:,.0f}",
            "per trading day"
        )
    
    with col2:
        st.metric(
            "Weekly Projection",
            f"${theta['weekly_theta']:,.0f}",
            "5 trading days"
        )
    
    with col3:
        st.metric(
            "Monthly Projection",
            f"${theta['monthly_theta']:,.0f}",
            "21 trading days"
        )
    
    # Section 3: Historical-Based Forecast
    st.markdown("---")
    st.markdown("### 📈 Historical-Based Forecast")
    st.markdown("*Projections based on your actual trading performance*")
    
    with st.spinner("Analyzing historical performance..."):
        historical = get_historical_performance(api, account_numbers, months=6)
    
    # Show historical metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "6-Month Net Premium",
            f"${historical['net_premium']:,.0f}"
        )
    
    with col2:
        st.metric(
            "Avg Monthly Premium",
            f"${historical['avg_monthly_premium']:,.0f}"
        )
    
    with col3:
        if portfolio_value > 0:
            monthly_yield = (historical['avg_monthly_premium'] / portfolio_value) * 100
            st.metric(
                "Avg Monthly Yield",
                f"{monthly_yield:.1f}%"
            )
        else:
            st.metric("Avg Monthly Yield", "N/A")
    
    with col4:
        st.metric(
            "Months Analyzed",
            f"{historical['months_analyzed']}"
        )
    
    # Projected income based on historical average
    if historical['avg_monthly_premium'] > 0:
        st.markdown("#### Projected Income (Based on Historical Average)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            next_month = historical['avg_monthly_premium']
            st.metric("Next Month", f"${next_month:,.0f}")
        
        with col2:
            next_quarter = historical['avg_monthly_premium'] * 3
            st.metric("Next Quarter", f"${next_quarter:,.0f}")
        
        with col3:
            next_year = historical['avg_monthly_premium'] * 12
            st.metric("Next 12 Months", f"${next_year:,.0f}")
    
    # Section 4: Scenario Modeling
    st.markdown("---")
    st.markdown("### 🎯 Scenario Modeling")
    st.markdown("*Project your portfolio growth under different yield assumptions*")
    
    # User inputs for scenario modeling
    col1, col2 = st.columns(2)
    
    with col1:
        starting_capital = st.number_input(
            "Starting Portfolio Value",
            min_value=0.0,
            value=float(portfolio_value),
            step=10000.0,
            format="%.0f",
            key="proj_starting_capital"
        )
    
    with col2:
        monthly_contribution = st.number_input(
            "Monthly Contribution",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            format="%.0f",
            help="Additional capital added each month",
            key="proj_monthly_contribution"
        )
    
    # Calculate scenarios
    scenarios = get_scenario_projections(starting_capital, monthly_contribution)
    
    # Display scenario results
    st.markdown("#### Portfolio Value Projections")
    
    # Create comparison table
    comparison_data = []
    for timeframe, months in [("6 Months", 6), ("12 Months", 12), ("24 Months", 24)]:
        row = {"Timeframe": timeframe}
        for scenario_name, scenario in scenarios.items():
            if months <= len(scenario['projections']):
                proj = scenario['projections'][months - 1]
                row[scenario['description']] = f"${proj['portfolio_value']:,.0f}"
        comparison_data.append(row)
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Cumulative income projections
    st.markdown("#### Cumulative Income Projections")
    
    income_data = []
    for timeframe, months in [("6 Months", 6), ("12 Months", 12), ("24 Months", 24)]:
        row = {"Timeframe": timeframe}
        for scenario_name, scenario in scenarios.items():
            if months <= len(scenario['projections']):
                proj = scenario['projections'][months - 1]
                row[scenario['description']] = f"${proj['cumulative_income']:,.0f}"
        income_data.append(row)
    
    df_income = pd.DataFrame(income_data)
    st.dataframe(df_income, use_container_width=True, hide_index=True)
    
    # Growth chart
    st.markdown("#### Portfolio Growth Visualization")
    
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    colors = {'conservative': '#EF4444', 'expected': '#F59E0B', 'optimistic': '#10B981'}
    milestone_months = [6, 12, 18, 24]
    
    # Get data for confidence band (area between conservative and optimistic)
    conservative_data = scenarios['conservative']['projections']
    optimistic_data = scenarios['optimistic']['projections']
    
    # Add confidence band (shaded area between conservative and optimistic)
    fig.add_trace(go.Scatter(
        x=[p['month'] for p in conservative_data] + [p['month'] for p in optimistic_data][::-1],
        y=[p['portfolio_value'] for p in conservative_data] + [p['portfolio_value'] for p in optimistic_data][::-1],
        fill='toself',
        fillcolor='rgba(249, 158, 11, 0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo='skip',
        showlegend=True,
        name='Projection Range'
    ))
    
    # Add lines for each scenario with enhanced tooltips
    for scenario_name, scenario in scenarios.items():
        months = [p['month'] for p in scenario['projections']]
        values = [p['portfolio_value'] for p in scenario['projections']]
        incomes = [p['cumulative_income'] for p in scenario['projections']]
        
        # Create custom hover text
        hover_text = [
            f"<b>{scenario['description']}</b><br>" +
            f"Month: {m}<br>" +
            f"Portfolio: ${v:,.0f}<br>" +
            f"Cumulative Income: ${inc:,.0f}"
            for m, v, inc in zip(months, values, incomes)
        ]
        
        # Determine line style
        if scenario_name == 'expected':
            line_width = 3
            line_dash = None
        else:
            line_width = 2
            line_dash = 'dot' if scenario_name == 'conservative' else 'dash'
        
        fig.add_trace(go.Scatter(
            x=months,
            y=values,
            mode='lines',
            name=scenario['description'],
            line=dict(color=colors[scenario_name], width=line_width, dash=line_dash),
            hovertemplate='%{text}<extra></extra>',
            text=hover_text
        ))
    
    # Add markers at milestone months (6, 12, 18, 24) for the Expected scenario
    expected_data = scenarios['expected']['projections']
    milestone_values = []
    milestone_labels = []
    
    for month in milestone_months:
        if month <= len(expected_data):
            proj = expected_data[month - 1]
            milestone_values.append(proj['portfolio_value'])
            milestone_labels.append(f"${proj['portfolio_value']/1000000:.1f}M")
    
    fig.add_trace(go.Scatter(
        x=milestone_months[:len(milestone_values)],
        y=milestone_values,
        mode='markers+text',
        marker=dict(size=12, color='#F59E0B', symbol='circle', line=dict(width=2, color='white')),
        text=milestone_labels,
        textposition='top center',
        textfont=dict(size=11, color='white'),
        name='Milestones (Expected)',
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title="Projected Portfolio Value Over Time",
        xaxis_title="Months",
        yaxis_title="Portfolio Value ($)",
        yaxis_tickformat="$,.0f",
        template="plotly_dark",
        height=450,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            tickmode='array',
            tickvals=[1, 6, 12, 18, 24],
            ticktext=['1', '6', '12', '18', '24']
        ),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Disclaimer
    st.markdown("---")
    st.caption(
        "⚠️ **Disclaimer:** These projections are based on historical performance and assumptions. "
        "Actual results may vary significantly. Past performance does not guarantee future results. "
        "Options trading involves risk and is not suitable for all investors."
    )
