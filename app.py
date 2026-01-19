import streamlit as st
# Force redeploy: 2026-01-16 15:53 MST - Add score buttons + remove oversold checkbox
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure absolute paths for persistent data storage
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

from utils.tastytrade_api import TastytradeAPI
from utils.csp_ladder_manager import render_csp_ladder_manager

# Helper function for RSI formatting with emoji indicators
def format_rsi_with_emoji(rsi_value):
    """Format RSI with color-coded emoji: green (<40), yellow (40-60), red (>60)"""
    try:
        if rsi_value is None:
            return None
        rsi = float(rsi_value)
        if rsi < 40:
            return f"🟢 {round(rsi, 1)}"
        elif rsi < 60:
            return f"🟡 {round(rsi, 1)}"
        else:
            return f"🔴 {round(rsi, 1)}"
    except (ValueError, TypeError):
        return None

# Helper function for BB %B formatting with emoji indicators
def format_bb_with_emoji(bb_value):
    """Format BB %B with color-coded emoji: green (<0.3 oversold), yellow (0.3-0.7), red (>0.7 overbought)"""
    try:
        if bb_value is None:
            return None
        bb = float(bb_value)
        if bb < 0.3:
            return f"🟢 {round(bb, 2)}"  # Green = Oversold (good for selling puts)
        elif bb > 0.7:
            return f"🔴 {round(bb, 2)}"  # Red = Overbought (risky for selling puts)
        else:
            return f"🟡 {round(bb, 2)}"  # Yellow = Neutral
    except (ValueError, TypeError):
        return None

# Helper function for order success celebration (balloons + cha-ching sound)
def celebrate_success():
    """Play cha-ching sound and show balloons for successful order submission"""
    st.balloons()
    # Embed audio player with cha-ching sound (auto-plays)
    cha_ching_audio = """
    <audio autoplay>
        <source src="https://www.myinstants.com/media/sounds/cash-register-purchase.mp3" type="audio/mpeg">
    </audio>
    """
    st.markdown(cha_ching_audio, unsafe_allow_html=True)

# Page config
st.set_page_config(
    page_title="Options Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API with session state for token management
if 'api' not in st.session_state:
    st.session_state.api = TastytradeAPI()

api = st.session_state.api

# Initialize accounts at the top so they are available for the sidebar
if 'accounts' not in st.session_state:
    try:
        accounts_data = api.get_accounts()
        if accounts_data:
            st.session_state.accounts = accounts_data
    except:
        st.session_state.accounts = []

# Initialize splash screen state
if 'splash_shown' not in st.session_state:
    st.session_state.splash_shown = False

# Show splash screen on first load
if not st.session_state.splash_shown:
    # Hide sidebar during splash
    st.markdown("""<style>[data-testid="stSidebar"] { display: none; }</style>""", unsafe_allow_html=True)
    
    # Center content vertically
    st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
    
    # Display banner
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("assets/prosper_trading_banner.png", use_column_width=True)
        st.markdown("""
        <div style='text-align: center; margin-top: 2rem;'>
            <div style='color: #9ca3af; font-size: 16px; letter-spacing: 3px; text-transform: uppercase;'>
                Loading Your Premium Trading Platform
            </div>
            <div style='margin-top: 2rem; display: flex; justify-content: center; gap: 0.5rem;'>
                <div style='width: 12px; height: 12px; border-radius: 50%; background: #d4af37;'></div>
                <div style='width: 12px; height: 12px; border-radius: 50%; background: #d4af37;'></div>
                <div style='width: 12px; height: 12px; border-radius: 50%; background: #d4af37;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Delay and mark as shown
    import time
    time.sleep(2)
    st.session_state.splash_shown = True
    st.rerun()

# Premium Sidebar CSS
st.markdown("""
<style>
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
    }
    
    /* Logo styling */
    .premium-logo {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }
    
    .logo-circle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        border: 2px solid #d4af37;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-weight: bold;
        color: #d4af37;
        background: linear-gradient(135deg, #1a1d23 0%, #0d1117 100%);
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.3);
        margin-bottom: 0.5rem;
    }
    
    .premium-title {
        font-size: 20px;
        font-weight: 600;
        color: #ffffff;
        margin: 0.5rem 0 0.2rem 0;
    }
    
    .premium-subtitle {
        font-size: 12px;
        color: #d4af37;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Account selector */
    .account-box {
        background: #1a1d23;
        border: 1px solid #d4af37;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 1rem 0;
    }
    
    .account-name {
        color: #ffffff;
        font-size: 14px;
        margin-bottom: 0.3rem;
    }
    
    .account-balance {
        color: #10b981;
        font-size: 18px;
        font-weight: 600;
    }
    
    /* Navigation sections */
    .nav-section {
        margin: 1.5rem 0 0.5rem 0;
        color: #d4af37;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    
    /* Radio buttons styling */
    [data-testid="stSidebar"] .stRadio > label {
        display: none;
    }
    
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.3rem;
    }
    
    [data-testid="stSidebar"] .stRadio > div > label {
        background-color: transparent;
        border-left: 3px solid transparent;
        padding: 0.6rem 0.8rem;
        border-radius: 4px;
        transition: all 0.2s;
        color: #9ca3af;
    }
    
    [data-testid="stSidebar"] .stRadio > div > label:hover {
        background-color: #1a1d23;
        color: #ffffff;
    }
    
    [data-testid="stSidebar"] .stRadio > div > label[data-baseweb="radio"] > div:first-child {
        display: none;
    }
    
    /* Selected navigation item */
    [data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
        background-color: #1a1d23;
        border-left: 3px solid #d4af37;
        color: #ffffff;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
    }
    
    /* Quick Stats panel */
    .quick-stats {
        background: #1a1d23;
        border-top: 2px solid #d4af37;
        border-radius: 8px;
        padding: 1rem;
        margin: 1.5rem 0;
    }
    
    .quick-stats-title {
        color: #ffffff;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    
    .stat-row {
        display: flex;
        justify-content: space-between;
        margin: 0.5rem 0;
        font-size: 13px;
    }
    
    .stat-label {
        color: #9ca3af;
    }
    
    .stat-value {
        color: #ffffff;
        font-weight: 600;
    }
    
    .stat-positive {
        color: #10b981;
    }
    
    .stat-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.3rem;
    }
    
    .dot-green { background-color: #10b981; }
    .dot-yellow { background-color: #fbbf24; }
    
    /* Market Status */
    .market-status {
        background: #1a1d23;
        border-radius: 8px;
        padding: 0.8rem;
        margin-top: 1rem;
        text-align: center;
    }
    
    .market-status-text {
        color: #10b981;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    
    .market-status-time {
        color: #6b7280;
        font-size: 12px;
    }
    
    .pulse-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #10b981;
        margin-right: 0.5rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    # Premium Logo with image
    logo_col1, logo_col2 = st.columns([1, 3])
    with logo_col1:
        st.image("assets/prosper_trading_logo.png", width=70)
    with logo_col2:
        st.markdown("""
        <div style="padding-top: 10px;">
            <div style="font-size: 18px; font-weight: 600; color: #ffffff; margin-bottom: 2px;">Prosper Trading</div>
            <div style="font-size: 11px; color: #d4af37; text-transform: uppercase; letter-spacing: 1px;">Premium Platform</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
    
    # Account selector
    accounts = api.get_accounts_with_names()
    
    if accounts:
        account_options = {acc['display']: acc['account_number'] for acc in accounts}
        
        default_account = os.getenv('TASTYTRADE_DEFAULT_ACCOUNT', '')
        default_index = 0
        
        for idx, acc in enumerate(accounts):
            if acc['account_number'] == default_account:
                default_index = idx
                break
        
        selected_display = st.selectbox(
            "Account",
            options=list(account_options.keys()),
            index=default_index,
            label_visibility="collapsed"
        )
        selected_account = account_options[selected_display]
        
        # Get account balance for display
        if selected_account:
            balances = api.get_account_balances(selected_account)
            if balances:
                nlv = float(balances.get('net-liquidating-value', 0))
                st.markdown(f"""
                <div class="account-box">
                    <div class="account-name">{selected_display}</div>
                    <div class="account-balance">${nlv:,.0f} ↗</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error("No accounts found")
        selected_account = None
    
    # Navigation - Combined approach with sections
    st.markdown('<div class="nav-section">TRADING</div>', unsafe_allow_html=True)
    
    # All navigation options
    all_pages = ["🏠 Dashboard", "💵 CSP Dashboard", "📈 Covered Calls", "🎯 PMCC Dashboard", "📊 Performance", "⚙️ Settings"]
    trading_pages = ["🏠 Dashboard", "💵 CSP Dashboard", "📈 Covered Calls", "🎯 PMCC Dashboard", "📊 Performance"]
    
    # Initialize default page
    if 'nav_page' not in st.session_state:
        st.session_state.nav_page = "🏠 Dashboard"
    
    # Trading section radio buttons
    for page_option in trading_pages:
        if st.session_state.nav_page == page_option:
            st.markdown(f'<div style="background-color: #1a1d23; border-left: 3px solid #d4af37; padding: 0.6rem 0.8rem; border-radius: 4px; color: #ffffff; box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);">{page_option}</div>', unsafe_allow_html=True)
        else:
            if st.button(page_option, key=f"nav_{page_option}"):
                st.session_state.nav_page = page_option
                st.rerun()
    
    # Management section
    st.markdown('<div class="nav-section">MANAGEMENT</div>', unsafe_allow_html=True)
    
    if st.session_state.nav_page == "⚙️ Settings":
        st.markdown(f'<div style="background-color: #1a1d23; border-left: 3px solid #d4af37; padding: 0.6rem 0.8rem; border-radius: 4px; color: #ffffff; box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);">⚙️ Settings</div>', unsafe_allow_html=True)
    else:
        if st.button("⚙️ Settings", key="nav_settings"):
            st.session_state.nav_page = "⚙️ Settings"
            st.rerun()
    
    page = st.session_state.nav_page
    
    # Quick Stats Panel
    if selected_account:
        # Aggregate all stats across all accounts
        all_account_numbers = []
        
        # Try to get accounts from session state first
        accounts_list = st.session_state.get('accounts', [])
        
        # If session state is empty, try to fetch them directly
        if not accounts_list:
            try:
                accounts_list = api.get_accounts()
                if accounts_list:
                    st.session_state.accounts = accounts_list
            except:
                pass
        
        # Extract account numbers robustly - handle nested structure from API
        if accounts_list:
            for acc in accounts_list:
                # Try nested structure first (from get_accounts API response)
                acc_num = None
                if isinstance(acc, dict):
                    if 'account' in acc and isinstance(acc['account'], dict):
                        acc_num = acc['account'].get('account-number')
                    # Fallback to flat structure
                    if not acc_num:
                        acc_num = acc.get('account-number') or acc.get('account_number')
                if acc_num:
                    all_account_numbers.append(acc_num)
        
        # Fallback to selected account if still empty
        if not all_account_numbers:
            all_account_numbers = [selected_account]
        
        # Debug: Log which accounts are being used for sidebar stats
        
        # Total positions count
        total_positions = 0
        for acc_num in all_account_numbers:
            try:
                positions = api.get_positions(acc_num)
                total_positions += len(positions) if positions else 0
            except:
                pass
            
        # Total working orders count
        total_orders = 0
        for acc_num in all_account_numbers:
            try:
                orders = api.get_live_orders(acc_num)
                total_orders += len([o for o in orders if o.get('status') == 'Live']) if orders else 0
            except:
                pass
        
        # Get real weekly and monthly premium (aggregated across all accounts)
        from utils.sidebar_stats import get_weekly_premium, get_monthly_premium, get_win_rate
        weekly_premium = get_weekly_premium(api, all_account_numbers)
        monthly_premium = get_monthly_premium(api, all_account_numbers)
        
        # Win rate (average across accounts or from selected)
        win_rate = get_win_rate(api, selected_account)
        
        w_premium_class = "stat-positive" if weekly_premium >= 0 else "stat-negative"
        w_premium_prefix = "+" if weekly_premium >= 0 else "-"
        
        m_premium_class = "stat-positive" if monthly_premium >= 0 else "stat-negative"
        m_premium_prefix = "+" if monthly_premium >= 0 else "-"
        
        st.markdown(f"""
        <div class="quick-stats">
            <div class="quick-stats-title">Quick Stats</div>
            <div class="stat-row">
                <span class="stat-label"><span class="stat-dot dot-green"></span>Open Positions</span>
                <span class="stat-value">{total_positions}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label"><span class="stat-dot dot-yellow"></span>Working Orders</span>
                <span class="stat-value">{total_orders}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">This Week</span>
                <span class="stat-value {w_premium_class}">{w_premium_prefix}${abs(weekly_premium):,.0f}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">This Month</span>
                <span class="stat-value {m_premium_class}">{m_premium_prefix}${abs(monthly_premium):,.0f}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Win Rate</span>
                <span class="stat-value">{win_rate:.0f}% ⭐</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Market Status
    from utils.market_hours import get_market_status
    market_status = get_market_status()
    status_text = "Market Open" if market_status['is_open'] else "Market Closed"
    status_color = "#10b981" if market_status['is_open'] else "#ef4444"
    
    st.markdown(f"""
    <div class="market-status">
        <div class="market-status-text" style="color: {status_color};">
            <span class="pulse-dot" style="background-color: {status_color};"></span>
            {status_text}
        </div>
        <div class="market-status-time">{market_status.get('message', '')}</div>
    </div>
    """, unsafe_allow_html=True)

# Map page names back to original names for compatibility
page_mapping = {
    "🏠 Dashboard": "Home",
    "💵 CSP Dashboard": "CSP Dashboard",
    "📈 Covered Calls": "CC Dashboard",
    "🎯 PMCC Dashboard": "PMCC Dashboard",
    "📊 Performance": "Performance",
    "⚙️ Settings": "Settings"
}
page = page_mapping.get(page, page)

# Main content area
# Premium Home Page CSS
st.markdown("""
<style>
    .premium-metric-card {
        background: linear-gradient(135deg, #1a1d23 0%, #0f1419 100%);
        border: 1px solid #d4af37;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.15);
        margin-bottom: 1rem;
    }
    
    .metric-label {
        color: #9ca3af;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 32px;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    
    .metric-value-positive {
        color: #10b981;
    }
    
    .metric-change {
        color: #10b981;
        font-size: 14px;
    }
    
    .section-header {
        color: #d4af37;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin: 2rem 0 1rem 0;
        border-bottom: 1px solid #d4af37;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Main content area
if page == "Home":
    # Premium Header
    st.markdown('<h1 style="color: #ffffff; font-size: 36px; font-weight: 600; margin-bottom: 0.5rem;">🏠 Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="color: #9ca3af; font-size: 14px; margin-bottom: 2rem;">Welcome back to your premium trading platform</p>', unsafe_allow_html=True)
    
    if selected_account:
        # Get account balances first
        balances = api.get_account_balances(selected_account)
        
        if balances:
            nlv = float(balances.get('net-liquidating-value', 0))
            cash = float(balances.get('cash-balance', 0))
            buying_power = float(balances.get('derivative-buying-power', 0))
            
            # Premium Metric Cards Row
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="premium-metric-card">
                    <div class="metric-label">Net Liquidating Value</div>
                    <div class="metric-value">${nlv:,.0f}</div>
                    <div class="metric-change">↗ +2.3%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="premium-metric-card">
                    <div class="metric-label">Cash Balance</div>
                    <div class="metric-value">${cash:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="premium-metric-card">
                    <div class="metric-label">Buying Power</div>
                    <div class="metric-value metric-value-positive">${buying_power:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Get all account numbers for aggregation (used by both monthly summary and chart)
        all_account_numbers = []
        accounts_list = st.session_state.get('accounts', [])
        
        if accounts_list:
            for acc in accounts_list:
                acc_num = None
                if isinstance(acc, dict):
                    if 'account' in acc and isinstance(acc['account'], dict):
                        acc_num = acc['account'].get('account-number')
                    if not acc_num:
                        acc_num = acc.get('account-number') or acc.get('account_number')
                if acc_num:
                    all_account_numbers.append(acc_num)
        
        # Fallback to selected account if empty
        if not all_account_numbers:
            all_account_numbers = [selected_account]
        
        # Monthly Premium Summary Section
        st.markdown('<div class="section-header">💰 Monthly Premium Performance</div>', unsafe_allow_html=True)
        from utils.monthly_premium import render_monthly_premium_summary
        render_monthly_premium_summary(api, all_account_numbers, call_id="main_dashboard")
        
        st.divider()
        
        # ============================================
        # PREMIUM EARNINGS OVER TIME CHART
        # ============================================
        from utils.monthly_premium import get_live_monthly_premium_data
        import plotly.graph_objects as go
        
        st.subheader("Premium Earnings Over Time")
        
        # Aggregate monthly data across all accounts using LIVE (non-cached) data
        from collections import defaultdict
        aggregated_monthly = defaultdict(lambda: {'net_premium': 0, 'month_name': '', 'month_key': (0, 0)})
        
        for acc_num in all_account_numbers:
            try:
                monthly_data = get_live_monthly_premium_data(api, acc_num, months=6)
                for month in monthly_data:
                    # Use month_year tuple as key for proper sorting
                    key = month.get('month_year', (0, 0))
                    if key == (0, 0):
                        # Fallback: parse from month_name
                        from datetime import datetime as dt
                        try:
                            parsed = dt.strptime(month['month_name'], '%b %Y')
                            key = (parsed.month, parsed.year)
                        except:
                            key = month['month_name']
                    aggregated_monthly[key]['net_premium'] += month['net_premium']
                    aggregated_monthly[key]['month_name'] = month['month_name']
                    aggregated_monthly[key]['month_key'] = key
            except:
                pass
        
        # Convert to sorted list (newest first to match Performance page)
        # Sort by (year, month) tuple descending
        months_list = sorted(
            aggregated_monthly.values(), 
            key=lambda x: (x['month_key'][1], x['month_key'][0]) if isinstance(x['month_key'], tuple) else (0, 0), 
            reverse=True
        )
        
        if months_list:
            month_names = [m['month_name'] for m in months_list]
            monthly_values = [m['net_premium'] for m in months_list]
            
            # Calculate cumulative values
            cumulative_values = []
            running_total = 0
            for v in monthly_values:
                running_total += v
                cumulative_values.append(running_total)
            
            # Create combined bar + line chart
            fig = go.Figure()
            
            # Add bars for monthly premium
            fig.add_trace(go.Bar(
                x=month_names,
                y=monthly_values,
                name='Monthly Net Premium',
                marker_color='#28a745',
                opacity=0.8,
                text=[f"${v:,.0f}" for v in monthly_values],
                textposition='outside'
            ))
            
            # Add line for cumulative premium
            fig.add_trace(go.Scatter(
                x=month_names,
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
        else:
            st.info("No premium data available yet.")
        
        st.divider()
        
        # ============================================
        # RECOVERY PROGRESS BY POSITION CHART
        # ============================================
        from utils.recovery_tracker import render_recovery_chart_only
        from utils.fetch_cc_premiums import fetch_and_save_cc_premiums
        from utils.performance_dashboard import fetch_all_positions_from_api
        
        # Initialize cache for homepage
        if 'home_stock_positions' not in st.session_state:
            st.session_state.home_stock_positions = None
        if 'home_cc_premiums' not in st.session_state:
            st.session_state.home_cc_premiums = None
        
        # Fetch CC premiums from Tastytrade API
        if st.session_state.home_cc_premiums is None:
            with st.spinner("Loading recovery data..."):
                result = fetch_and_save_cc_premiums(api, lookback_days=365)
                if result:
                    st.session_state.home_cc_premiums = result.get('cc_premiums', {})
                else:
                    st.session_state.home_cc_premiums = {}
        
        # Fetch stock positions
        if st.session_state.home_stock_positions is None:
            all_positions = fetch_all_positions_from_api(api)
            st.session_state.home_stock_positions = all_positions.get('stocks', [])
        
        cc_premiums = st.session_state.home_cc_premiums
        stock_positions = st.session_state.home_stock_positions
        
        if stock_positions:
            render_recovery_chart_only(stock_positions, cc_premiums)


elif page == "CSP Dashboard":
    st.title("💰 Cash-Secured Puts Dashboard")
    
    from utils.tradier_api import TradierAPI
    from utils.yahoo_finance import get_technical_indicators
    from utils.cash_secured_puts import get_existing_csp_positions
    
    tradier = TradierAPI()
    
    # Display existing CSP positions
    st.subheader("📊 Existing CSP Positions")
    
    existing_csp_data = get_existing_csp_positions(api, selected_account)
    short_put_details = existing_csp_data['short_put_details']
    
    if short_put_details:
        csp_df = pd.DataFrame(short_put_details)
        
        # Format columns for display
        display_df = csp_df[[
            'symbol', 'contracts', 'strike', 'expiration', 'dte',
            'premium_collected', 'current_value', 'pl', 'pct_recognized', 'collateral_required'
        ]].copy()
        
        display_df.columns = [
            'Symbol', 'Contracts', 'Strike', 'Expiration', 'DTE',
            'Premium Collected', 'Current Value', 'P/L', '% Recognized', 'Collateral'
        ]
        
        # Format currency and percentages
        display_df['Strike'] = display_df['Strike'].apply(lambda x: f"${x:.2f}" if x and x == x else "N/A")
        display_df['Premium Collected'] = display_df['Premium Collected'].apply(lambda x: f"${x:.2f}" if x and x == x else "N/A")
        display_df['Current Value'] = display_df['Current Value'].apply(lambda x: f"${x:.2f}" if x and x == x else "N/A")
        display_df['P/L'] = display_df['P/L'].apply(lambda x: f"${x:.2f}" if x and x == x else "N/A")
        display_df['% Recognized'] = display_df['% Recognized'].apply(lambda x: f"{x:.1f}%" if x and x == x else "N/A")
        display_df['Collateral'] = display_df['Collateral'].apply(lambda x: f"${x:,.0f}" if x and x == x else "N/A")
        
        st.dataframe(display_df, hide_index=True)
        
        # Summary metrics
        total_premium = sum([p['premium_collected'] for p in short_put_details])
        total_current = sum([p['current_value'] for p in short_put_details])
        total_pl = sum([p['pl'] for p in short_put_details])
        total_collateral = sum([p['collateral_required'] for p in short_put_details])
        
        # Get Option Buying Power from Tastytrade API
        # Try derivative-buying-power first (margin accounts), fall back to cash-available-to-withdraw for IRA/cash accounts
        balances = api.get_account_balances(selected_account)
        if balances:
            option_buying_power = float(balances.get('derivative-buying-power', 0))
            # For IRA accounts, derivative-buying-power might be 0, use cash-available-to-withdraw or net-liquidating-value
            if option_buying_power == 0:
                option_buying_power = float(balances.get('cash-available-to-withdraw', 0))
            if option_buying_power == 0:
                option_buying_power = float(balances.get('net-liquidating-value', 0))
        else:
            option_buying_power = 0
        
        available_after_collateral = option_buying_power - total_collateral
        
        # Simplified 3-metric display
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Premium Collected", f"${total_premium:,.2f}")
        with col2:
            st.metric("Total P/L", f"${total_pl:,.2f}", delta=f"{(total_pl/total_premium*100) if total_premium > 0 else 0:.1f}%")
        with col3:
            st.metric("Option Buying Power", f"${option_buying_power:,.0f}", delta=f"${available_after_collateral:,.0f} available")
    else:
        # Show Option Buying Power even when no CSP positions exist
        balances = api.get_account_balances(selected_account)
        if balances:
            option_buying_power = float(balances.get('derivative-buying-power', 0))
            if option_buying_power == 0:
                option_buying_power = float(balances.get('cash-available-to-withdraw', 0))
            if option_buying_power == 0:
                option_buying_power = float(balances.get('net-liquidating-value', 0))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Premium Collected", "$0.00")
            with col2:
                st.metric("Total P/L", "$0.00")
            with col3:
                st.metric("Option Buying Power", f"${option_buying_power:,.0f}", delta="100% available")
        
        st.info("ℹ️ No existing CSP positions found")
    
    st.divider()
    
    # Read watchlist from persistent data directory (using absolute paths)
    watchlist_file = os.path.join(DATA_DIR, 'watchlist.txt')
    default_watchlist_file = os.path.join(BASE_DIR, 'watchlist.txt.default')
    
    try:
        with open(watchlist_file, 'r') as f:
            watchlist = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        # First time setup: copy from default template or create empty
        try:
            import shutil
            if os.path.exists(default_watchlist_file):
                shutil.copy(default_watchlist_file, watchlist_file)
                with open(watchlist_file, 'r') as f:
                    watchlist = [line.strip() for line in f if line.strip()]
            else:
                watchlist = []
        except:
            watchlist = []
    except:
        watchlist = []
    
    # ========== WATCHLIST MANAGEMENT ==========
    st.subheader("📝 Watchlist Management")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.info(f"📋 Currently monitoring **{len(watchlist)}** symbols from watchlist")
    
    with col2:
        if st.button("👁️ View/Edit Watchlist"):
            st.session_state.show_watchlist_editor = not st.session_state.get('show_watchlist_editor', False)
    
    with col3:
        if st.button("🗑️ Clear Watchlist", type="secondary"):
            if len(watchlist) > 0:
                with open(watchlist_file, 'w') as f:
                    f.write("")
                st.success("✅ Watchlist cleared!")
                st.rerun()
    
    # Show watchlist editor if toggled
    if st.session_state.get('show_watchlist_editor', False):
        st.subheader("✏️ Edit Watchlist")
        
        # Add new ticker section
        st.markdown("**➕ Add New Ticker(s)**")
        add_col1, add_col2 = st.columns([3, 1])
        with add_col1:
            new_ticker_input = st.text_input(
                "Enter ticker symbol(s)",
                placeholder="e.g., AAPL or AAPL, MSFT, GOOGL",
                key="new_ticker_input",
                label_visibility="collapsed"
            ).upper().strip()
        with add_col2:
            if st.button("➕ Add Ticker(s)", type="primary"):
                if new_ticker_input:
                    # Parse comma-separated tickers and remove duplicates from input
                    new_tickers = list(dict.fromkeys([t.strip() for t in new_ticker_input.split(',') if t.strip()]))
                    added = []
                    already_in_watchlist = []
                    
                    for ticker in new_tickers:
                        if ticker in watchlist:
                            already_in_watchlist.append(ticker)
                        else:
                            watchlist.append(ticker)
                            added.append(ticker)
                    
                    if added:
                        # Save updated watchlist
                        updated_watchlist = sorted(watchlist)
                        with open(watchlist_file, 'w') as f:
                            for symbol in updated_watchlist:
                                f.write(f"{symbol}\n")
                        st.success(f"✅ Added {len(added)} ticker(s): {', '.join(added)}")
                    
                    if already_in_watchlist:
                        st.info(f"ℹ️ Already in watchlist (skipped): {', '.join(already_in_watchlist)}")
                    
                    if added:
                        # Close the dialog after adding
                        st.session_state.show_watchlist_editor = False
                        st.rerun()
                else:
                    st.warning("⚠️ Please enter a ticker symbol")
        
        st.divider()
        
        if len(watchlist) > 0:
            # Create DataFrame for editing
            watchlist_df = pd.DataFrame({
                'Remove': [False] * len(watchlist),
                'Symbol': watchlist
            })
            
            edited_watchlist = st.data_editor(
                watchlist_df,
                column_config={
                    "Remove": st.column_config.CheckboxColumn(
                        "Remove",
                        help="Check to remove from watchlist",
                        default=False,
                    ),
                    "Symbol": st.column_config.TextColumn("Symbol", disabled=True),
                },
                hide_index=True,
                key="watchlist_editor"
            )
            
            # Remove selected symbols
            if st.button("🗑️ Remove Selected", type="primary"):
                symbols_to_keep = edited_watchlist[edited_watchlist['Remove'] == False]['Symbol'].tolist()
                
                with open(watchlist_file, 'w') as f:
                    for symbol in sorted(symbols_to_keep):
                        f.write(f"{symbol}\n")
                
                removed_count = len(watchlist) - len(symbols_to_keep)
                st.success(f"✅ Removed {removed_count} symbols from watchlist!")
                st.session_state.show_watchlist_editor = False
                st.rerun()
        else:
            st.info("📭 Watchlist is empty. Add stocks from the Analysis Dashboard!")
    
    # Display current watchlist symbols
    if len(watchlist) > 0:
        with st.expander("📊 Current Watchlist Symbols", expanded=True):
            # Display in columns for better readability
            cols_per_row = 8
            rows = [watchlist[i:i+cols_per_row] for i in range(0, len(watchlist), cols_per_row)]
            
            for row in rows:
                cols = st.columns(cols_per_row)
                for idx, symbol in enumerate(row):
                    with cols[idx]:
                        st.markdown(f"**{symbol}**")
    else:
        st.warning("⚠️ Watchlist is empty. Add stocks from the Analysis Dashboard first!")
        st.stop()
    
    st.divider()
    
    # Max orders sett    # Order Submission Settings section removed - no artificial limits on order countfault filter values for fetching (no UI, just defaults)
    min_delta = 0.05
    max_delta = 0.50
    min_volume = 0
    min_oi = 0
    min_dte = 0
    max_dte = 365
    fetch_technicals = False
    
    st.divider()
    
    # Scan buttons row
    scan_col1, scan_col2 = st.columns([3, 1])
    
    with scan_col1:
        fetch_clicked = st.button("🔄 Fetch Opportunities", type="primary")
    
    with scan_col2:
        if st.button("🗑️ Clear Results", key="csp_clear_results", help="Clear all scan results and start fresh"):
            # Clear scan results
            if 'csp_opportunities' in st.session_state:
                del st.session_state.csp_opportunities
            if 'csp_scan_duration' in st.session_state:
                del st.session_state.csp_scan_duration
            if 'csp_active_preset' in st.session_state:
                del st.session_state.csp_active_preset
            st.success("✅ Results cleared!")
            st.rerun()
    
    if fetch_clicked:
      try:
        # Start scan timer
        import time
        scan_start_time = time.time()
        
        # Get existing CSP positions first
        from utils.cash_secured_puts import get_existing_csp_positions
        existing_csp_data = get_existing_csp_positions(api, selected_account)
        existing_short_puts = existing_csp_data['short_puts']  # Dict: symbol -> contracts
        
        # Initialize logging
        log_lines = []
        log_lines.append(f"=== CSP Opportunity Scan Log ===")
        log_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_lines.append(f"Watchlist Size: {len(watchlist)} symbols")
        log_lines.append(f"Existing Short Puts: {existing_short_puts}")
        log_lines.append(f"")
        log_lines.append(f"FILTER SETTINGS:")
        log_lines.append(f"  Min Delta: {min_delta}")
        log_lines.append(f"  Max Delta: {max_delta}")
        log_lines.append(f"  Min Volume: {min_volume}")
        log_lines.append(f"  Min Open Interest: {min_oi}")
        log_lines.append(f"  DTE Range: {min_dte}-{max_dte} days")
        log_lines.append(f"  ⚠️ NO RETURN FILTER - All options shown with calculated returns")
        log_lines.append(f"")
        log_lines.append(f"=" * 80)
        log_lines.append(f"")
        
        # Tracking stats
        stats = {
            'symbols_processed': 0,
            'symbols_with_chains': 0,
            'symbols_no_chains': 0,
            'total_puts_found': 0,
            'puts_after_delta_filter': 0,
            'puts_after_volume_filter': 0,
            'puts_after_oi_filter': 0,
            'rejected_bid_zero': 0,
            'rejected_strike_zero': 0,
            'rejected_dte_zero': 0,
            'used_mid_price': 0,
            'final_opportunities': 0
        }
        
        with st.status(f"Fetching opportunities for {len(watchlist)} symbols...", expanded=True) as status:
            opportunities = []
            
            # Create progress indicators
            progress_bar = st.progress(0, text="Starting scan...")
            
            # OPTIMIZATION 1: Prefetch indicators (RSI + IV Rank) for all symbols in parallel
            progress_bar.progress(0, text="⚡ Prefetching RSI & IV Rank for all symbols (parallel)...")
            st.write(f"⚡ Prefetching technical indicators for {len(watchlist)} symbols...")
            prefetched_indicators = tradier.prefetch_indicators(watchlist, max_workers=10)
            
            # OPTIMIZATION 2: Batch fetch all stock quotes at once
            progress_bar.progress(0.05, text="⚡ Fetching stock quotes in batch...")
            st.write(f"⚡ Batch fetching quotes for {len(watchlist)} symbols...")
            batch_quotes = tradier.get_batch_quotes(watchlist)
            
            # OPTIMIZATION 3: Prefetch option chains for all symbols in parallel
            progress_bar.progress(0.10, text="⚡ Prefetching option chains for all symbols (parallel)...")
            st.write(f"⚡ Prefetching option chains for {len(watchlist)} symbols (5 parallel threads)...")
            prefetched_chains = tradier.prefetch_option_chains(watchlist, min_dte=min_dte, max_dte=max_dte, max_workers=5)
            
            log_lines.append(f"OPTIMIZATION: Prefetched {len(prefetched_indicators)} indicators in parallel")
            log_lines.append(f"OPTIMIZATION: Batch fetched {len(batch_quotes)} quotes")
            log_lines.append(f"OPTIMIZATION: Prefetched {len(prefetched_chains)} option chains in parallel")
            log_lines.append(f"")
            
            for idx, symbol in enumerate(watchlist):
                # Update progress bar with percentage and current symbol (start at 20% after all prefetch)
                progress_pct = 0.2 + (idx + 1) / len(watchlist) * 0.8
                progress_bar.progress(progress_pct, text=f"📊 Processing {symbol}... ({idx+1}/{len(watchlist)}) - {int(progress_pct * 100)}% complete")
                stats['symbols_processed'] += 1
                
                log_lines.append(f"--- {symbol} ---")
                
                # Use prefetched chain data (no API call needed)
                chain_data = prefetched_chains.get(symbol)
                
                if not chain_data:
                    stats['symbols_no_chains'] += 1
                    log_lines.append(f"  ❌ No chain data returned from API")
                    log_lines.append(f"")
                    continue
                
                if not chain_data.get('options'):
                    stats['symbols_no_chains'] += 1
                    log_lines.append(f"  ❌ Chain data exists but no options found")
                    log_lines.append(f"  Underlying Price: ${chain_data.get('underlying_price', 'N/A')}")
                    log_lines.append(f"")
                    continue
                
                stats['symbols_with_chains'] += 1
                underlying_price = chain_data.get('underlying_price', 0)
                log_lines.append(f"  ✅ Chain data received")
                log_lines.append(f"  Underlying Price: ${underlying_price}")
                
                # Get IV Rank, RSI, and BB %B from prefetched cache (no API call needed)
                indicators = prefetched_indicators.get(symbol, {'rsi': None, 'iv_rank': None, 'bb_pct_b': None})
                iv_rank = indicators.get('iv_rank')
                rsi = indicators.get('rsi')
                bb_pct_b = indicators.get('bb_pct_b')
                log_lines.append(f"  IV Rank: {iv_rank if iv_rank else 'N/A'}, RSI: {rsi if rsi else 'N/A'}, BB%B: {bb_pct_b if bb_pct_b else 'N/A'} (cached)")
                
                puts = tradier.filter_put_options(chain_data, min_delta=min_delta, max_delta=max_delta)
                stats['total_puts_found'] += len(puts)
                log_lines.append(f"  Total PUT options in chain: {len(chain_data.get('options', []))}")
                log_lines.append(f"  PUTs after delta filter ({min_delta}-{max_delta}): {len(puts)}")
                
                if len(puts) == 0:
                    log_lines.append(f"  ⚠️ No puts matched delta range")
                    log_lines.append(f"")
                    continue
                
                stats['puts_after_delta_filter'] += len(puts)
                
                puts_passing_filters = 0
                
                for put in puts:
                    volume = put.get('volume', 0)
                    oi = put.get('open_interest', 0)
                    bid = put.get('bid', 0)
                    ask = put.get('ask', 0)
                    strike = put.get('strike', 0)
                    delta = abs(put.get('greeks', {}).get('delta', 0))
                    expiration = put.get('expiration_date', '')
                    
                    # Calculate DTE from expiration date (don't trust Tradier's DTE field)
                    try:
                        exp_date = datetime.strptime(expiration, '%Y-%m-%d')
                        dte = (exp_date - datetime.now()).days
                    except:
                        dte = 0  # Invalid expiration date
                    
                    # Volume filter
                    if volume < min_volume:
                        continue
                    stats['puts_after_volume_filter'] += 1
                    
                    # OI filter
                    if oi < min_oi:
                        continue
                    stats['puts_after_oi_filter'] += 1
                    
                    # Use mid-price if bid is 0 (market closed or low liquidity)
                    if bid <= 0 and ask > 0:
                        bid = ask / 2  # Use half of ask as estimate
                        stats['used_mid_price'] += 1
                    
                    # Validate data (skip if still invalid)
                    if bid <= 0:
                        stats['rejected_bid_zero'] += 1
                        continue
                    if strike <= 0:
                        stats['rejected_strike_zero'] += 1
                        continue
                    if dte <= 0:
                        stats['rejected_dte_zero'] += 1
                        continue
                    
                    # Calculate returns (NO FILTER, just calculate)
                    premium_pct = (bid / strike) * 100
                    
                    # Weekly return (normalized to 7 days)
                    weekly_return = (premium_pct / dte) * 7
                    
                    # Monthly return (normalized to 30 days)
                    monthly_return = (premium_pct / dte) * 30
                    
                    # Annual return (normalized to 365 days)
                    annual_return = (premium_pct / dte) * 365
                    
                    puts_passing_filters += 1
                    
                    # Check for existing CSP positions on this symbol
                    existing_contracts = existing_short_puts.get(symbol, 0)
                    
                    # Calculate spread percentage and MID price
                    mid = (bid + ask) / 2
                    spread_pct = ((ask - bid) / mid * 100) if mid > 0 else 999
                    
                    opp = {
                        'Symbol': symbol,
                        'Strike': strike,
                        'Current Price': underlying_price,
                        'Expiration': expiration,
                        'DTE': dte,
                        'Premium': round(mid, 2),  # MID price for order submission
                        'Bid': bid,
                        'Ask': ask,
                        'Premium %': round(premium_pct, 2),
                        'Weekly %': round(weekly_return, 2),
                        'Monthly %': round(monthly_return, 2),
                        'Annual %': round(annual_return, 1),
                        'Delta': round(delta, 2),
                        'Theta': round(put.get('greeks', {}).get('theta', 0), 3),
                        'Volume': volume,
                        'Open Int': oi,
                        'RSI': format_rsi_with_emoji(rsi),
                        'IV Rank': round(iv_rank, 1) if iv_rank else None,
                        'BB %B': format_bb_with_emoji(bb_pct_b),
                        'Spread %': round(spread_pct, 1),
                        'Existing CSPs': existing_contracts,
                    }
                    
                    if fetch_technicals:
                        indicators = get_technical_indicators(symbol)
                        if indicators:
                            opp['RSI'] = round(indicators['rsi'], 1) if indicators['rsi'] else None
                            opp['BB %'] = round(indicators['bb_percent'], 1) if indicators['bb_percent'] else None
                            opp['52W %'] = round(indicators['week_52_percent'], 1) if indicators['week_52_percent'] else None
                    
                    opportunities.append(opp)
                
                log_lines.append(f"  ✅ Final opportunities from {symbol}: {puts_passing_filters}")
                log_lines.append(f"")
            
            stats['final_opportunities'] = len(opportunities)
            
            # Calculate scan duration
            scan_duration = time.time() - scan_start_time
            scan_minutes = int(scan_duration // 60)
            scan_seconds = scan_duration % 60
            
            if scan_minutes > 0:
                status.update(label=f"✅ Scan complete in {scan_minutes}m {scan_seconds:.1f}s!", state="complete")
            else:
                status.update(label=f"✅ Scan complete in {scan_seconds:.1f}s!", state="complete")
            
            # Store scan duration in session state
            st.session_state.csp_scan_duration = scan_duration
        
        # Add summary to log
        log_lines.append(f"")
        log_lines.append(f"=" * 80)
        log_lines.append(f"SUMMARY STATISTICS:")
        log_lines.append(f"  Symbols Processed: {stats['symbols_processed']}")
        log_lines.append(f"  Symbols with Chain Data: {stats['symbols_with_chains']}")
        log_lines.append(f"  Symbols with NO Chain Data: {stats['symbols_no_chains']}")
        log_lines.append(f"  Total PUT options found: {stats['total_puts_found']}")
        log_lines.append(f"  After Delta filter: {stats['puts_after_delta_filter']}")
        log_lines.append(f"  After Volume filter: {stats['puts_after_volume_filter']}")
        log_lines.append(f"  After OI filter: {stats['puts_after_oi_filter']}")
        log_lines.append(f"  Used mid-price (bid=0): {stats['used_mid_price']}")
        log_lines.append(f"  Rejected (bid=0): {stats['rejected_bid_zero']}")
        log_lines.append(f"  Rejected (strike=0): {stats['rejected_strike_zero']}")
        log_lines.append(f"  Rejected (dte=0): {stats['rejected_dte_zero']}")
        log_lines.append(f"  FINAL OPPORTUNITIES: {stats['final_opportunities']}")
        log_lines.append(f"")
        log_lines.append(f"=" * 80)
        
        # Store log in session state
        st.session_state.csp_scan_log = "\n".join(log_lines)
        
        # Display summary stats
        st.subheader("📊 Scan Summary")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Symbols Scanned", stats['symbols_processed'])
        with col2:
            st.metric("With Chain Data", stats['symbols_with_chains'])
        with col3:
            st.metric("Total PUTs Found", stats['total_puts_found'])
        with col4:
            st.metric("Final Opportunities", stats['final_opportunities'])
        with col5:
            if scan_minutes > 0:
                st.metric("⏱️ Scan Time", f"{scan_minutes}m {scan_seconds:.0f}s")
            else:
                st.metric("⏱️ Scan Time", f"{scan_seconds:.1f}s")
        
        if stats['used_mid_price'] > 0:
            st.info(f"ℹ️ Used mid-price for {stats['used_mid_price']} options (bid was $0)")
        
        if stats['rejected_bid_zero'] > 0:
            st.warning(f"⚠️ Rejected {stats['rejected_bid_zero']} options due to bid=$0 (even after mid-price fallback)")
        
        # Store scan time for validation later
        st.session_state.csp_scan_time = datetime.now()
        
        # Store opportunities in session state for display
        if opportunities:
            df = pd.DataFrame(opportunities)
            
            # Calculate CSP Composite Score (0-100)
            def calculate_csp_score(row):
                """
                CSP Composite Score based on:
                - Weekly Return % (25%): Higher = Better
                - Delta (20%): Closer to 0.30 = Best (sweet spot)
                - RSI (20%): Lower = Better (oversold stocks bounce)
                - BB %B (15%): Lower = Better (near lower band)
                - IV Rank (10%): Higher = Better (elevated premium)
                - Spread % (10%): Lower = Better (tighter spreads)
                """
                score = 0
                
                # 1. Weekly Return % (25 points) - Scale 0.5% to 2.5%
                weekly = row.get('Weekly %', 0) or 0
                if weekly >= 2.5:
                    score += 25
                elif weekly >= 0.5:
                    score += 25 * (weekly - 0.5) / 2.0
                
                # 2. Delta (20 points) - Sweet spot around 0.25-0.35
                delta = abs(row.get('Delta', 0) or 0)
                if 0.25 <= delta <= 0.35:
                    score += 20  # Perfect range
                elif 0.15 <= delta <= 0.45:
                    score += 15  # Good range
                elif 0.10 <= delta <= 0.50:
                    score += 10  # Acceptable
                else:
                    score += 5  # Outside ideal range
                
                # 3. RSI (20 points) - Lower is better for CSP (oversold)
                rsi_val = row.get('RSI', None)
                if rsi_val is not None:
                    # Extract numeric RSI from emoji string if needed
                    if isinstance(rsi_val, str):
                        import re
                        match = re.search(r'[\d.]+', str(rsi_val))
                        rsi_val = float(match.group()) if match else 50
                    if rsi_val < 30:
                        score += 20  # Oversold - excellent
                    elif rsi_val < 40:
                        score += 16
                    elif rsi_val < 50:
                        score += 12
                    elif rsi_val < 60:
                        score += 8
                    elif rsi_val < 70:
                        score += 4
                    # > 70 = 0 points (overbought)
                else:
                    score += 10  # Neutral if no data
                
                # 4. BB %B (15 points) - Lower is better for CSP
                bb = row.get('BB %B', None)
                if bb is not None:
                    # Extract numeric BB from emoji string if needed
                    if isinstance(bb, str):
                        import re
                        match = re.search(r'[\d.]+', str(bb))
                        bb = float(match.group()) if match else 0.5
                    if bb < 0.2:
                        score += 15  # Near lower band - excellent
                    elif bb < 0.3:
                        score += 12
                    elif bb < 0.5:
                        score += 9
                    elif bb < 0.7:
                        score += 6
                    elif bb < 0.8:
                        score += 3
                    # > 0.8 = 0 points (near upper band)
                else:
                    score += 7  # Neutral if no data
                
                # 5. IV Rank (10 points) - Higher is better
                iv = row.get('IV Rank', None)
                if iv is not None:
                    if iv > 75:
                        score += 10
                    elif iv > 50:
                        score += 8
                    elif iv > 30:
                        score += 5
                    else:
                        score += 2
                else:
                    score += 5  # Neutral if no data
                
                # 6. Spread % (10 points) - Lower is better
                spread = row.get('Spread %', None)
                if spread is not None:
                    if spread <= 1:
                        score += 10
                    elif spread <= 3:
                        score += 8
                    elif spread <= 5:
                        score += 5
                    elif spread <= 10:
                        score += 2
                    # > 10% = 0 points
                else:
                    score += 5  # Neutral if no data
                
                return round(score)
            
            # Apply score calculation to each row
            df['score'] = df.apply(calculate_csp_score, axis=1)
            
            df.insert(0, 'Select', False)
            df.insert(1, 'Qty', 1)  # Add quantity column with default value of 1
            df = df.sort_values('score', ascending=False)  # Sort by score instead of Weekly %
            st.session_state.csp_opportunities = df
            
            # Reset UI state after fresh scan - show all opportunities, no filters
            st.session_state.csp_show_selected_only = False  # Show all opportunities
            st.session_state.csp_min_score = 0  # Reset score filter to 0 (no filter)
            st.session_state.csp_active_preset = None  # Clear any active preset
            
            # Force rerun to update toggle widget state
            st.rerun()
        else:
            # Clear opportunities if none found
            if 'csp_opportunities' in st.session_state:
                del st.session_state.csp_opportunities
      except Exception as e:
        st.error(f"❌ Scan Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    # Display opportunities if they exist in session state
    if 'csp_opportunities' in st.session_state and len(st.session_state.csp_opportunities) > 0:
        # Get the DataFrame from session state
        df = st.session_state.csp_opportunities
        
        st.success(f"✅ Found {len(df)} opportunities!")
        
        # Store in session state (always update with fresh scan results)
        st.session_state.csp_opportunities_fresh = True
        
        # Selection controls
        st.subheader("📋 Select Options to Trade")
        
        # Initialize preset criteria in session state (defaults)
        if 'csp_conservative_delta_min' not in st.session_state:
            st.session_state.csp_conservative_delta_min = 0.10
            st.session_state.csp_conservative_delta_max = 0.20
            st.session_state.csp_conservative_dte_min = 7
            st.session_state.csp_conservative_dte_max = 30
            st.session_state.csp_conservative_oi_min = 50
        # Initialize RSI, IV Rank, BB %B separately to handle existing sessions
        if 'csp_conservative_rsi_max' not in st.session_state:
            st.session_state.csp_conservative_rsi_max = 70  # Filter overbought only
        if 'csp_conservative_iv_rank_min' not in st.session_state:
            st.session_state.csp_conservative_iv_rank_min = 0  # No IV filter by default
        if 'csp_conservative_bb_max' not in st.session_state:
            st.session_state.csp_conservative_bb_max = 1.0  # No BB filter by default
        if 'csp_conservative_min_score' not in st.session_state:
            st.session_state.csp_conservative_min_score = 50  # Min composite score for Conservative
        
        if 'csp_medium_delta_min' not in st.session_state:
            st.session_state.csp_medium_delta_min = 0.15
            st.session_state.csp_medium_delta_max = 0.30
            st.session_state.csp_medium_dte_min = 7
            st.session_state.csp_medium_dte_max = 30
            st.session_state.csp_medium_oi_min = 50
        if 'csp_medium_rsi_max' not in st.session_state:
            st.session_state.csp_medium_rsi_max = 80  # Slight overbought filter
        if 'csp_medium_iv_rank_min' not in st.session_state:
            st.session_state.csp_medium_iv_rank_min = 0  # No IV filter by default
        if 'csp_medium_bb_max' not in st.session_state:
            st.session_state.csp_medium_bb_max = 1.0  # No BB filter by default
        if 'csp_medium_min_score' not in st.session_state:
            st.session_state.csp_medium_min_score = 40  # Min composite score for Medium
        
        if 'csp_aggressive_delta_min' not in st.session_state:
            st.session_state.csp_aggressive_delta_min = 0.20
            st.session_state.csp_aggressive_delta_max = 0.40
            st.session_state.csp_aggressive_dte_min = 7
            st.session_state.csp_aggressive_dte_max = 21
            st.session_state.csp_aggressive_oi_min = 25
        if 'csp_aggressive_rsi_max' not in st.session_state:
            st.session_state.csp_aggressive_rsi_max = 100  # No RSI filter
        if 'csp_aggressive_iv_rank_min' not in st.session_state:
            st.session_state.csp_aggressive_iv_rank_min = 0  # No IV filter by default
        if 'csp_aggressive_bb_max' not in st.session_state:
            st.session_state.csp_aggressive_bb_max = 1.0  # No BB filter by default
        if 'csp_aggressive_min_score' not in st.session_state:
            st.session_state.csp_aggressive_min_score = 30  # Min composite score for Aggressive
        
        # Initialize oversold filter toggle
        if 'csp_oversold_filter' not in st.session_state:
            st.session_state.csp_oversold_filter = False
        
        # Helper function to select best per ticker
        def select_best_csp_per_ticker(df, delta_min, delta_max, dte_min, dte_max, oi_min, rsi_max=100, iv_rank_min=0, bb_max=1.0, oversold_only=False, qty=1, min_score=0):
            """Select best CSP option per ticker based on criteria including RSI, IV Rank, BB %B, and Score filters"""
            selections = []
            
            # Helper function to extract numeric RSI from emoji string
            def extract_rsi(rsi_val):
                if rsi_val is None:
                    return None
                if isinstance(rsi_val, (int, float)):
                    return float(rsi_val)
                # Extract number from string like "🟢 35.2" or "🟡 52.1"
                try:
                    import re
                    match = re.search(r'[\d.]+', str(rsi_val))
                    return float(match.group()) if match else None
                except:
                    return None
            
            # Filter by criteria (using correct column names from DataFrame)
            filtered = df[
                (df['Delta'].abs() >= delta_min) &
                (df['Delta'].abs() <= delta_max) &
                (df['DTE'] >= dte_min) &
                (df['DTE'] <= dte_max) &
                (df['Open Int'] >= oi_min)
            ]
            
            # Apply RSI filter if RSI column exists and rsi_max < 100
            if 'RSI' in filtered.columns and rsi_max < 100:
                filtered = filtered[filtered['RSI'].apply(lambda x: extract_rsi(x) is None or extract_rsi(x) <= rsi_max)]
            
            # Apply IV Rank filter if column exists and iv_rank_min > 0
            if 'IV Rank' in filtered.columns and iv_rank_min > 0:
                filtered = filtered[filtered['IV Rank'].apply(lambda x: x is None or x >= iv_rank_min)]
            
            # Apply BB %B filter if column exists and bb_max < 1.0
            if 'BB %B' in filtered.columns and bb_max < 1.0:
                def check_bb_max(x):
                    if x is None or pd.isna(x):
                        return True
                    if isinstance(x, str):
                        return True  # Skip string values like 'N/A'
                    try:
                        return float(x) <= bb_max
                    except (ValueError, TypeError):
                        return True
                filtered = filtered[filtered['BB %B'].apply(check_bb_max)]
            
            # Apply oversold filter if enabled (RSI < 40 AND BB %B < 0.3)
            if oversold_only:
                if 'RSI' in filtered.columns:
                    filtered = filtered[filtered['RSI'].apply(lambda x: extract_rsi(x) is None or extract_rsi(x) < 40)]
                if 'BB %B' in filtered.columns:
                    def check_bb_oversold(x):
                        if x is None or pd.isna(x):
                            return True
                        if isinstance(x, str):
                            return True  # Skip string values like 'N/A'
                        try:
                            return float(x) < 0.3
                        except (ValueError, TypeError):
                            return True
                    filtered = filtered[filtered['BB %B'].apply(check_bb_oversold)]
            
            # Apply minimum score filter if Score column exists and min_score > 0
            if 'Score' in filtered.columns and min_score > 0:
                filtered = filtered[filtered['Score'] >= min_score]
            
            if len(filtered) == 0:
                return selections
            
            # Group by symbol and select best (highest Score, then Weekly %)
            for symbol in filtered['Symbol'].unique():
                symbol_opps = filtered[filtered['Symbol'] == symbol]
                if len(symbol_opps) > 0:
                    # Select highest Score for this symbol (fall back to Weekly % if no Score)
                    if 'Score' in symbol_opps.columns:
                        best_idx = symbol_opps['Score'].idxmax()
                    else:
                        best_idx = symbol_opps['Weekly %'].idxmax()
                    selections.append((best_idx, qty))
            
            return selections
        
        # Preset Filter Buttons
        st.write("")
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1.5, 1.5, 1.5, 1, 1])
        
        with col1:
            if st.button("🗑️ Clear All", key="csp_clear_all"):
                st.session_state.csp_opportunities['Select'] = False
                st.rerun()
        
        with col2:
            if st.button("🟢 Conservative", key="csp_preset_conservative", 
                       help=f"Δ {st.session_state.csp_conservative_delta_min}-{st.session_state.csp_conservative_delta_max}, DTE {st.session_state.csp_conservative_dte_min}-{st.session_state.csp_conservative_dte_max}, OI ≥{st.session_state.csp_conservative_oi_min}, RSI ≤{st.session_state.csp_conservative_rsi_max}, Score ≥{st.session_state.csp_conservative_min_score}"):
                # Track active preset for Delta formatting
                st.session_state.csp_active_preset = 'conservative'
                
                # Clear all first
                st.session_state.csp_opportunities['Select'] = False
                st.session_state.csp_opportunities['Qty'] = 1
                
                # Use smart per-ticker selection with all filters
                selections = select_best_csp_per_ticker(
                    st.session_state.csp_opportunities,
                    st.session_state.csp_conservative_delta_min,
                    st.session_state.csp_conservative_delta_max,
                    st.session_state.csp_conservative_dte_min,
                    st.session_state.csp_conservative_dte_max,
                    st.session_state.csp_conservative_oi_min,
                    rsi_max=st.session_state.csp_conservative_rsi_max,
                    iv_rank_min=st.session_state.csp_conservative_iv_rank_min,
                    bb_max=st.session_state.csp_conservative_bb_max,
                    oversold_only=st.session_state.csp_oversold_filter,
                    qty=1,
                    min_score=st.session_state.csp_conservative_min_score
                )
                
                # Apply selections
                for idx, qty in selections:
                    st.session_state.csp_opportunities.loc[idx, 'Select'] = True
                    st.session_state.csp_opportunities.loc[idx, 'Qty'] = qty
                
                st.rerun()
        
        with col3:
            if st.button("🟡 Medium", key="csp_preset_medium",
                       help=f"Δ {st.session_state.csp_medium_delta_min}-{st.session_state.csp_medium_delta_max}, DTE {st.session_state.csp_medium_dte_min}-{st.session_state.csp_medium_dte_max}, OI ≥{st.session_state.csp_medium_oi_min}, RSI ≤{st.session_state.csp_medium_rsi_max}, Score ≥{st.session_state.csp_medium_min_score}"):
                # Track active preset for Delta formatting
                st.session_state.csp_active_preset = 'medium'
                
                # Clear all first
                st.session_state.csp_opportunities['Select'] = False
                st.session_state.csp_opportunities['Qty'] = 1
                
                # Use smart per-ticker selection with all filters
                selections = select_best_csp_per_ticker(
                    st.session_state.csp_opportunities,
                    st.session_state.csp_medium_delta_min,
                    st.session_state.csp_medium_delta_max,
                    st.session_state.csp_medium_dte_min,
                    st.session_state.csp_medium_dte_max,
                    st.session_state.csp_medium_oi_min,
                    rsi_max=st.session_state.csp_medium_rsi_max,
                    iv_rank_min=st.session_state.csp_medium_iv_rank_min,
                    bb_max=st.session_state.csp_medium_bb_max,
                    oversold_only=st.session_state.csp_oversold_filter,
                    qty=1,
                    min_score=st.session_state.csp_medium_min_score
                )
                
                # Apply selections
                for idx, qty in selections:
                    st.session_state.csp_opportunities.loc[idx, 'Select'] = True
                    st.session_state.csp_opportunities.loc[idx, 'Qty'] = qty
                
                st.rerun()
        
        with col4:
            if st.button("🔴 Aggressive", key="csp_preset_aggressive",
                       help=f"Δ {st.session_state.csp_aggressive_delta_min}-{st.session_state.csp_aggressive_delta_max}, DTE {st.session_state.csp_aggressive_dte_min}-{st.session_state.csp_aggressive_dte_max}, OI ≥{st.session_state.csp_aggressive_oi_min}, RSI ≤{st.session_state.csp_aggressive_rsi_max}, Score ≥{st.session_state.csp_aggressive_min_score}"):
                # Track active preset for Delta formatting
                st.session_state.csp_active_preset = 'aggressive'
                
                # Clear all first
                st.session_state.csp_opportunities['Select'] = False
                st.session_state.csp_opportunities['Qty'] = 1
                
                # Use smart per-ticker selection with all filters (Aggressive has looser limits)
                selections = select_best_csp_per_ticker(
                    st.session_state.csp_opportunities,
                    st.session_state.csp_aggressive_delta_min,
                    st.session_state.csp_aggressive_delta_max,
                    st.session_state.csp_aggressive_dte_min,
                    st.session_state.csp_aggressive_dte_max,
                    st.session_state.csp_aggressive_oi_min,
                    rsi_max=st.session_state.csp_aggressive_rsi_max,
                    iv_rank_min=st.session_state.csp_aggressive_iv_rank_min,
                    bb_max=st.session_state.csp_aggressive_bb_max,
                    oversold_only=st.session_state.csp_oversold_filter,
                    qty=1,
                    min_score=st.session_state.csp_aggressive_min_score
                )
                
                # Apply selections
                for idx, qty in selections:
                    st.session_state.csp_opportunities.loc[idx, 'Select'] = True
                    st.session_state.csp_opportunities.loc[idx, 'Qty'] = qty
                
                st.rerun()
        
        with col5:
            if st.button("✅ Select All", key="csp_select_all"):
                st.session_state.csp_opportunities['Select'] = True
                st.rerun()
        
        with col6:
            selected_count = st.session_state.csp_opportunities['Select'].sum()
            st.metric("Selected", selected_count)
        
        st.write("")
        st.write("---")
        
        # Filter Configuration Expanders
        st.subheader("⚙️ Preset Filter Configuration")
        
        # Conservative Expander
        with st.expander("🟢 Conservative Filter Configuration", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                cons_delta_min = st.number_input("Min Delta", value=st.session_state.csp_conservative_delta_min, min_value=0.0, max_value=1.0, step=0.01, key="csp_cons_delta_min_input")
                cons_delta_max = st.number_input("Max Delta", value=st.session_state.csp_conservative_delta_max, min_value=0.0, max_value=1.0, step=0.01, key="csp_cons_delta_max_input")
            with col2:
                cons_dte_min = st.number_input("Min DTE", value=st.session_state.csp_conservative_dte_min, min_value=0, max_value=365, step=1, key="csp_cons_dte_min_input")
                cons_dte_max = st.number_input("Max DTE", value=st.session_state.csp_conservative_dte_max, min_value=0, max_value=365, step=1, key="csp_cons_dte_max_input")
            with col3:
                cons_oi_min = st.number_input("Min Open Interest", value=st.session_state.csp_conservative_oi_min, min_value=0, step=10, key="csp_cons_oi_min_input")
                cons_rsi_max = st.number_input("Max RSI", value=st.session_state.csp_conservative_rsi_max, min_value=0, max_value=100, step=5, key="csp_cons_rsi_max_input", help="Filter out overbought stocks. Lower = more conservative.")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                cons_iv_rank_min = st.number_input("Min IV Rank", value=st.session_state.csp_conservative_iv_rank_min, min_value=0, max_value=100, step=5, key="csp_cons_iv_rank_min_input", help="Higher IV = better premium. 30+ recommended.")
            with col2:
                cons_bb_max = st.number_input("Max BB %B", value=st.session_state.csp_conservative_bb_max, min_value=0.0, max_value=1.5, step=0.1, key="csp_cons_bb_max_input", help="Lower = stock near lower band. 0.5 = middle of range.")
            with col3:
                cons_min_score = st.number_input("Min Score", value=st.session_state.csp_conservative_min_score, min_value=0, max_value=100, step=5, key="csp_cons_min_score_input", help="Minimum composite score (0-100). Higher = stricter quality filter.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Commit Conservative", key="csp_commit_conservative"):
                    st.session_state.csp_conservative_delta_min = cons_delta_min
                    st.session_state.csp_conservative_delta_max = cons_delta_max
                    st.session_state.csp_conservative_dte_min = cons_dte_min
                    st.session_state.csp_conservative_dte_max = cons_dte_max
                    st.session_state.csp_conservative_oi_min = cons_oi_min
                    st.session_state.csp_conservative_rsi_max = cons_rsi_max
                    st.session_state.csp_conservative_iv_rank_min = cons_iv_rank_min
                    st.session_state.csp_conservative_bb_max = cons_bb_max
                    st.session_state.csp_conservative_min_score = cons_min_score
                    st.success("✅ Conservative criteria committed!")
                    st.rerun()
            with col2:
                if st.button("🔄 Reset Conservative", key="csp_reset_conservative"):
                    st.session_state.csp_conservative_delta_min = 0.10
                    st.session_state.csp_conservative_delta_max = 0.20
                    st.session_state.csp_conservative_dte_min = 7
                    st.session_state.csp_conservative_dte_max = 30
                    st.session_state.csp_conservative_oi_min = 50
                    st.session_state.csp_conservative_rsi_max = 70  # Filter overbought only
                    st.session_state.csp_conservative_iv_rank_min = 0  # No IV filter
                    st.session_state.csp_conservative_bb_max = 1.0  # No BB filter
                    st.session_state.csp_conservative_min_score = 50  # Default min score
                    st.success("✅ Conservative reset to defaults!")
                    st.rerun()
        
        # Medium Expander
        with st.expander("🟡 Medium Filter Configuration", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                med_delta_min = st.number_input("Min Delta", value=st.session_state.csp_medium_delta_min, min_value=0.0, max_value=1.0, step=0.01, key="csp_med_delta_min_input")
                med_delta_max = st.number_input("Max Delta", value=st.session_state.csp_medium_delta_max, min_value=0.0, max_value=1.0, step=0.01, key="csp_med_delta_max_input")
            with col2:
                med_dte_min = st.number_input("Min DTE", value=st.session_state.csp_medium_dte_min, min_value=0, max_value=365, step=1, key="csp_med_dte_min_input")
                med_dte_max = st.number_input("Max DTE", value=st.session_state.csp_medium_dte_max, min_value=0, max_value=365, step=1, key="csp_med_dte_max_input")
            with col3:
                med_oi_min = st.number_input("Min Open Interest", value=st.session_state.csp_medium_oi_min, min_value=0, step=10, key="csp_med_oi_min_input")
                med_rsi_max = st.number_input("Max RSI", value=st.session_state.csp_medium_rsi_max, min_value=0, max_value=100, step=5, key="csp_med_rsi_max_input", help="Filter out overbought stocks. Lower = more conservative.")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                med_iv_rank_min = st.number_input("Min IV Rank", value=st.session_state.csp_medium_iv_rank_min, min_value=0, max_value=100, step=5, key="csp_med_iv_rank_min_input", help="Higher IV = better premium. 40+ recommended.")
            with col2:
                med_bb_max = st.number_input("Max BB %B", value=st.session_state.csp_medium_bb_max, min_value=0.0, max_value=1.5, step=0.1, key="csp_med_bb_max_input", help="Lower = stock near lower band. 0.6 = slightly below middle.")
            with col3:
                med_min_score = st.number_input("Min Score", value=st.session_state.csp_medium_min_score, min_value=0, max_value=100, step=5, key="csp_med_min_score_input", help="Minimum composite score (0-100). Higher = stricter quality filter.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Commit Medium", key="csp_commit_medium"):
                    st.session_state.csp_medium_delta_min = med_delta_min
                    st.session_state.csp_medium_delta_max = med_delta_max
                    st.session_state.csp_medium_dte_min = med_dte_min
                    st.session_state.csp_medium_dte_max = med_dte_max
                    st.session_state.csp_medium_oi_min = med_oi_min
                    st.session_state.csp_medium_rsi_max = med_rsi_max
                    st.session_state.csp_medium_iv_rank_min = med_iv_rank_min
                    st.session_state.csp_medium_bb_max = med_bb_max
                    st.session_state.csp_medium_min_score = med_min_score
                    st.success("✅ Medium criteria committed!")
                    st.rerun()
            with col2:
                if st.button("🔄 Reset Medium", key="csp_reset_medium"):
                    st.session_state.csp_medium_delta_min = 0.15
                    st.session_state.csp_medium_delta_max = 0.30
                    st.session_state.csp_medium_dte_min = 7
                    st.session_state.csp_medium_dte_max = 30
                    st.session_state.csp_medium_oi_min = 50
                    st.session_state.csp_medium_rsi_max = 80  # Slight overbought filter
                    st.session_state.csp_medium_iv_rank_min = 0  # No IV filter
                    st.session_state.csp_medium_bb_max = 1.0  # No BB filter
                    st.session_state.csp_medium_min_score = 40  # Default min score
                    st.success("✅ Medium reset to defaults!")
                    st.rerun()
        
        # Aggressive Expander
        with st.expander("🔴 Aggressive Filter Configuration", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                agg_delta_min = st.number_input("Min Delta", value=st.session_state.csp_aggressive_delta_min, min_value=0.0, max_value=1.0, step=0.01, key="csp_agg_delta_min_input")
                agg_delta_max = st.number_input("Max Delta", value=st.session_state.csp_aggressive_delta_max, min_value=0.0, max_value=1.0, step=0.01, key="csp_agg_delta_max_input")
            with col2:
                agg_dte_min = st.number_input("Min DTE", value=st.session_state.csp_aggressive_dte_min, min_value=0, max_value=365, step=1, key="csp_agg_dte_min_input")
                agg_dte_max = st.number_input("Max DTE", value=st.session_state.csp_aggressive_dte_max, min_value=0, max_value=365, step=1, key="csp_agg_dte_max_input")
            with col3:
                agg_oi_min = st.number_input("Min Open Interest", value=st.session_state.csp_aggressive_oi_min, min_value=0, step=10, key="csp_agg_oi_min_input")
                agg_rsi_max = st.number_input("Max RSI", value=st.session_state.csp_aggressive_rsi_max, min_value=0, max_value=100, step=5, key="csp_agg_rsi_max_input", help="Set to 100 for no RSI filter.")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                agg_iv_rank_min = st.number_input("Min IV Rank", value=st.session_state.csp_aggressive_iv_rank_min, min_value=0, max_value=100, step=5, key="csp_agg_iv_rank_min_input", help="Higher IV = better premium. 50+ for aggressive.")
            with col2:
                agg_bb_max = st.number_input("Max BB %B", value=st.session_state.csp_aggressive_bb_max, min_value=0.0, max_value=1.5, step=0.1, key="csp_agg_bb_max_input", help="Set to 1.0+ for no BB filter.")
            with col3:
                agg_min_score = st.number_input("Min Score", value=st.session_state.csp_aggressive_min_score, min_value=0, max_value=100, step=5, key="csp_agg_min_score_input", help="Minimum composite score (0-100). Higher = stricter quality filter.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Commit Aggressive", key="csp_commit_aggressive"):
                    st.session_state.csp_aggressive_delta_min = agg_delta_min
                    st.session_state.csp_aggressive_delta_max = agg_delta_max
                    st.session_state.csp_aggressive_dte_min = agg_dte_min
                    st.session_state.csp_aggressive_dte_max = agg_dte_max
                    st.session_state.csp_aggressive_oi_min = agg_oi_min
                    st.session_state.csp_aggressive_rsi_max = agg_rsi_max
                    st.session_state.csp_aggressive_iv_rank_min = agg_iv_rank_min
                    st.session_state.csp_aggressive_bb_max = agg_bb_max
                    st.session_state.csp_aggressive_min_score = agg_min_score
                    st.success("✅ Aggressive criteria committed!")
                    st.rerun()
            with col2:
                if st.button("🔄 Reset Aggressive", key="csp_reset_aggressive"):
                    st.session_state.csp_aggressive_delta_min = 0.20
                    st.session_state.csp_aggressive_delta_max = 0.40
                    st.session_state.csp_aggressive_dte_min = 7
                    st.session_state.csp_aggressive_dte_max = 21
                    st.session_state.csp_aggressive_oi_min = 25
                    st.session_state.csp_aggressive_rsi_max = 100  # No RSI filter
                    st.session_state.csp_aggressive_iv_rank_min = 0  # No IV filter
                    st.session_state.csp_aggressive_bb_max = 1.0  # No BB filter
                    st.session_state.csp_aggressive_min_score = 30  # Default min score
                    st.success("✅ Aggressive reset to defaults!")
                    st.rerun()
        
        st.write("")
        st.write("---")
        
        # Row 2: Quantity adjustment buttons
        st.write("**Adjust Quantities for Selected:**")
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 2])
        
        with col1:
            if st.button("➕ +1", key="csp_qty_plus1", help="Add 1 to selected quantities"):
                mask = st.session_state.csp_opportunities['Select'] == True
                st.session_state.csp_opportunities.loc[mask, 'Qty'] = st.session_state.csp_opportunities.loc[mask, 'Qty'] + 1
                st.rerun()
        
        with col2:
            if st.button("➕ +5", key="csp_qty_plus5", help="Add 5 to selected quantities"):
                mask = st.session_state.csp_opportunities['Select'] == True
                st.session_state.csp_opportunities.loc[mask, 'Qty'] = st.session_state.csp_opportunities.loc[mask, 'Qty'] + 5
                st.rerun()
        
        with col3:
            if st.button("➕ +10", key="csp_qty_plus10", help="Add 10 to selected quantities"):
                mask = st.session_state.csp_opportunities['Select'] == True
                st.session_state.csp_opportunities.loc[mask, 'Qty'] = st.session_state.csp_opportunities.loc[mask, 'Qty'] + 10
                st.rerun()
        
        with col4:
            if st.button("➖ -1", key="csp_qty_minus1", help="Subtract 1 from selected quantities (min 1)"):
                mask = st.session_state.csp_opportunities['Select'] == True
                st.session_state.csp_opportunities.loc[mask, 'Qty'] = st.session_state.csp_opportunities.loc[mask, 'Qty'].apply(lambda x: max(1, x - 1))
                st.rerun()
        
        with col5:
            if st.button("🔄 Reset", key="csp_qty_reset", help="Reset selected quantities to 1"):
                mask = st.session_state.csp_opportunities['Select'] == True
                st.session_state.csp_opportunities.loc[mask, 'Qty'] = 1
                st.rerun()
        
        with col6:
            # Show total contracts for selected
            if selected_count > 0:
                selected_qty_sum = st.session_state.csp_opportunities[st.session_state.csp_opportunities['Select'] == True]['Qty'].sum()
                st.info(f"📊 Selected: {int(selected_qty_sum)} contracts ({selected_count} options)")
        
        st.write("")
        
        # Initialize mark tracking in session state if not exists
        if 'csp_marked_indices' not in st.session_state:
            st.session_state.csp_marked_indices = set()
        
        # Initialize show_selected_only toggle in session state
        if 'csp_show_selected_only' not in st.session_state:
            st.session_state.csp_show_selected_only = False
        
        # Toggle to show only selected contracts
        col1, col2 = st.columns([1, 4])
        with col1:
            show_selected_only = st.toggle(
                "👁️ Selected Only",
                value=st.session_state.csp_show_selected_only,
                key="csp_show_selected_toggle",
                help="Show only the contracts you've selected (checked)"
            )
            st.session_state.csp_show_selected_only = show_selected_only
        with col2:
            selected_count = st.session_state.csp_opportunities['Select'].sum()
            total_count = len(st.session_state.csp_opportunities)
            if show_selected_only:
                st.caption(f"Showing {selected_count} selected of {total_count} total opportunities")
            else:
                st.caption(f"Showing all {total_count} opportunities ({selected_count} selected)")
        
        st.write("")
        
        # Score-based selection buttons - right above the table
        st.write("**Filter by Composite Score:**")
        score_cols = st.columns(11)
        
        opp_df = st.session_state.csp_opportunities
        
        # Define score thresholds and their button configs
        score_buttons = [
            (100, "⭐ 100", "csp_score_100"),
            (90, "🟢 90+", "csp_score_90"),
            (80, "🟢 80+", "csp_score_80"),
            (75, "🟢 75+", "csp_score_75"),
            (70, "🟡 70+", "csp_score_70"),
            (65, "🟡 65+", "csp_score_65"),
            (60, "🟠 60+", "csp_score_60"),
            (55, "🟠 55+", "csp_score_55"),
            (50, "🔴 50+", "csp_score_50"),
            (45, "🔴 45+", "csp_score_45"),
            (40, "⚫ 40+", "csp_score_40"),
        ]
        
        # Debug info above buttons
        if 'score' in opp_df.columns and 'Select' in opp_df.columns:
            total_selected = int(opp_df['Select'].sum() if opp_df['Select'].dtype == 'bool' else opp_df['Select'].astype(bool).sum())
            st.caption(f"🔍 Debug: {total_selected} opportunities currently selected in dataframe")
        
        for idx, (threshold, label, key) in enumerate(score_buttons):
            with score_cols[idx]:
                # Count currently SELECTED opportunities with score >= threshold
                if 'score' in opp_df.columns and 'Select' in opp_df.columns:
                    try:
                        selected_df = opp_df[opp_df['Select'].astype(bool)]
                        count = len(selected_df[selected_df['score'] >= threshold])
                    except Exception as e:
                        count = 0
                        st.error(f"Error counting: {e}")
                else:
                    count = 0
                
                if st.button(f"{label} ({count})", key=key, help=f"Refine selection: Keep only opportunities with score >= {threshold}"):
                    # Uncheck opportunities with score < threshold (refine the selection)
                    if 'score' in st.session_state.csp_opportunities.columns and 'Select' in st.session_state.csp_opportunities.columns:
                        # Only uncheck opportunities that are currently selected AND have score < threshold
                        mask = (st.session_state.csp_opportunities['Select'].astype(bool)) & (st.session_state.csp_opportunities['score'] < threshold)
                        st.session_state.csp_opportunities.loc[mask, 'Select'] = False
                    st.rerun()
        
        st.write("")
        
        # Format IV Rank and Spread % with colored emoji indicators (like CC Dashboard)
        display_df = st.session_state.csp_opportunities.copy()
        
        # Apply "show selected only" filter if enabled
        if show_selected_only:
            display_df = display_df[display_df['Select'] == True].copy()
        
        # Format IV Rank with emoji indicators
        def format_iv_rank(val):
            # Skip if already formatted (contains emoji)
            if isinstance(val, str) and any(emoji in val for emoji in ['🟢', '🟡', '🔴']):
                return val
            # Handle None or NaN
            if val is None or (isinstance(val, float) and val != val):
                return "N/A"
            # Convert to float if string
            if isinstance(val, str):
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    return "N/A"
            # Apply color coding
            if val > 75:
                return f"🟢 {val:.0f}%"  # Green = High IV (good for selling)
            elif val < 25:
                return f"🔴 {val:.0f}%"  # Red = Low IV (bad for selling)
            else:
                return f"🟡 {val:.0f}%"  # Yellow = Medium IV
        
        # Format Spread % with emoji indicators
        def format_spread(val):
            # Skip if already formatted (contains emoji)
            if isinstance(val, str) and any(emoji in val for emoji in ['🟢', '🟡', '🔴']):
                return val
            # Handle None or NaN
            if val is None or (isinstance(val, float) and val != val):
                return "N/A"
            # Convert to float if string
            if isinstance(val, str):
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    return "N/A"
            # Apply color coding
            if val <= 1.0:  # ≤1% spread
                return f"🟢 {val:.1f}%"  # Green = Tight spread (good)
            elif val <= 3.0:  # 1-3% spread
                return f"🟡 {val:.1f}%"  # Yellow = Medium spread
            else:  # >3% spread
                return f"🔴 {val:.1f}%"  # Red = Wide spread (bad)
        
        # Format Delta with emoji indicators (dynamic based on active preset)
        def format_delta(val):
            # Skip if already formatted (contains emoji)
            if isinstance(val, str) and any(emoji in val for emoji in ['🟢', '🟡', '🔴']):
                return val
            # Handle None or NaN
            if val is None or (isinstance(val, float) and val != val):
                return "N/A"
            # Convert to float if string
            if isinstance(val, str):
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    return "N/A"
            
            # Get active preset range (if any)
            if 'csp_active_preset' in st.session_state:
                preset = st.session_state.csp_active_preset
                
                if preset == 'conservative':
                    delta_min = st.session_state.csp_conservative_delta_min
                    delta_max = st.session_state.csp_conservative_delta_max
                elif preset == 'medium':
                    delta_min = st.session_state.csp_medium_delta_min
                    delta_max = st.session_state.csp_medium_delta_max
                elif preset == 'aggressive':
                    delta_min = st.session_state.csp_aggressive_delta_min
                    delta_max = st.session_state.csp_aggressive_delta_max
                else:
                    # No preset active, return plain value
                    return f"{val:.2f}"
                
                # Apply dynamic color coding based on preset range
                abs_val = abs(val)
                tolerance = 0.05  # ±0.05 for yellow zone
                
                if delta_min <= abs_val <= delta_max:
                    return f"🟢 {val:.2f}"  # Green = Within range
                elif (delta_min - tolerance) <= abs_val <= (delta_max + tolerance):
                    return f"🟡 {val:.2f}"  # Yellow = Close to range
                else:
                    return f"🔴 {val:.2f}"  # Red = Outside range
            else:
                # No preset active, return plain value
                return f"{val:.2f}"
        
        # Format Score with emoji indicators
        def format_score(val):
            if val is None or (isinstance(val, float) and val != val):
                return "N/A"
            try:
                val = int(val)
            except (ValueError, TypeError):
                return "N/A"
            if val >= 80:
                return f"🟢 {val}"  # Green = Excellent
            elif val >= 60:
                return f"🟡 {val}"  # Yellow = Good
            elif val >= 40:
                return f"🟠 {val}"  # Orange = Acceptable
            else:
                return f"🔴 {val}"  # Red = Poor
        
        # Apply formatting to display columns
        if 'Score' in display_df.columns:
            display_df['Score'] = display_df['Score'].apply(format_score)
        if 'Delta' in display_df.columns:
            display_df['Delta'] = display_df['Delta'].apply(format_delta)
        if 'IV Rank' in display_df.columns:
            display_df['IV Rank'] = display_df['IV Rank'].apply(format_iv_rank)
        if 'Spread %' in display_df.columns:
            display_df['Spread %'] = display_df['Spread %'].apply(format_spread)
        
        # No Mark column in table - we'll add individual buttons below
        
        # Display editable table (but encourage using buttons instead of editing cells)
        # Use dynamic key based on active preset to force re-render when formatting changes
        editor_key = f"csp_selector_{st.session_state.get('csp_active_preset', 'none')}"
        
        # Calculate dynamic height based on row count (35px per row + 60px header)
        # When "Selected Only" is ON: show ALL rows without scrolling (no max cap)
        # When "Selected Only" is OFF: cap at 800px to prevent white screen on large datasets
        calculated_height = len(display_df) * 35 + 60
        if show_selected_only:
            # No max cap - show all selected contracts without scrolling
            dynamic_height = max(200, calculated_height)
        else:
            # Cap at 800px for large datasets
            dynamic_height = max(400, min(calculated_height, 800))
        
        edited_df = st.data_editor(
            display_df,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select options to submit as orders",
                    default=False,
                ),
                "Qty": st.column_config.NumberColumn(
                    "Qty",
                    help="Use buttons above to adjust quantities (editing cells may be unreliable)",
                    min_value=1,
                    max_value=100,
                    step=1,
                    default=1,
                    format="%d"
                ),
            },
            disabled=[col for col in display_df.columns if col not in ['Select', 'Qty']],
            hide_index=True,
            height=dynamic_height,
            key=editor_key
        )
        
        # Update session state - only copy Select and Qty columns (user-editable)
        # Keep original numeric values for other columns (formatted columns are display-only)
        # When showing selected only, we need to update by index to preserve unshown rows
        if show_selected_only:
            for idx in edited_df.index:
                st.session_state.csp_opportunities.loc[idx, 'Select'] = edited_df.loc[idx, 'Select']
                st.session_state.csp_opportunities.loc[idx, 'Qty'] = edited_df.loc[idx, 'Qty']
        else:
            st.session_state.csp_opportunities['Select'] = edited_df['Select']
            st.session_state.csp_opportunities['Qty'] = edited_df['Qty']
        
        # ========== MANUAL MARKING CONTROLS (Below Table) ==========
        st.write("")
        st.write("**🏷️ Manual Mark & Remove:**")
        st.caption("Click buttons below to mark options for removal. Marked options can be batch-removed with the 'Remove Marked' button.")
        
        # Get currently selected rows
        selected_indices = st.session_state.csp_opportunities[st.session_state.csp_opportunities['Select'] == True].index.tolist()
        
        if len(selected_indices) > 0:
            # Display mark buttons for selected rows in a grid
            # Show up to 20 buttons at a time (4 columns x 5 rows)
            buttons_per_row = 4
            
            for i in range(0, min(len(selected_indices), 20), buttons_per_row):
                cols = st.columns(buttons_per_row)
                
                for col_idx, idx in enumerate(selected_indices[i:i+buttons_per_row]):
                    with cols[col_idx]:
                        row = st.session_state.csp_opportunities.loc[idx]
                        symbol = row['Symbol']
                        strike = row['Strike']
                        expiration = row['Expiration']
                        
                        is_marked = idx in st.session_state.csp_marked_indices
                        
                        if is_marked:
                            button_label = f"✅ {symbol} ${strike:.0f}"
                            button_type = "secondary"
                        else:
                            button_label = f"🏷️ {symbol} ${strike:.0f}"
                            button_type = "secondary"
                        
                        if st.button(button_label, key=f"mark_btn_{idx}", type=button_type,
                                   help=f"{symbol} ${strike:.0f} exp {expiration}"):
                            # Toggle mark state
                            if idx in st.session_state.csp_marked_indices:
                                st.session_state.csp_marked_indices.remove(idx)
                            else:
                                st.session_state.csp_marked_indices.add(idx)
                            st.rerun()
            
            if len(selected_indices) > 20:
                st.info(f"ℹ️ Showing first 20 of {len(selected_indices)} selected options. Use Auto-Trim for large selections.")
            
            st.write("")
            
            # Action buttons
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
            
            with col1:
                if st.button("➕ +1 Marked", 
                           disabled=len(st.session_state.csp_marked_indices) == 0,
                           help="Increment quantity by 1 for marked options"):
                    for idx in st.session_state.csp_marked_indices:
                        if idx in st.session_state.csp_opportunities.index:
                            current_qty = st.session_state.csp_opportunities.loc[idx, 'Qty']
                            st.session_state.csp_opportunities.loc[idx, 'Qty'] = current_qty + 1
                    st.success(f"✅ +1 qty for {len(st.session_state.csp_marked_indices)} marked options")
                    st.rerun()
            
            with col2:
                if st.button("➖ -1 Marked", 
                           disabled=len(st.session_state.csp_marked_indices) == 0,
                           help="Decrement quantity by 1 for marked options (min 1)"):
                    for idx in st.session_state.csp_marked_indices:
                        if idx in st.session_state.csp_opportunities.index:
                            current_qty = st.session_state.csp_opportunities.loc[idx, 'Qty']
                            st.session_state.csp_opportunities.loc[idx, 'Qty'] = max(1, current_qty - 1)
                    st.success(f"✅ -1 qty for {len(st.session_state.csp_marked_indices)} marked options")
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Remove Marked", type="primary", 
                           disabled=len(st.session_state.csp_marked_indices) == 0,
                           help=f"Remove {len(st.session_state.csp_marked_indices)} marked options"):
                    # Unselect all marked rows
                    for idx in st.session_state.csp_marked_indices:
                        if idx in st.session_state.csp_opportunities.index:
                            st.session_state.csp_opportunities.loc[idx, 'Select'] = False
                    
                    removed_count = len(st.session_state.csp_marked_indices)
                    st.session_state.csp_marked_indices = set()  # Clear marks
                    st.success(f"✅ Removed {removed_count} marked options")
                    st.rerun()
            
            with col4:
                if st.button("↩️ Clear Marks", 
                           disabled=len(st.session_state.csp_marked_indices) == 0,
                           help="Clear all marks without removing"):
                    st.session_state.csp_marked_indices = set()
                    st.success("✅ Cleared all marks")
                    st.rerun()
            
            with col5:
                if len(st.session_state.csp_marked_indices) > 0:
                    marked_symbols = []
                    for idx in st.session_state.csp_marked_indices:
                        if idx in st.session_state.csp_opportunities.index:
                            symbol = st.session_state.csp_opportunities.loc[idx, 'Symbol']
                            marked_symbols.append(symbol)
                    st.info(f"🏷️ Marked ({len(marked_symbols)}): {', '.join(marked_symbols[:8])}{'...' if len(marked_symbols) > 8 else ''}")
                else:
                    st.caption("🏷️ Click ticker buttons above to mark them")
        else:
            st.info("ℹ️ No options selected. Select options above to enable manual marking.")
        
        st.divider()
        
        # Order Summary Card
        # Use original DataFrame (with numeric values) for calculations
        selected_rows = st.session_state.csp_opportunities[st.session_state.csp_opportunities['Select'] == True]
        
        if len(selected_rows) > 0:
            st.subheader("💰 Order Summary")
            
            # Calculate totals accounting for quantities
            total_contracts = selected_rows['Qty'].sum()
            total_premium = (selected_rows['Premium'] * selected_rows['Qty'] * 100).sum()  # MID price, each contract = 100 shares
            total_collateral = (selected_rows['Strike'] * selected_rows['Qty'] * 100).sum()  # Each contract = 100 shares
            avg_weekly_return = selected_rows['Weekly %'].mean()
            avg_monthly_return = selected_rows['Monthly %'].mean()
            avg_delta = selected_rows['Delta'].mean()
            num_different_options = len(selected_rows)
            
            # Display summary card
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric("Total Contracts", int(total_contracts))
                st.caption(f"{num_different_options} different options")
            with col2:
                st.metric("Total Premium", f"${total_premium:,.2f}")
            with col3:
                st.metric("Total Collateral", f"${total_collateral:,.2f}")
            with col4:
                st.metric("Avg Weekly Return", f"{avg_weekly_return:.2f}%")
            with col5:
                st.metric("Avg Monthly Return", f"{avg_monthly_return:.2f}%")
            with col6:
                st.metric("Avg Delta", f"{avg_delta:.2f}")
            
            # Check buying power (90% limit for safety buffer)
            balances = api.get_account_balances(selected_account)
            if balances:
                # For CSP, use Derivative Buying Power (API field name)
                # This is what Tastytrade UI shows as "Option Buying Power"
                option_buying_power = float(balances.get('derivative-buying-power', 0))
                
                # Apply 90% limit - leave 10% buffer for safety
                max_deployable = option_buying_power * 0.90
                remaining_under_limit = max_deployable - total_collateral
                utilization = (total_collateral / option_buying_power * 100) if option_buying_power > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Option Buying Power", f"${option_buying_power:,.2f}")
                with col2:
                    st.metric("90% Limit", f"${max_deployable:,.2f}")
                with col3:
                    st.metric("Required Collateral", f"${total_collateral:,.2f}")
                with col4:
                    st.metric("Utilization", f"{utilization:.1f}%")
                
                # Warning if exceeds 90% limit
                if total_collateral > max_deployable:
                    excess = total_collateral - max_deployable
                    st.error(f"⚠️ **Exceeds 90% Limit!** Over by ${excess:,.2f} - reduce order quantity")
                    can_submit = False
                else:
                    st.success(f"✅ Within 90% limit - ${remaining_under_limit:,.2f} remaining")
                    can_submit = True
                
            else:
                st.warning("⚠️ Could not fetch account balances")
                can_submit = False
            
            st.divider()
            
            # AI Analysis and Order submission
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button(
                    "🤖 AI Analysis",
                    help="Analyze selected stocks for earnings, news, and risks"
                ):
                    # Get unique symbols from selected rows
                    unique_symbols = selected_rows['Symbol'].unique().tolist()
                    
                    with st.spinner(f"Analyzing {len(unique_symbols)} stocks with AI..."):
                        from utils.ai_analysis import analyze_stocks_with_ai, get_ai_analysis_summary
                        
                        ai_results = analyze_stocks_with_ai(unique_symbols)
                        st.session_state.ai_analysis_results = ai_results
            
            with col2:
                if st.button(
                    f"🚀 Submit {int(total_contracts)} Contracts",
                    type="primary",
                    disabled=not can_submit
                ):
                    st.session_state.show_order_confirmation = True
            
            # Display AI Analysis Results if available
            if 'ai_analysis_results' in st.session_state and st.session_state.ai_analysis_results:
                st.divider()
                
                results = st.session_state.ai_analysis_results
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📊 Analyzed", results['total_analyzed'])
                with col2:
                    st.metric("✅ Safe", len(results['safe_stocks']))
                with col3:
                    st.metric("⚠️ Caution", len(results['caution_stocks']))
                with col4:
                    st.metric("❌ Avoid", len(results['avoid_stocks']))
                
                # Full analysis in expander
                with st.expander("📝 View Full AI Analysis", expanded=True):
                    st.markdown(results['full_analysis'])
                
                # Download and Clear buttons
                col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
                
                with col1:
                    # Download as DOCX
                    try:
                        from utils.export_functions import generate_ai_analysis_docx
                        docx_data = generate_ai_analysis_docx(results)
                        st.download_button(
                            label="📄 Download DOCX",
                            data=docx_data,
                            file_name=f"AI_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    except Exception as e:
                        st.error(f"DOCX export error: {str(e)}")
                
                with col2:
                    # Download as PDF
                    try:
                        from utils.export_functions import generate_ai_analysis_pdf
                        pdf_data = generate_ai_analysis_pdf(results)
                        st.download_button(
                            label="📕 Download PDF",
                            data=pdf_data,
                            file_name=f"AI_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"PDF export error: {str(e)}")
                
                with col3:
                    # Clear button
                    if st.button("🗑️ Clear Analysis"):
                        del st.session_state.ai_analysis_results
                        st.rerun()
            
            # Order confirmation dialog

            # Order confirmation dialog with AUTOMATED VALIDATION
            if st.session_state.get('show_order_confirmation', False):
                
                # Initialize dry run mode in session state
                if 'dry_run_mode' not in st.session_state:
                    st.session_state.dry_run_mode = True  # Default to DRY RUN for safety
                
                # Initialize scan time if not set
                if 'csp_scan_time' not in st.session_state:
                    st.session_state.csp_scan_time = datetime.now()
                
                # DRY RUN TOGGLE at the top
                st.divider()
                col1, col2 = st.columns([1, 3])
                with col1:
                    dry_run = st.toggle(
                        "🧪 Dry Run Mode (Test Only)",
                        value=st.session_state.dry_run_mode,
                        help="When enabled, simulates orders without actually submitting them",
                        key="dry_run_toggle"
                    )
                    st.session_state.dry_run_mode = dry_run
                
                with col2:
                    if dry_run:
                        st.info("🧪 **DRY RUN MODE** - Orders will be simulated, not submitted")
                    else:
                        st.error("⚠️ **LIVE MODE** - Real orders will be submitted to your account!")
                
                st.divider()
                
                st.warning("⚠️ **Automated Pre-Flight Validation**")
                
                # Run automated validations
                validation_results = []
                all_passed = True
                
                # Get current time for freshness check
                scan_time = st.session_state.get('csp_scan_time', datetime.now())
                time_since_scan = (datetime.now() - scan_time).total_seconds() / 60  # minutes
                
                # VALIDATION 1: Strike & Expiration Validation
                st.subheader("1️⃣ Strike & Expiration Validation")
                
                strike_issues = []
                exp_issues = []
                
                for idx, row in selected_rows.iterrows():
                    strike = row['Strike']
                    current_price = row['Current Price']
                    expiration = row['Expiration']
                    dte = row['DTE']
                    
                    # Check strike is reasonable (within 50% of current price)
                    if strike > current_price * 1.5 or strike < current_price * 0.3:
                        strike_issues.append(f"{row['Symbol']}: Strike ${strike} is {abs((strike/current_price - 1) * 100):.0f}% away from current price ${current_price}")
                    
                    # Check expiration is in the future
                    exp_date = datetime.strptime(expiration, '%Y-%m-%d')
                    if exp_date <= datetime.now():
                        exp_issues.append(f"{row['Symbol']}: Expiration {expiration} is in the past!")
                    
                    # Check DTE is reasonable
                    if dte <= 0:
                        exp_issues.append(f"{row['Symbol']}: DTE is {dte} (expired or invalid)")
                    elif dte > 90:
                        exp_issues.append(f"{row['Symbol']}: DTE is {dte} days (very long term)")
                
                if len(strike_issues) == 0 and len(exp_issues) == 0:
                    st.success(f"✅ All {len(selected_rows)} strikes and expirations validated")
                    validation_results.append(("Strike & Expiration", True, "All valid"))
                else:
                    st.error("❌ Issues found:")
                    for issue in strike_issues + exp_issues:
                        st.write(f"  - {issue}")
                    validation_results.append(("Strike & Expiration", False, f"{len(strike_issues + exp_issues)} issues"))
                    all_passed = False
                
                st.divider()
                
                # VALIDATION 2: Buying Power (90% limit for safety buffer)
                st.subheader("2️⃣ Buying Power Validation")
                
                balances = api.get_account_balances(selected_account)
                if balances:
                    # Use Derivative Buying Power (API field name)
                    # This is what Tastytrade UI shows as "Option Buying Power"
                    option_buying_power = float(balances.get('derivative-buying-power', 0))
                    
                    # Apply 90% limit - leave 10% buffer for safety
                    max_deployable = option_buying_power * 0.90
                    buffer_after_orders = max_deployable - total_collateral
                    utilization_pct = (total_collateral / option_buying_power * 100) if option_buying_power > 0 else 0
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Option Buying Power", f"${option_buying_power:,.2f}")
                    with col2:
                        st.metric("90% Limit (Max Deployable)", f"${max_deployable:,.2f}")
                    with col3:
                        st.metric("Required Collateral", f"${total_collateral:,.2f}")
                    with col4:
                        st.metric("Utilization", f"{utilization_pct:.1f}%")
                    
                    if total_collateral <= max_deployable:
                        remaining_pct = (buffer_after_orders / option_buying_power * 100) if option_buying_power > 0 else 0
                        st.success(f"✅ Within 90% limit - ${buffer_after_orders:,.2f} remaining under limit ({remaining_pct:.1f}% of total BP)")
                        validation_results.append(("Buying Power (90% Limit)", True, f"${buffer_after_orders:,.2f} under limit"))
                    else:
                        excess = total_collateral - max_deployable
                        st.error(f"❌ Exceeds 90% limit! Over by ${excess:,.2f} - reduce order quantity")
                        validation_results.append(("Buying Power (90% Limit)", False, f"Over limit by ${excess:,.2f}"))
                        all_passed = False
                else:
                    st.error("❌ Could not fetch account balances")
                    validation_results.append(("Buying Power (90% Limit)", False, "API error"))
                    all_passed = False
                
                st.divider()
                
                # VALIDATION 3: Price Freshness
                st.subheader("3️⃣ Price Freshness Validation")
                
                if time_since_scan < 5:
                    st.success(f"✅ Data is fresh ({time_since_scan:.1f} minutes old)")
                    validation_results.append(("Price Freshness", True, f"{time_since_scan:.1f}min old"))
                elif time_since_scan < 30:
                    st.warning(f"⚠️ Data is {time_since_scan:.1f} minutes old - consider re-scanning")
                    validation_results.append(("Price Freshness", True, f"{time_since_scan:.1f}min old (acceptable)"))
                elif time_since_scan < 60:
                    st.warning(f"⚠️ Data is {time_since_scan:.1f} minutes old - prices may have changed")
                    validation_results.append(("Price Freshness", True, f"{time_since_scan:.1f}min old (use caution)"))
                else:
                    st.error(f"❌ Data is stale ({time_since_scan:.1f} minutes old) - please re-scan!")
                    validation_results.append(("Price Freshness", False, f"{time_since_scan:.1f}min old (stale)"))
                    all_passed = False
                
                st.divider()
                
                # VALIDATION 4: Risk Assessment
                st.subheader("4️⃣ Risk Assessment")
                
                # Calculate weighted delta (accounting for quantities)
                total_delta = (selected_rows['Delta'] * selected_rows['Qty']).sum()
                avg_delta = selected_rows['Delta'].mean()  # Average delta per option (not weighted)
                expected_assignments = total_delta  # Delta approximates assignment probability
                expected_win_rate = (1 - avg_delta) * 100
                max_loss = total_collateral - total_premium  # If all assigned
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Delta Exposure", f"{total_delta:.2f}")
                with col2:
                    st.metric("Avg Delta", f"{avg_delta:.2f}")
                with col3:
                    st.metric("Expected Win Rate", f"{expected_win_rate:.1f}%")
                with col4:
                    st.metric("Max Loss (if all assigned)", f"${max_loss:,.2f}")
                
                # Risk level assessment
                if avg_delta <= 0.20:
                    risk_level = "🟢 LOW RISK"
                    risk_color = "success"
                elif avg_delta <= 0.30:
                    risk_level = "🟡 MEDIUM RISK"
                    risk_color = "warning"
                else:
                    risk_level = "🔴 HIGH RISK"
                    risk_color = "error"
                
                if risk_color == "success":
                    st.success(f"✅ {risk_level} - Conservative delta range")
                elif risk_color == "warning":
                    st.warning(f"⚠️ {risk_level} - Moderate assignment probability")
                else:
                    st.error(f"⚠️ {risk_level} - High assignment probability")
                
                validation_results.append(("Risk Assessment", True, risk_level))
                
                st.divider()
                
                # Order limit validation removed - no artificial limits on order count
                
                st.divider()
                
                # VALIDATION SUMMARY
                st.subheader("📋 Validation Summary")
                
                summary_df = pd.DataFrame(validation_results, columns=['Check', 'Passed', 'Details'])
                
                # Color code the results
                def color_result(val):
                    if val == True:
                        return '✅'
                    else:
                        return '❌'
                
                summary_df['Status'] = summary_df['Passed'].apply(color_result)
                display_df = summary_df[['Check', 'Status', 'Details']]
                
                st.dataframe(display_df, hide_index=True)
                
                if all_passed:
                    st.success("🎉 **ALL VALIDATIONS PASSED** - Ready to proceed!")
                else:
                    st.error("❌ **VALIDATION FAILED** - Please resolve issues before submitting")
                
                st.divider()
                
                # Show order details
                st.write("**Order Details:**")
                order_details = selected_rows[['Symbol', 'Qty', 'Strike', 'Expiration', 'DTE', 'Premium', 'Premium %', 'Weekly %', 'Delta']]
                st.dataframe(order_details)
                
                st.write(f"**Total Premium to Collect:** ${total_premium:,.2f}")
                st.write(f"**Total Collateral Required:** ${total_collateral:,.2f}")
                
                st.divider()
                
                # SUBMIT BUTTONS
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if dry_run:
                        button_label = "🧪 Run Dry Run Test"
                        button_type = "primary"
                        button_disabled = not all_passed
                    else:
                        button_label = "🚀 Submit REAL Orders"
                        button_type = "primary"
                        button_disabled = not all_passed
                    
                    if st.button(button_label, type=button_type, disabled=button_disabled, key="submit_orders_btn"):
                        # Submit orders (or simulate)
                        with st.spinner("Processing orders..." if not dry_run else "Simulating orders..."):
                            success_count = 0
                            failed_orders = []
                            
                            for idx, row in selected_rows.iterrows():
                                try:
                                    # Build option symbol (OCC format)
                                    exp_date = datetime.strptime(row['Expiration'], '%Y-%m-%d')
                                    # Build OCC symbol with proper 6-character ticker padding
                                    ticker_padded = row['Symbol'].ljust(6)  # Pad to 6 chars with spaces
                                    option_symbol = f"{ticker_padded}{exp_date.strftime('%y%m%d')}P{int(row['Strike']*1000):08d}"
                                    qty = int(row['Qty'])  # Get quantity from row
                                    
                                    if dry_run:
                                        # DRY RUN - Just simulate
                                        st.write(f"🧪 [DRY RUN] Would submit: {qty}x {option_symbol} @ ${row['Premium']:.2f} (MID)")
                                        success_count += 1
                                    else:
                                        # LIVE - Actually submit at MID price
                                        result = api.submit_csp_order(
                                            account_number=selected_account,
                                            symbol=option_symbol,
                                            quantity=qty,  # Use quantity from row
                                            price=row['Premium']  # MID price: (bid + ask) / 2
                                        )
                                        
                                        if result:
                                            success_count += 1
                                        else:
                                            failed_orders.append(f"{qty}x {row['Symbol']} ${row['Strike']}")
                                
                                except Exception as e:
                                    failed_orders.append(f"{int(row['Qty'])}x {row['Symbol']} ${row['Strike']} - {str(e)}")
                            
                            # Show results
                            if dry_run:
                                st.success(f"🧪 **DRY RUN COMPLETE!** {success_count} orders simulated successfully")
                                st.info("💡 Toggle off 'Dry Run Mode' to submit real orders")
                            else:
                                if success_count == len(selected_rows):
                                    st.success(f"🎉 **All {success_count} orders submitted successfully!**")
                                    celebrate_success()
                                    
                                    # Clear selections
                                    st.session_state.csp_opportunities['Select'] = False
                                    st.session_state.show_order_confirmation = False
                                    st.rerun()
                                
                                elif success_count > 0:
                                    st.warning(f"⚠️ **Partial Success:** {success_count}/{len(selected_rows)} orders submitted")
                                    if failed_orders:
                                        st.error("**Failed orders:**")
                                        for order in failed_orders:
                                            st.write(f"- {order}")
                                else:
                                    st.error("❌ **All orders failed!**")
                                    if failed_orders:
                                        for order in failed_orders:
                                            st.write(f"- {order}")
                
                with col2:
                    if st.button("❌ Cancel", key="cancel_orders_btn"):
                        st.session_state.show_order_confirmation = False
                        st.rerun()
                
                with col3:
                    if st.button("🔄 Re-scan Prices", key="rescan_btn"):
                        st.session_state.show_order_confirmation = False
                        st.info("Please click 'Fetch Opportunities' again to refresh prices")

        # Download buttons
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.drop(columns=['Select']).to_csv(index=False)
            st.download_button(
                label="📥 Download Opportunities CSV",
                data=csv,
                file_name=f"csp_opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            if 'csp_scan_log' in st.session_state:
                st.download_button(
                    label="📄 Download Scan Log",
                    data=st.session_state.csp_scan_log,
                    file_name=f"csp_scan_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            else:
                st.info("ℹ️ Scan log will be available after first scan")
    else:
        st.warning("⚠️ No opportunities found matching your criteria")
        st.info("💡 Try lowering the delta, volume, or OI thresholds")
        
        # Show detailed log
        if 'csp_scan_log' in st.session_state:
            with st.expander("🔍 View Detailed Scan Log", expanded=True):
                st.text(st.session_state.csp_scan_log)
            
            st.download_button(
                label="📄 Download Scan Log for Analysis",
                data=st.session_state.csp_scan_log,
                file_name=f"csp_scan_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

# This is the complete refactored CC Dashboard section
# Replace lines 1912-end of CC Dashboard in app.py with this code

elif page == "CC Dashboard":
    # Market Status Indicator
    from utils.market_hours import get_market_status
    market_status = get_market_status()
    
    # Premium Header
    st.markdown('<h1 style="color: #ffffff; font-size: 36px; font-weight: 600; margin-bottom: 0.5rem;">📞 Covered Calls</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #9ca3af; font-size: 14px; margin-bottom: 1.5rem;">Generate income from your stock positions</p>', unsafe_allow_html=True)
    
    # Market Status in top right
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("")  # Spacer
    with col2:
        if market_status['status'] == 'open':
            st.success(f"{market_status['icon']} {market_status['message']}")
        elif market_status['status'] == 'closing_soon':
            st.warning(f"{market_status['icon']} {market_status['message']}")
        else:
            st.error(f"{market_status['icon']} {market_status['message']}")
        st.caption(f"Current time: {market_status['current_time_et']}")
    
    # Initialize Tradier API for option chains with greeks
    from utils.tradier_api import TradierAPI
    tradier = TradierAPI()
    
    # Use the account selected in the sidebar
    if not selected_account:
        st.error("❌ No account selected. Please select an account from the sidebar.")
        st.stop()
    
    st.subheader(f"Account: {selected_display}")
    
    # Track current account and clear data when account changes
    if 'cc_current_account' not in st.session_state:
        st.session_state.cc_current_account = selected_account
    elif st.session_state.cc_current_account != selected_account:
        # Account changed - clear all CC data
        st.session_state.cc_current_account = selected_account
        st.session_state.cc_eligible_holdings = None
        st.session_state.cc_breakdown = None
        st.session_state.cc_selected_stocks = []
        if 'cc_opportunities' in st.session_state:
            del st.session_state.cc_opportunities
        st.info("🔄 Account changed - data cleared. Please fetch positions and scan again.")
    
    # Initialize session state for selected stocks
    if 'cc_selected_stocks' not in st.session_state:
        st.session_state.cc_selected_stocks = []
    if 'cc_eligible_holdings' not in st.session_state:
        st.session_state.cc_eligible_holdings = []
    if 'cc_breakdown' not in st.session_state:
        st.session_state.cc_breakdown = {}
    
    # Step 1: Fetch Positions Button
    st.write("")
    if st.button("🔍 Fetch Portfolio Positions", type="primary"):
        try:
            from utils.covered_calls import get_eligible_stock_positions
            
            with st.status("Fetching positions...", expanded=True) as status:
                st.write("📊 Fetching all positions...")
                
                # Use the global API instance from sidebar
                # api is already initialized at the top of the file
                
                holdings, breakdown = get_eligible_stock_positions(api, selected_account)
                
                # Store in session state
                st.session_state.cc_eligible_holdings = holdings
                st.session_state.cc_breakdown = breakdown
                
                status.update(label="✅ Positions fetched!", state="complete")
                st.rerun()
                
        except Exception as e:
            st.error(f"Error fetching positions: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
    
    # Display results if we have data
    if st.session_state.cc_breakdown:
        breakdown = st.session_state.cc_breakdown
        holdings = st.session_state.cc_eligible_holdings
        
        st.write("")
        st.write("---")
        
        # Position Summary Section
        st.markdown('<div class="section-header">📊 Position Summary</div>', unsafe_allow_html=True)
        
        # Calculate total eligible contracts (shares / 100)
        total_eligible_contracts = sum([h.get('max_contracts', 0) for h in holdings])
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">Total Positions</div>
                <div class="metric-value">{breakdown.get('total_positions', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">Stock Positions</div>
                <div class="metric-value">{breakdown.get('stock_positions', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">Existing Calls</div>
                <div class="metric-value">{breakdown.get('existing_calls', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">Eligible for CC</div>
                <div class="metric-value metric-value-positive">{breakdown.get('eligible_positions', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col5:
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">💼 Eligible Contracts</div>
                <div class="metric-value metric-value-positive">{total_eligible_contracts}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        
        # Show friendly message if account has no stock positions
        if breakdown.get('stock_positions', 0) == 0:
            st.info("📊 This account has no stock positions. Stock positions are required to write covered calls.")
            st.stop()
        

        # TABLE 2: Eligible Positions (Selectable)
        if holdings:
            st.markdown('<div class="section-header">✅ Eligible Positions for New Covered Calls</div>', unsafe_allow_html=True)
            st.write("Select stocks to scan for covered call opportunities")
            
            # Filter out positions with 0 max contracts (all shares already have calls sold)
            available_holdings = [h for h in holdings if h.get('max_contracts', 0) > 0]
            
            if not available_holdings:
                st.info("📊 All your stock positions already have covered calls sold against them. No additional contracts available.")
                st.stop()
            
            # Create dataframe
            import pandas as pd
            eligible_df = pd.DataFrame(available_holdings)
            
            # Add selection column
            eligible_df['Select'] = eligible_df['symbol'].isin(st.session_state.cc_selected_stocks)
            
            # Reorder columns
            display_cols = ['Select', 'symbol', 'quantity', 'current_price', 'market_value', 'max_contracts']
            eligible_display = eligible_df[display_cols].copy()
            eligible_display.columns = ['Select', 'Symbol', 'Shares', 'Price', 'Market Value', 'Max Contracts']
            
            # Format numbers
            eligible_display['Price'] = eligible_display['Price'].apply(lambda x: f"${x:.2f}" if x and x == x else "N/A")
            eligible_display['Market Value'] = eligible_display['Market Value'].apply(lambda x: f"${x:,.2f}" if x and x == x else "N/A")
            
            # Selection buttons
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("🔘 Select All"):
                    st.session_state.cc_selected_stocks = eligible_df['symbol'].tolist()
                    st.rerun()
            with col2:
                if st.button("⭕ Clear All"):
                    st.session_state.cc_selected_stocks = []
                    st.rerun()
            
            # Display table with checkboxes
            edited_df = st.data_editor(
                eligible_display,
                hide_index=True,
                disabled=['Symbol', 'Shares', 'Price', 'Market Value', 'Max Contracts'],
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select stocks to scan for covered calls",
                        default=False,
                    )
                },
                key="cc_eligible_table"
            )
            
            # Update selected stocks based on checkboxes
            selected_symbols = eligible_df[edited_df['Select']]['symbol'].tolist()
            st.session_state.cc_selected_stocks = selected_symbols
            
            st.write(f"**Selected:** {len(selected_symbols)} stocks")
            if selected_symbols:
                st.write(f"**Symbols:** {', '.join(selected_symbols)}")
            
            st.write("")
            st.write("---")
            
            # Use default pre-scan settings (wide range to catch all opportunities)
            min_prescan_delta = 0.05
            max_prescan_delta = 0.99
            prescan_min_dte = 1
            prescan_max_dte = 90
            
            # Scan Selected Stocks Button
            if not selected_symbols:
                st.warning("⚠️ Please select at least one stock to scan")
            else:
                cc_scan_col1, cc_scan_col2 = st.columns([3, 1])
                
                with cc_scan_col1:
                    cc_scan_clicked = st.button(f"🔍 Scan {len(selected_symbols)} Selected Stocks for Covered Calls", type="primary")
                
                with cc_scan_col2:
                    if st.button("🗑️ Clear Results", key="cc_clear_results", help="Clear all scan results and start fresh"):
                        # Clear scan results
                        if 'cc_opportunities' in st.session_state:
                            del st.session_state.cc_opportunities
                        if 'cc_active_preset' in st.session_state:
                            del st.session_state.cc_active_preset
                        st.success("✅ Results cleared!")
                        st.rerun()
                
                if cc_scan_clicked:
                    try:
                        from utils.covered_calls import pre_scan_covered_calls
                        
                        with st.status(f"Scanning {len(selected_symbols)} stocks...", expanded=True) as status:
                            # Filter holdings to only selected stocks
                            selected_holdings = [h for h in holdings if h['symbol'] in selected_symbols]
                            
                            st.write(f"🔍 Pre-scanning option chains for {len(selected_holdings)} stocks...")
                            st.write(f"Pre-scan range: Delta {min_prescan_delta}-{max_prescan_delta}, DTE {prescan_min_dte}-{prescan_max_dte}")
                            
                            # Pre-scan
                            all_opportunities = pre_scan_covered_calls(
                                api,
                                tradier,
                                selected_holdings,
                                min_prescan_delta=min_prescan_delta,
                                max_prescan_delta=max_prescan_delta,
                                min_dte=prescan_min_dte,
                                max_dte=prescan_max_dte
                            )
                            
                            if not all_opportunities:
                                st.warning("⚠️ No opportunities found in pre-scan range")
                                st.info("💡 Try widening the pre-scan delta or DTE range")
                                status.update(label="⚠️ No opportunities found", state="complete")
                                st.stop()
                            
                            st.success(f"✅ Found {len(all_opportunities)} opportunities!")
                            status.update(label=f"✅ Found {len(all_opportunities)} opportunities", state="complete")
                            
                            # Store in session state as DataFrame (like CSP Dashboard)
                            df = pd.DataFrame(all_opportunities)
                            
                            # Calculate CC Composite Score (0-100)
                            def calculate_cc_score(row):
                                """
                                CC Composite Score based on:
                                - Weekly Return % (25%): Higher = Better
                                - Delta (20%): 0.20-0.35 = Best (balance premium vs getting called)
                                - RSI (15%): Higher = Better for CC (overbought = good time to sell calls)
                                - BB %B (15%): Higher = Better for CC (stock near upper band)
                                - Distance to Strike % (15%): Higher = Better (more room before assignment)
                                - Spread % (10%): Lower = Better (tighter spreads)
                                """
                                score = 0
                                
                                # 1. Weekly Return % (25 points) - Scale 0.3% to 2.0%
                                weekly = row.get('weekly_return_pct', 0) or 0
                                if weekly >= 2.0:
                                    score += 25
                                elif weekly >= 0.3:
                                    score += 25 * (weekly - 0.3) / 1.7
                                
                                # 2. Delta (20 points) - Sweet spot around 0.20-0.35
                                delta = abs(row.get('delta', 0) or 0)
                                if 0.20 <= delta <= 0.35:
                                    score += 20  # Perfect range
                                elif 0.15 <= delta <= 0.40:
                                    score += 15  # Good range
                                elif 0.10 <= delta <= 0.50:
                                    score += 10  # Acceptable
                                else:
                                    score += 5  # Outside ideal range
                                
                                # 3. RSI (15 points) - Higher is better for CC (overbought)
                                rsi_val = row.get('rsi', None)
                                if rsi_val is not None:
                                    if rsi_val > 70:
                                        score += 15  # Overbought - excellent for selling calls
                                    elif rsi_val > 60:
                                        score += 12
                                    elif rsi_val > 50:
                                        score += 9
                                    elif rsi_val > 40:
                                        score += 6
                                    elif rsi_val > 30:
                                        score += 3
                                    # < 30 = 0 points (oversold - bad for selling calls)
                                else:
                                    score += 7  # Neutral if no data
                                
                                # 4. BB %B (15 points) - Higher is better for CC
                                bb = row.get('bb_pct_b', None)
                                if bb is not None:
                                    if bb > 0.8:
                                        score += 15  # Near upper band - excellent
                                    elif bb > 0.7:
                                        score += 12
                                    elif bb > 0.5:
                                        score += 9
                                    elif bb > 0.3:
                                        score += 6
                                    elif bb > 0.2:
                                        score += 3
                                    # < 0.2 = 0 points (near lower band)
                                else:
                                    score += 7  # Neutral if no data
                                
                                # 5. Distance to Strike % (15 points) - Higher is better
                                current_price = row.get('current_price', 0) or 0
                                strike = row.get('strike', 0) or 0
                                if current_price > 0 and strike > 0:
                                    distance_pct = ((strike - current_price) / current_price) * 100
                                    if distance_pct > 10:
                                        score += 15
                                    elif distance_pct > 7:
                                        score += 12
                                    elif distance_pct > 5:
                                        score += 9
                                    elif distance_pct > 3:
                                        score += 6
                                    elif distance_pct > 1:
                                        score += 3
                                    # < 1% = 0 points (too close)
                                else:
                                    score += 7  # Neutral if no data
                                
                                # 6. Spread % (10 points) - Lower is better
                                spread = row.get('spread_pct', None)
                                if spread is not None:
                                    if spread <= 1:
                                        score += 10
                                    elif spread <= 2:
                                        score += 8
                                    elif spread <= 5:
                                        score += 5
                                    elif spread <= 10:
                                        score += 2
                                    # > 10% = 0 points
                                else:
                                    score += 5  # Neutral if no data
                                
                                return round(score)
                            
                            # Apply score calculation to each row
                            df['score'] = df.apply(calculate_cc_score, axis=1)
                            
                            df.insert(0, 'Select', False)  # Add Select column
                            df.insert(1, 'Qty', 1)  # Add Qty column with default value of 1
                            df = df.sort_values('score', ascending=False)  # Sort by Score
                            st.session_state.cc_opportunities = df
                            
                            # Reset UI state after fresh scan - show all opportunities, no filters
                            st.session_state.cc_min_score = 0  # Reset score filter to 0 (no filter)
                            st.session_state.cc_active_preset = None  # Clear any active preset
                            st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error scanning: {str(e)}")
                        import traceback
                        st.error(traceback.format_exc())
        
        # Display opportunities if we have them
        if 'cc_opportunities' in st.session_state and len(st.session_state.cc_opportunities) > 0:
            st.write("")
            st.write("---")
            st.write("### 🎯 Covered Call Opportunities")
            
            # Helper function: Find best opportunity per ticker with criteria relaxation
            def select_best_per_ticker(df, delta_min, delta_max, dte_min, dte_max, oi_min, weekly_min, qty_mode='conservative', min_score=0):
                """
                For each ticker, find the BEST opportunity (highest score) that matches criteria.
                If no match, relax criteria to find closest match.
                
                Args:
                    df: DataFrame of all opportunities
                    delta_min, delta_max, dte_min, dte_max, oi_min, weekly_min: Filter criteria
                    qty_mode: 'conservative' (1), 'medium' (50%), 'aggressive' (100%)
                    min_score: Minimum composite score required (0-100)
                
                Returns:
                    List of (index, qty) tuples to select
                """
                import math
                selections = []
                
                # Group by ticker
                for symbol in df['symbol'].unique():
                    ticker_opps = df[df['symbol'] == symbol]
                    
                    # Try to find match with original criteria
                    mask = (
                        (ticker_opps['delta'] >= delta_min) &
                        (ticker_opps['delta'] <= delta_max) &
                        (ticker_opps['dte'] >= dte_min) &
                        (ticker_opps['dte'] <= dte_max) &
                        (ticker_opps['open_interest'] >= oi_min) &
                        (ticker_opps['weekly_return_pct'] >= weekly_min)
                    )
                    matches = ticker_opps[mask]
                    
                    # If no match, relax ONLY weekly return and OI (NEVER relax delta or DTE)
                    if len(matches) == 0:
                        # Relax weekly return (keep delta and DTE as hard limits)
                        mask = (
                            (ticker_opps['delta'] >= delta_min) &
                            (ticker_opps['delta'] <= delta_max) &
                            (ticker_opps['dte'] >= dte_min) &
                            (ticker_opps['dte'] <= dte_max) &
                            (ticker_opps['open_interest'] >= oi_min)
                        )
                        matches = ticker_opps[mask]
                    
                    if len(matches) == 0:
                        # Relax open interest (keep delta and DTE as hard limits)
                        mask = (
                            (ticker_opps['delta'] >= delta_min) &
                            (ticker_opps['delta'] <= delta_max) &
                            (ticker_opps['dte'] >= dte_min) &
                            (ticker_opps['dte'] <= dte_max)
                        )
                        matches = ticker_opps[mask]
                    
                    # If still no match, skip this ticker (Delta and DTE are HARD LIMITS)
                    if len(matches) == 0:
                        continue  # Skip this ticker - no contracts within delta/DTE range
                    
                    # Apply minimum score filter if score column exists
                    if 'score' in matches.columns and min_score > 0:
                        matches = matches[matches['score'] >= min_score]
                    
                    if len(matches) == 0:
                        continue  # Skip this ticker - no contracts meet score threshold
                    
                    # Find the best match: highest score, then closest to target delta
                    # Target delta is the middle of the range
                    target_delta = (delta_min + delta_max) / 2
                    matches = matches.copy()
                    matches['delta_distance'] = abs(matches['delta'] - target_delta)
                    
                    # Sort by: 1) highest score, 2) closest to target delta
                    if 'score' in matches.columns:
                        matches = matches.sort_values(['score', 'delta_distance'], ascending=[False, True])
                    else:
                        matches = matches.sort_values(['delta_distance', 'weekly_return_pct'], ascending=[True, False])
                    best_idx = matches.index[0]
                    best_opp = matches.loc[best_idx]
                    
                    # Calculate quantity based on mode
                    if qty_mode == 'conservative':
                        qty = 1
                    elif qty_mode == 'medium':
                        qty = max(1, math.ceil(best_opp['max_contracts'] * 0.5))
                    else:  # aggressive
                        qty = best_opp['max_contracts']
                    
                    selections.append((best_idx, qty))
                
                return selections
            
            # Initialize preset criteria in session state (defaults)
            if 'cc_conservative_delta_min' not in st.session_state:
                st.session_state.cc_conservative_delta_min = 0.10
                st.session_state.cc_conservative_delta_max = 0.20
                st.session_state.cc_conservative_dte_min = 7
                st.session_state.cc_conservative_dte_max = 30
                st.session_state.cc_conservative_oi_min = 50
                st.session_state.cc_conservative_weekly_min = 0.3
            # Initialize RSI separately to handle existing sessions
            if 'cc_conservative_rsi_max' not in st.session_state:
                st.session_state.cc_conservative_rsi_max = 70
            if 'cc_conservative_weekly_min' not in st.session_state:
                st.session_state.cc_conservative_weekly_min = 0.3
            if 'cc_conservative_min_score' not in st.session_state:
                st.session_state.cc_conservative_min_score = 50
            
            if 'cc_medium_delta_min' not in st.session_state:
                st.session_state.cc_medium_delta_min = 0.15
                st.session_state.cc_medium_delta_max = 0.30
                st.session_state.cc_medium_dte_min = 7
                st.session_state.cc_medium_dte_max = 30
                st.session_state.cc_medium_oi_min = 50
                st.session_state.cc_medium_weekly_min = 0.3
            if 'cc_medium_rsi_max' not in st.session_state:
                st.session_state.cc_medium_rsi_max = 80
            if 'cc_medium_weekly_min' not in st.session_state:
                st.session_state.cc_medium_weekly_min = 0.3
            if 'cc_medium_min_score' not in st.session_state:
                st.session_state.cc_medium_min_score = 40
            
            if 'cc_aggressive_delta_min' not in st.session_state:
                st.session_state.cc_aggressive_delta_min = 0.20
                st.session_state.cc_aggressive_delta_max = 0.40
                st.session_state.cc_aggressive_dte_min = 7
                st.session_state.cc_aggressive_dte_max = 21
                st.session_state.cc_aggressive_oi_min = 25
                st.session_state.cc_aggressive_weekly_min = 0.3
            if 'cc_aggressive_rsi_max' not in st.session_state:
                st.session_state.cc_aggressive_rsi_max = 100
            if 'cc_aggressive_weekly_min' not in st.session_state:
                st.session_state.cc_aggressive_weekly_min = 0.3
            if 'cc_aggressive_min_score' not in st.session_state:
                st.session_state.cc_aggressive_min_score = 30
            
            # Initialize minimum score filter
            if 'cc_min_score' not in st.session_state:
                st.session_state.cc_min_score = 0
            
            # Get DataFrame from session state (already has Select column)
            opp_df = st.session_state.cc_opportunities
            
            # Preset Filter Buttons
            st.write("")
            col1, col2, col3, col4, col5, col6 = st.columns([1, 1.5, 1.5, 1.5, 1, 1])
            
            with col1:
                if st.button("🗑️ Clear All", key="cc_clear_all"):
                    st.session_state.cc_opportunities['Select'] = False
                    st.rerun()
            
            with col2:
                if st.button("🟢 Conservative", key="cc_preset_conservative", 
                           help=f"Δ {st.session_state.cc_conservative_delta_min}-{st.session_state.cc_conservative_delta_max}, DTE {st.session_state.cc_conservative_dte_min}-{st.session_state.cc_conservative_dte_max}, Score ≥{st.session_state.cc_conservative_min_score} | Qty=1 contract"):
                    # Track active preset for Delta formatting
                    st.session_state.cc_active_preset = 'conservative'
                    
                    # Clear all first
                    st.session_state.cc_opportunities['Select'] = False
                    st.session_state.cc_opportunities['Qty'] = 1  # Reset all to 1
                    
                    # Use smart per-ticker selection
                    selections = select_best_per_ticker(
                        st.session_state.cc_opportunities,
                        st.session_state.cc_conservative_delta_min,
                        st.session_state.cc_conservative_delta_max,
                        st.session_state.cc_conservative_dte_min,
                        st.session_state.cc_conservative_dte_max,
                        st.session_state.cc_conservative_oi_min,
                        st.session_state.cc_conservative_weekly_min,
                        qty_mode='conservative',
                        min_score=st.session_state.cc_conservative_min_score
                    )
                    
                    # Apply selections
                    for idx, qty in selections:
                        st.session_state.cc_opportunities.loc[idx, 'Select'] = True
                        st.session_state.cc_opportunities.loc[idx, 'Qty'] = qty
                    
                    st.rerun()
            
            with col3:
                if st.button("🟡 Medium", key="cc_preset_medium",
                           help=f"Δ {st.session_state.cc_medium_delta_min}-{st.session_state.cc_medium_delta_max}, DTE {st.session_state.cc_medium_dte_min}-{st.session_state.cc_medium_dte_max}, Score ≥{st.session_state.cc_medium_min_score} | Qty=50% of shares"):
                    # Track active preset for Delta formatting
                    st.session_state.cc_active_preset = 'medium'
                    
                    # Clear all first
                    st.session_state.cc_opportunities['Select'] = False
                    st.session_state.cc_opportunities['Qty'] = 1  # Reset all to 1
                    
                    # Use smart per-ticker selection
                    selections = select_best_per_ticker(
                        st.session_state.cc_opportunities,
                        st.session_state.cc_medium_delta_min,
                        st.session_state.cc_medium_delta_max,
                        st.session_state.cc_medium_dte_min,
                        st.session_state.cc_medium_dte_max,
                        st.session_state.cc_medium_oi_min,
                        st.session_state.cc_medium_weekly_min,
                        qty_mode='medium',
                        min_score=st.session_state.cc_medium_min_score
                    )
                    
                    # Apply selections
                    for idx, qty in selections:
                        st.session_state.cc_opportunities.loc[idx, 'Select'] = True
                        st.session_state.cc_opportunities.loc[idx, 'Qty'] = qty
                    
                    st.rerun()
            
            with col4:
                if st.button("🔴 Aggressive", key="cc_preset_aggressive",
                           help=f"Δ {st.session_state.cc_aggressive_delta_min}-{st.session_state.cc_aggressive_delta_max}, DTE {st.session_state.cc_aggressive_dte_min}-{st.session_state.cc_aggressive_dte_max}, Score ≥{st.session_state.cc_aggressive_min_score} | Qty=100% of shares"):
                    # Track active preset for Delta formatting
                    st.session_state.cc_active_preset = 'aggressive'
                    
                    # Clear all first
                    st.session_state.cc_opportunities['Select'] = False
                    st.session_state.cc_opportunities['Qty'] = 1  # Reset all to 1
                    
                    # Use smart per-ticker selection
                    selections = select_best_per_ticker(
                        st.session_state.cc_opportunities,
                        st.session_state.cc_aggressive_delta_min,
                        st.session_state.cc_aggressive_delta_max,
                        st.session_state.cc_aggressive_dte_min,
                        st.session_state.cc_aggressive_dte_max,
                        st.session_state.cc_aggressive_oi_min,
                        st.session_state.cc_aggressive_weekly_min,
                        qty_mode='aggressive',
                        min_score=st.session_state.cc_aggressive_min_score
                    )
                    
                    # Apply selections
                    for idx, qty in selections:
                        st.session_state.cc_opportunities.loc[idx, 'Select'] = True
                        st.session_state.cc_opportunities.loc[idx, 'Qty'] = qty
                    
                    st.rerun()
            
            with col5:
                if st.button("✅ Select All", key="cc_select_all"):
                    st.session_state.cc_opportunities['Select'] = True
                    st.rerun()
            
            with col6:
                selected_count = opp_df['Select'].sum()
                st.metric("Selected", int(selected_count))
            
            st.write("")
            
            # Row 2: Quantity adjustment buttons
            st.write("**Adjust Quantities for Selected:**")
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 1, 1.2, 1, 2])
            
            with col1:
                if st.button("➥ +1", key="cc_qty_plus1", help="Add 1 to selected quantities"):
                    mask = st.session_state.cc_opportunities['Select'] == True
                    st.session_state.cc_opportunities.loc[mask, 'Qty'] = st.session_state.cc_opportunities.loc[mask, 'Qty'] + 1
                    st.rerun()
            
            with col2:
                if st.button("➥ +5", key="cc_qty_plus5", help="Add 5 to selected quantities"):
                    mask = st.session_state.cc_opportunities['Select'] == True
                    st.session_state.cc_opportunities.loc[mask, 'Qty'] = st.session_state.cc_opportunities.loc[mask, 'Qty'] + 5
                    st.rerun()
            
            with col3:
                if st.button("➥ +10", key="cc_qty_plus10", help="Add 10 to selected quantities"):
                    mask = st.session_state.cc_opportunities['Select'] == True
                    st.session_state.cc_opportunities.loc[mask, 'Qty'] = st.session_state.cc_opportunities.loc[mask, 'Qty'] + 10
                    st.rerun()
            
            with col4:
                if st.button("➖ -1", key="cc_qty_minus1", help="Subtract 1 from selected quantities (min 1)"):
                    mask = st.session_state.cc_opportunities['Select'] == True
                    st.session_state.cc_opportunities.loc[mask, 'Qty'] = st.session_state.cc_opportunities.loc[mask, 'Qty'].apply(lambda x: max(1, x - 1))
                    st.rerun()
            
            with col5:
                if st.button("🔺 Max Out", key="cc_qty_max", help="Set selected quantities to maximum available contracts"):
                    mask = st.session_state.cc_opportunities['Select'] == True
                    # Set Qty to max_contracts for selected rows
                    for idx in st.session_state.cc_opportunities[mask].index:
                        max_contracts = st.session_state.cc_opportunities.loc[idx, 'max_contracts']
                        st.session_state.cc_opportunities.loc[idx, 'Qty'] = max_contracts
                    st.rerun()
            
            with col6:
                if st.button("🔄 Reset", key="cc_qty_reset", help="Reset selected quantities to 1"):
                    mask = st.session_state.cc_opportunities['Select'] == True
                    st.session_state.cc_opportunities.loc[mask, 'Qty'] = 1
                    st.rerun()
            
            with col7:
                # Show total contracts for selected
                if selected_count > 0:
                    selected_qty_sum = st.session_state.cc_opportunities[st.session_state.cc_opportunities['Select'] == True]['Qty'].sum()
                    st.info(f"📊 Selected: {int(selected_qty_sum)} contracts ({int(selected_count)} options)")
            
            st.write("")
            
            # ===== PRESET CONFIGURATION EXPANDERS =====
            st.write("### ⚙️ Configure Preset Filters")
            st.write("Adjust criteria for each preset, then click **Commit** to save. Click the preset button above to apply.")
            
            # Conservative Expander
            with st.expander("🟢 Conservative Filter Configuration", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    cons_delta_min = st.number_input("Min Delta", value=st.session_state.cc_conservative_delta_min, min_value=0.0, max_value=1.0, step=0.01, key="cons_delta_min_input")
                    cons_delta_max = st.number_input("Max Delta", value=st.session_state.cc_conservative_delta_max, min_value=0.0, max_value=1.0, step=0.01, key="cons_delta_max_input")
                    cons_dte_min = st.number_input("Min DTE", value=st.session_state.cc_conservative_dte_min, min_value=0, max_value=365, step=1, key="cons_dte_min_input")
                with col2:
                    cons_dte_max = st.number_input("Max DTE", value=st.session_state.cc_conservative_dte_max, min_value=0, max_value=365, step=1, key="cons_dte_max_input")
                    cons_oi_min = st.number_input("Min Open Interest", value=st.session_state.cc_conservative_oi_min, min_value=0, step=10, key="cons_oi_min_input")
                    cons_rsi_max = st.number_input("Max RSI", value=st.session_state.cc_conservative_rsi_max, min_value=0, max_value=100, step=5, key="cons_rsi_max_input", help="For CCs, higher RSI is better (stock has momentum). Set to 70 for conservative.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Commit Conservative", key="commit_conservative"):
                        st.session_state.cc_conservative_delta_min = cons_delta_min
                        st.session_state.cc_conservative_delta_max = cons_delta_max
                        st.session_state.cc_conservative_dte_min = cons_dte_min
                        st.session_state.cc_conservative_dte_max = cons_dte_max
                        st.session_state.cc_conservative_oi_min = cons_oi_min
                        st.session_state.cc_conservative_rsi_max = cons_rsi_max
                        st.success("✅ Conservative criteria committed!")
                        st.rerun()
                with col2:
                    if st.button("🔄 Reset Conservative", key="reset_conservative"):
                        st.session_state.cc_conservative_delta_min = 0.10
                        st.session_state.cc_conservative_delta_max = 0.20
                        st.session_state.cc_conservative_dte_min = 7
                        st.session_state.cc_conservative_dte_max = 30
                        st.session_state.cc_conservative_oi_min = 50
                        st.session_state.cc_conservative_rsi_max = 70
                        st.success("✅ Conservative reset to defaults!")
                        st.rerun()
            
            # Medium Expander
            with st.expander("🟡 Medium Filter Configuration", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    med_delta_min = st.number_input("Min Delta", value=st.session_state.cc_medium_delta_min, min_value=0.0, max_value=1.0, step=0.01, key="med_delta_min_input")
                    med_delta_max = st.number_input("Max Delta", value=st.session_state.cc_medium_delta_max, min_value=0.0, max_value=1.0, step=0.01, key="med_delta_max_input")
                    med_dte_min = st.number_input("Min DTE", value=st.session_state.cc_medium_dte_min, min_value=0, max_value=365, step=1, key="med_dte_min_input")
                with col2:
                    med_dte_max = st.number_input("Max DTE", value=st.session_state.cc_medium_dte_max, min_value=0, max_value=365, step=1, key="med_dte_max_input")
                    med_oi_min = st.number_input("Min Open Interest", value=st.session_state.cc_medium_oi_min, min_value=0, step=10, key="med_oi_min_input")
                    med_rsi_max = st.number_input("Max RSI", value=st.session_state.cc_medium_rsi_max, min_value=0, max_value=100, step=5, key="med_rsi_max_input", help="For CCs, higher RSI is better. Set to 80 for medium.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Commit Medium", key="commit_medium"):
                        st.session_state.cc_medium_delta_min = med_delta_min
                        st.session_state.cc_medium_delta_max = med_delta_max
                        st.session_state.cc_medium_dte_min = med_dte_min
                        st.session_state.cc_medium_dte_max = med_dte_max
                        st.session_state.cc_medium_oi_min = med_oi_min
                        st.session_state.cc_medium_rsi_max = med_rsi_max
                        st.success("✅ Medium criteria committed!")
                        st.rerun()
                with col2:
                    if st.button("🔄 Reset Medium", key="reset_medium"):
                        st.session_state.cc_medium_delta_min = 0.15
                        st.session_state.cc_medium_delta_max = 0.30
                        st.session_state.cc_medium_dte_min = 7
                        st.session_state.cc_medium_dte_max = 30
                        st.session_state.cc_medium_oi_min = 50
                        st.session_state.cc_medium_rsi_max = 80
                        st.success("✅ Medium reset to defaults!")
                        st.rerun()
            
            # Aggressive Expander
            with st.expander("🔴 Aggressive Filter Configuration", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    agg_delta_min = st.number_input("Min Delta", value=st.session_state.cc_aggressive_delta_min, min_value=0.0, max_value=1.0, step=0.01, key="agg_delta_min_input")
                    agg_delta_max = st.number_input("Max Delta", value=st.session_state.cc_aggressive_delta_max, min_value=0.0, max_value=1.0, step=0.01, key="agg_delta_max_input")
                    agg_dte_min = st.number_input("Min DTE", value=st.session_state.cc_aggressive_dte_min, min_value=0, max_value=365, step=1, key="agg_dte_min_input")
                with col2:
                    agg_dte_max = st.number_input("Max DTE", value=st.session_state.cc_aggressive_dte_max, min_value=0, max_value=365, step=1, key="agg_dte_max_input")
                    agg_oi_min = st.number_input("Min Open Interest", value=st.session_state.cc_aggressive_oi_min, min_value=0, step=10, key="agg_oi_min_input")
                    agg_rsi_max = st.number_input("Max RSI", value=st.session_state.cc_aggressive_rsi_max, min_value=0, max_value=100, step=5, key="agg_rsi_max_input", help="Set to 100 for no RSI filter.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Commit Aggressive", key="commit_aggressive"):
                        st.session_state.cc_aggressive_delta_min = agg_delta_min
                        st.session_state.cc_aggressive_delta_max = agg_delta_max
                        st.session_state.cc_aggressive_dte_min = agg_dte_min
                        st.session_state.cc_aggressive_dte_max = agg_dte_max
                        st.session_state.cc_aggressive_oi_min = agg_oi_min
                        st.session_state.cc_aggressive_rsi_max = agg_rsi_max
                        st.success("✅ Aggressive criteria committed!")
                        st.rerun()
                with col2:
                    if st.button("🔄 Reset Aggressive", key="reset_aggressive"):
                        st.session_state.cc_aggressive_delta_min = 0.20
                        st.session_state.cc_aggressive_delta_max = 0.40
                        st.session_state.cc_aggressive_dte_min = 7
                        st.session_state.cc_aggressive_dte_max = 21
                        st.session_state.cc_aggressive_oi_min = 25
                        st.session_state.cc_aggressive_rsi_max = 100
                        st.success("✅ Aggressive reset to defaults!")
                        st.rerun()
            
            st.write("")
            st.write("---")
            
            # Initialize show_selected_only toggle in session state
            if 'cc_show_selected_only' not in st.session_state:
                st.session_state.cc_show_selected_only = False
            
            # Toggle to show only selected contracts
            col1, col2 = st.columns([1, 4])
            with col1:
                show_selected_only = st.toggle(
                    "👁️ Selected Only",
                    value=st.session_state.cc_show_selected_only,
                    key="cc_show_selected_toggle",
                    help="Show only the contracts you've selected (checked)"
                )
                st.session_state.cc_show_selected_only = show_selected_only
            with col2:
                selected_count = st.session_state.cc_opportunities['Select'].sum()
                total_count = len(st.session_state.cc_opportunities)
                if show_selected_only:
                    st.caption(f"Showing {selected_count} selected of {total_count} total opportunities")
                else:
                    st.caption(f"Showing all {total_count} opportunities ({selected_count} selected)")
            
            st.write("")
            
            # Score-based selection buttons - right above the table
            st.write("**Filter by Composite Score:**")
            score_cols = st.columns(11)
            
            # Define score thresholds and their button configs
            score_buttons = [
                (100, "⭐ 100", "cc_score_100"),
                (90, "🟢 90+", "cc_score_90"),
                (80, "🟢 80+", "cc_score_80"),
                (75, "🟢 75+", "cc_score_75"),
                (70, "🟡 70+", "cc_score_70"),
                (65, "🟡 65+", "cc_score_65"),
                (60, "🟠 60+", "cc_score_60"),
                (55, "🟠 55+", "cc_score_55"),
                (50, "🔴 50+", "cc_score_50"),
                (45, "🔴 45+", "cc_score_45"),
                (40, "⚫ 40+", "cc_score_40"),
            ]
            
            # Debug info above buttons
            if 'score' in opp_df.columns and 'Select' in opp_df.columns:
                total_selected = int(opp_df['Select'].sum() if opp_df['Select'].dtype == 'bool' else opp_df['Select'].astype(bool).sum())
                st.caption(f"🔍 Debug: {total_selected} opportunities currently selected in dataframe")
            
            for idx, (threshold, label, key) in enumerate(score_buttons):
                with score_cols[idx]:
                    # Count currently SELECTED opportunities with score >= threshold
                    if 'score' in opp_df.columns and 'Select' in opp_df.columns:
                        try:
                            selected_df = opp_df[opp_df['Select'].astype(bool)]
                            count = len(selected_df[selected_df['score'] >= threshold])
                        except Exception as e:
                            count = 0
                            st.error(f"Error counting: {e}")
                    else:
                        count = 0
                    
                    if st.button(f"{label} ({count})", key=key, help=f"Refine selection: Keep only opportunities with score >= {threshold}"):
                        # Uncheck opportunities with score < threshold (refine the selection)
                        if 'score' in st.session_state.cc_opportunities.columns and 'Select' in st.session_state.cc_opportunities.columns:
                            # Only uncheck opportunities that are currently selected AND have score < threshold
                            mask = (st.session_state.cc_opportunities['Select'].astype(bool)) & (st.session_state.cc_opportunities['score'] < threshold)
                            st.session_state.cc_opportunities.loc[mask, 'Select'] = False
                        st.rerun()
            
            st.write("")
            
            # Apply "show selected only" filter if enabled
            if show_selected_only:
                opp_df = opp_df[opp_df['Select'] == True].copy()
            
            # Display dataframe - include Score column if it exists
            base_cols = ['Select', 'Qty', 'symbol']
            if 'score' in opp_df.columns:
                base_cols.append('score')
            base_cols.extend(['current_price', 'strike', 'expiration', 'dte', 'delta', 'premium', 'weekly_return_pct', 'rsi', 'iv_rank', 'bb_pct_b', 'spread_pct', 'open_interest', 'volume', 'max_contracts'])
            display_opp = opp_df[[col for col in base_cols if col in opp_df.columns]].copy()
            
            # Calculate Available column (remaining contracts)
            display_opp['Available'] = display_opp['max_contracts'] - display_opp['Qty']
            
            # Add visual indicator to Available column
            def format_available(val):
                if val > 0:
                    return f"🟢 {int(val)}"  # Green circle for available
                else:
                    return f"⚫ {int(val)}"  # Black circle for none available
            
            display_opp['Available_Display'] = display_opp['Available'].apply(format_available)
            
            # Rename columns - dynamically include Score if present
            if 'score' in opp_df.columns:
                display_opp.columns = ['Select', 'Qty', 'Symbol', 'Score', 'Stock Price', 'Strike', 'Expiration', 'DTE', 'Delta', 'Premium', 'Weekly %', 'RSI', 'IV Rank', 'BB %B', 'Spread %', 'OI', 'Volume', 'max_contracts', 'Available', 'Available_Display']
            else:
                display_opp.columns = ['Select', 'Qty', 'Symbol', 'Stock Price', 'Strike', 'Expiration', 'DTE', 'Delta', 'Premium', 'Weekly %', 'RSI', 'IV Rank', 'BB %B', 'Spread %', 'OI', 'Volume', 'max_contracts', 'Available', 'Available_Display']
            
            # Format RSI with emoji indicators
            def format_rsi(val):
                if val is None or val != val:  # Check for None or NaN
                    return "N/A"
                if val > 70:
                    return f"🔴 {val:.0f}"  # Red = Overbought
                elif val < 30:
                    return f"🟡 {val:.0f}"  # Yellow = Oversold
                else:
                    return f"🟢 {val:.0f}"  # Green = Normal
            
            # Format IV Rank with emoji indicators
            def format_iv_rank(val):
                if val is None or val != val:  # Check for None or NaN
                    return "N/A"
                if val > 75:
                    return f"🟢 {val:.0f}%"  # Green = High IV (good for selling)
                elif val < 25:
                    return f"🔴 {val:.0f}%"  # Red = Low IV (bad for selling)
                else:
                    return f"🟡 {val:.0f}%"  # Yellow = Medium IV
            
            # Format Spread % with emoji indicators
            def format_spread(val):
                if val is None or val != val:  # Check for None or NaN
                    return "N/A"
                if val < 2:
                    return f"🟢 {val:.1f}%"  # Green = Tight spread (good)
                elif val < 5:
                    return f"🟡 {val:.1f}%"  # Yellow = Medium spread
                else:
                    return f"🔴 {val:.1f}%"  # Red = Wide spread (bad)
            
            # Format BB %B with emoji indicators
            def format_bb_pct_b(val):
                if val is None or val != val:  # Check for None or NaN
                    return "N/A"
                if val < 0.3:
                    return f"🟢 {val:.2f}"  # Green = Oversold (good for selling calls)
                elif val > 0.7:
                    return f"🔴 {val:.2f}"  # Red = Overbought (risky for selling calls)
                else:
                    return f"🟡 {val:.2f}"  # Yellow = Neutral
            
            # Format Delta with emoji indicators (dynamic based on active preset)
            def format_delta(val):
                # Skip if already formatted (contains emoji)
                if isinstance(val, str) and any(emoji in val for emoji in ['🟢', '🟡', '🔴']):
                    return val
                # Handle None or NaN
                if val is None or (isinstance(val, float) and val != val):
                    return "N/A"
                # Convert to float if string
                if isinstance(val, str):
                    try:
                        val = float(val)
                    except (ValueError, TypeError):
                        return "N/A"
                
                # Get active preset range (if any)
                if 'cc_active_preset' in st.session_state:
                    preset = st.session_state.cc_active_preset
                    
                    if preset == 'conservative':
                        delta_min = st.session_state.cc_conservative_delta_min
                        delta_max = st.session_state.cc_conservative_delta_max
                    elif preset == 'medium':
                        delta_min = st.session_state.cc_medium_delta_min
                        delta_max = st.session_state.cc_medium_delta_max
                    elif preset == 'aggressive':
                        delta_min = st.session_state.cc_aggressive_delta_min
                        delta_max = st.session_state.cc_aggressive_delta_max
                    else:
                        # No preset active, return plain value
                        return f"{val:.3f}"
                    
                    # Apply dynamic color coding based on preset range
                    abs_val = abs(val)
                    tolerance = 0.05  # ±0.05 for yellow zone
                    
                    if delta_min <= abs_val <= delta_max:
                        return f"🟢 {val:.3f}"  # Green = Within range
                    elif (delta_min - tolerance) <= abs_val <= (delta_max + tolerance):
                        return f"🟡 {val:.3f}"  # Yellow = Close to range
                    else:
                        return f"🔴 {val:.3f}"  # Red = Outside range
                else:
                    # No preset active, return plain value
                    return f"{val:.3f}"
            
            # Format Score with emoji indicators
            def format_score(val):
                if val is None or (isinstance(val, float) and val != val):
                    return "N/A"
                try:
                    val = int(val)
                except (ValueError, TypeError):
                    return "N/A"
                if val >= 80:
                    return f"🟢 {val}"  # Green = Excellent
                elif val >= 60:
                    return f"🟡 {val}"  # Yellow = Good
                elif val >= 40:
                    return f"🟠 {val}"  # Orange = Acceptable
                else:
                    return f"🔴 {val}"  # Red = Poor
            
            # Apply formatting
            if 'Score' in display_opp.columns:
                display_opp['Score'] = display_opp['Score'].apply(format_score)
            display_opp['Stock Price'] = display_opp['Stock Price'].apply(lambda x: f"${x:.2f}" if x and x == x else "N/A")
            display_opp['Strike'] = display_opp['Strike'].apply(lambda x: f"${x:.2f}" if x and x == x else "N/A")
            display_opp['Delta'] = display_opp['Delta'].apply(format_delta)
            display_opp['Premium'] = display_opp['Premium'].apply(lambda x: f"${x:.2f}" if x and x == x else "N/A")
            display_opp['Weekly %'] = display_opp['Weekly %'].apply(lambda x: f"{x:.2f}%" if x and x == x else "N/A")
            display_opp['RSI'] = display_opp['RSI'].apply(format_rsi)
            display_opp['IV Rank'] = display_opp['IV Rank'].apply(format_iv_rank)
            display_opp['BB %B'] = display_opp['BB %B'].apply(format_bb_pct_b)
            display_opp['Spread %'] = display_opp['Spread %'].apply(format_spread)
            
            # Reorder columns to put Available after Qty, Score after Symbol (use display version with emoji)
            if 'Score' in display_opp.columns:
                display_opp = display_opp[['Select', 'Qty', 'Available_Display', 'Symbol', 'Score', 'Stock Price', 'Strike', 'Expiration', 'DTE', 'Delta', 'Premium', 'Weekly %', 'RSI', 'IV Rank', 'BB %B', 'Spread %', 'OI', 'Volume']]
            else:
                display_opp = display_opp[['Select', 'Qty', 'Available_Display', 'Symbol', 'Stock Price', 'Strike', 'Expiration', 'DTE', 'Delta', 'Premium', 'Weekly %', 'RSI', 'IV Rank', 'BB %B', 'Spread %', 'OI', 'Volume']]
            
            edited_opp = st.data_editor(
                display_opp,
                hide_index=True,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select opportunities to execute",
                        default=False,
                    ),
                    "Qty": st.column_config.NumberColumn(
                        "Qty",
                        help="Number of contracts to trade",
                        min_value=1,
                        max_value=100,
                        step=1,
                        default=1,
                        format="%d"
                    ),
                    "Available_Display": st.column_config.TextColumn(
                        "Available",
                        help="Remaining contracts available for this stock (🟢 = available, ⚫ = none)",
                        disabled=True
                    )
                },
                key="cc_selector"
            )
            
            # Update session state with manual selections and quantities from data_editor
            if 'Select' in edited_opp.columns:
                st.session_state.cc_opportunities['Select'] = edited_opp['Select']
            if 'Qty' in edited_opp.columns:
                st.session_state.cc_opportunities['Qty'] = edited_opp['Qty']       
            st.divider()
            
            # Order Summary Card
            selected_rows = st.session_state.cc_opportunities[st.session_state.cc_opportunities['Select'] == True]
            
            if len(selected_rows) > 0:
                st.subheader("💰 Order Summary")
                
                # Calculate totals (multiply by quantity)
                total_contracts = selected_rows['Qty'].sum()  # Sum of all quantities
                total_premium = (selected_rows['premium'] * selected_rows['Qty']).sum()  # Premium * Qty
                total_shares_covered = total_contracts * 100  # Each contract covers 100 shares
                avg_weekly_return = selected_rows['weekly_return_pct'].mean()
                avg_delta = selected_rows['delta'].mean()
                avg_dte = selected_rows['dte'].mean()
                
                # Display summary metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Total Contracts", int(total_contracts))
                    st.caption(f"{total_shares_covered:,} shares covered")
                with col2:
                    st.metric("Total Premium", f"${total_premium:,.2f}")
                    st.caption("Income collected")
                with col3:
                    st.metric("Avg Weekly Return", f"{avg_weekly_return:.2f}%")
                    monthly = avg_weekly_return * 4.33
                    st.caption(f"~{monthly:.2f}% monthly")
                with col4:
                    st.metric("Avg Delta", f"{avg_delta:.3f}")
                    assignment_prob = avg_delta * 100
                    st.caption(f"~{assignment_prob:.0f}% assignment risk")
                with col5:
                    st.metric("Avg DTE", f"{int(avg_dte)} days")
                    st.caption(f"Time to expiration")
                
                st.write("")
                
                # Show selected opportunities grouped by symbol
                st.write("**Selected Opportunities:**")
                for symbol in selected_rows['symbol'].unique():
                    symbol_rows = selected_rows[selected_rows['symbol'] == symbol]
                    symbol_premium = (symbol_rows['premium'] * symbol_rows['Qty']).sum()
                    symbol_contracts = symbol_rows['Qty'].sum()
                    st.write(f"- **{symbol}**: {int(symbol_contracts)} contract(s) = ${symbol_premium:.2f} premium")
                
                st.write("")
                
                # Order Submission
                st.write("---")
                
                # Initialize dry run mode in session state (default to True for safety)
                if 'cc_dry_run_mode' not in st.session_state:
                    st.session_state.cc_dry_run_mode = True
                
                # DRY RUN TOGGLE
                col1, col2 = st.columns([1, 3])
                with col1:
                    dry_run = st.toggle(
                        "🧪 Dry Run Mode (Test Only)",
                        value=st.session_state.cc_dry_run_mode,
                        help="When enabled, simulates orders without actually submitting them",
                        key="cc_dry_run_toggle"
                    )
                    st.session_state.cc_dry_run_mode = dry_run
                
                with col2:
                    if dry_run:
                        st.info("🧪 **DRY RUN MODE** - Orders will be simulated, not submitted")
                    else:
                        st.error("⚠️ **LIVE MODE** - Real orders will be submitted to your account!")
                
                st.write("")
                
                # Submit button
                col1, col2 = st.columns([3, 1])
                with col1:
                    if dry_run:
                        st.write("🧪 **Test order submission (no real orders)**")
                        st.caption(f"This will simulate {int(total_contracts)} covered call order(s) without submitting to Tastytrade.")
                    else:
                        st.write("📤 **Ready to submit REAL orders to Tastytrade?**")
                        st.caption(f"This will submit {int(total_contracts)} covered call order(s) as limit orders at the mid price (between bid/ask).")
                with col2:
                    button_label = "🧪 Run Dry Run Test" if dry_run else "🚀 Submit REAL Orders"
                    if st.button(button_label, type="primary", key="submit_cc_orders"):
                        # Submit orders (or simulate)
                        spinner_msg = "Simulating orders..." if dry_run else "📫 Submitting orders to Tastytrade..."
                        with st.spinner(spinner_msg):
                            try:
                                # Use the selected_account variable from CC Dashboard scope
                                account_number = selected_account
                                
                                if not account_number and not dry_run:
                                    st.error("⚠️ No account selected. Please select an account first.")
                                else:
                                    if dry_run:
                                        # DRY RUN - Just simulate
                                        st.write("")
                                        st.write("### 🧪 Dry Run Results")
                                        st.write("")
                                        
                                        for idx, row in selected_rows.iterrows():
                                            st.write(f"🧪 [DRY RUN] Would submit: **{row['symbol']}** ${row['strike']} Call x{int(row['Qty'])} @ ${row['premium']:.2f}")
                                        
                                        st.success(f"🧪 **DRY RUN COMPLETE!** {len(selected_rows)} orders simulated successfully")
                                        st.info("💡 Toggle off 'Dry Run Mode' to submit real orders")
                                    
                                    else:
                                        # LIVE - Actually submit
                                        from utils.tastytrade_api import TastytradeAPI
                                        api = TastytradeAPI()
                                        
                                        # Prepare orders
                                        orders = []
                                        for idx, row in selected_rows.iterrows():
                                            orders.append({
                                                'symbol': row['symbol'],
                                                'strike': row['strike'],
                                                'expiration': row['expiration'],
                                                'quantity': int(row['Qty']),
                                                'price': round(row['bid'], 2)  # Use bid price for reliable fills
                                            })
                                        
                                        # Submit batch
                                        results = api.submit_covered_call_orders_batch(account_number, orders)
                                        
                                        # Display results
                                        st.write("")
                                        st.write("### 📊 Order Results")
                                        
                                        success_count = sum(1 for r in results if r.get('success'))
                                        fail_count = len(results) - success_count
                                        
                                        if success_count > 0:
                                            st.success(f"✅ {success_count} order(s) submitted successfully!")
                                            if success_count == len(results):
                                                celebrate_success()
                                            
                                            # Auto-fetch positions to update available contracts
                                            st.info("🔄 Refreshing positions to update available contracts...")
                                            try:
                                                import time
                                                from utils.covered_calls import get_eligible_stock_positions
                                                eligible_holdings, breakdown = get_eligible_stock_positions(api, account_number)
                                                st.session_state.cc_eligible_holdings = eligible_holdings
                                                st.session_state.cc_breakdown = breakdown
                                                st.success(f"✅ Positions refreshed! {len(eligible_holdings)} eligible holdings found.")
                                                # Trigger page rerun to update the display
                                                time.sleep(1)  # Brief pause to show success message
                                                st.rerun()
                                            except Exception as e:
                                                st.warning(f"⚠️ Could not auto-refresh positions: {str(e)}. Please manually refresh if needed.")
                                        
                                        if fail_count > 0:
                                            st.error(f"❌ {fail_count} order(s) failed")
                                        
                                        # Show details
                                        for result in results:
                                            if result.get('success'):
                                                st.write(f"✅ **{result['symbol']}** ${result['strike']} Call x{result['quantity']} - Order ID: {result.get('order_id')}")
                                            else:
                                                st.write(f"❌ **{result['symbol']}** ${result['strike']} Call x{result['quantity']} - {result.get('message')}")
                                    
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                                import traceback
                                st.error(traceback.format_exc())
            else:
                st.info("👆 Select opportunities using the checkboxes or preset filters above")

    
    else:
        st.info("👆 Click 'Fetch Portfolio Positions' to get started")





elif page == "PMCC Dashboard":
    # Premium Header
    st.markdown('<h1 style="color: #ffffff; font-size: 36px; font-weight: 600; margin-bottom: 0.5rem;">🎯 PMCC Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #9ca3af; font-size: 14px; margin-bottom: 2rem;">Poor Man\'s Covered Calls - Buy LEAPs and sell short calls for income</p>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'pmcc_watchlist' not in st.session_state:
        st.session_state.pmcc_watchlist = []
    if 'pmcc_leap_positions' not in st.session_state:
        st.session_state.pmcc_leap_positions = []
    if 'pmcc_short_calls' not in st.session_state:
        st.session_state.pmcc_short_calls = []
    
    # ========================================
    # SECTION 1: ACTIVE PMCC POSITIONS
    # ========================================
    st.markdown('<div class="section-header">🎯 Active PMCC Positions</div>', unsafe_allow_html=True)
    
    # Fetch LEAP positions
    if st.button("🔍 Refresh PMCC Positions", type="primary"):
        try:
            with st.status("Fetching PMCC positions...", expanded=True) as status:
                st.write("📊 Fetching LEAP positions...")
                
                # Get all positions
                positions = api.get_positions(selected_account)
                
                # Filter for LEAP calls (long calls with DTE > 270 days)
                leap_positions = []
                short_call_positions = []
                
                for pos in positions:
                    if pos.get('instrument-type') == 'Equity Option':
                        quantity = pos.get('quantity', 0)
                        symbol = pos.get('symbol', '')
                        
                        # Parse option symbol to get expiration
                        # Format: SYMBOL YYMMDD C/P STRIKE
                        try:
                            parts = symbol.split()
                            if len(parts) >= 3:
                                underlying = parts[0]
                                exp_date_str = parts[1]
                                option_type = parts[2][0]  # C or P
                                strike = float(parts[2][1:]) / 1000  # Strike in cents
                                
                                # Calculate DTE
                                from datetime import datetime
                                exp_date = datetime.strptime(exp_date_str, '%y%m%d')
                                dte = (exp_date - datetime.now()).days
                                
                                # LEAP: long call with DTE > 270
                                if quantity > 0 and option_type == 'C' and dte > 270:
                                    leap_positions.append({
                                        'symbol': symbol,
                                        'underlying': underlying,
                                        'quantity': quantity,
                                        'strike': strike,
                                        'expiration': exp_date.strftime('%Y-%m-%d'),
                                        'dte': dte,
                                        'cost_basis': pos.get('average-open-price', 0) * 100 * quantity,
                                        'current_value': pos.get('mark', 0) * 100 * quantity,
                                        'pl': (pos.get('mark', 0) - pos.get('average-open-price', 0)) * 100 * quantity
                                    })
                                
                                # Short call: negative quantity, call option
                                elif quantity < 0 and option_type == 'C':
                                    short_call_positions.append({
                                        'symbol': symbol,
                                        'underlying': underlying,
                                        'quantity': abs(quantity),
                                        'strike': strike,
                                        'expiration': exp_date.strftime('%Y-%m-%d'),
                                        'dte': dte,
                                        'premium_collected': pos.get('average-open-price', 0) * 100 * abs(quantity),
                                        'current_value': pos.get('mark', 0) * 100 * abs(quantity),
                                        'pl': (pos.get('average-open-price', 0) - pos.get('mark', 0)) * 100 * abs(quantity)
                                    })
                        except Exception as e:
                            st.write(f"⚠️ Error parsing {symbol}: {str(e)}")
                            continue
                
                # Store in session state
                st.session_state.pmcc_leap_positions = leap_positions
                st.session_state.pmcc_short_calls = short_call_positions
                
                status.update(label=f"✅ Found {len(leap_positions)} LEAP(s) and {len(short_call_positions)} short call(s)", state="complete")
                st.rerun()
                
        except Exception as e:
            st.error(f"Error fetching PMCC positions: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
    
    # Display LEAP Positions
    if st.session_state.pmcc_leap_positions:
        st.write("")
        st.markdown("### 📈 LEAP Call Positions")
        
        leap_df = pd.DataFrame(st.session_state.pmcc_leap_positions)
        
        # Format for display
        display_leap_df = leap_df[[
            'underlying', 'quantity', 'strike', 'expiration', 'dte',
            'cost_basis', 'current_value', 'pl'
        ]].copy()
        
        display_leap_df.columns = [
            'Underlying', 'Contracts', 'Strike', 'Expiration', 'DTE',
            'Cost Basis', 'Current Value', 'P/L'
        ]
        
        # Format currency
        display_leap_df['Strike'] = display_leap_df['Strike'].apply(lambda x: f"${x:.2f}" if x and x == x else "N/A")
        display_leap_df['Cost Basis'] = display_leap_df['Cost Basis'].apply(lambda x: f"${x:,.0f}" if x and x == x else "N/A")
        display_leap_df['Current Value'] = display_leap_df['Current Value'].apply(lambda x: f"${x:,.0f}" if x and x == x else "N/A")
        display_leap_df['P/L'] = display_leap_df['P/L'].apply(lambda x: f"${x:,.0f}" if x and x == x else "N/A")
        
        st.dataframe(display_leap_df, hide_index=True)
        
        # Summary metrics
        total_cost = sum([p['cost_basis'] for p in st.session_state.pmcc_leap_positions])
        total_value = sum([p['current_value'] for p in st.session_state.pmcc_leap_positions])
        total_pl = sum([p['pl'] for p in st.session_state.pmcc_leap_positions])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">Total LEAP Cost</div>
                <div class="metric-value">${total_cost:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">Current Value</div>
                <div class="metric-value">${total_value:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            pl_color = "metric-value-positive" if total_pl >= 0 else "metric-value"
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">LEAP P/L</div>
                <div class="{pl_color}">${total_pl:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📊 No LEAP positions found. Start by scanning for LEAP opportunities below!")
    
    # Display Short Call Positions
    if st.session_state.pmcc_short_calls:
        st.write("")
        st.markdown("### 📞 Short Calls Against LEAPs")
        
        short_df = pd.DataFrame(st.session_state.pmcc_short_calls)
        
        # Format for display
        display_short_df = short_df[[
            'underlying', 'quantity', 'strike', 'expiration', 'dte',
            'premium_collected', 'current_value', 'pl'
        ]].copy()
        
        display_short_df.columns = [
            'Underlying', 'Contracts', 'Strike', 'Expiration', 'DTE',
            'Premium Collected', 'Current Value', 'P/L'
        ]
        
        # Format currency
        display_short_df['Strike'] = display_short_df['Strike'].apply(lambda x: f"${x:.2f}" if x and x == x else "N/A")
        display_short_df['Premium Collected'] = display_short_df['Premium Collected'].apply(lambda x: f"${x:,.0f}" if x and x == x else "N/A")
        display_short_df['Current Value'] = display_short_df['Current Value'].apply(lambda x: f"${x:,.0f}" if x and x == x else "N/A")
        display_short_df['P/L'] = display_short_df['P/L'].apply(lambda x: f"${x:,.0f}" if x and x == x else "N/A")
        
        st.dataframe(display_short_df, hide_index=True)
        
        # Summary metrics
        total_premium = sum([p['premium_collected'] for p in st.session_state.pmcc_short_calls])
        total_current = sum([p['current_value'] for p in st.session_state.pmcc_short_calls])
        total_short_pl = sum([p['pl'] for p in st.session_state.pmcc_short_calls])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">Premium Collected</div>
                <div class="metric-value metric-value-positive">${total_premium:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">Current Value</div>
                <div class="metric-value">${total_current:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            pl_color = "metric-value-positive" if total_short_pl >= 0 else "metric-value"
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">Short Call P/L</div>
                <div class="{pl_color}">${total_short_pl:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # ROI Tracking Section
        if st.session_state.pmcc_leap_positions and st.session_state.pmcc_short_calls:
            st.write("")
            st.markdown("### 📈 PMCC ROI Tracking")
            
            from utils.pmcc_scanner import calculate_pmcc_roi
            
            # Calculate total ROI across all positions
            total_leap_cost = sum([p['cost_basis'] for p in st.session_state.pmcc_leap_positions])
            total_premiums_collected = sum([p['premium_collected'] for p in st.session_state.pmcc_short_calls])
            
            overall_roi = calculate_pmcc_roi(total_leap_cost, total_premiums_collected)
            
            # Determine progress towards target (50-100% ROI)
            target_roi_min = 50
            target_roi_max = 100
            
            if overall_roi >= target_roi_max:
                roi_status = "✅ EXCELLENT"
                roi_color = "metric-value-positive"
            elif overall_roi >= target_roi_min:
                roi_status = "🎯 ON TARGET"
                roi_color = "metric-value-positive"
            else:
                roi_status = "📈 BUILDING"
                roi_color = "metric-value"
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="premium-metric-card">
                    <div class="metric-label">Total LEAP Cost</div>
                    <div class="metric-value">${total_leap_cost:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="premium-metric-card">
                    <div class="metric-label">Premiums Collected</div>
                    <div class="metric-value metric-value-positive">${total_premiums_collected:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="premium-metric-card">
                    <div class="metric-label">Current ROI</div>
                    <div class="{roi_color}">{overall_roi:.1f}%</div>
                    <div class="metric-change">{roi_status}</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                remaining_to_target = max(0, target_roi_min - overall_roi)
                remaining_dollars = (remaining_to_target / 100) * total_leap_cost
                st.markdown(f"""
                <div class="premium-metric-card">
                    <div class="metric-label">To Target (50%)</div>
                    <div class="metric-value">${remaining_dollars:,.0f}</div>
                    <div class="metric-change">{remaining_to_target:.1f}% more</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Assignment Risk Alerts
        st.write("")
        st.markdown("### ⚠️ Assignment Risk Alerts")
        
        from utils.pmcc_scanner import check_assignment_risk
        from utils.tradier_api import TradierAPI
        
        tradier = TradierAPI()
        
        risk_alerts = []
        
        for short_call in st.session_state.pmcc_short_calls:
            # Get current underlying price
            try:
                import requests
                quote_url = f"{tradier.base_url}/markets/quotes"
                quote_params = {"symbols": short_call['underlying']}
                quote_response = requests.get(quote_url, headers=tradier.headers, params=quote_params)
                
                if quote_response.status_code == 200:
                    quote_data = quote_response.json()
                    if 'quotes' in quote_data and 'quote' in quote_data['quotes']:
                        quote = quote_data['quotes']['quote']
                        current_price = quote.get('last', 0)
                        
                        # Check risk
                        risk_info = check_assignment_risk(
                            current_price,
                            short_call['strike'],
                            short_call['dte']
                        )
                        
                        risk_alerts.append({
                            'symbol': short_call['underlying'],
                            'strike': short_call['strike'],
                            'expiration': short_call['expiration'],
                            'dte': short_call['dte'],
                            'current_price': current_price,
                            'risk_level': risk_info['risk_level'],
                            'message': risk_info['message'],
                            'color': risk_info['color']
                        })
            except Exception as e:
                print(f"Error checking risk for {short_call['underlying']}: {str(e)}")
                continue
        
        if risk_alerts:
            # Sort by risk level (CRITICAL first)
            risk_order = {'CRITICAL': 0, 'HIGH': 1, 'MODERATE': 2, 'LOW': 3}
            risk_alerts.sort(key=lambda x: risk_order.get(x['risk_level'], 999))
            
            for alert in risk_alerts:
                if alert['risk_level'] == 'CRITICAL':
                    st.error(alert['message'])
                elif alert['risk_level'] == 'HIGH':
                    st.warning(alert['message'])
                elif alert['risk_level'] == 'MODERATE':
                    st.info(alert['message'])
                else:
                    st.success(alert['message'])
            
            # Add notification button if high-risk alerts exist
            high_risk_count = sum(1 for a in risk_alerts if a['risk_level'] in ['CRITICAL', 'HIGH'])
            
            if high_risk_count > 0:
                st.write("")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.warning(f"⚠️ {high_risk_count} position(s) require immediate attention")
                
                with col2:
                    if st.button("📧 Send Alert", key="pmcc_send_alert"):
                        from utils.pmcc_notifications import send_assignment_risk_alert, get_notification_preferences
                        
                        prefs = get_notification_preferences()
                        
                        if not prefs['enabled']:
                            st.info("🚧 Notifications not enabled. Set NOTIFICATIONS_ENABLED=true in .env file.")
                        elif not prefs['email'] and not prefs['phone']:
                            st.info("🚧 No notification recipients configured. Set NOTIFICATION_EMAIL and/or NOTIFICATION_PHONE in .env file.")
                        else:
                            with st.spinner("Sending alerts..."):
                                results = send_assignment_risk_alert(
                                    risk_alerts,
                                    recipient_email=prefs['email'] if prefs['email'] else None,
                                    recipient_phone=prefs['phone'] if prefs['phone'] else None
                                )
                                
                                if results['email']:
                                    if results['email']['success']:
                                        st.success(f"✅ {results['email']['message']}")
                                    else:
                                        st.error(f"❌ {results['email']['message']}")
                                
                                if results['sms']:
                                    if results['sms']['success']:
                                        st.success(f"✅ {results['sms']['message']}")
                                    else:
                                        st.error(f"❌ {results['sms']['message']}")
        else:
            st.info("✅ No active short calls to monitor")
    
    st.divider()
    
    # ========================================
    # SECTION 2: WATCHLIST MANAGEMENT (Same style as CSP Dashboard)
    # ========================================
    st.subheader("📝 Watchlist Management")
    
    # Read watchlist (using absolute paths)
    pmcc_watchlist_file = os.path.join(DATA_DIR, 'pmcc_watchlist.txt')
    try:
        with open(pmcc_watchlist_file, 'r') as f:
            pmcc_watchlist = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        pmcc_watchlist = []
    except:
        pmcc_watchlist = []
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.info(f"📋 Currently monitoring **{len(pmcc_watchlist)}** symbols from watchlist")
    
    with col2:
        if st.button("👁️ View/Edit Watchlist", key="pmcc_view_edit"):
            st.session_state.show_pmcc_watchlist_editor = not st.session_state.get('show_pmcc_watchlist_editor', False)
    
    with col3:
        if st.button("🗑️ Clear Watchlist", type="secondary", key="pmcc_clear_watchlist"):
            if len(pmcc_watchlist) > 0:
                with open(pmcc_watchlist_file, 'w') as f:
                    f.write("")
                st.success("✅ Watchlist cleared!")
                st.rerun()
    
    # Show watchlist editor if toggled
    if st.session_state.get('show_pmcc_watchlist_editor', False):
        st.subheader("✏️ Edit Watchlist")
        
        # Add new ticker section
        st.markdown("**➕ Add New Ticker(s)**")
        add_col1, add_col2 = st.columns([3, 1])
        with add_col1:
            new_ticker_input = st.text_input(
                "Enter ticker symbol(s)",
                placeholder="e.g., AAPL or AAPL, MSFT, GOOGL",
                key="pmcc_new_ticker_input",
                label_visibility="collapsed"
            ).upper().strip()
        with add_col2:
            if st.button("➕ Add Ticker(s)", type="primary", key="pmcc_add_tickers"):
                if new_ticker_input:
                    # Parse comma-separated tickers and remove duplicates from input
                    new_tickers = list(dict.fromkeys([t.strip() for t in new_ticker_input.split(',') if t.strip()]))
                    added = []
                    already_in_watchlist = []
                    
                    for ticker in new_tickers:
                        if ticker in pmcc_watchlist:
                            already_in_watchlist.append(ticker)
                        else:
                            pmcc_watchlist.append(ticker)
                            added.append(ticker)
                    
                    if added:
                        # Save updated watchlist
                        updated_watchlist = sorted(pmcc_watchlist)
                        with open(pmcc_watchlist_file, 'w') as f:
                            for symbol in updated_watchlist:
                                f.write(f"{symbol}\n")
                        st.success(f"✅ Added {len(added)} ticker(s): {', '.join(added)}")
                    
                    if already_in_watchlist:
                        st.info(f"ℹ️ Already in watchlist (skipped): {', '.join(already_in_watchlist)}")
                    
                    if added:
                        # Close the dialog after adding
                        st.session_state.show_pmcc_watchlist_editor = False
                        st.rerun()
                else:
                    st.warning("⚠️ Please enter a ticker symbol")
        
        st.divider()
        
        if len(pmcc_watchlist) > 0:
            # Create DataFrame for editing
            watchlist_df = pd.DataFrame({
                'Remove': [False] * len(pmcc_watchlist),
                'Symbol': pmcc_watchlist
            })
            
            edited_watchlist = st.data_editor(
                watchlist_df,
                column_config={
                    "Remove": st.column_config.CheckboxColumn(
                        "Remove",
                        help="Check to remove from watchlist",
                        default=False,
                    ),
                    "Symbol": st.column_config.TextColumn("Symbol", disabled=True),
                },
                hide_index=True,
                key="pmcc_watchlist_editor"
            )
            
            # Remove selected symbols
            if st.button("🗑️ Remove Selected", type="primary", key="pmcc_remove_selected"):
                symbols_to_keep = edited_watchlist[edited_watchlist['Remove'] == False]['Symbol'].tolist()
                
                with open(pmcc_watchlist_file, 'w') as f:
                    for symbol in sorted(symbols_to_keep):
                        f.write(f"{symbol}\n")
                
                removed_count = len(pmcc_watchlist) - len(symbols_to_keep)
                st.success(f"✅ Removed {removed_count} symbols from watchlist!")
                st.session_state.show_pmcc_watchlist_editor = False
                st.rerun()
        else:
            st.info("📝 No tickers in watchlist. Add some above!")
    
    # Show current watchlist symbols in a grid (collapsed by default)
    with st.expander(f"📋 Current Watchlist Symbols ({len(pmcc_watchlist)} tickers)", expanded=False):
        if pmcc_watchlist:
            # Display in a grid of 8 columns
            cols = st.columns(8)
            for i, symbol in enumerate(sorted(pmcc_watchlist)):
                cols[i % 8].write(symbol)
        else:
            st.info("📝 No tickers in watchlist. Add some to get started!")
    
    st.divider()
    
    # ========================================
    # SECTION 3: LEAP SCANNER
    # ========================================
    st.markdown('<div class="section-header">🔍 LEAP Scanner</div>', unsafe_allow_html=True)
    
    st.markdown("**Scan for LEAP call options (9-15 months out, deep ITM for PMCC strategy)**")
    
    # Basic Option Filters
    st.markdown("##### 🎯 Option Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dte_min = st.number_input("Min DTE (days)", min_value=180, max_value=730, value=270, step=30, key="pmcc_dte_min")
        dte_max = st.number_input("Max DTE (days)", min_value=180, max_value=730, value=450, step=30, key="pmcc_dte_max")
    
    with col2:
        delta_min = st.number_input("Min Delta", min_value=0.5, max_value=1.0, value=0.70, step=0.05, key="pmcc_delta_min")
        delta_max = st.number_input("Max Delta", min_value=0.5, max_value=1.0, value=0.90, step=0.05, key="pmcc_delta_max")
    
    with col3:
        min_oi = st.number_input("Min Open Interest", min_value=0, max_value=1000, value=50, step=10, key="pmcc_min_oi")
        max_bid_ask_spread = st.number_input("Max Bid-Ask Spread %", min_value=0.0, max_value=20.0, value=5.0, step=0.5, key="pmcc_max_spread", help="Filter out options with wide spreads (higher cost to enter/exit)")
    
    # Advanced Filters - Expandable
    with st.expander("📊 Advanced Filters (Technical & Value)", expanded=False):
        adv_col1, adv_col2, adv_col3 = st.columns(3)
        
        with adv_col1:
            st.markdown("**💰 Value Filters**")
            max_extrinsic_pct = st.number_input(
                "Max Extrinsic Value %", 
                min_value=0.0, max_value=50.0, value=15.0, step=1.0, 
                key="pmcc_max_extrinsic",
                help="Extrinsic value as % of option price. Lower = less time premium you're paying for."
            )
            max_iv = st.number_input(
                "Max IV %", 
                min_value=0.0, max_value=200.0, value=100.0, step=5.0, 
                key="pmcc_max_iv",
                help="Maximum implied volatility. Lower IV = cheaper LEAPs."
            )
        
        with adv_col2:
            st.markdown("**📈 Trend Filters**")
            require_above_ma = st.checkbox(
                "Price above 50-day MA", 
                value=False, 
                key="pmcc_above_ma",
                help="Only show stocks trading above their 50-day moving average (uptrend)"
            )
            min_rsi = st.number_input(
                "Min RSI", 
                min_value=0, max_value=100, value=30, step=5, 
                key="pmcc_min_rsi",
                help="Minimum RSI to avoid oversold stocks. Default 30."
            )
            max_rsi = st.number_input(
                "Max RSI", 
                min_value=0, max_value=100, value=70, step=5, 
                key="pmcc_max_rsi",
                help="Maximum RSI to avoid overbought stocks. Default 70."
            )
        
        with adv_col3:
            st.markdown("**🎯 Efficiency Filters**")
            min_capital_efficiency = st.number_input(
                "Min Capital Efficiency %", 
                min_value=0.0, max_value=100.0, value=0.0, step=5.0, 
                key="pmcc_min_efficiency",
                help="LEAP cost as % of 100 shares. Lower = more capital efficient. E.g., 60% means LEAP costs 60% of owning shares."
            )
            max_capital_efficiency = st.number_input(
                "Max Capital Efficiency %", 
                min_value=0.0, max_value=100.0, value=85.0, step=5.0, 
                key="pmcc_max_efficiency",
                help="Maximum capital efficiency. Typically want < 85% to make PMCC worthwhile."
            )
    
    st.write("")
    
    # Initialize session state for scan results
    if 'pmcc_leap_scan_results' not in st.session_state:
        st.session_state.pmcc_leap_scan_results = []
    
    # Scan button
    if st.button("🔍 Scan for LEAPs", type="primary", key="pmcc_scan"):
        if not pmcc_watchlist:
            st.warning("⚠️ Please add tickers to your watchlist first!")
        else:
            try:
                with st.status("Scanning for LEAP opportunities...", expanded=True) as status:
                    from utils.pmcc_scanner import scan_leap_options
                    from utils.tradier_api import TradierAPI
                    
                    tradier = TradierAPI()
                    
                    st.write(f"🔍 Scanning {len(pmcc_watchlist)} symbols...")
                    st.write(f"🎯 Option Filters: DTE {dte_min}-{dte_max}, Delta {delta_min:.2f}-{delta_max:.2f}")
                    st.write(f"💰 Value Filters: Max Spread {max_bid_ask_spread}%, Max Extrinsic {max_extrinsic_pct}%")
                    
                    # Get advanced filter values (with defaults if not set)
                    adv_max_iv = st.session_state.get('pmcc_max_iv', 100.0)
                    adv_require_above_ma = st.session_state.get('pmcc_above_ma', False)
                    adv_min_rsi = st.session_state.get('pmcc_min_rsi', 30)
                    adv_max_rsi = st.session_state.get('pmcc_max_rsi', 70)
                    adv_min_efficiency = st.session_state.get('pmcc_min_efficiency', 0.0)
                    adv_max_efficiency = st.session_state.get('pmcc_max_efficiency', 85.0)
                    adv_max_extrinsic = st.session_state.get('pmcc_max_extrinsic', 15.0)
                    
                    if adv_require_above_ma:
                        st.write(f"📈 Trend Filter: Requiring price above 50-day MA")
                    
                    # Scan for LEAPs with all filters
                    results = scan_leap_options(
                        tradier,
                        pmcc_watchlist,
                        dte_min=dte_min,
                        dte_max=dte_max,
                        delta_min=delta_min,
                        delta_max=delta_max,
                        min_oi=min_oi,
                        max_bid_ask_spread=max_bid_ask_spread,
                        max_extrinsic_pct=adv_max_extrinsic,
                        max_iv=adv_max_iv,
                        require_above_ma=adv_require_above_ma,
                        min_rsi=adv_min_rsi,
                        max_rsi=adv_max_rsi,
                        min_capital_efficiency=adv_min_efficiency,
                        max_capital_efficiency=adv_max_efficiency,
                        include_technical=True
                    )
                    
                    st.session_state.pmcc_leap_scan_results = results
                    
                    status.update(label=f"✅ Found {len(results)} LEAP opportunities!", state="complete")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error scanning for LEAPs: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
    
    # Display scan results
    if st.session_state.pmcc_leap_scan_results:
        st.write("")
        st.markdown(f"### 📊 LEAP Scan Results")
        
        # Initialize opportunities DataFrame in session state (like CSP Dashboard)
        if 'pmcc_opportunities' not in st.session_state or st.session_state.get('pmcc_needs_refresh', False):
            results_df = pd.DataFrame(st.session_state.pmcc_leap_scan_results)
            
            # Add Select and Qty columns
            results_df['Select'] = False
            results_df['Qty'] = 1
            
            # Store raw data for order submission
            results_df['_raw_data'] = st.session_state.pmcc_leap_scan_results
            
            st.session_state.pmcc_opportunities = results_df
            st.session_state.pmcc_needs_refresh = False
        
        # Initialize show_selected_only toggle
        if 'pmcc_show_selected_only' not in st.session_state:
            st.session_state.pmcc_show_selected_only = False
        
        # Initialize PMCC preset criteria in session state (defaults for LEAP selection)
        # Conservative: High delta (0.80-0.90), low extrinsic, low capital efficiency
        if 'pmcc_conservative_delta_min' not in st.session_state:
            st.session_state.pmcc_conservative_delta_min = 0.80
            st.session_state.pmcc_conservative_delta_max = 0.95
            st.session_state.pmcc_conservative_dte_min = 300
            st.session_state.pmcc_conservative_dte_max = 500
            st.session_state.pmcc_conservative_extrinsic_max = 10.0
            st.session_state.pmcc_conservative_cap_eff_max = 70.0
            st.session_state.pmcc_conservative_spread_max = 3.0
            st.session_state.pmcc_conservative_rsi_min = 30
            st.session_state.pmcc_conservative_rsi_max = 70
        
        # Medium: Moderate delta (0.75-0.85), moderate filters
        if 'pmcc_medium_delta_min' not in st.session_state:
            st.session_state.pmcc_medium_delta_min = 0.75
            st.session_state.pmcc_medium_delta_max = 0.90
            st.session_state.pmcc_medium_dte_min = 270
            st.session_state.pmcc_medium_dte_max = 450
            st.session_state.pmcc_medium_extrinsic_max = 15.0
            st.session_state.pmcc_medium_cap_eff_max = 80.0
            st.session_state.pmcc_medium_spread_max = 5.0
            st.session_state.pmcc_medium_rsi_min = 25
            st.session_state.pmcc_medium_rsi_max = 75
        
        # Aggressive: Lower delta (0.70-0.80), looser filters, more leverage
        if 'pmcc_aggressive_delta_min' not in st.session_state:
            st.session_state.pmcc_aggressive_delta_min = 0.70
            st.session_state.pmcc_aggressive_delta_max = 0.85
            st.session_state.pmcc_aggressive_dte_min = 240
            st.session_state.pmcc_aggressive_dte_max = 400
            st.session_state.pmcc_aggressive_extrinsic_max = 20.0
            st.session_state.pmcc_aggressive_cap_eff_max = 90.0
            st.session_state.pmcc_aggressive_spread_max = 8.0
            st.session_state.pmcc_aggressive_rsi_min = 20
            st.session_state.pmcc_aggressive_rsi_max = 80
        
        # Function to select best LEAP per ticker based on criteria
        def select_best_leap_per_ticker(df, delta_min, delta_max, dte_min, dte_max, 
                                         extrinsic_max=100, cap_eff_max=100, spread_max=100,
                                         rsi_min=0, rsi_max=100, qty=1):
            """Select best LEAP option per ticker based on PMCC criteria"""
            selections = []
            
            # Start with all data
            filtered = df.copy()
            
            # Filter by Delta
            if 'delta' in filtered.columns:
                filtered = filtered[(filtered['delta'] >= delta_min) & (filtered['delta'] <= delta_max)]
            
            # Filter by DTE
            if 'dte' in filtered.columns:
                filtered = filtered[(filtered['dte'] >= dte_min) & (filtered['dte'] <= dte_max)]
            
            # Filter by Extrinsic %
            if 'extrinsic_pct' in filtered.columns and extrinsic_max < 100:
                filtered = filtered[filtered['extrinsic_pct'] <= extrinsic_max]
            
            # Filter by Capital Efficiency %
            if 'capital_efficiency' in filtered.columns and cap_eff_max < 100:
                filtered = filtered[filtered['capital_efficiency'] <= cap_eff_max]
            
            # Filter by Bid-Ask Spread %
            if 'bid_ask_spread_pct' in filtered.columns and spread_max < 100:
                filtered = filtered[filtered['bid_ask_spread_pct'] <= spread_max]
            
            # Filter by RSI range
            if 'rsi' in filtered.columns:
                filtered = filtered[(filtered['rsi'].isna()) | ((filtered['rsi'] >= rsi_min) & (filtered['rsi'] <= rsi_max))]
            
            if len(filtered) == 0:
                return selections
            
            # Group by symbol and select best (highest PMCC score, or highest delta if no score)
            for symbol in filtered['symbol'].unique():
                symbol_opps = filtered[filtered['symbol'] == symbol]
                if len(symbol_opps) > 0:
                    # Select by highest PMCC score if available, otherwise highest delta
                    if 'pmcc_score' in symbol_opps.columns and symbol_opps['pmcc_score'].notna().any():
                        best_idx = symbol_opps['pmcc_score'].idxmax()
                    else:
                        best_idx = symbol_opps['delta'].idxmax()
                    selections.append((best_idx, qty))
            
            return selections
        
        # Preset Filter Buttons Row (like CSP Dashboard)
        st.write("")
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1.5, 1.5, 1.5, 1, 1])
        
        with col1:
            if st.button("🗑️ Clear All", key="pmcc_clear_all"):
                st.session_state.pmcc_opportunities['Select'] = False
                if 'pmcc_active_preset' in st.session_state:
                    del st.session_state.pmcc_active_preset
                st.rerun()
        
        with col2:
            if st.button("🟢 Conservative", key="pmcc_preset_conservative",
                       help=f"Δ {st.session_state.pmcc_conservative_delta_min}-{st.session_state.pmcc_conservative_delta_max}, DTE {st.session_state.pmcc_conservative_dte_min}-{st.session_state.pmcc_conservative_dte_max}, Extr≤{st.session_state.pmcc_conservative_extrinsic_max}%"):
                # Track active preset
                st.session_state.pmcc_active_preset = 'conservative'
                
                # Clear all first
                st.session_state.pmcc_opportunities['Select'] = False
                st.session_state.pmcc_opportunities['Qty'] = 1
                
                # Select best LEAPs per ticker
                selections = select_best_leap_per_ticker(
                    st.session_state.pmcc_opportunities,
                    st.session_state.pmcc_conservative_delta_min,
                    st.session_state.pmcc_conservative_delta_max,
                    st.session_state.pmcc_conservative_dte_min,
                    st.session_state.pmcc_conservative_dte_max,
                    extrinsic_max=st.session_state.pmcc_conservative_extrinsic_max,
                    cap_eff_max=st.session_state.pmcc_conservative_cap_eff_max,
                    spread_max=st.session_state.pmcc_conservative_spread_max,
                    rsi_min=st.session_state.pmcc_conservative_rsi_min,
                    rsi_max=st.session_state.pmcc_conservative_rsi_max,
                    qty=1
                )
                
                # Apply selections
                for idx, qty in selections:
                    st.session_state.pmcc_opportunities.loc[idx, 'Select'] = True
                    st.session_state.pmcc_opportunities.loc[idx, 'Qty'] = qty
                
                st.rerun()
        
        with col3:
            if st.button("🟡 Medium", key="pmcc_preset_medium",
                       help=f"Δ {st.session_state.pmcc_medium_delta_min}-{st.session_state.pmcc_medium_delta_max}, DTE {st.session_state.pmcc_medium_dte_min}-{st.session_state.pmcc_medium_dte_max}, Extr≤{st.session_state.pmcc_medium_extrinsic_max}%"):
                # Track active preset
                st.session_state.pmcc_active_preset = 'medium'
                
                # Clear all first
                st.session_state.pmcc_opportunities['Select'] = False
                st.session_state.pmcc_opportunities['Qty'] = 1
                
                # Select best LEAPs per ticker
                selections = select_best_leap_per_ticker(
                    st.session_state.pmcc_opportunities,
                    st.session_state.pmcc_medium_delta_min,
                    st.session_state.pmcc_medium_delta_max,
                    st.session_state.pmcc_medium_dte_min,
                    st.session_state.pmcc_medium_dte_max,
                    extrinsic_max=st.session_state.pmcc_medium_extrinsic_max,
                    cap_eff_max=st.session_state.pmcc_medium_cap_eff_max,
                    spread_max=st.session_state.pmcc_medium_spread_max,
                    rsi_min=st.session_state.pmcc_medium_rsi_min,
                    rsi_max=st.session_state.pmcc_medium_rsi_max,
                    qty=1
                )
                
                # Apply selections
                for idx, qty in selections:
                    st.session_state.pmcc_opportunities.loc[idx, 'Select'] = True
                    st.session_state.pmcc_opportunities.loc[idx, 'Qty'] = qty
                
                st.rerun()
        
        with col4:
            if st.button("🔴 Aggressive", key="pmcc_preset_aggressive",
                       help=f"Δ {st.session_state.pmcc_aggressive_delta_min}-{st.session_state.pmcc_aggressive_delta_max}, DTE {st.session_state.pmcc_aggressive_dte_min}-{st.session_state.pmcc_aggressive_dte_max}, Extr≤{st.session_state.pmcc_aggressive_extrinsic_max}%"):
                # Track active preset
                st.session_state.pmcc_active_preset = 'aggressive'
                
                # Clear all first
                st.session_state.pmcc_opportunities['Select'] = False
                st.session_state.pmcc_opportunities['Qty'] = 1
                
                # Select best LEAPs per ticker
                selections = select_best_leap_per_ticker(
                    st.session_state.pmcc_opportunities,
                    st.session_state.pmcc_aggressive_delta_min,
                    st.session_state.pmcc_aggressive_delta_max,
                    st.session_state.pmcc_aggressive_dte_min,
                    st.session_state.pmcc_aggressive_dte_max,
                    extrinsic_max=st.session_state.pmcc_aggressive_extrinsic_max,
                    cap_eff_max=st.session_state.pmcc_aggressive_cap_eff_max,
                    spread_max=st.session_state.pmcc_aggressive_spread_max,
                    rsi_min=st.session_state.pmcc_aggressive_rsi_min,
                    rsi_max=st.session_state.pmcc_aggressive_rsi_max,
                    qty=1
                )
                
                # Apply selections
                for idx, qty in selections:
                    st.session_state.pmcc_opportunities.loc[idx, 'Select'] = True
                    st.session_state.pmcc_opportunities.loc[idx, 'Qty'] = qty
                
                st.rerun()
        
        with col5:
            if st.button("✅ Select All", key="pmcc_select_all"):
                st.session_state.pmcc_opportunities['Select'] = True
                st.rerun()
        
        with col6:
            selected_count = st.session_state.pmcc_opportunities['Select'].sum()
            st.metric("Selected", int(selected_count))
        
        # Quantity adjustment buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("➕ +1 Qty", key="pmcc_qty_plus1"):
                mask = st.session_state.pmcc_opportunities['Select'] == True
                st.session_state.pmcc_opportunities.loc[mask, 'Qty'] += 1
                st.rerun()
        with col2:
            if st.button("➖ -1 Qty", key="pmcc_qty_minus1"):
                mask = st.session_state.pmcc_opportunities['Select'] == True
                st.session_state.pmcc_opportunities.loc[mask, 'Qty'] = st.session_state.pmcc_opportunities.loc[mask, 'Qty'].apply(lambda x: max(1, x - 1))
                st.rerun()
        with col3:
            if st.button("🔄 Reset Qty", key="pmcc_qty_reset"):
                st.session_state.pmcc_opportunities['Qty'] = 1
                st.rerun()
        with col4:
            # Show active preset indicator
            active_preset = st.session_state.get('pmcc_active_preset', None)
            if active_preset:
                preset_colors = {'conservative': '🟢', 'medium': '🟡', 'aggressive': '🔴'}
                st.caption(f"Active: {preset_colors.get(active_preset, '')} {active_preset.title()}")
        
        st.write("---")
        
        # Preset Filter Configuration Expanders (like CSP Dashboard)
        st.subheader("⚙️ Preset Filter Configuration")
        
        # Conservative Expander
        with st.expander("🟢 Conservative Filter Configuration", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                cons_delta_min = st.number_input("Min Delta", value=st.session_state.pmcc_conservative_delta_min, min_value=0.5, max_value=1.0, step=0.05, key="pmcc_cons_delta_min")
                cons_delta_max = st.number_input("Max Delta", value=st.session_state.pmcc_conservative_delta_max, min_value=0.5, max_value=1.0, step=0.05, key="pmcc_cons_delta_max")
            with col2:
                cons_dte_min = st.number_input("Min DTE", value=st.session_state.pmcc_conservative_dte_min, min_value=180, max_value=730, step=30, key="pmcc_cons_dte_min")
                cons_dte_max = st.number_input("Max DTE", value=st.session_state.pmcc_conservative_dte_max, min_value=180, max_value=730, step=30, key="pmcc_cons_dte_max")
            with col3:
                cons_extr_max = st.number_input("Max Extrinsic %", value=st.session_state.pmcc_conservative_extrinsic_max, min_value=0.0, max_value=50.0, step=1.0, key="pmcc_cons_extr_max")
                cons_cap_eff_max = st.number_input("Max Cap Eff %", value=st.session_state.pmcc_conservative_cap_eff_max, min_value=0.0, max_value=100.0, step=5.0, key="pmcc_cons_cap_eff_max")
            
            col1, col2 = st.columns(2)
            with col1:
                cons_spread_max = st.number_input("Max Spread %", value=st.session_state.pmcc_conservative_spread_max, min_value=0.0, max_value=20.0, step=0.5, key="pmcc_cons_spread_max")
            with col2:
                cons_rsi_min = st.number_input("Min RSI", value=st.session_state.pmcc_conservative_rsi_min, min_value=0, max_value=100, step=5, key="pmcc_cons_rsi_min")
                cons_rsi_max = st.number_input("Max RSI", value=st.session_state.pmcc_conservative_rsi_max, min_value=0, max_value=100, step=5, key="pmcc_cons_rsi_max")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Commit Conservative", key="pmcc_commit_conservative"):
                    st.session_state.pmcc_conservative_delta_min = cons_delta_min
                    st.session_state.pmcc_conservative_delta_max = cons_delta_max
                    st.session_state.pmcc_conservative_dte_min = cons_dte_min
                    st.session_state.pmcc_conservative_dte_max = cons_dte_max
                    st.session_state.pmcc_conservative_extrinsic_max = cons_extr_max
                    st.session_state.pmcc_conservative_cap_eff_max = cons_cap_eff_max
                    st.session_state.pmcc_conservative_spread_max = cons_spread_max
                    st.session_state.pmcc_conservative_rsi_min = cons_rsi_min
                    st.session_state.pmcc_conservative_rsi_max = cons_rsi_max
                    st.success("✅ Conservative criteria committed!")
                    st.rerun()
            with col2:
                if st.button("🔄 Reset Conservative", key="pmcc_reset_conservative"):
                    st.session_state.pmcc_conservative_delta_min = 0.80
                    st.session_state.pmcc_conservative_delta_max = 0.95
                    st.session_state.pmcc_conservative_dte_min = 300
                    st.session_state.pmcc_conservative_dte_max = 500
                    st.session_state.pmcc_conservative_extrinsic_max = 10.0
                    st.session_state.pmcc_conservative_cap_eff_max = 70.0
                    st.session_state.pmcc_conservative_spread_max = 3.0
                    st.session_state.pmcc_conservative_rsi_min = 30
                    st.session_state.pmcc_conservative_rsi_max = 70
                    st.success("✅ Conservative reset to defaults!")
                    st.rerun()
        
        # Medium Expander
        with st.expander("🟡 Medium Filter Configuration", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                med_delta_min = st.number_input("Min Delta", value=st.session_state.pmcc_medium_delta_min, min_value=0.5, max_value=1.0, step=0.05, key="pmcc_med_delta_min")
                med_delta_max = st.number_input("Max Delta", value=st.session_state.pmcc_medium_delta_max, min_value=0.5, max_value=1.0, step=0.05, key="pmcc_med_delta_max")
            with col2:
                med_dte_min = st.number_input("Min DTE", value=st.session_state.pmcc_medium_dte_min, min_value=180, max_value=730, step=30, key="pmcc_med_dte_min")
                med_dte_max = st.number_input("Max DTE", value=st.session_state.pmcc_medium_dte_max, min_value=180, max_value=730, step=30, key="pmcc_med_dte_max")
            with col3:
                med_extr_max = st.number_input("Max Extrinsic %", value=st.session_state.pmcc_medium_extrinsic_max, min_value=0.0, max_value=50.0, step=1.0, key="pmcc_med_extr_max")
                med_cap_eff_max = st.number_input("Max Cap Eff %", value=st.session_state.pmcc_medium_cap_eff_max, min_value=0.0, max_value=100.0, step=5.0, key="pmcc_med_cap_eff_max")
            
            col1, col2 = st.columns(2)
            with col1:
                med_spread_max = st.number_input("Max Spread %", value=st.session_state.pmcc_medium_spread_max, min_value=0.0, max_value=20.0, step=0.5, key="pmcc_med_spread_max")
            with col2:
                med_rsi_min = st.number_input("Min RSI", value=st.session_state.pmcc_medium_rsi_min, min_value=0, max_value=100, step=5, key="pmcc_med_rsi_min")
                med_rsi_max = st.number_input("Max RSI", value=st.session_state.pmcc_medium_rsi_max, min_value=0, max_value=100, step=5, key="pmcc_med_rsi_max")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Commit Medium", key="pmcc_commit_medium"):
                    st.session_state.pmcc_medium_delta_min = med_delta_min
                    st.session_state.pmcc_medium_delta_max = med_delta_max
                    st.session_state.pmcc_medium_dte_min = med_dte_min
                    st.session_state.pmcc_medium_dte_max = med_dte_max
                    st.session_state.pmcc_medium_extrinsic_max = med_extr_max
                    st.session_state.pmcc_medium_cap_eff_max = med_cap_eff_max
                    st.session_state.pmcc_medium_spread_max = med_spread_max
                    st.session_state.pmcc_medium_rsi_min = med_rsi_min
                    st.session_state.pmcc_medium_rsi_max = med_rsi_max
                    st.success("✅ Medium criteria committed!")
                    st.rerun()
            with col2:
                if st.button("🔄 Reset Medium", key="pmcc_reset_medium"):
                    st.session_state.pmcc_medium_delta_min = 0.75
                    st.session_state.pmcc_medium_delta_max = 0.90
                    st.session_state.pmcc_medium_dte_min = 270
                    st.session_state.pmcc_medium_dte_max = 450
                    st.session_state.pmcc_medium_extrinsic_max = 15.0
                    st.session_state.pmcc_medium_cap_eff_max = 80.0
                    st.session_state.pmcc_medium_spread_max = 5.0
                    st.session_state.pmcc_medium_rsi_min = 25
                    st.session_state.pmcc_medium_rsi_max = 75
                    st.success("✅ Medium reset to defaults!")
                    st.rerun()
        
        # Aggressive Expander
        with st.expander("🔴 Aggressive Filter Configuration", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                agg_delta_min = st.number_input("Min Delta", value=st.session_state.pmcc_aggressive_delta_min, min_value=0.5, max_value=1.0, step=0.05, key="pmcc_agg_delta_min")
                agg_delta_max = st.number_input("Max Delta", value=st.session_state.pmcc_aggressive_delta_max, min_value=0.5, max_value=1.0, step=0.05, key="pmcc_agg_delta_max")
            with col2:
                agg_dte_min = st.number_input("Min DTE", value=st.session_state.pmcc_aggressive_dte_min, min_value=180, max_value=730, step=30, key="pmcc_agg_dte_min")
                agg_dte_max = st.number_input("Max DTE", value=st.session_state.pmcc_aggressive_dte_max, min_value=180, max_value=730, step=30, key="pmcc_agg_dte_max")
            with col3:
                agg_extr_max = st.number_input("Max Extrinsic %", value=st.session_state.pmcc_aggressive_extrinsic_max, min_value=0.0, max_value=50.0, step=1.0, key="pmcc_agg_extr_max")
                agg_cap_eff_max = st.number_input("Max Cap Eff %", value=st.session_state.pmcc_aggressive_cap_eff_max, min_value=0.0, max_value=100.0, step=5.0, key="pmcc_agg_cap_eff_max")
            
            col1, col2 = st.columns(2)
            with col1:
                agg_spread_max = st.number_input("Max Spread %", value=st.session_state.pmcc_aggressive_spread_max, min_value=0.0, max_value=20.0, step=0.5, key="pmcc_agg_spread_max")
            with col2:
                agg_rsi_min = st.number_input("Min RSI", value=st.session_state.pmcc_aggressive_rsi_min, min_value=0, max_value=100, step=5, key="pmcc_agg_rsi_min")
                agg_rsi_max = st.number_input("Max RSI", value=st.session_state.pmcc_aggressive_rsi_max, min_value=0, max_value=100, step=5, key="pmcc_agg_rsi_max")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Commit Aggressive", key="pmcc_commit_aggressive"):
                    st.session_state.pmcc_aggressive_delta_min = agg_delta_min
                    st.session_state.pmcc_aggressive_delta_max = agg_delta_max
                    st.session_state.pmcc_aggressive_dte_min = agg_dte_min
                    st.session_state.pmcc_aggressive_dte_max = agg_dte_max
                    st.session_state.pmcc_aggressive_extrinsic_max = agg_extr_max
                    st.session_state.pmcc_aggressive_cap_eff_max = agg_cap_eff_max
                    st.session_state.pmcc_aggressive_spread_max = agg_spread_max
                    st.session_state.pmcc_aggressive_rsi_min = agg_rsi_min
                    st.session_state.pmcc_aggressive_rsi_max = agg_rsi_max
                    st.success("✅ Aggressive criteria committed!")
                    st.rerun()
            with col2:
                if st.button("🔄 Reset Aggressive", key="pmcc_reset_aggressive"):
                    st.session_state.pmcc_aggressive_delta_min = 0.70
                    st.session_state.pmcc_aggressive_delta_max = 0.85
                    st.session_state.pmcc_aggressive_dte_min = 240
                    st.session_state.pmcc_aggressive_dte_max = 400
                    st.session_state.pmcc_aggressive_extrinsic_max = 20.0
                    st.session_state.pmcc_aggressive_cap_eff_max = 90.0
                    st.session_state.pmcc_aggressive_spread_max = 8.0
                    st.session_state.pmcc_aggressive_rsi_min = 20
                    st.session_state.pmcc_aggressive_rsi_max = 80
                    st.success("✅ Aggressive reset to defaults!")
                    st.rerun()
        
        st.write("---")
        
        # Toggle to show only selected (like CSP Dashboard)
        col1, col2 = st.columns([1, 4])
        with col1:
            show_selected_only = st.toggle(
                "👁️ Selected Only",
                value=st.session_state.pmcc_show_selected_only,
                key="pmcc_show_selected_toggle",
                help="Show only the LEAPs you've selected (checked)"
            )
            st.session_state.pmcc_show_selected_only = show_selected_only
        with col2:
            total_count = len(st.session_state.pmcc_opportunities)
            if show_selected_only:
                st.caption(f"Showing {int(selected_count)} selected of {total_count} total opportunities")
            else:
                st.caption(f"Showing all {total_count} opportunities ({int(selected_count)} selected)")
        
        st.write("")
        
        # Prepare display DataFrame
        display_df = st.session_state.pmcc_opportunities.copy()
        
        # Apply "show selected only" filter if enabled
        if show_selected_only:
            display_df = display_df[display_df['Select'] == True].copy()
        
        # Helper functions for emoji indicators
        def score_emoji(val):
            """PMCC Score: higher is better"""
            if val is None or pd.isna(val):
                return ""
            if val >= 80:
                return f"🟢 {val:.0f}"
            elif val >= 60:
                return f"🟡 {val:.0f}"
            else:
                return f"🔴 {val:.0f}"
        
        def extrinsic_emoji(val):
            """Extrinsic %: lower is better (less time premium)"""
            if val is None or pd.isna(val):
                return ""
            if val <= 8:
                return f"🟢 {val:.1f}%"
            elif val <= 15:
                return f"🟡 {val:.1f}%"
            else:
                return f"🔴 {val:.1f}%"
        
        def cap_eff_emoji(val):
            """Capital Efficiency %: lower is better (cheaper than shares)"""
            if val is None or pd.isna(val):
                return ""
            if val <= 50:
                return f"🟢 {val:.0f}%"
            elif val <= 70:
                return f"🟡 {val:.0f}%"
            else:
                return f"🔴 {val:.0f}%"
        
        def spread_emoji(val):
            """Bid-Ask Spread %: lower is better (more liquid)"""
            if val is None or pd.isna(val):
                return ""
            if val <= 2:
                return f"🟢 {val:.1f}%"
            elif val <= 5:
                return f"🟡 {val:.1f}%"
            else:
                return f"🔴 {val:.1f}%"
        
        def iv_emoji(val):
            """IV %: lower is better for buying LEAPs"""
            if val is None or pd.isna(val):
                return ""
            if val <= 40:
                return f"🟢 {val:.0f}%"
            elif val <= 60:
                return f"🟡 {val:.0f}%"
            else:
                return f"🔴 {val:.0f}%"
        
        def rsi_emoji(val):
            """RSI: 40-60 ideal, 30-70 ok, outside is warning"""
            if val is None or pd.isna(val):
                return ""
            if 40 <= val <= 60:
                return f"🟢 {val:.0f}"
            elif 30 <= val <= 70:
                return f"🟡 {val:.0f}"
            else:
                return f"🔴 {val:.0f}"
        
        def ma_emoji(val):
            """MA %: above MA (positive) is better for PMCC"""
            if val is None or pd.isna(val):
                return ""
            if val > 5:
                return f"🟢 +{val:.1f}%"
            elif val > -5:
                return f"🟡 {val:+.1f}%"
            else:
                return f"🔴 {val:+.1f}%"
        
        def delta_emoji(val):
            """Delta: higher is better for PMCC (more stock-like)"""
            if val is None or pd.isna(val):
                return ""
            if val >= 0.85:
                return f"🟢 {val:.2f}"
            elif val >= 0.75:
                return f"🟡 {val:.2f}"
            else:
                return f"🔴 {val:.2f}"
        
        # Select columns for display FIRST (before formatting)
        display_cols = ['Select', 'Qty', 'symbol', 'underlying_price', 'strike', 'expiration', 'dte', 'delta', 'price', 'cost_per_contract']
        
        # Add enhanced columns if available
        for col in ['pmcc_score', 'extrinsic_pct', 'capital_efficiency', 'bid_ask_spread_pct', 'iv', 'rsi', 'ma_percent', 'open_interest', 'volume']:
            if col in display_df.columns:
                display_cols.append(col)
        
        # Filter to only existing columns
        display_cols = [c for c in display_cols if c in display_df.columns]
        display_df = display_df[display_cols].copy()
        
        # Now apply emoji formatting to indicator columns (after column selection)
        if 'pmcc_score' in display_df.columns:
            display_df['pmcc_score'] = display_df['pmcc_score'].apply(score_emoji).astype(str)
        if 'extrinsic_pct' in display_df.columns:
            display_df['extrinsic_pct'] = display_df['extrinsic_pct'].apply(extrinsic_emoji).astype(str)
        if 'capital_efficiency' in display_df.columns:
            display_df['capital_efficiency'] = display_df['capital_efficiency'].apply(cap_eff_emoji).astype(str)
        if 'bid_ask_spread_pct' in display_df.columns:
            display_df['bid_ask_spread_pct'] = display_df['bid_ask_spread_pct'].apply(spread_emoji).astype(str)
        if 'iv' in display_df.columns:
            display_df['iv'] = display_df['iv'].apply(iv_emoji).astype(str)
        if 'rsi' in display_df.columns:
            display_df['rsi'] = display_df['rsi'].apply(rsi_emoji).astype(str)
        if 'ma_percent' in display_df.columns:
            display_df['ma_percent'] = display_df['ma_percent'].apply(ma_emoji).astype(str)
        if 'delta' in display_df.columns:
            display_df['delta'] = display_df['delta'].apply(delta_emoji).astype(str)
        
        # Format cost as clean dollars
        if 'cost_per_contract' in display_df.columns:
            display_df['cost_per_contract'] = display_df['cost_per_contract'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "").astype(str)
        
        # Format other currency columns
        if 'underlying_price' in display_df.columns:
            display_df['underlying_price'] = display_df['underlying_price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "").astype(str)
        if 'strike' in display_df.columns:
            display_df['strike'] = display_df['strike'].apply(lambda x: f"${x:.0f}" if pd.notna(x) else "").astype(str)
        if 'price' in display_df.columns:
            display_df['price'] = display_df['price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "").astype(str)
        
        # Rename columns for display
        col_rename = {
            'symbol': 'Symbol',
            'underlying_price': 'Stock $',
            'strike': 'Strike',
            'expiration': 'Expiration',
            'dte': 'DTE',
            'delta': 'Delta',
            'price': 'Premium',
            'cost_per_contract': 'Cost',
            'pmcc_score': '🎯 Score',
            'extrinsic_pct': 'Extr %',
            'capital_efficiency': 'Cap Eff %',
            'bid_ask_spread_pct': 'Spread %',
            'iv': 'IV %',
            'rsi': 'RSI',
            'ma_percent': 'MA %',
            'open_interest': 'OI',
            'volume': 'Vol'
        }
        display_df.rename(columns=col_rename, inplace=True)
        
        # Calculate dynamic height
        calculated_height = len(display_df) * 35 + 60
        if show_selected_only:
            dynamic_height = max(200, calculated_height)
        else:
            dynamic_height = max(400, min(calculated_height, 800))
        
        # Display editable table with checkbox column
        edited_df = st.data_editor(
            display_df,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select LEAPs to purchase",
                    default=False,
                ),
                "Qty": st.column_config.NumberColumn(
                    "Qty",
                    help="Number of contracts to buy",
                    min_value=1,
                    max_value=100,
                    step=1,
                    default=1,
                ),
                "Stock $": st.column_config.TextColumn("Stock $"),
                "Strike": st.column_config.TextColumn("Strike"),
                "Delta": st.column_config.TextColumn("Delta"),
                "Premium": st.column_config.TextColumn("Premium"),
                "Cost": st.column_config.TextColumn("Cost"),
                "🎯 Score": st.column_config.TextColumn("🎯 Score"),
                "Extr %": st.column_config.TextColumn("Extr %"),
                "Cap Eff %": st.column_config.TextColumn("Cap Eff %"),
                "Spread %": st.column_config.TextColumn("Spread %"),
                "IV %": st.column_config.TextColumn("IV %"),
                "RSI": st.column_config.TextColumn("RSI"),
                "MA %": st.column_config.TextColumn("MA %"),
            },
            hide_index=True,
            height=dynamic_height,
            key="pmcc_leap_editor"
        )
        
        # Update session state with edits
        if show_selected_only:
            # Update by matching indices
            for idx, row in edited_df.iterrows():
                orig_idx = display_df.index[edited_df.index.get_loc(idx)]
                st.session_state.pmcc_opportunities.loc[orig_idx, 'Select'] = row['Select']
                st.session_state.pmcc_opportunities.loc[orig_idx, 'Qty'] = row['Qty']
        else:
            # Direct update
            st.session_state.pmcc_opportunities['Select'] = edited_df['Select'].values
            st.session_state.pmcc_opportunities['Qty'] = edited_df['Qty'].values
        
        # Summary of selected LEAPs
        selected_leaps = st.session_state.pmcc_opportunities[st.session_state.pmcc_opportunities['Select'] == True]
        if len(selected_leaps) > 0:
            st.write("")
            st.markdown("### 💰 Selected LEAPs Summary")
            
            total_contracts = int(selected_leaps['Qty'].sum())
            total_cost = (selected_leaps['cost_per_contract'] * selected_leaps['Qty']).sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("LEAPs Selected", len(selected_leaps))
            with col2:
                st.metric("Total Contracts", total_contracts)
            with col3:
                st.metric("Total Cost", f"${total_cost:,.0f}")
            
            st.write("")
            
            # Submit orders button
            if st.button("💰 Buy Selected LEAPs (Submit Orders)", type="primary", key="pmcc_buy_selected"):
                try:
                    with st.status("Submitting LEAP buy orders...", expanded=True) as status:
                        from utils.pmcc_orders import submit_leap_buy_order
                        
                        success_count = 0
                        fail_count = 0
                        
                        for idx, row in selected_leaps.iterrows():
                            symbol = row['symbol']
                            qty = int(row['Qty'])
                            price = row['price']
                            option_symbol = row.get('option_symbol', '')
                            
                            st.write(f"💰 Buying {qty} contract(s) of {symbol} at ${price:.2f}...")
                            
                            try:
                                result = submit_leap_buy_order(
                                    api,
                                    selected_account,
                                    option_symbol,
                                    qty,
                                    price,
                                    order_type='Limit'
                                )
                                
                                if result['success']:
                                    st.write(f"✅ {symbol}: Order submitted (ID: {result.get('order_id', 'N/A')})")
                                    success_count += 1
                                else:
                                    st.write(f"❌ {symbol}: {result['message']}")
                                    fail_count += 1
                            except Exception as e:
                                st.write(f"❌ {symbol}: {str(e)}")
                                fail_count += 1
                        
                        if fail_count == 0:
                            status.update(label=f"✅ All {success_count} orders submitted successfully!", state="complete")
                            celebrate_success()
                        else:
                            status.update(label=f"⚠️ {success_count} succeeded, {fail_count} failed", state="complete")
                        
                except Exception as e:
                    st.error(f"Error submitting orders: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
    
    st.divider()
    
    # ========================================
    # SECTION 4: SHORT CALL OPPORTUNITY SCANNER
    # ========================================
    st.markdown('<div class="section-header">💰 Sell Calls Against LEAPs</div>', unsafe_allow_html=True)
    
    if st.session_state.pmcc_leap_positions:
        st.markdown("**Select a LEAP position to find short call opportunities:**")
        
        # Create dropdown of LEAP positions
        leap_options = [f"{pos['underlying']} ${pos['strike']:.2f} exp {pos['expiration']}" 
                       for pos in st.session_state.pmcc_leap_positions]
        
        selected_leap_idx = st.selectbox(
            "Select LEAP Position",
            range(len(leap_options)),
            format_func=lambda x: leap_options[x],
            key="pmcc_selected_leap"
        )
        
        if selected_leap_idx is not None:
            selected_leap = st.session_state.pmcc_leap_positions[selected_leap_idx]
            
            st.write("")
            st.markdown(f"**Scanning for short calls on {selected_leap['underlying']}...**")
            
            # Short call filters
            col1, col2 = st.columns(2)
            with col1:
                short_dte_min = st.number_input("Min DTE", min_value=7, max_value=90, value=30, step=7, key="pmcc_short_dte_min")
                short_dte_max = st.number_input("Max DTE", min_value=7, max_value=90, value=45, step=7, key="pmcc_short_dte_max")
            
            with col2:
                short_delta_max = st.number_input("Max Delta", min_value=0.1, max_value=0.5, value=0.30, step=0.05, key="pmcc_short_delta_max")
                min_premium = st.number_input("Min Premium ($)", min_value=0, max_value=1000, value=50, step=10, key="pmcc_min_premium")
            
            # Initialize session state for short call scan results
            if 'pmcc_short_call_scan_results' not in st.session_state:
                st.session_state.pmcc_short_call_scan_results = []
            
            st.write("")
            if st.button("🔍 Scan Short Calls", type="primary", key="pmcc_scan_short"):
                try:
                    with st.status("Scanning for short call opportunities...", expanded=True) as status:
                        from utils.pmcc_scanner import scan_short_call_opportunities
                        from utils.tradier_api import TradierAPI
                        
                        tradier = TradierAPI()
                        
                        st.write(f"🔍 Scanning {selected_leap['underlying']}...")
                        st.write(f"🎯 Filters: DTE {short_dte_min}-{short_dte_max}, Max Delta {short_delta_max:.2f}, Min Premium ${min_premium}")
                        st.write(f"⚠️ Strike must be above LEAP strike ${selected_leap['strike']:.2f}")
                        
                        # Scan for short calls
                        results = scan_short_call_opportunities(
                            tradier,
                            selected_leap['underlying'],
                            selected_leap['strike'],
                            dte_min=short_dte_min,
                            dte_max=short_dte_max,
                            delta_max=short_delta_max,
                            min_premium=min_premium
                        )
                        
                        st.session_state.pmcc_short_call_scan_results = results
                        
                        status.update(label=f"✅ Found {len(results)} short call opportunities!", state="complete")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error scanning for short calls: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
            
            # Display short call scan results
            if st.session_state.pmcc_short_call_scan_results:
                st.write("")
                st.markdown(f"### 📊 Short Call Opportunities ({len(st.session_state.pmcc_short_call_scan_results)} found)")
                
                results_df = pd.DataFrame(st.session_state.pmcc_short_call_scan_results)
                
                # Format for display
                display_df = results_df[[
                    'strike', 'expiration', 'dte', 'delta',
                    'premium_per_contract', 'distance_from_price_pct', 'distance_from_leap',
                    'open_interest', 'volume'
                ]].copy()
                
                display_df.columns = [
                    'Strike', 'Expiration', 'DTE', 'Delta',
                    'Premium', 'Distance %', 'Above LEAP',
                    'Open Int', 'Volume'
                ]
                
                # Format columns
                display_df['Strike'] = display_df['Strike'].apply(lambda x: f"${x:.2f}" if x and x == x else "N/A")
                display_df['Delta'] = display_df['Delta'].apply(lambda x: f"{x:.3f}" if x and x == x else "N/A")
                display_df['Premium'] = display_df['Premium'].apply(lambda x: f"${x:.0f}" if x and x == x else "N/A")
                display_df['Distance %'] = display_df['Distance %'].apply(lambda x: f"{x:.1f}%" if x and x == x else "N/A")
                display_df['Above LEAP'] = display_df['Above LEAP'].apply(lambda x: f"${x:.2f}" if x and x == x else "N/A")
                
                st.dataframe(display_df, hide_index=True)
                
                # Add action to sell short call
                st.write("")
                st.markdown("**Select a short call to sell:**")
                
                # Create selection dropdown
                short_call_options = [f"${r['strike']:.2f} exp {r['expiration']} (${r['premium_per_contract']:.0f} premium)" 
                                     for r in st.session_state.pmcc_short_call_scan_results]
                
                selected_short_idx = st.selectbox(
                    "Choose Short Call",
                    range(len(short_call_options)),
                    format_func=lambda x: short_call_options[x],
                    key="pmcc_selected_short_to_sell"
                )
                
                if selected_short_idx is not None:
                    selected_short = st.session_state.pmcc_short_call_scan_results[selected_short_idx]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        num_short_contracts = st.number_input(
                            "Number of Contracts",
                            min_value=1,
                            max_value=selected_leap['quantity'],
                            value=1,
                            step=1,
                            key="pmcc_num_short_contracts",
                            help=f"Max {selected_leap['quantity']} (limited by LEAP position)"
                        )
                    
                    with col2:
                        total_premium = selected_short['premium_per_contract'] * num_short_contracts
                        st.metric("Total Premium", f"${total_premium:,.0f}")
                    
                    # Calculate ROI if this short call is sold
                    from utils.pmcc_scanner import calculate_pmcc_roi
                    current_roi = calculate_pmcc_roi(selected_leap['cost_basis'], total_premium)
                    
                    st.info(f"📊 This trade would contribute **{current_roi:.1f}% ROI** on your LEAP cost basis")
                    
                    st.write("")
                    if st.button("💰 Sell Short Call (Submit Order)", type="primary", key="pmcc_sell_short"):
                        try:
                            with st.status("Submitting short call order...", expanded=True) as status:
                                from utils.pmcc_orders import submit_short_call_order
                                
                                st.write(f"💰 Selling {num_short_contracts} contract(s) of {selected_short['symbol']} ${selected_short['strike']:.2f}")
                                st.write(f"💵 Limit Price: ${selected_short['price']:.2f} per contract")
                                st.write(f"💸 Total Premium: ${total_premium:,.0f}")
                                st.write(f"🎯 ROI Contribution: {current_roi:.1f}%")
                                
                                # Submit order via Tastytrade API
                                result = submit_short_call_order(
                                    api,
                                    selected_account,
                                    selected_short['option_symbol'],
                                    num_short_contracts,
                                    selected_short['price'],
                                    order_type='Limit'
                                )
                                
                                if result['success']:
                                    status.update(label=f"✅ Order submitted successfully! Order ID: {result.get('order_id', 'N/A')}", state="complete")
                                    st.success(f"✅ {result['message']}")
                                    st.info(f"📊 Order ID: {result.get('order_id', 'N/A')}")
                                    st.info(f"🕒 Status: {result.get('status', 'Pending')}")
                                    celebrate_success()
                                else:
                                    status.update(label="❌ Order failed", state="error")
                                    st.error(f"❌ {result['message']}")
                                    if 'traceback' in result:
                                        with st.expander("Error Details"):
                                            st.code(result['traceback'])
                                
                        except Exception as e:
                            st.error(f"Error submitting order: {str(e)}")
                            import traceback
                            st.error(traceback.format_exc())
    else:
        st.info("📊 No LEAP positions found. Buy a LEAP first, then come back here to sell calls against it!")


elif page == "Performance":
    # Premium Header
    st.markdown('<h1 style="color: #ffffff; font-size: 36px; font-weight: 600; margin-bottom: 0.5rem;">📊 Performance</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #9ca3af; font-size: 14px; margin-bottom: 1rem;">Track your trading performance and analyze results</p>', unsafe_allow_html=True)
    
    # Import required modules first
    from utils.performance_dashboard import (
        render_active_positions,
        render_stock_basis,
        render_performance_overview
    )
    from utils.performance_overview_new import render_performance_overview_real
    from utils.projections import render_projections_tab
    from utils.working_orders import render_working_orders_dashboard
    from utils.monthly_premium import render_monthly_premium_summary
    
    # Get all account numbers for projections
    all_account_numbers_perf = []
    try:
        accounts_list_perf = api.get_accounts()
        if accounts_list_perf:
            for acc in accounts_list_perf:
                if isinstance(acc, dict):
                    if 'account' in acc and isinstance(acc['account'], dict):
                        acc_num = acc['account'].get('account-number')
                    else:
                        acc_num = acc.get('account-number') or acc.get('account_number')
                    if acc_num:
                        all_account_numbers_perf.append(acc_num)
    except:
        pass
    if not all_account_numbers_perf and selected_account:
        all_account_numbers_perf = [selected_account]
    
    # Get portfolio value for projections
    portfolio_value_perf = 0
    for acc_num in all_account_numbers_perf:
        try:
            balances = api.get_account_balances(acc_num)
            if balances:
                nlv = float(balances.get('net-liquidating-value', 0) or 0)
                portfolio_value_perf += nlv
        except:
            pass
    
    # Create tabs FIRST - at the top of the page (Performance Overview is default/first)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Performance Overview", "📋 Working Orders", "📈 Active Positions", "💰 Stock Basis & Returns", "📈 Projections"])
    
    with tab1:
        # Use the new REAL DATA version of Performance Overview
        render_performance_overview_real(api, all_account_numbers_perf)
    
    with tab2:
        render_working_orders_dashboard(api, selected_account)
    
    with tab3:
        render_active_positions(api)
    
    with tab4:
        render_stock_basis(api)
    
    with tab5:
        render_projections_tab(api, all_account_numbers_perf, portfolio_value_perf)

elif page == "Settings":
    st.title("⚙️ Settings")
    
    st.subheader("🔐 API Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Tastytrade**")
        if os.getenv('TASTYTRADE_USERNAME'):
            st.success(f"✅ Username: {os.getenv('TASTYTRADE_USERNAME')}")
        else:
            st.error("❌ Not configured")
        
        st.write(f"**Accounts:** {len(api.get_accounts())} configured")
    
    with col2:
        st.write("**Tradier**")
        tradier_key = os.getenv("TRADIER_API_KEY", "")
        if tradier_key and tradier_key != "not_configured":
            st.success("✅ Configured ✅ Using PRODUCTION")
        else:
            st.warning("⚠️ Not configured (optional)")
    
    st.divider()
    
    # Debug Balance Viewer
    st.subheader("🔍 Debug: API Balance Fields")
    st.info("This section shows ALL balance fields returned by the Tastytrade API for comparison with the Tastytrade UI.")
    
    if st.button("🔄 Fetch All Balance Fields", key="fetch_debug_balances"):
        with st.spinner("Fetching balance data from Tastytrade API..."):
            try:
                accounts = api.get_accounts_with_names()
                
                if accounts:
                    for acc in accounts:
                        account_number = acc['account_number']
                        nickname = acc.get('nickname', 'Unknown')
                        
                        with st.expander(f"📊 {nickname} ({account_number})", expanded=True):
                            balances = api.get_account_balances(account_number)
                            
                            if balances:
                                # Key buying power fields comparison
                                st.markdown("**💰 Key Buying Power Fields:**")
                                
                                key_fields = [
                                    ('net-liquidating-value', 'Net Liquidating Value'),
                                    ('derivative-buying-power', 'Derivative Buying Power (Options)'),
                                    ('stock-buying-power', 'Stock Buying Power'),
                                    ('equity-buying-power', 'Equity Buying Power'),
                                    ('cash-available-to-withdraw', 'Cash Available to Withdraw'),
                                    ('cash-balance', 'Cash Balance'),
                                    ('maintenance-excess', 'Maintenance Excess'),
                                    ('day-trading-buying-power', 'Day Trading Buying Power'),
                                ]
                                
                                bp_data = []
                                for field, label in key_fields:
                                    value = balances.get(field, 'N/A')
                                    if isinstance(value, (int, float)):
                                        bp_data.append({'Field': label, 'API Field Name': field, 'Value': f"${value:,.2f}"})
                                    else:
                                        bp_data.append({'Field': label, 'API Field Name': field, 'Value': str(value)})
                                
                                import pandas as pd
                                bp_df = pd.DataFrame(bp_data)
                                st.dataframe(bp_df, hide_index=True)
                                
                                # Show ALL fields in expandable section
                                with st.expander("📄 View ALL API Fields (Raw)"):
                                    all_data = []
                                    for key in sorted(balances.keys()):
                                        value = balances[key]
                                        if isinstance(value, (int, float)):
                                            all_data.append({'Field': key, 'Value': f"${value:,.2f}" if abs(value) > 1 else str(value)})
                                        else:
                                            all_data.append({'Field': key, 'Value': str(value)})
                                    
                                    all_df = pd.DataFrame(all_data)
                                    st.dataframe(all_df, hide_index=True)
                            else:
                                st.error(f"❌ Could not fetch balances for {account_number}")
                else:
                    st.error("❌ No accounts found")
            except Exception as e:
                st.error(f"❌ Error fetching balances: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

st.write("---")
st.caption("Built with ❤️ using Streamlit | Options Trading Dashboard v1.0")