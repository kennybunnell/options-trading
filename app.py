import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

from utils.tastytrade_api import TastytradeAPI
from utils.csp_ladder_manager import render_csp_ladder_manager

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
    all_pages = ["🏠 Dashboard", "💰 CSP Dashboard", "📞 Covered Calls", "📈 Performance", "⚙️ Settings"]
    trading_pages = ["🏠 Dashboard", "💰 CSP Dashboard", "📞 Covered Calls", "📈 Performance"]
    
    # Initialize default page
    if 'nav_page' not in st.session_state:
        st.session_state.nav_page = "🏠 Dashboard"
    
    # Trading section radio buttons
    for page_option in trading_pages:
        if st.session_state.nav_page == page_option:
            st.markdown(f'<div style="background-color: #1a1d23; border-left: 3px solid #d4af37; padding: 0.6rem 0.8rem; border-radius: 4px; color: #ffffff; box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);">{page_option}</div>', unsafe_allow_html=True)
        else:
            if st.button(page_option, key=f"nav_{page_option}", use_container_width=True):
                st.session_state.nav_page = page_option
                st.rerun()
    
    # Management section
    st.markdown('<div class="nav-section">MANAGEMENT</div>', unsafe_allow_html=True)
    
    if st.session_state.nav_page == "⚙️ Settings":
        st.markdown(f'<div style="background-color: #1a1d23; border-left: 3px solid #d4af37; padding: 0.6rem 0.8rem; border-radius: 4px; color: #ffffff; box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);">⚙️ Settings</div>', unsafe_allow_html=True)
    else:
        if st.button("⚙️ Settings", key="nav_settings", use_container_width=True):
            st.session_state.nav_page = "⚙️ Settings"
            st.rerun()
    
    page = st.session_state.nav_page
    
    # Quick Stats Panel
    if selected_account:
        # Get positions count
        positions = api.get_positions(selected_account)
        positions_count = len(positions) if positions else 0
        
        # Get working orders count
        orders = api.get_live_orders(selected_account)
        orders_count = len([o for o in orders if o.get('status') == 'Live']) if orders else 0
        
        st.markdown(f"""
        <div class="quick-stats">
            <div class="quick-stats-title">Quick Stats</div>
            <div class="stat-row">
                <span class="stat-label"><span class="stat-dot dot-green"></span>Open Positions</span>
                <span class="stat-value">{positions_count}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label"><span class="stat-dot dot-yellow"></span>Working Orders</span>
                <span class="stat-value">{orders_count}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">This Week</span>
                <span class="stat-value stat-positive">+$8,432</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Win Rate</span>
                <span class="stat-value">87% ⭐</span>
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
    "💰 CSP Dashboard": "CSP Dashboard",
    "📞 Covered Calls": "CC Dashboard",
    "📈 Performance": "Performance",
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
        
        # Monthly Premium Summary Section
        st.markdown('<div class="section-header">💰 Monthly Premium Performance</div>', unsafe_allow_html=True)
        from utils.monthly_premium import render_monthly_premium_summary
        render_monthly_premium_summary(api, selected_account)
        
        # Quick Actions Section
        st.markdown('<div class="section-header">⚡ Quick Actions</div>', unsafe_allow_html=True)
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        
        with action_col1:
            if st.button("💰 Scan CSPs", use_container_width=True):
                st.session_state.nav_page = "💰 CSP Dashboard"
                st.rerun()
        
        with action_col2:
            if st.button("📞 Scan CCs", use_container_width=True):
                st.session_state.nav_page = "📞 Covered Calls"
                st.rerun()
        
        with action_col3:
            if st.button("📈 View Performance", use_container_width=True):
                st.session_state.nav_page = "📈 Performance"
                st.rerun()
        
        with action_col4:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
        
        # CSP Ladder Manager Section
        st.markdown('<div class="section-header">📅 Weekly CSP Ladder</div>', unsafe_allow_html=True)
        render_csp_ladder_manager(api, selected_account)
        
        # Current Positions Section
        st.markdown('<div class="section-header">📊 Current Positions</div>', unsafe_allow_html=True)
        positions = api.get_positions(selected_account)
        
        if positions:
            # Count position types
            short_puts = len([p for p in positions if p.get('instrument-type') == 'Equity Option' and 'PUT' in p.get('symbol', '') and p.get('quantity', 0) < 0])
            short_calls = len([p for p in positions if p.get('instrument-type') == 'Equity Option' and 'CALL' in p.get('symbol', '') and p.get('quantity', 0) < 0])
            stocks = len([p for p in positions if p.get('instrument-type') == 'Equity'])
            
            pos_col1, pos_col2, pos_col3, pos_col4 = st.columns(4)
            
            with pos_col1:
                st.metric("Total Positions", len(positions))
            with pos_col2:
                st.metric("Short Puts (CSPs)", short_puts)
            with pos_col3:
                st.metric("Short Calls (CCs)", short_calls)
            with pos_col4:
                st.metric("Stock Positions", stocks)
        else:
            st.info("📊 No open positions. Start by scanning for CSP or CC opportunities!")


elif page == "CSP Dashboard":
    # Premium Header
    st.markdown('<h1 style="color: #ffffff; font-size: 36px; font-weight: 600; margin-bottom: 0.5rem;">💰 Cash-Secured Puts</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #9ca3af; font-size: 14px; margin-bottom: 2rem;">Manage your CSP positions and discover new opportunities</p>', unsafe_allow_html=True)
    
    from utils.tradier_api import TradierAPI
    from utils.yahoo_finance import get_technical_indicators
    from utils.cash_secured_puts import get_existing_csp_positions
    
    tradier = TradierAPI()
    
    # Existing CSP Positions Section
    st.markdown('<div class="section-header">📊 Existing CSP Positions</div>', unsafe_allow_html=True)
    
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
        display_df['Strike'] = display_df['Strike'].apply(lambda x: f"${x:.2f}")
        display_df['Premium Collected'] = display_df['Premium Collected'].apply(lambda x: f"${x:.2f}")
        display_df['Current Value'] = display_df['Current Value'].apply(lambda x: f"${x:.2f}")
        display_df['P/L'] = display_df['P/L'].apply(lambda x: f"${x:.2f}")
        display_df['% Recognized'] = display_df['% Recognized'].apply(lambda x: f"{x:.1f}%")
        display_df['Collateral'] = display_df['Collateral'].apply(lambda x: f"${x:,.0f}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Premium Summary Metrics
        total_premium = sum([p['premium_collected'] for p in short_put_details])
        total_current = sum([p['current_value'] for p in short_put_details])
        total_pl = sum([p['pl'] for p in short_put_details])
        total_collateral = sum([p['collateral_required'] for p in short_put_details])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">Total Premium Collected</div>
                <div class="metric-value">${total_premium:,.0f}</div>
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
            pl_color = "metric-value-positive" if total_pl >= 0 else "metric-value"
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">Total P/L</div>
                <div class="{pl_color}">${total_pl:,.0f}</div>
                <div class="metric-change">↗ {(total_pl/total_premium*100) if total_premium > 0 else 0:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="premium-metric-card">
                <div class="metric-label">Total Collateral</div>
                <div class="metric-value">${total_collateral:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ No existing CSP positions found")
    
    # Working Orders Monitor Section
    st.markdown('<div class="section-header">📋 Working Orders Monitor</div>', unsafe_allow_html=True)
    from utils.working_orders import render_working_orders_monitor
    render_working_orders_monitor(api, selected_account, order_type='csp')
    
    # Watchlist Management Section
    st.markdown('<div class="section-header">📝 Watchlist Management</div>', unsafe_allow_html=True)
    
    # Read watchlist
    try:
        with open('watchlist.txt', 'r') as f:
            watchlist = [line.strip() for line in f if line.strip()]
    except:
        watchlist = []
    
    # CSV Import Section
    with st.expander("📥 Import from TradingView", expanded=False):
        st.markdown("""
        **Quick Import from TradingView:**
        
        1. Export your TradingView screener results as CSV
        2. Upload the CSV file below
        3. Choose to Replace or Append to current watchlist
        """)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            import_file = st.file_uploader(
                "Upload TradingView CSV",
                type=['csv'],
                help="CSV file from TradingView with Symbol column",
                key="tradingview_csv_import"
            )
        
        with col2:
            import_mode = st.radio(
                "Import Mode",
                ["Replace", "Append"],
                help="Replace: Clear existing watchlist\\nAppend: Add to existing",
                key="import_mode"
            )
        
        if import_file is not None:
            try:
                import pandas as pd
                
                # Read CSV
                df = pd.read_csv(import_file)
                
                # Find Symbol column
                symbol_col = None
                for col in df.columns:
                    if col.lower() in ['symbol', 'ticker', 'stock']:
                        symbol_col = col
                        break
                
                if symbol_col:
                    # Extract and clean symbols
                    new_symbols = df[symbol_col].dropna().unique().tolist()
                    new_symbols = [str(s).strip().upper() for s in new_symbols if str(s).strip()]
                    new_symbols = sorted(set(new_symbols))
                    
                    st.success(f"✅ Found {len(new_symbols)} symbols in CSV")
                    
                    # Display preview
                    preview_cols = st.columns(8)
                    for idx, symbol in enumerate(new_symbols[:16]):
                        with preview_cols[idx % 8]:
                            st.markdown(f"**{symbol}**")
                    
                    if len(new_symbols) > 16:
                        st.info(f"... and {len(new_symbols) - 16} more")
                    
                    if st.button(f"✅ {import_mode} Watchlist with {len(new_symbols)} Symbols", type="primary", use_container_width=True, key="import_watchlist_btn"):
                        if import_mode == "Replace":
                            with open('watchlist.txt', 'w') as f:
                                for symbol in new_symbols:
                                    f.write(f"{symbol}\\n")
                            st.success(f"✅ Replaced watchlist with {len(new_symbols)} symbols!")
                        else:
                            try:
                                with open('watchlist.txt', 'r') as f:
                                    existing = [line.strip() for line in f if line.strip()]
                            except:
                                existing = []
                            
                            combined = sorted(set(existing + new_symbols))
                            added_count = len(combined) - len(existing)
                            
                            with open('watchlist.txt', 'w') as f:
                                for symbol in combined:
                                    f.write(f"{symbol}\\n")
                            
                            st.success(f"✅ Added {added_count} new symbols! Total: {len(combined)}")
                        
                        st.rerun()
                else:
                    st.error("❌ No 'Symbol' or 'Ticker' column found in CSV")
                    st.info("Available columns: " + ", ".join(df.columns.tolist()))
                    
            except Exception as e:
                st.error(f"❌ Error reading CSV: {str(e)}")
    
    st.write("")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.info(f"📋 Currently monitoring **{len(watchlist)}** symbols from watchlist")
    
    with col2:
        if st.button("👁️ View/Edit Watchlist", use_container_width=True):
            st.session_state.show_watchlist_editor = not st.session_state.get('show_watchlist_editor', False)
    
    with col3:
        if st.button("🗑️ Clear Watchlist", use_container_width=True, type="secondary"):
            if len(watchlist) > 0:
                with open('watchlist.txt', 'w') as f:
                    f.write("")
                st.success("✅ Watchlist cleared!")
                st.rerun()


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
    
    # Working Orders Monitor Section
    st.markdown('<div class="section-header">📋 Working Orders Monitor</div>', unsafe_allow_html=True)
    from utils.working_orders import render_working_orders_monitor
    render_working_orders_monitor(api, selected_account, order_type='cc')
    
    st.divider()
    
    # Step 1: Fetch Positions Button
    st.write("")
    if st.button("🔍 Fetch Portfolio Positions", type="primary", use_container_width=True):
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
            
            # Create dataframe
            import pandas as pd
            eligible_df = pd.DataFrame(holdings)
            
            # Add selection column
            eligible_df['Select'] = eligible_df['symbol'].isin(st.session_state.cc_selected_stocks)
            
            # Reorder columns
            display_cols = ['Select', 'symbol', 'quantity', 'current_price', 'market_value', 'max_contracts']
            eligible_display = eligible_df[display_cols].copy()
            eligible_display.columns = ['Select', 'Symbol', 'Shares', 'Price', 'Market Value', 'Max Contracts']
            
            # Format numbers
            eligible_display['Price'] = eligible_display['Price'].apply(lambda x: f"${x:.2f}")
            eligible_display['Market Value'] = eligible_display['Market Value'].apply(lambda x: f"${x:,.2f}")
            
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
                use_container_width=True,
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
                if st.button(f"🔍 Scan {len(selected_symbols)} Selected Stocks for Covered Calls", type="primary", use_container_width=True):
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
                            df.insert(0, 'Select', False)  # Add Select column
                            df.insert(1, 'Qty', 1)  # Add Qty column with default value of 1
                            df = df.sort_values('weekly_return_pct', ascending=False)
                            st.session_state.cc_opportunities = df
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
            def select_best_per_ticker(df, delta_min, delta_max, dte_min, dte_max, oi_min, weekly_min, qty_mode='conservative'):
                """
                For each ticker, find the BEST opportunity (highest weekly return) that matches criteria.
                If no match, relax criteria to find closest match.
                
                Args:
                    df: DataFrame of all opportunities
                    delta_min, delta_max, dte_min, dte_max, oi_min, weekly_min: Filter criteria
                    qty_mode: 'conservative' (1), 'medium' (50%), 'aggressive' (100%)
                
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
                    
                    # Find the best match: closest to target delta, then highest weekly return
                    # Target delta is the middle of the range
                    target_delta = (delta_min + delta_max) / 2
                    matches['delta_distance'] = abs(matches['delta'] - target_delta)
                    
                    # Sort by: 1) closest to target delta, 2) highest weekly return
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
            
            if 'cc_medium_delta_min' not in st.session_state:
                st.session_state.cc_medium_delta_min = 0.15
                st.session_state.cc_medium_delta_max = 0.30
                st.session_state.cc_medium_dte_min = 7
                st.session_state.cc_medium_dte_max = 30
                st.session_state.cc_medium_oi_min = 50
                st.session_state.cc_medium_weekly_min = 0.3
            
            if 'cc_aggressive_delta_min' not in st.session_state:
                st.session_state.cc_aggressive_delta_min = 0.20
                st.session_state.cc_aggressive_delta_max = 0.40
                st.session_state.cc_aggressive_dte_min = 7
                st.session_state.cc_aggressive_dte_max = 21
                st.session_state.cc_aggressive_oi_min = 25
                st.session_state.cc_aggressive_weekly_min = 0.3
            
            # Get DataFrame from session state (already has Select column)
            opp_df = st.session_state.cc_opportunities
            
            # Preset Filter Buttons
            st.write("")
            col1, col2, col3, col4, col5, col6 = st.columns([1, 1.5, 1.5, 1.5, 1, 1])
            
            with col1:
                if st.button("🗑️ Clear All", use_container_width=True, key="cc_clear_all"):
                    st.session_state.cc_opportunities['Select'] = False
                    st.rerun()
            
            with col2:
                if st.button("🟢 Conservative", use_container_width=True, key="cc_preset_conservative", 
                           help="Δ 0.10-0.20, DTE 7-30, OI ≥50, Weekly ≥0.3% | Qty=1 contract"):
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
                        qty_mode='conservative'
                    )
                    
                    # Apply selections
                    for idx, qty in selections:
                        st.session_state.cc_opportunities.loc[idx, 'Select'] = True
                        st.session_state.cc_opportunities.loc[idx, 'Qty'] = qty
                    
                    st.rerun()
            
            with col3:
                if st.button("🟡 Medium", use_container_width=True, key="cc_preset_medium",
                           help="Δ 0.15-0.30, DTE 7-30, OI ≥50, Weekly ≥0.3% | Qty=50% of shares"):
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
                        qty_mode='medium'
                    )
                    
                    # Apply selections
                    for idx, qty in selections:
                        st.session_state.cc_opportunities.loc[idx, 'Select'] = True
                        st.session_state.cc_opportunities.loc[idx, 'Qty'] = qty
                    
                    st.rerun()
            
            with col4:
                if st.button("🔴 Aggressive", use_container_width=True, key="cc_preset_aggressive",
                           help="Δ 0.20-0.40, DTE 7-21, OI ≥25, Weekly ≥0.3% | Qty=100% of shares"):
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
                        qty_mode='aggressive'
                    )
                    
                    # Apply selections
                    for idx, qty in selections:
                        st.session_state.cc_opportunities.loc[idx, 'Select'] = True
                        st.session_state.cc_opportunities.loc[idx, 'Qty'] = qty
                    
                    st.rerun()
            
            with col5:
                if st.button("✅ Select All", use_container_width=True, key="cc_select_all"):
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
                if st.button("➥ +1", use_container_width=True, key="cc_qty_plus1", help="Add 1 to selected quantities"):
                    mask = st.session_state.cc_opportunities['Select'] == True
                    st.session_state.cc_opportunities.loc[mask, 'Qty'] = st.session_state.cc_opportunities.loc[mask, 'Qty'] + 1
                    st.rerun()
            
            with col2:
                if st.button("➥ +5", use_container_width=True, key="cc_qty_plus5", help="Add 5 to selected quantities"):
                    mask = st.session_state.cc_opportunities['Select'] == True
                    st.session_state.cc_opportunities.loc[mask, 'Qty'] = st.session_state.cc_opportunities.loc[mask, 'Qty'] + 5
                    st.rerun()
            
            with col3:
                if st.button("➥ +10", use_container_width=True, key="cc_qty_plus10", help="Add 10 to selected quantities"):
                    mask = st.session_state.cc_opportunities['Select'] == True
                    st.session_state.cc_opportunities.loc[mask, 'Qty'] = st.session_state.cc_opportunities.loc[mask, 'Qty'] + 10
                    st.rerun()
            
            with col4:
                if st.button("➖ -1", use_container_width=True, key="cc_qty_minus1", help="Subtract 1 from selected quantities (min 1)"):
                    mask = st.session_state.cc_opportunities['Select'] == True
                    st.session_state.cc_opportunities.loc[mask, 'Qty'] = st.session_state.cc_opportunities.loc[mask, 'Qty'].apply(lambda x: max(1, x - 1))
                    st.rerun()
            
            with col5:
                if st.button("🔺 Max Out", use_container_width=True, key="cc_qty_max", help="Set selected quantities to maximum available contracts"):
                    mask = st.session_state.cc_opportunities['Select'] == True
                    # Set Qty to max_contracts for selected rows
                    for idx in st.session_state.cc_opportunities[mask].index:
                        max_contracts = st.session_state.cc_opportunities.loc[idx, 'max_contracts']
                        st.session_state.cc_opportunities.loc[idx, 'Qty'] = max_contracts
                    st.rerun()
            
            with col6:
                if st.button("🔄 Reset", use_container_width=True, key="cc_qty_reset", help="Reset selected quantities to 1"):
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
                    cons_weekly_min = st.number_input("Min Weekly Return %", value=st.session_state.cc_conservative_weekly_min, min_value=0.0, step=0.1, key="cons_weekly_min_input")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Commit Conservative", use_container_width=True, key="commit_conservative"):
                        st.session_state.cc_conservative_delta_min = cons_delta_min
                        st.session_state.cc_conservative_delta_max = cons_delta_max
                        st.session_state.cc_conservative_dte_min = cons_dte_min
                        st.session_state.cc_conservative_dte_max = cons_dte_max
                        st.session_state.cc_conservative_oi_min = cons_oi_min
                        st.session_state.cc_conservative_weekly_min = cons_weekly_min
                        st.success("✅ Conservative criteria committed!")
                        st.rerun()
                with col2:
                    if st.button("🔄 Reset Conservative", use_container_width=True, key="reset_conservative"):
                        st.session_state.cc_conservative_delta_min = 0.10
                        st.session_state.cc_conservative_delta_max = 0.20
                        st.session_state.cc_conservative_dte_min = 7
                        st.session_state.cc_conservative_dte_max = 30
                        st.session_state.cc_conservative_oi_min = 50
                        st.session_state.cc_conservative_weekly_min = 0.3
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
                    med_weekly_min = st.number_input("Min Weekly Return %", value=st.session_state.cc_medium_weekly_min, min_value=0.0, step=0.1, key="med_weekly_min_input")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Commit Medium", use_container_width=True, key="commit_medium"):
                        st.session_state.cc_medium_delta_min = med_delta_min
                        st.session_state.cc_medium_delta_max = med_delta_max
                        st.session_state.cc_medium_dte_min = med_dte_min
                        st.session_state.cc_medium_dte_max = med_dte_max
                        st.session_state.cc_medium_oi_min = med_oi_min
                        st.session_state.cc_medium_weekly_min = med_weekly_min
                        st.success("✅ Medium criteria committed!")
                        st.rerun()
                with col2:
                    if st.button("🔄 Reset Medium", use_container_width=True, key="reset_medium"):
                        st.session_state.cc_medium_delta_min = 0.15
                        st.session_state.cc_medium_delta_max = 0.30
                        st.session_state.cc_medium_dte_min = 7
                        st.session_state.cc_medium_dte_max = 30
                        st.session_state.cc_medium_oi_min = 50
                        st.session_state.cc_medium_weekly_min = 0.3
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
                    agg_weekly_min = st.number_input("Min Weekly Return %", value=st.session_state.cc_aggressive_weekly_min, min_value=0.0, step=0.1, key="agg_weekly_min_input")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Commit Aggressive", use_container_width=True, key="commit_aggressive"):
                        st.session_state.cc_aggressive_delta_min = agg_delta_min
                        st.session_state.cc_aggressive_delta_max = agg_delta_max
                        st.session_state.cc_aggressive_dte_min = agg_dte_min
                        st.session_state.cc_aggressive_dte_max = agg_dte_max
                        st.session_state.cc_aggressive_oi_min = agg_oi_min
                        st.session_state.cc_aggressive_weekly_min = agg_weekly_min
                        st.success("✅ Aggressive criteria committed!")
                        st.rerun()
                with col2:
                    if st.button("🔄 Reset Aggressive", use_container_width=True, key="reset_aggressive"):
                        st.session_state.cc_aggressive_delta_min = 0.20
                        st.session_state.cc_aggressive_delta_max = 0.40
                        st.session_state.cc_aggressive_dte_min = 7
                        st.session_state.cc_aggressive_dte_max = 21
                        st.session_state.cc_aggressive_oi_min = 25
                        st.session_state.cc_aggressive_weekly_min = 0.3
                        st.success("✅ Aggressive reset to defaults!")
                        st.rerun()
            
            st.write("")
            st.write("---")
            
            # Display dataframe
            display_opp = opp_df[['Select', 'Qty', 'symbol', 'current_price', 'strike', 'expiration', 'dte', 'delta', 'premium', 'weekly_return_pct', 'rsi', 'iv_rank', 'spread_pct', 'open_interest', 'volume', 'max_contracts']].copy()
            
            # Calculate Available column (remaining contracts)
            display_opp['Available'] = display_opp['max_contracts'] - display_opp['Qty']
            
            # Add visual indicator to Available column
            def format_available(val):
                if val > 0:
                    return f"🟢 {int(val)}"  # Green circle for available
                else:
                    return f"⚫ {int(val)}"  # Black circle for none available
            
            display_opp['Available_Display'] = display_opp['Available'].apply(format_available)
            
            # Rename columns
            display_opp.columns = ['Select', 'Qty', 'Symbol', 'Stock Price', 'Strike', 'Expiration', 'DTE', 'Delta', 'Premium', 'Weekly %', 'RSI', 'IV Rank', 'Spread %', 'OI', 'Volume', 'max_contracts', 'Available', 'Available_Display']
            
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
            
            # Apply formatting
            display_opp['Stock Price'] = display_opp['Stock Price'].apply(lambda x: f"${x:.2f}")
            display_opp['Strike'] = display_opp['Strike'].apply(lambda x: f"${x:.2f}")
            display_opp['Delta'] = display_opp['Delta'].apply(format_delta)
            display_opp['Premium'] = display_opp['Premium'].apply(lambda x: f"${x:.2f}")
            display_opp['Weekly %'] = display_opp['Weekly %'].apply(lambda x: f"{x:.2f}%")
            display_opp['RSI'] = display_opp['RSI'].apply(format_rsi)
            display_opp['IV Rank'] = display_opp['IV Rank'].apply(format_iv_rank)
            display_opp['Spread %'] = display_opp['Spread %'].apply(format_spread)
            
            # Reorder columns to put Available after Qty, Stock Price after Symbol (use display version with emoji)
            display_opp = display_opp[['Select', 'Qty', 'Available_Display', 'Symbol', 'Stock Price', 'Strike', 'Expiration', 'DTE', 'Delta', 'Premium', 'Weekly %', 'RSI', 'IV Rank', 'Spread %', 'OI', 'Volume']]
            
            edited_opp = st.data_editor(
                display_opp,
                use_container_width=True,
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
                        st.caption(f"This will submit {int(total_contracts)} covered call order(s) as limit orders at the current bid price.")
                with col2:
                    button_label = "🧪 Run Dry Run Test" if dry_run else "🚀 Submit REAL Orders"
                    if st.button(button_label, type="primary", use_container_width=True, key="submit_cc_orders"):
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
                                                'price': row['premium']  # Use current bid as limit price
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
                                                st.balloons()
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



elif page == "Performance":
    # Premium Header
    st.markdown('<h1 style="color: #ffffff; font-size: 36px; font-weight: 600; margin-bottom: 0.5rem;">📊 Performance</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #9ca3af; font-size: 14px; margin-bottom: 2rem;">Track your trading performance and analyze results</p>', unsafe_allow_html=True)
    
    # Premium Performance Metrics
    if selected_account:
        # Get account balances and positions
        balances = api.get_account_balances(selected_account)
        positions = api.get_positions(selected_account)
        
        if balances:
            nlv = float(balances.get('net-liquidating-value', 0))
            
            # Count positions
            total_positions = len(positions) if positions else 0
            stock_positions = len([p for p in positions if p.get('instrument-type') == 'Equity']) if positions else 0
            option_positions = len([p for p in positions if p.get('instrument-type') == 'Equity Option']) if positions else 0
            
            # Calculate total P/L from positions
            total_pl = sum([float(p.get('realized-day-gain-effect', 0)) for p in positions]) if positions else 0
            
            # Premium Metric Cards Row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="premium-metric-card">
                    <div class="metric-label">Total Positions</div>
                    <div class="metric-value">{total_positions}</div>
                    <div class="metric-change">Stocks: {stock_positions} | Options: {option_positions}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="premium-metric-card">
                    <div class="metric-label">Portfolio Value</div>
                    <div class="metric-value">${nlv:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                pl_class = "metric-value-positive" if total_pl >= 0 else ""
                pl_symbol = "+" if total_pl >= 0 else ""
                st.markdown(f"""
                <div class="premium-metric-card">
                    <div class="metric-label">Today's P/L</div>
                    <div class="metric-value {pl_class}">{pl_symbol}${total_pl:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                # Calculate win rate (placeholder - would need historical data)
                st.markdown(f"""
                <div class="premium-metric-card">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value metric-value-positive">47% / 53%</div>
                    <div class="metric-change">CSP / CC</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
    
    # Monthly Premium Summary
    from utils.monthly_premium import render_monthly_premium_summary
    if selected_account:
        render_monthly_premium_summary(api, selected_account)
    
    from utils.performance_dashboard import (
        render_active_positions,
        render_stock_basis,
        render_performance_overview,
        render_positions_view
    )
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Positions", "Active Positions", "Stock Basis & Returns", "Performance Overview"])
    
    with tab1:
        render_positions_view(api, selected_account)
    
    with tab2:
        render_active_positions(api)
    
    with tab3:
        render_stock_basis(api)
    
    with tab4:
        render_performance_overview()

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

st.write("---")
st.caption("Built with ❤️ using Streamlit | Options Trading Dashboard v1.0")