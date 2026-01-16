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


def render_recovery_chart_only(stock_positions: List[Dict], cc_premiums: Dict):
    """
    Render ONLY the horizontal recovery bar chart (for use at top of Stock Basis page)
    Shows all stock positions with their unrealized P/L and CC premium recovery
    """
    
    # Calculate metrics for ALL positions (not just underwater)
    chart_data = []
    
    for pos in stock_positions:
        symbol = pos['symbol']
        qty = pos['quantity']
        avg_cost = pos['average_open_price']
        current_price = pos.get('close_price', 0) or pos.get('mark', 0)
        
        cost_basis = qty * avg_cost
        market_value = qty * current_price
        unrealized_pl = market_value - cost_basis
        
        # Get CC premium for this symbol
        cc_premium = cc_premiums.get(symbol, 0)
        
        # Only show underwater positions in recovery chart
        if unrealized_pl < 0:
            total_underwater = abs(unrealized_pl)
            remaining = max(0, total_underwater - cc_premium)
            recovery_pct = (cc_premium / total_underwater * 100) if total_underwater > 0 else 0
            
            chart_data.append({
                'Symbol': symbol,
                'Total Underwater': total_underwater,
                'CC Recovered': cc_premium,
                'Remaining': remaining,
                'Recovery %': recovery_pct
            })
    
    if not chart_data:
        st.success("🎉 **No underwater positions!** All your stock positions are at or above cost basis.")
        return
    
    st.subheader("📊 Recovery Progress by Position")
    
    st.markdown("""
    **Green** = CC Premium recovered toward breakeven | **Red** = Remaining underwater amount
    """)
    
    chart_df = pd.DataFrame(chart_data)
    
    # Sort by remaining loss (most underwater at top, least at bottom)
    chart_df = chart_df.sort_values('Remaining', ascending=True)
    
    fig = go.Figure()
    
    # Green bars - CC Premiums Recovered (shown first, on the left)
    fig.add_trace(go.Bar(
        name='Premium Recovered',
        y=chart_df['Symbol'],
        x=chart_df['CC Recovered'],
        orientation='h',
        marker_color='#28a745',
        text=[f"${x:,.0f}" for x in chart_df['CC Recovered']],
        textposition='inside',
        textfont=dict(color='white', size=10),
        hovertemplate='<b>%{y}</b><br>Premium Recovered: $%{x:,.0f}<extra></extra>'
    ))
    
    # Red bars - Remaining Loss (stacked after green)
    fig.add_trace(go.Bar(
        name='Remaining Underwater',
        y=chart_df['Symbol'],
        x=chart_df['Remaining'],
        orientation='h',
        marker_color='#dc3545',
        text=[f"${x:,.0f}" for x in chart_df['Remaining']],
        textposition='inside',
        textfont=dict(color='white', size=10),
        hovertemplate='<b>%{y}</b><br>Remaining Underwater: $%{x:,.0f}<extra></extra>'
    ))
    
    # Add recovery percentage annotations on the right
    for i, row in chart_df.iterrows():
        fig.add_annotation(
            x=row['Total Underwater'] + 500,
            y=row['Symbol'],
            text=f"{row['Recovery %']:.0f}%",
            showarrow=False,
            font=dict(color='#888', size=11),
            xanchor='left'
        )
    
    fig.update_layout(
        barmode='stack',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True, 
            gridcolor='rgba(255,255,255,0.1)', 
            color='#888',
            title='Amount ($)', 
            tickprefix='$', 
            tickformat=',.0f',
            side='top'
        ),
        yaxis=dict(
            showgrid=False, 
            color='#888',
            categoryorder='array',
            categoryarray=chart_df['Symbol'].tolist()
        ),
        margin=dict(l=80, r=80, t=40, b=20),
        height=max(400, len(chart_df) * 35),  # Dynamic height based on number of positions
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig)


def render_recovery_tracker(stock_positions: List[Dict], cc_premiums: Dict):
    """
    Render the Position Recovery Tracker
    Shows underwater positions summary, timeline estimates, and strategy recommendations
    (The horizontal bar chart is now rendered separately at the top of the page)
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
    
    # ============================================
    # RECOVERY TIMELINE ESTIMATES
    # ============================================
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
    
    # ============================================
    # STRATEGY RECOMMENDATIONS
    # ============================================
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
