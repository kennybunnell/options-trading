"""
Position Recovery Tracker - Track underwater positions and recovery progress
Shows how CC premiums are reducing cost basis and path to breakeven
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict


def calculate_recovery_metrics(stock_positions: List[Dict], cc_premiums: Dict) -> Dict:
    """
    Calculate recovery metrics for underwater positions
    Returns summary stats and position-level recovery data
    """
    underwater_positions = []
    total_unrealized_loss = 0
    total_cc_premium_collected = 0
    
    for pos in stock_positions:
        symbol = pos['symbol']
        qty = pos['quantity']
        avg_cost = pos['average_open_price']
        current_price = pos.get('close_price', 0) or pos.get('mark', 0)
        
        cost_basis = qty * avg_cost
        market_value = qty * current_price
        unrealized_pl = market_value - cost_basis
        
        # Only track underwater positions (negative P/L)
        if unrealized_pl < 0:
            cc_premium = cc_premiums.get(symbol, 0)
            total_cc_premium_collected += cc_premium
            
            # Calculate recovery percentage
            recovery_pct = (cc_premium / abs(unrealized_pl) * 100) if unrealized_pl != 0 else 0
            
            # Adjusted cost basis after CC premiums
            adjusted_basis = avg_cost - (cc_premium / qty)
            
            # Gap to close (remaining loss after CC premiums)
            remaining_loss = unrealized_pl + cc_premium
            
            underwater_positions.append({
                'symbol': symbol,
                'quantity': qty,
                'cost_basis': avg_cost,
                'current_price': current_price,
                'total_cost': cost_basis,
                'market_value': market_value,
                'unrealized_loss': unrealized_pl,
                'cc_premium': cc_premium,
                'recovery_pct': recovery_pct,
                'adjusted_basis': adjusted_basis,
                'remaining_loss': remaining_loss
            })
            
            total_unrealized_loss += unrealized_pl
    
    # Calculate overall recovery percentage
    overall_recovery_pct = (total_cc_premium_collected / abs(total_unrealized_loss) * 100) if total_unrealized_loss != 0 else 0
    
    # Net position after CC premiums
    net_position = total_unrealized_loss + total_cc_premium_collected
    
    return {
        'total_unrealized_loss': total_unrealized_loss,
        'total_cc_premium': total_cc_premium_collected,
        'overall_recovery_pct': overall_recovery_pct,
        'net_position': net_position,
        'underwater_positions': underwater_positions,
        'num_underwater': len(underwater_positions)
    }


def estimate_recovery_timeline(remaining_loss: float, monthly_cc_rate: float) -> float:
    """
    Estimate months to breakeven at given monthly CC premium rate
    """
    if monthly_cc_rate <= 0:
        return float('inf')
    return abs(remaining_loss) / monthly_cc_rate


def render_recovery_tracker(stock_positions: List[Dict], cc_premiums: Dict):
    """
    Render the Position Recovery Tracker
    Shows underwater positions and recovery progress through CC premiums
    """
    
    # Calculate recovery metrics
    metrics = calculate_recovery_metrics(stock_positions, cc_premiums)
    
    # Only show if there are underwater positions
    if metrics['num_underwater'] == 0:
        st.success("🎉 **No underwater positions!** All your stock positions are at or above cost basis.")
        return
    
    st.subheader("📊 Underwater Position Recovery")
    
    st.markdown("""
    This section tracks your underwater stock positions (from assigned CSPs) and shows how covered call premiums 
    are reducing your cost basis over time.
    """)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Unrealized Loss",
            f"${metrics['total_unrealized_loss']:,.0f}",
            help="Total loss on underwater positions at current market prices"
        )
    
    with col2:
        st.metric(
            "CC Premiums Collected",
            f"${metrics['total_cc_premium']:,.0f}",
            help="Total covered call premiums collected on these positions"
        )
    
    with col3:
        st.metric(
            "Net Position",
            f"${metrics['net_position']:,.0f}",
            f"{metrics['overall_recovery_pct']:.1f}% recovered",
            help="Remaining loss after CC premiums applied"
        )
    
    with col4:
        st.metric(
            "Positions Underwater",
            f"{metrics['num_underwater']}",
            help="Number of stock positions currently below cost basis"
        )
    
    # Progress bar
    st.divider()
    
    progress_value = min(metrics['overall_recovery_pct'] / 100, 1.0)
    st.progress(progress_value, text=f"Recovery Progress: {metrics['overall_recovery_pct']:.1f}% to breakeven")
    
    st.divider()
    
    # Recovery timeline estimates
    st.subheader("⏱️ Recovery Timeline Estimates")
    
    # Calculate historical monthly CC rate (from total CC premiums)
    # Assuming 3.5 months of trading (Sept 18 - Jan 3)
    historical_months = 3.5
    historical_monthly_rate = metrics['total_cc_premium'] / historical_months
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**At Current CC Rate:**")
        current_months = estimate_recovery_timeline(metrics['net_position'], historical_monthly_rate)
        if current_months == float('inf'):
            st.warning("⚠️ No CC premiums collected yet")
        else:
            st.info(f"**{current_months:.1f} months** to breakeven at ${historical_monthly_rate:,.0f}/month")
    
    with col2:
        st.markdown("**At Target CC Rate:**")
        # User can input target monthly CC premium
        target_monthly = st.number_input(
            "Target Monthly CC Premium",
            min_value=0,
            value=int(historical_monthly_rate * 3),  # Default to 3x current
            step=1000,
            help="Enter your target monthly CC premium collection goal"
        )
        
        if target_monthly > 0:
            target_months = estimate_recovery_timeline(metrics['net_position'], target_monthly)
            st.success(f"**{target_months:.1f} months** to breakeven at ${target_monthly:,.0f}/month")
        else:
            st.warning("Enter target monthly CC premium")
    
    st.divider()
    
    # Position-by-position recovery table
    st.subheader("📋 Position-by-Position Recovery")
    
    # Sort by remaining loss (worst first)
    sorted_positions = sorted(metrics['underwater_positions'], key=lambda x: x['remaining_loss'])
    
    table_data = []
    for pos in sorted_positions:
        table_data.append({
            'Symbol': pos['symbol'],
            'Shares': pos['quantity'],
            'Cost Basis': f"${pos['cost_basis']:.2f}",
            'Current Price': f"${pos['current_price']:.2f}",
            'Unrealized Loss': pos['unrealized_loss'],
            'CC Premiums': pos['cc_premium'],
            'Adjusted Basis': f"${pos['adjusted_basis']:.2f}",
            'Remaining Loss': pos['remaining_loss'],
            'Recovery %': pos['recovery_pct']
        })
    
    df = pd.DataFrame(table_data)
    
    # Format for display
    df_display = df.copy()
    df_display['Unrealized Loss'] = df_display['Unrealized Loss'].apply(lambda x: f"-${abs(x):,.0f}")
    df_display['CC Premiums'] = df_display['CC Premiums'].apply(lambda x: f"${x:,.0f}")
    df_display['Remaining Loss'] = df_display['Remaining Loss'].apply(lambda x: f"-${abs(x):,.0f}")
    df_display['Recovery %'] = df_display['Recovery %'].apply(lambda x: f"{x:.1f}%")
    
    # Color code recovery percentage
    def color_recovery(val):
        pct = float(val.replace('%', ''))
        if pct >= 50:
            return 'background-color: #28a745; color: white'
        elif pct >= 25:
            return 'background-color: #ffc107; color: black'
        else:
            return 'background-color: #dc3545; color: white'
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Symbol": st.column_config.TextColumn("Symbol", width="small"),
            "Shares": st.column_config.NumberColumn("Shares", width="small"),
            "Cost Basis": st.column_config.TextColumn("Cost/Share", width="small"),
            "Current Price": st.column_config.TextColumn("Current", width="small"),
            "Unrealized Loss": st.column_config.TextColumn("Unrealized Loss", width="medium"),
            "CC Premiums": st.column_config.TextColumn("CC Premiums", width="medium"),
            "Adjusted Basis": st.column_config.TextColumn("Adj. Basis", width="small"),
            "Remaining Loss": st.column_config.TextColumn("Remaining Loss", width="medium"),
            "Recovery %": st.column_config.TextColumn("Recovery %", width="small"),
        }
    )
    
    st.divider()
    
    # Recovery visualization - Bar chart
    st.subheader("📊 Recovery Progress by Position")
    
    chart_data = []
    for pos in sorted_positions:
        chart_data.append({
            'Symbol': pos['symbol'],
            'Unrealized Loss': abs(pos['unrealized_loss']),
            'CC Premiums': pos['cc_premium'],
            'Remaining Loss': abs(pos['remaining_loss'])
        })
    
    chart_df = pd.DataFrame(chart_data)
    
    fig = go.Figure()
    
    # Stacked bar chart showing unrealized loss and CC premium recovery
    fig.add_trace(go.Bar(
        name='CC Premiums (Recovered)',
        x=chart_df['Symbol'],
        y=chart_df['CC Premiums'],
        marker_color='#28a745'
    ))
    
    fig.add_trace(go.Bar(
        name='Remaining Loss',
        x=chart_df['Symbol'],
        y=chart_df['Remaining Loss'],
        marker_color='#dc3545'
    ))
    
    fig.update_layout(
        barmode='stack',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, color='#888', tickangle=-45),
        yaxis=dict(
            showgrid=True, 
            gridcolor='rgba(255,255,255,0.1)', 
            color='#888',
            title='Amount ($)', 
            tickprefix='$', 
            tickformat=',.0f'
        ),
        margin=dict(l=80, r=20, t=20, b=100),
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Strategy recommendations
    st.divider()
    st.subheader("💡 Recovery Strategy Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Aggressive Recovery:**")
        st.markdown("""
        - Sell **weekly CCs** instead of monthly
        - Use **30-40 delta** for higher premiums (accept assignment risk)
        - Focus on high IV stocks (MSTR, HIMS, IREN)
        - Target: 2-3% of stock value per month
        """)
    
    with col2:
        st.markdown("**Conservative Recovery:**")
        st.markdown("""
        - Sell **monthly CCs** at 10-20 delta
        - Roll for credit when threatened
        - Wait for stock price recovery + collect premium
        - Target: 1-1.5% of stock value per month
        """)
    
    st.info("💡 **Remember:** You have TWO paths to recovery - stock price appreciation AND CC premium collection. Most likely you'll recover through a combination of both!")
