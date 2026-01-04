"""
CSP Ladder Manager - Weekly CSP Deployment Tracker
Tracks 4-week rolling CSP ladder with dynamic buying power allocation
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List


def calculate_tranche_targets(buying_power: float, num_tranches: int = 4) -> float:
    """Calculate optimal tranche size based on buying power"""
    return buying_power / num_tranches


def get_deployed_csp_capital(positions: List[Dict]) -> Dict:
    """
    Calculate capital deployed in CSPs grouped by expiration week
    Returns dict with expiration dates as keys and deployed capital as values
    """
    deployed_by_week = {}
    total_deployed = 0
    
    for pos in positions:
        # Check if this is a CSP (short put)
        instrument_type = pos.get('instrument-type', '')
        quantity_direction = pos.get('quantity-direction', '')
        
        if instrument_type == 'Equity Option' and quantity_direction == 'Short':
            # Parse option symbol to get type
            symbol = pos.get('symbol', '')
            if 'P' in symbol:  # It's a put
                # Get strike price and quantity
                strike = float(pos.get('strike-price', 0))
                quantity = abs(int(pos.get('quantity', 0)))
                
                # Capital deployed = strike * quantity * 100
                capital = strike * quantity * 100
                total_deployed += capital
                
                # Get expiration date
                expires_at = pos.get('expires-at', '')
                if expires_at:
                    exp_date = expires_at.split('T')[0]  # Get just the date part
                    if exp_date not in deployed_by_week:
                        deployed_by_week[exp_date] = 0
                    deployed_by_week[exp_date] += capital
    
    return {
        'by_week': deployed_by_week,
        'total': total_deployed
    }


def get_next_friday(weeks_ahead: int = 0) -> str:
    """Get the date of the next Friday (or Friday N weeks ahead)"""
    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0 and today.hour >= 16:  # After market close on Friday
        days_until_friday = 7
    
    next_friday = today + timedelta(days=days_until_friday + (weeks_ahead * 7))
    return next_friday.strftime('%Y-%m-%d')


def render_csp_ladder_manager(api, account_id: str):
    """
    Render the CSP Ladder Manager on Home Dashboard
    Shows 4-week rolling ladder with deployment targets and status
    """
    st.subheader("📅 Weekly CSP Ladder Manager")
    
    # Get account balances
    balances = api.get_account_balances(account_id)
    if not balances:
        st.error("Could not fetch account balances")
        return
    
    buying_power = float(balances.get('derivative-buying-power', 0))
    
    # Get positions to calculate deployed capital
    positions = api.get_positions(account_id)
    deployed_data = get_deployed_csp_capital(positions)
    deployed_by_week = deployed_data['by_week']
    total_deployed = deployed_data['total']
    
    # Calculate targets
    optimal_tranche_size = calculate_tranche_targets(buying_power, 4)
    available_capital = buying_power - total_deployed
    deployment_pct = (total_deployed / buying_power * 100) if buying_power > 0 else 0
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Buying Power",
            f"${buying_power:,.0f}",
            help="Total derivative buying power available"
        )
    
    with col2:
        st.metric(
            "Deployed in CSPs",
            f"${total_deployed:,.0f}",
            f"{deployment_pct:.1f}%",
            help="Capital currently deployed in active CSPs"
        )
    
    with col3:
        st.metric(
            "Available to Deploy",
            f"${available_capital:,.0f}",
            help="Remaining capital available for new CSPs"
        )
    
    st.divider()
    
    # Generate 4-week ladder
    tranches = []
    for week in range(4):
        exp_date = get_next_friday(week)
        deployed = deployed_by_week.get(exp_date, 0)
        target = optimal_tranche_size
        gap = target - deployed
        pct_deployed = (deployed / target * 100) if target > 0 else 0
        
        # Calculate days until expiration
        exp_datetime = datetime.strptime(exp_date, '%Y-%m-%d')
        days_until = (exp_datetime - datetime.now()).days
        
        # Determine status and action
        if pct_deployed >= 95:
            status = "✅ Fully Deployed"
            action = "Rolling weekly"
        elif pct_deployed >= 50:
            status = "⚠️ Partially Deployed"
            action = f"Add ${gap:,.0f}"
        else:
            status = "❌ Not Deployed"
            if days_until <= 7:
                action = f"⚡ Deploy ${target:,.0f} NOW"
            else:
                action = f"Deploy ${target:,.0f} by {exp_date}"
        
        tranches.append({
            'Tranche': f"Week {week + 1}",
            'Expiration': exp_date,
            'Days': days_until,
            'Target': target,
            'Deployed': deployed,
            'Gap': gap,
            'Progress': pct_deployed,
            'Status': status,
            'Action': action
        })
    
    # Display tranches table
    df = pd.DataFrame(tranches)
    
    # Format for display
    df_display = df.copy()
    df_display['Target'] = df_display['Target'].apply(lambda x: f"${x:,.0f}")
    df_display['Deployed'] = df_display['Deployed'].apply(lambda x: f"${x:,.0f}")
    df_display['Gap'] = df_display['Gap'].apply(lambda x: f"${x:,.0f}" if x > 0 else "—")
    df_display['Progress'] = df_display['Progress'].apply(lambda x: f"{x:.0f}%")
    
    st.dataframe(
        df_display[['Tranche', 'Expiration', 'Days', 'Deployed', 'Target', 'Progress', 'Status', 'Action']],
        use_container_width=True,
        hide_index=True
    )
    
    # Calculate projected weekly premium
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Current weekly premium (assuming 1% per week on deployed capital)
        current_weekly_premium = total_deployed * 0.01
        st.metric(
            "Current Weekly Premium",
            f"${current_weekly_premium:,.0f}",
            help="Estimated weekly premium at 1% of deployed capital"
        )
    
    with col2:
        # Potential weekly premium if fully deployed
        potential_weekly_premium = buying_power * 0.01
        potential_monthly = potential_weekly_premium * 4
        st.metric(
            "Potential (Fully Deployed)",
            f"${potential_weekly_premium:,.0f}/week",
            f"${potential_monthly:,.0f}/month",
            help="Potential weekly premium if all buying power deployed"
        )
    
    # Next action alert
    next_action_tranches = [t for t in tranches if t['Days'] <= 7 and t['Progress'] < 95]
    if next_action_tranches:
        st.warning(f"⚡ **Action Required:** {len(next_action_tranches)} tranche(s) expiring this week need deployment!")
        for t in next_action_tranches:
            st.info(f"**{t['Tranche']}** expires {t['Expiration']} ({t['Days']} days) - {t['Action']}")
    
    # Capital addition detector
    if available_capital > optimal_tranche_size * 0.5:
        st.info(f"💡 **New capital detected:** You have ${available_capital:,.0f} available. Consider adding ${available_capital/4:,.0f} to each tranche to maintain balance.")
