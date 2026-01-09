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
    all_pages = ["🏠 Dashboard", "💰 CSP Dashboard", "📞 Covered Calls", "🎯 PMCC Dashboard", "📈 Performance", "⚙️ Settings"]
    trading_pages = ["🏠 Dashboard", "💰 CSP Dashboard", "📞 Covered Calls", "🎯 PMCC Dashboard", "📈 Performance"]
    
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
        
        # Get real weekly premium
        from utils.sidebar_stats import get_weekly_premium, get_win_rate
        weekly_premium = get_weekly_premium(api, selected_account)
        win_rate = get_win_rate(api, selected_account)
        
        premium_class = "stat-positive" if weekly_premium >= 0 else "stat-negative"
        premium_prefix = "+" if weekly_premium >= 0 else "-"
        
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
                <span class="stat-value {premium_class}">{premium_prefix}${abs(weekly_premium):,.0f}</span>
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
    "💰 CSP Dashboard": "CSP Dashboard",
    "📞 Covered Calls": "CC Dashboard",
    "🎯 PMCC Dashboard": "PMCC Dashboard",
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
        display_df['Strike'] = display_df['Strike'].apply(lambda x: f"${x:.2f}")
        display_df['Premium Collected'] = display_df['Premium Collected'].apply(lambda x: f"${x:.2f}")
        display_df['Current Value'] = display_df['Current Value'].apply(lambda x: f"${x:.2f}")
        display_df['P/L'] = display_df['P/L'].apply(lambda x: f"${x:.2f}")
        display_df['% Recognized'] = display_df['% Recognized'].apply(lambda x: f"{x:.1f}%")
        display_df['Collateral'] = display_df['Collateral'].apply(lambda x: f"${x:,.0f}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Summary metrics
        total_premium = sum([p['premium_collected'] for p in short_put_details])
        total_current = sum([p['current_value'] for p in short_put_details])
        total_pl = sum([p['pl'] for p in short_put_details])
        total_collateral = sum([p['collateral_required'] for p in short_put_details])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Premium Collected", f"${total_premium:,.2f}")
        with col2:
            st.metric("Current Value", f"${total_current:,.2f}")
        with col3:
            st.metric("Total P/L", f"${total_pl:,.2f}", delta=f"{(total_pl/total_premium*100) if total_premium > 0 else 0:.1f}%")
        with col4:
            st.metric("Total Collateral", f"${total_collateral:,.0f}")
    else:
        st.info("ℹ️ No existing CSP positions found")
    
    st.divider()
    
    # Read watchlist
    try:
        with open('watchlist.txt', 'r') as f:
            watchlist = [line.strip() for line in f if line.strip()]
    except:
        watchlist = []
    
    # ========== TRADINGVIEW CSV IMPORT ==========
    st.subheader("📝 Watchlist Management")
    
    # Prominent CSV import section
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
                help="Replace: Clear existing watchlist\nAppend: Add to existing",
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
                    new_symbols = sorted(set(new_symbols))  # Remove duplicates and sort
                    
                    # Show preview
                    st.success(f"✅ Found {len(new_symbols)} symbols in CSV")
                    
                    # Display preview
                    preview_cols = st.columns(8)
                    for idx, symbol in enumerate(new_symbols[:16]):  # Show first 16
                        with preview_cols[idx % 8]:
                            st.markdown(f"**{symbol}**")
                    
                    if len(new_symbols) > 16:
                        st.info(f"... and {len(new_symbols) - 16} more")
                    
                    # Import button with unique key
                    if st.button(f"✅ {import_mode} Watchlist with {len(new_symbols)} Symbols", type="primary", use_container_width=True, key="import_watchlist_btn"):
                        if import_mode == "Replace":
                            # Replace entire watchlist
                            with open('watchlist.txt', 'w') as f:
                                for symbol in new_symbols:
                                    f.write(f"{symbol}\n")
                            st.success(f"✅ Replaced watchlist with {len(new_symbols)} symbols!")
                        else:  # Append
                            # Read existing watchlist
                            try:
                                with open('watchlist.txt', 'r') as f:
                                    existing = [line.strip() for line in f if line.strip()]
                            except:
                                existing = []
                            
                            # Combine and deduplicate
                            combined = sorted(set(existing + new_symbols))
                            added_count = len(combined) - len(existing)
                            
                            # Write back
                            with open('watchlist.txt', 'w') as f:
                                for symbol in combined:
                                    f.write(f"{symbol}\n")
                            
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
    
    # Show watchlist editor if toggled
    if st.session_state.get('show_watchlist_editor', False):
        st.subheader("✏️ Edit Watchlist")
        
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
                use_container_width=True,
                key="watchlist_editor"
            )
            
            # Remove selected symbols
            if st.button("🗑️ Remove Selected", type="primary"):
                symbols_to_keep = edited_watchlist[edited_watchlist['Remove'] == False]['Symbol'].tolist()
                
                with open('watchlist.txt', 'w') as f:
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
    
    if st.button("🔄 Fetch Opportunities", type="primary", use_container_width=True):
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
        
        with st.status(f"Fetching opportunities for {len(watchlist)} symbols...", expanded=False) as status:
            opportunities = []
            progress_bar = st.progress(0)
            
            for idx, symbol in enumerate(watchlist):
                st.write(f"Processing {symbol}... ({idx+1}/{len(watchlist)})")
                stats['symbols_processed'] += 1
                
                log_lines.append(f"--- {symbol} ---")
                
                chain_data = tradier.get_option_chains(symbol, min_dte=min_dte, max_dte=max_dte)
                
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
                
                # Fetch IV Rank for this symbol (once per symbol, not per option)
                iv_rank = tradier.get_iv_rank(symbol)
                log_lines.append(f"  IV Rank: {iv_rank if iv_rank else 'N/A'}")
                
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
                        'IV Rank': round(iv_rank, 1) if iv_rank else None,
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
                
                progress_bar.progress((idx + 1) / len(watchlist))
            
            stats['final_opportunities'] = len(opportunities)
            
            status.update(label=f"✅ Scan complete!", state="complete")
        
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
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Symbols Scanned", stats['symbols_processed'])
        with col2:
            st.metric("With Chain Data", stats['symbols_with_chains'])
        with col3:
            st.metric("Total PUTs Found", stats['total_puts_found'])
        with col4:
            st.metric("Final Opportunities", stats['final_opportunities'])
        
        if stats['used_mid_price'] > 0:
            st.info(f"ℹ️ Used mid-price for {stats['used_mid_price']} options (bid was $0)")
        
        if stats['rejected_bid_zero'] > 0:
            st.warning(f"⚠️ Rejected {stats['rejected_bid_zero']} options due to bid=$0 (even after mid-price fallback)")
        
        # Store scan time for validation later
        st.session_state.csp_scan_time = datetime.now()
        
        # Store opportunities in session state for display
        if opportunities:
            df = pd.DataFrame(opportunities)
            df.insert(0, 'Select', False)
            df.insert(1, 'Qty', 1)  # Add quantity column with default value of 1
            df = df.sort_values('Weekly %', ascending=False)
            st.session_state.csp_opportunities = df
        else:
            # Clear opportunities if none found
            if 'csp_opportunities' in st.session_state:
                del st.session_state.csp_opportunities
    # Display opportunities if they exist in session state
    if 'csp_opportunities' in st.session_state and len(st.session_state.csp_opportunities) > 0:
        # Get the DataFrame from session state
        df = st.session_state.csp_opportunities
        
        st.success(f"✅ Found {len(df)} opportunities!")
        
        # Store in session state (always update with fresh scan results)
        st.session_state.csp_opportunities_fresh = True
        
        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_weekly = df['Weekly %'].mean()
            st.metric("Avg Weekly Return", f"{avg_weekly:.2f}%")
        with col2:
            max_weekly = df['Weekly %'].max()
            st.metric("Max Weekly Return", f"{max_weekly:.2f}%")
        with col3:
            avg_delta = df['Delta'].mean()
            st.metric("Avg Delta", f"{avg_delta:.2f}")
        with col4:
            high_return_count = (df['Weekly %'] >= 1.5).sum()
            st.metric("≥1.5% Weekly", high_return_count)
        
        st.divider()
        
        # Selection controls
        st.subheader("📋 Select Options to Trade")
        
        # Initialize preset criteria in session state (defaults)
        if 'csp_conservative_delta_min' not in st.session_state:
            st.session_state.csp_conservative_delta_min = 0.10
            st.session_state.csp_conservative_delta_max = 0.20
            st.session_state.csp_conservative_dte_min = 7
            st.session_state.csp_conservative_dte_max = 30
            st.session_state.csp_conservative_oi_min = 50
            st.session_state.csp_conservative_weekly_min = 0.3
        
        if 'csp_medium_delta_min' not in st.session_state:
            st.session_state.csp_medium_delta_min = 0.15
            st.session_state.csp_medium_delta_max = 0.30
            st.session_state.csp_medium_dte_min = 7
            st.session_state.csp_medium_dte_max = 30
            st.session_state.csp_medium_oi_min = 50
            st.session_state.csp_medium_weekly_min = 0.3
        
        if 'csp_aggressive_delta_min' not in st.session_state:
            st.session_state.csp_aggressive_delta_min = 0.20
            st.session_state.csp_aggressive_delta_max = 0.40
            st.session_state.csp_aggressive_dte_min = 7
            st.session_state.csp_aggressive_dte_max = 21
            st.session_state.csp_aggressive_oi_min = 25
            st.session_state.csp_aggressive_weekly_min = 0.3
        
        # Helper function to select best per ticker
        def select_best_csp_per_ticker(df, delta_min, delta_max, dte_min, dte_max, oi_min, weekly_min, qty=1):
            """Select best CSP option per ticker based on criteria"""
            selections = []
            
            # Filter by criteria (using correct column names from DataFrame)
            filtered = df[
                (df['Delta'].abs() >= delta_min) &
                (df['Delta'].abs() <= delta_max) &
                (df['DTE'] >= dte_min) &
                (df['DTE'] <= dte_max) &
                (df['Open Int'] >= oi_min) &  # Column is 'Open Int' not 'Open Interest'
                (df['Weekly %'] >= weekly_min)
            ]
            
            if len(filtered) == 0:
                return selections
            
            # Group by symbol and select best (highest weekly return)
            for symbol in filtered['Symbol'].unique():
                symbol_opps = filtered[filtered['Symbol'] == symbol]
                if len(symbol_opps) > 0:
                    # Select highest weekly return for this symbol
                    best_idx = symbol_opps['Weekly %'].idxmax()
                    selections.append((best_idx, qty))
            
            return selections
        
        # Preset Filter Buttons
        st.write("")
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1.5, 1.5, 1.5, 1, 1])
        
        with col1:
            if st.button("🗑️ Clear All", use_container_width=True, key="csp_clear_all"):
                st.session_state.csp_opportunities['Select'] = False
                st.rerun()
        
        with col2:
            if st.button("🟢 Conservative", use_container_width=True, key="csp_preset_conservative", 
                       help=f"Δ {st.session_state.csp_conservative_delta_min}-{st.session_state.csp_conservative_delta_max}, DTE {st.session_state.csp_conservative_dte_min}-{st.session_state.csp_conservative_dte_max}, OI ≥{st.session_state.csp_conservative_oi_min}, Weekly ≥{st.session_state.csp_conservative_weekly_min}%"):
                # Track active preset for Delta formatting
                st.session_state.csp_active_preset = 'conservative'
                
                # Clear all first
                st.session_state.csp_opportunities['Select'] = False
                st.session_state.csp_opportunities['Qty'] = 1
                
                # Use smart per-ticker selection
                selections = select_best_csp_per_ticker(
                    st.session_state.csp_opportunities,
                    st.session_state.csp_conservative_delta_min,
                    st.session_state.csp_conservative_delta_max,
                    st.session_state.csp_conservative_dte_min,
                    st.session_state.csp_conservative_dte_max,
                    st.session_state.csp_conservative_oi_min,
                    st.session_state.csp_conservative_weekly_min,
                    qty=1
                )
                
                # Apply selections
                for idx, qty in selections:
                    st.session_state.csp_opportunities.loc[idx, 'Select'] = True
                    st.session_state.csp_opportunities.loc[idx, 'Qty'] = qty
                
                st.rerun()
        
        with col3:
            if st.button("🟡 Medium", use_container_width=True, key="csp_preset_medium",
                       help=f"Δ {st.session_state.csp_medium_delta_min}-{st.session_state.csp_medium_delta_max}, DTE {st.session_state.csp_medium_dte_min}-{st.session_state.csp_medium_dte_max}, OI ≥{st.session_state.csp_medium_oi_min}, Weekly ≥{st.session_state.csp_medium_weekly_min}%"):
                # Track active preset for Delta formatting
                st.session_state.csp_active_preset = 'medium'
                
                # Clear all first
                st.session_state.csp_opportunities['Select'] = False
                st.session_state.csp_opportunities['Qty'] = 1
                
                # Use smart per-ticker selection
                selections = select_best_csp_per_ticker(
                    st.session_state.csp_opportunities,
                    st.session_state.csp_medium_delta_min,
                    st.session_state.csp_medium_delta_max,
                    st.session_state.csp_medium_dte_min,
                    st.session_state.csp_medium_dte_max,
                    st.session_state.csp_medium_oi_min,
                    st.session_state.csp_medium_weekly_min,
                    qty=1
                )
                
                # Apply selections
                for idx, qty in selections:
                    st.session_state.csp_opportunities.loc[idx, 'Select'] = True
                    st.session_state.csp_opportunities.loc[idx, 'Qty'] = qty
                
                st.rerun()
        
        with col4:
            if st.button("🔴 Aggressive", use_container_width=True, key="csp_preset_aggressive",
                       help=f"Δ {st.session_state.csp_aggressive_delta_min}-{st.session_state.csp_aggressive_delta_max}, DTE {st.session_state.csp_aggressive_dte_min}-{st.session_state.csp_aggressive_dte_max}, OI ≥{st.session_state.csp_aggressive_oi_min}, Weekly ≥{st.session_state.csp_aggressive_weekly_min}%"):
                # Track active preset for Delta formatting
                st.session_state.csp_active_preset = 'aggressive'
                
                # Clear all first
                st.session_state.csp_opportunities['Select'] = False
                st.session_state.csp_opportunities['Qty'] = 1
                
                # Use smart per-ticker selection
                selections = select_best_csp_per_ticker(
                    st.session_state.csp_opportunities,
                    st.session_state.csp_aggressive_delta_min,
                    st.session_state.csp_aggressive_delta_max,
                    st.session_state.csp_aggressive_dte_min,
                    st.session_state.csp_aggressive_dte_max,
                    st.session_state.csp_aggressive_oi_min,
                    st.session_state.csp_aggressive_weekly_min,
                    qty=1
                )
                
                # Apply selections
                for idx, qty in selections:
                    st.session_state.csp_opportunities.loc[idx, 'Select'] = True
                    st.session_state.csp_opportunities.loc[idx, 'Qty'] = qty
                
                st.rerun()
        
        with col5:
            if st.button("✅ Select All", use_container_width=True, key="csp_select_all"):
                st.session_state.csp_opportunities['Select'] = True
                st.rerun()
        
        with col6:
            selected_count = st.session_state.csp_opportunities['Select'].sum()
            st.metric("Selected", selected_count)
        
        st.write("")
        st.write("---")
        
        # ========== AUTO-TRIM TO WEEKLY TARGET ==========
        st.subheader("🎯 Trim to Weekly Target")
        
        # Initialize mark column in session state if not exists
        if 'Mark' not in st.session_state.csp_opportunities.columns:
            st.session_state.csp_opportunities.insert(2, 'Mark', False)
        
        # Calculate current selection totals
        selected_rows = st.session_state.csp_opportunities[st.session_state.csp_opportunities['Select'] == True]
        if len(selected_rows) > 0:
            current_collateral = (selected_rows['Strike'] * selected_rows['Qty'] * 100).sum()
        else:
            current_collateral = 0
        
        # Get weekly target from ladder manager
        from utils.csp_ladder_manager import calculate_tranche_targets
        balances = api.get_account_balances(selected_account)
        if balances:
            buying_power = float(balances.get('derivative-buying-power', 0))
            weekly_target = calculate_tranche_targets(buying_power, 4)
        else:
            weekly_target = 0
        
        # Display current vs target
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Selection", f"${current_collateral:,.0f}")
        with col2:
            st.metric("Weekly Target", f"${weekly_target:,.0f}")
        with col3:
            if current_collateral > weekly_target:
                over_amount = current_collateral - weekly_target
                st.metric("Over by", f"${over_amount:,.0f}", delta=f"-${over_amount:,.0f}", delta_color="inverse")
            else:
                under_amount = weekly_target - current_collateral
                st.metric("Under by", f"${under_amount:,.0f}", delta=f"+${under_amount:,.0f}")
        
        # Auto-Trim controls
        col1, col2 = st.columns([2, 1])
        
        with col1:
            trim_strategy = st.selectbox(
                "Trim Strategy",
                [
                    "Keep Lowest Delta (Most Conservative)",
                    "Keep Highest Premium (Most Income)",
                    "Keep Highest Weekly % (Best Efficiency)",
                    "Keep Highest IV Rank (Best Volatility)"
                ],
                help="Choose which options to keep when trimming to target"
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("🎯 Auto-Trim to Target", use_container_width=True, type="primary", disabled=(current_collateral <= weekly_target)):
                # Only trim if over target
                if current_collateral > weekly_target:
                    # Sort selected rows by chosen strategy
                    selected_indices = st.session_state.csp_opportunities[st.session_state.csp_opportunities['Select'] == True].index.tolist()
                    selected_df = st.session_state.csp_opportunities.loc[selected_indices].copy()
                    
                    # Add collateral column for sorting
                    selected_df['Collateral'] = selected_df['Strike'] * selected_df['Qty'] * 100
                    
                    # Sort by strategy (ascending for "keep lowest", descending for "keep highest")
                    if "Lowest Delta" in trim_strategy:
                        selected_df = selected_df.sort_values('Delta', key=lambda x: abs(x), ascending=True)
                    elif "Highest Premium" in trim_strategy:
                        selected_df = selected_df.sort_values('Bid', ascending=False)
                    elif "Highest Weekly" in trim_strategy:
                        selected_df = selected_df.sort_values('Weekly %', ascending=False)
                    elif "Highest IV Rank" in trim_strategy:
                        # Handle None/NaN in IV Rank
                        selected_df['IV Rank Filled'] = selected_df['IV Rank'].fillna(-999)
                        selected_df = selected_df.sort_values('IV Rank Filled', ascending=False)
                    
                    # Keep removing from bottom until we're under target
                    running_collateral = current_collateral
                    indices_to_keep = []
                    removed_count = 0
                    
                    for idx in selected_df.index:
                        row_collateral = selected_df.loc[idx, 'Collateral']
                        
                        # If keeping this row would still be over target, keep it
                        # Otherwise, check if removing it gets us closer to target
                        if running_collateral - row_collateral >= weekly_target:
                            # Remove this row (don't add to keep list)
                            running_collateral -= row_collateral
                            removed_count += 1
                        else:
                            # Keep this row
                            indices_to_keep.append(idx)
                    
                    # Update selections: unselect removed rows
                    for idx in selected_indices:
                        if idx not in indices_to_keep:
                            st.session_state.csp_opportunities.loc[idx, 'Select'] = False
                    
                    final_collateral = (st.session_state.csp_opportunities[st.session_state.csp_opportunities['Select'] == True]['Strike'] * 
                                      st.session_state.csp_opportunities[st.session_state.csp_opportunities['Select'] == True]['Qty'] * 100).sum()
                    
                    st.success(f"✅ Removed {removed_count} options. New total: ${final_collateral:,.0f}")
                    st.rerun()
        
        st.write("")
        st.write("---")
        
        # Filter Configuration Expanders
        st.subheader("⚙️ Preset Filter Configuration")
        
        # Conservative Expander
        with st.expander("🟢 Conservative Filter Configuration", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                cons_delta_min = st.number_input("Min Delta", value=st.session_state.csp_conservative_delta_min, min_value=0.0, max_value=1.0, step=0.01, key="csp_cons_delta_min_input")
                cons_delta_max = st.number_input("Max Delta", value=st.session_state.csp_conservative_delta_max, min_value=0.0, max_value=1.0, step=0.01, key="csp_cons_delta_max_input")
                cons_dte_min = st.number_input("Min DTE", value=st.session_state.csp_conservative_dte_min, min_value=0, max_value=365, step=1, key="csp_cons_dte_min_input")
            with col2:
                cons_dte_max = st.number_input("Max DTE", value=st.session_state.csp_conservative_dte_max, min_value=0, max_value=365, step=1, key="csp_cons_dte_max_input")
                cons_oi_min = st.number_input("Min Open Interest", value=st.session_state.csp_conservative_oi_min, min_value=0, step=10, key="csp_cons_oi_min_input")
                cons_weekly_min = st.number_input("Min Weekly Return %", value=st.session_state.csp_conservative_weekly_min, min_value=0.0, step=0.1, key="csp_cons_weekly_min_input")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Commit Conservative", use_container_width=True, key="csp_commit_conservative"):
                    st.session_state.csp_conservative_delta_min = cons_delta_min
                    st.session_state.csp_conservative_delta_max = cons_delta_max
                    st.session_state.csp_conservative_dte_min = cons_dte_min
                    st.session_state.csp_conservative_dte_max = cons_dte_max
                    st.session_state.csp_conservative_oi_min = cons_oi_min
                    st.session_state.csp_conservative_weekly_min = cons_weekly_min
                    st.success("✅ Conservative criteria committed!")
                    st.rerun()
            with col2:
                if st.button("🔄 Reset Conservative", use_container_width=True, key="csp_reset_conservative"):
                    st.session_state.csp_conservative_delta_min = 0.10
                    st.session_state.csp_conservative_delta_max = 0.20
                    st.session_state.csp_conservative_dte_min = 7
                    st.session_state.csp_conservative_dte_max = 30
                    st.session_state.csp_conservative_oi_min = 50
                    st.session_state.csp_conservative_weekly_min = 0.3
                    st.success("✅ Conservative reset to defaults!")
                    st.rerun()
        
        # Medium Expander
        with st.expander("🟡 Medium Filter Configuration", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                med_delta_min = st.number_input("Min Delta", value=st.session_state.csp_medium_delta_min, min_value=0.0, max_value=1.0, step=0.01, key="csp_med_delta_min_input")
                med_delta_max = st.number_input("Max Delta", value=st.session_state.csp_medium_delta_max, min_value=0.0, max_value=1.0, step=0.01, key="csp_med_delta_max_input")
                med_dte_min = st.number_input("Min DTE", value=st.session_state.csp_medium_dte_min, min_value=0, max_value=365, step=1, key="csp_med_dte_min_input")
            with col2:
                med_dte_max = st.number_input("Max DTE", value=st.session_state.csp_medium_dte_max, min_value=0, max_value=365, step=1, key="csp_med_dte_max_input")
                med_oi_min = st.number_input("Min Open Interest", value=st.session_state.csp_medium_oi_min, min_value=0, step=10, key="csp_med_oi_min_input")
                med_weekly_min = st.number_input("Min Weekly Return %", value=st.session_state.csp_medium_weekly_min, min_value=0.0, step=0.1, key="csp_med_weekly_min_input")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Commit Medium", use_container_width=True, key="csp_commit_medium"):
                    st.session_state.csp_medium_delta_min = med_delta_min
                    st.session_state.csp_medium_delta_max = med_delta_max
                    st.session_state.csp_medium_dte_min = med_dte_min
                    st.session_state.csp_medium_dte_max = med_dte_max
                    st.session_state.csp_medium_oi_min = med_oi_min
                    st.session_state.csp_medium_weekly_min = med_weekly_min
                    st.success("✅ Medium criteria committed!")
                    st.rerun()
            with col2:
                if st.button("🔄 Reset Medium", use_container_width=True, key="csp_reset_medium"):
                    st.session_state.csp_medium_delta_min = 0.15
                    st.session_state.csp_medium_delta_max = 0.30
                    st.session_state.csp_medium_dte_min = 7
                    st.session_state.csp_medium_dte_max = 30
                    st.session_state.csp_medium_oi_min = 50
                    st.session_state.csp_medium_weekly_min = 0.3
                    st.success("✅ Medium reset to defaults!")
                    st.rerun()
        
        # Aggressive Expander
        with st.expander("🔴 Aggressive Filter Configuration", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                agg_delta_min = st.number_input("Min Delta", value=st.session_state.csp_aggressive_delta_min, min_value=0.0, max_value=1.0, step=0.01, key="csp_agg_delta_min_input")
                agg_delta_max = st.number_input("Max Delta", value=st.session_state.csp_aggressive_delta_max, min_value=0.0, max_value=1.0, step=0.01, key="csp_agg_delta_max_input")
                agg_dte_min = st.number_input("Min DTE", value=st.session_state.csp_aggressive_dte_min, min_value=0, max_value=365, step=1, key="csp_agg_dte_min_input")
            with col2:
                agg_dte_max = st.number_input("Max DTE", value=st.session_state.csp_aggressive_dte_max, min_value=0, max_value=365, step=1, key="csp_agg_dte_max_input")
                agg_oi_min = st.number_input("Min Open Interest", value=st.session_state.csp_aggressive_oi_min, min_value=0, step=10, key="csp_agg_oi_min_input")
                agg_weekly_min = st.number_input("Min Weekly Return %", value=st.session_state.csp_aggressive_weekly_min, min_value=0.0, step=0.1, key="csp_agg_weekly_min_input")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Commit Aggressive", use_container_width=True, key="csp_commit_aggressive"):
                    st.session_state.csp_aggressive_delta_min = agg_delta_min
                    st.session_state.csp_aggressive_delta_max = agg_delta_max
                    st.session_state.csp_aggressive_dte_min = agg_dte_min
                    st.session_state.csp_aggressive_dte_max = agg_dte_max
                    st.session_state.csp_aggressive_oi_min = agg_oi_min
                    st.session_state.csp_aggressive_weekly_min = agg_weekly_min
                    st.success("✅ Aggressive criteria committed!")
                    st.rerun()
            with col2:
                if st.button("🔄 Reset Aggressive", use_container_width=True, key="csp_reset_aggressive"):
                    st.session_state.csp_aggressive_delta_min = 0.20
                    st.session_state.csp_aggressive_delta_max = 0.40
                    st.session_state.csp_aggressive_dte_min = 7
                    st.session_state.csp_aggressive_dte_max = 21
                    st.session_state.csp_aggressive_oi_min = 25
                    st.session_state.csp_aggressive_weekly_min = 0.3
                    st.success("✅ Aggressive reset to defaults!")
                    st.rerun()
        
        st.write("")
        st.write("---")
        
        # Row 2: Quantity adjustment buttons
        st.write("**Adjust Quantities for Selected:**")
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 2])
        
        with col1:
            if st.button("➕ +1", use_container_width=True, key="csp_qty_plus1", help="Add 1 to selected quantities"):
                mask = st.session_state.csp_opportunities['Select'] == True
                st.session_state.csp_opportunities.loc[mask, 'Qty'] = st.session_state.csp_opportunities.loc[mask, 'Qty'] + 1
                st.rerun()
        
        with col2:
            if st.button("➕ +5", use_container_width=True, key="csp_qty_plus5", help="Add 5 to selected quantities"):
                mask = st.session_state.csp_opportunities['Select'] == True
                st.session_state.csp_opportunities.loc[mask, 'Qty'] = st.session_state.csp_opportunities.loc[mask, 'Qty'] + 5
                st.rerun()
        
        with col3:
            if st.button("➕ +10", use_container_width=True, key="csp_qty_plus10", help="Add 10 to selected quantities"):
                mask = st.session_state.csp_opportunities['Select'] == True
                st.session_state.csp_opportunities.loc[mask, 'Qty'] = st.session_state.csp_opportunities.loc[mask, 'Qty'] + 10
                st.rerun()
        
        with col4:
            if st.button("➖ -1", use_container_width=True, key="csp_qty_minus1", help="Subtract 1 from selected quantities (min 1)"):
                mask = st.session_state.csp_opportunities['Select'] == True
                st.session_state.csp_opportunities.loc[mask, 'Qty'] = st.session_state.csp_opportunities.loc[mask, 'Qty'].apply(lambda x: max(1, x - 1))
                st.rerun()
        
        with col5:
            if st.button("🔄 Reset", use_container_width=True, key="csp_qty_reset", help="Reset selected quantities to 1"):
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
        
        st.write("")
        
        # Format IV Rank and Spread % with colored emoji indicators (like CC Dashboard)
        display_df = st.session_state.csp_opportunities.copy()
        
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
        
        # Apply formatting to display columns
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
            use_container_width=True,
            height=600,
            key=editor_key
        )
        
        # Update session state - only copy Select and Qty columns (user-editable)
        # Keep original numeric values for other columns (formatted columns are display-only)
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
                        
                        if st.button(button_label, key=f"mark_btn_{idx}", use_container_width=True, type=button_type,
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
            col1, col2, col3 = st.columns([1, 1, 4])
            
            with col1:
                if st.button("🗑️ Remove Marked", use_container_width=True, type="primary", 
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
            
            with col2:
                if st.button("↩️ Clear Marks", use_container_width=True, 
                           disabled=len(st.session_state.csp_marked_indices) == 0,
                           help="Clear all marks without removing"):
                    st.session_state.csp_marked_indices = set()
                    st.success("✅ Cleared all marks")
                    st.rerun()
            
            with col3:
                if len(st.session_state.csp_marked_indices) > 0:
                    marked_symbols = []
                    for idx in st.session_state.csp_marked_indices:
                        if idx in st.session_state.csp_opportunities.index:
                            symbol = st.session_state.csp_opportunities.loc[idx, 'Symbol']
                            marked_symbols.append(symbol)
                    st.info(f"🏷️ Marked ({len(marked_symbols)}): {', '.join(marked_symbols[:8])}{'...' if len(marked_symbols) > 8 else ''}")
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
            num_different_options = len(selected_rows)
            
            # Display summary card
            col1, col2, col3, col4, col5 = st.columns(5)
            
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
            
            # Check buying power
            balances = api.get_account_balances(selected_account)
            if balances:
                # For CSP, use Derivative Buying Power (API field name)
                # This is what Tastytrade UI shows as "Option Buying Power"
                buying_power = float(balances.get('derivative-buying-power', 0))
                bp_label = "Option Buying Power"
                
                # Get cash balance for reference
                cash_balance = float(balances.get('cash-balance', 0))
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(bp_label, f"${buying_power:,.2f}")
                with col2:
                    remaining = buying_power - total_collateral
                    st.metric("After Orders", f"${remaining:,.2f}", 
                             delta=f"-${total_collateral:,.2f}",
                             delta_color="inverse")
                with col3:
                    utilization = (total_collateral / buying_power * 100) if buying_power > 0 else 0
                    st.metric("BP Utilization", f"{utilization:.1f}%")
                
                # Warning if insufficient buying power
                if total_collateral > buying_power:
                    st.error(f"⚠️ **Insufficient Buying Power!** You need ${total_collateral:,.2f} but only have ${buying_power:,.2f}")
                    can_submit = False
                else:
                    can_submit = True
                
                # Weekly Deployment Tracker
                st.divider()
                st.subheader("📅 Weekly Deployment Tracker")
                
                # Import helper functions
                from utils.csp_ladder_manager import get_next_friday, get_deployed_csp_capital, calculate_tranche_targets
                
                # Get positions to calculate deployed capital
                positions = api.get_positions(selected_account)
                deployed_data = get_deployed_csp_capital(positions)
                deployed_by_week = deployed_data['by_week']
                total_deployed = deployed_data['total']
                
                # Calculate this week's target
                optimal_tranche_size = calculate_tranche_targets(buying_power, 4)
                
                # Get current week (Week 1 = next Friday)
                current_week_exp = get_next_friday(0)
                deployed_this_week = deployed_by_week.get(current_week_exp, 0)
                
                # Calculate if this order would exceed weekly limit
                total_after_order = deployed_this_week + total_collateral
                remaining_capacity = optimal_tranche_size - deployed_this_week
                exceeds_limit = total_after_order > optimal_tranche_size
                
                # Display weekly tracker
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Weekly Target",
                        f"${optimal_tranche_size:,.0f}",
                        help="Target deployment per week (25% of buying power)"
                    )
                
                with col2:
                    pct_deployed = (deployed_this_week / optimal_tranche_size * 100) if optimal_tranche_size > 0 else 0
                    st.metric(
                        "Deployed This Week",
                        f"${deployed_this_week:,.0f}",
                        f"{pct_deployed:.0f}%",
                        help=f"Capital deployed for week ending {current_week_exp}"
                    )
                
                with col3:
                    st.metric(
                        "Remaining Capacity",
                        f"${remaining_capacity:,.0f}",
                        help="Available capacity for this week's target"
                    )
                
                with col4:
                    pct_after = (total_after_order / optimal_tranche_size * 100) if optimal_tranche_size > 0 else 0
                    st.metric(
                        "After This Order",
                        f"${total_after_order:,.0f}",
                        f"{pct_after:.0f}%",
                        delta_color="normal" if not exceeds_limit else "inverse"
                    )
                
                # Warning if exceeds weekly limit
                if exceeds_limit:
                    excess = total_after_order - optimal_tranche_size
                    st.warning(f"⚠️ **Weekly Limit Warning:** This order would exceed your weekly target by ${excess:,.0f} ({pct_after-100:.0f}% over)")
                    st.info(f"💡 Consider reducing to ${remaining_capacity:,.0f} to stay within this week's target, or proceed if intentional.")
                elif remaining_capacity > 0:
                    st.success(f"✅ Within weekly target! You can deploy up to ${remaining_capacity:,.0f} more this week.")
                else:
                    st.info(f"✅ Weekly target met! This week's allocation is complete.")
                
            else:
                st.warning("⚠️ Could not fetch account balances")
                can_submit = False
            
            st.divider()
            
            # AI Analysis and Order submission
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button(
                    "🤖 AI Analysis",
                    use_container_width=True,
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
                    disabled=not can_submit,
                    use_container_width=True
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
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
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
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"PDF export error: {str(e)}")
                
                with col3:
                    # Clear button
                    if st.button("🗑️ Clear Analysis", use_container_width=True):
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
                
                # VALIDATION 2: Buying Power
                st.subheader("2️⃣ Buying Power Validation")
                
                balances = api.get_account_balances(selected_account)
                if balances:
                    # Use Derivative Buying Power (API field name)
                    # This is what Tastytrade UI shows as "Option Buying Power"
                    buying_power = float(balances.get('derivative-buying-power', 0))
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Available Option BP", f"${buying_power:,.2f}")
                    with col2:
                        st.metric("Required Collateral", f"${total_collateral:,.2f}")
                    with col3:
                        buffer = buying_power - total_collateral
                        st.metric("Buffer After Orders", f"${buffer:,.2f}")
                    
                    if total_collateral <= buying_power:
                        buffer_pct = (buffer / buying_power * 100) if buying_power > 0 else 0
                        st.success(f"✅ Sufficient buying power ({buffer_pct:.1f}% buffer remaining)")
                        validation_results.append(("Buying Power", True, f"${buffer:,.2f} buffer"))
                    else:
                        shortage = total_collateral - buying_power
                        st.error(f"❌ Insufficient buying power! Short by ${shortage:,.2f}")
                        validation_results.append(("Buying Power", False, f"Short ${shortage:,.2f}"))
                        all_passed = False
                else:
                    st.error("❌ Could not fetch account balances")
                    validation_results.append(("Buying Power", False, "API error"))
                    all_passed = False
                
                st.divider()
                
                # VALIDATION 3: Price Freshness
                st.subheader("3️⃣ Price Freshness Validation")
                
                if time_since_scan < 5:
                    st.success(f"✅ Data is fresh ({time_since_scan:.1f} minutes old)")
                    validation_results.append(("Price Freshness", True, f"{time_since_scan:.1f}min old"))
                elif time_since_scan < 15:
                    st.warning(f"⚠️ Data is {time_since_scan:.1f} minutes old - consider re-scanning")
                    validation_results.append(("Price Freshness", True, f"{time_since_scan:.1f}min old (acceptable)"))
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
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                if all_passed:
                    st.success("🎉 **ALL VALIDATIONS PASSED** - Ready to proceed!")
                else:
                    st.error("❌ **VALIDATION FAILED** - Please resolve issues before submitting")
                
                st.divider()
                
                # Show order details
                st.write("**Order Details:**")
                order_details = selected_rows[['Symbol', 'Qty', 'Strike', 'Expiration', 'DTE', 'Premium', 'Premium %', 'Weekly %', 'Delta']]
                st.dataframe(order_details, use_container_width=True)
                
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
                    
                    if st.button(button_label, type=button_type, use_container_width=True, disabled=button_disabled, key="submit_orders_btn"):
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
                                    st.balloons()
                                    
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
                    if st.button("❌ Cancel", use_container_width=True, key="cancel_orders_btn"):
                        st.session_state.show_order_confirmation = False
                        st.rerun()
                
                with col3:
                    if st.button("🔄 Re-scan Prices", use_container_width=True, key="rescan_btn"):
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
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            if 'csp_scan_log' in st.session_state:
                st.download_button(
                    label="📄 Download Scan Log",
                    data=st.session_state.csp_scan_log,
                    file_name=f"csp_scan_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
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
                mime="text/plain",
                use_container_width=True
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
                        st.caption(f"This will submit {int(total_contracts)} covered call order(s) as limit orders at the mid price (between bid/ask).")
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
                                                st.balloons()
                                            
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
    
    # Working Orders Monitor Section
    st.markdown('<div class="section-header">📋 Working Orders Monitor</div>', unsafe_allow_html=True)
    from utils.working_orders import render_working_orders_monitor
    render_working_orders_monitor(api, selected_account, order_type='pmcc')
    
    st.divider()
    
    # ========================================
    # SECTION 1: ACTIVE PMCC POSITIONS
    # ========================================
    st.markdown('<div class="section-header">🎯 Active PMCC Positions</div>', unsafe_allow_html=True)
    
    # Fetch LEAP positions
    if st.button("🔍 Refresh PMCC Positions", type="primary", use_container_width=True):
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
        display_leap_df['Strike'] = display_leap_df['Strike'].apply(lambda x: f"${x:.2f}")
        display_leap_df['Cost Basis'] = display_leap_df['Cost Basis'].apply(lambda x: f"${x:,.0f}")
        display_leap_df['Current Value'] = display_leap_df['Current Value'].apply(lambda x: f"${x:,.0f}")
        display_leap_df['P/L'] = display_leap_df['P/L'].apply(lambda x: f"${x:,.0f}")
        
        st.dataframe(display_leap_df, use_container_width=True, hide_index=True)
        
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
        display_short_df['Strike'] = display_short_df['Strike'].apply(lambda x: f"${x:.2f}")
        display_short_df['Premium Collected'] = display_short_df['Premium Collected'].apply(lambda x: f"${x:,.0f}")
        display_short_df['Current Value'] = display_short_df['Current Value'].apply(lambda x: f"${x:,.0f}")
        display_short_df['P/L'] = display_short_df['P/L'].apply(lambda x: f"${x:,.0f}")
        
        st.dataframe(display_short_df, use_container_width=True, hide_index=True)
        
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
                    if st.button("📧 Send Alert", use_container_width=True, key="pmcc_send_alert"):
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
    # SECTION 2: TRADINGVIEW IMPORT & WATCHLIST
    # ========================================
    st.markdown('<div class="section-header">📝 Watchlist Management</div>', unsafe_allow_html=True)
    
    # Read watchlist
    try:
        with open('pmcc_watchlist.txt', 'r') as f:
            watchlist = [line.strip() for line in f if line.strip()]
    except:
        watchlist = []
    
    # CSV Import Section
    with st.expander("📥 Import from TradingView", expanded=False):
        st.markdown("""
        **Quick Import from TradingView:**
        1. Export your TradingView watchlist as CSV
        2. Upload it here to automatically add tickers
        """)
        
        uploaded_file = st.file_uploader("Upload CSV", type=['csv'], key="pmcc_csv_upload")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                
                # Try to find ticker column
                ticker_col = None
                for col in df.columns:
                    if 'symbol' in col.lower() or 'ticker' in col.lower():
                        ticker_col = col
                        break
                
                if ticker_col:
                    new_tickers = df[ticker_col].str.upper().str.strip().tolist()
                    
                    # Add to watchlist file
                    with open('pmcc_watchlist.txt', 'a') as f:
                        for ticker in new_tickers:
                            if ticker and ticker not in watchlist:
                                f.write(f"{ticker}\\n")
                    
                    st.success(f"✅ Added {len(new_tickers)} tickers to watchlist!")
                    st.rerun()
                else:
                    st.error("❌ Could not find ticker/symbol column in CSV")
            except Exception as e:
                st.error(f"Error reading CSV: {str(e)}")
    
    # Manual ticker addition
    col1, col2 = st.columns([3, 1])
    with col1:
        new_ticker = st.text_input("Add ticker manually", placeholder="AAPL", key="pmcc_manual_ticker")
    with col2:
        st.write("")
        st.write("")
        if st.button("➕ Add", use_container_width=True, key="pmcc_add_ticker"):
            if new_ticker:
                ticker = new_ticker.upper().strip()
                if ticker not in watchlist:
                    with open('pmcc_watchlist.txt', 'a') as f:
                        f.write(f"{ticker}\\n")
                    st.success(f"✅ Added {ticker}")
                    st.rerun()
                else:
                    st.warning(f"{ticker} already in watchlist")
    
    # Display current watchlist
    if watchlist:
        st.write("")
        st.markdown(f"**Current Watchlist ({len(watchlist)} tickers):**")
        st.write(", ".join(watchlist))
        
        if st.button("🗑️ Clear Watchlist", key="pmcc_clear_watchlist"):
            with open('pmcc_watchlist.txt', 'w') as f:
                f.write("")
            st.success("✅ Watchlist cleared!")
            st.rerun()
    else:
        st.info("📝 No tickers in watchlist. Add some to get started!")
    
    st.divider()
    
    # ========================================
    # SECTION 3: LEAP SCANNER
    # ========================================
    st.markdown('<div class="section-header">🔍 LEAP Scanner</div>', unsafe_allow_html=True)
    
    st.markdown("**Scan for LEAP call options (9-15 months out, deep ITM for PMCC strategy)**")
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dte_min = st.number_input("Min DTE (days)", min_value=180, max_value=730, value=270, step=30, key="pmcc_dte_min")
        dte_max = st.number_input("Max DTE (days)", min_value=180, max_value=730, value=450, step=30, key="pmcc_dte_max")
    
    with col2:
        delta_min = st.number_input("Min Delta", min_value=0.5, max_value=1.0, value=0.70, step=0.05, key="pmcc_delta_min")
        delta_max = st.number_input("Max Delta", min_value=0.5, max_value=1.0, value=0.90, step=0.05, key="pmcc_delta_max")
    
    with col3:
        min_oi = st.number_input("Min Open Interest", min_value=0, max_value=1000, value=50, step=10, key="pmcc_min_oi")
        st.write("")
    
    # Preset filter buttons
    st.write("")
    preset_col1, preset_col2, preset_col3 = st.columns(3)
    
    with preset_col1:
        if st.button("🔥 Aggressive", use_container_width=True, key="pmcc_aggressive"):
            st.session_state.pmcc_dte_min = 360
            st.session_state.pmcc_dte_max = 450
            st.session_state.pmcc_delta_min = 0.85
            st.session_state.pmcc_delta_max = 0.95
            st.session_state.pmcc_min_oi = 100
            st.rerun()
    
    with preset_col2:
        if st.button("⚖️ Medium", use_container_width=True, key="pmcc_medium"):
            st.session_state.pmcc_dte_min = 300
            st.session_state.pmcc_dte_max = 390
            st.session_state.pmcc_delta_min = 0.75
            st.session_state.pmcc_delta_max = 0.85
            st.session_state.pmcc_min_oi = 50
            st.rerun()
    
    with preset_col3:
        if st.button("🛡️ Conservative", use_container_width=True, key="pmcc_conservative"):
            st.session_state.pmcc_dte_min = 270
            st.session_state.pmcc_dte_max = 330
            st.session_state.pmcc_delta_min = 0.70
            st.session_state.pmcc_delta_max = 0.80
            st.session_state.pmcc_min_oi = 25
            st.rerun()
    
    st.write("")
    
    # Initialize session state for scan results
    if 'pmcc_leap_scan_results' not in st.session_state:
        st.session_state.pmcc_leap_scan_results = []
    
    # Scan button
    if st.button("🔍 Scan for LEAPs", type="primary", use_container_width=True, key="pmcc_scan"):
        if not watchlist:
            st.warning("⚠️ Please add tickers to your watchlist first!")
        else:
            try:
                with st.status("Scanning for LEAP opportunities...", expanded=True) as status:
                    from utils.pmcc_scanner import scan_leap_options
                    from utils.tradier_api import TradierAPI
                    
                    tradier = TradierAPI()
                    
                    st.write(f"🔍 Scanning {len(watchlist)} symbols...")
                    st.write(f"🎯 Filters: DTE {dte_min}-{dte_max}, Delta {delta_min:.2f}-{delta_max:.2f}, Min OI {min_oi}")
                    
                    # Scan for LEAPs
                    results = scan_leap_options(
                        tradier,
                        watchlist,
                        dte_min=dte_min,
                        dte_max=dte_max,
                        delta_min=delta_min,
                        delta_max=delta_max,
                        min_oi=min_oi
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
        st.markdown(f"### 📊 LEAP Scan Results ({len(st.session_state.pmcc_leap_scan_results)} opportunities)")
        
        results_df = pd.DataFrame(st.session_state.pmcc_leap_scan_results)
        
        # Format for display
        display_df = results_df[[
            'symbol', 'underlying_price', 'strike', 'expiration', 'dte',
            'delta', 'price', 'cost_per_contract', 'open_interest', 'volume'
        ]].copy()
        
        display_df.columns = [
            'Symbol', 'Stock Price', 'Strike', 'Expiration', 'DTE',
            'Delta', 'Premium', 'Cost/Contract', 'Open Int', 'Volume'
        ]
        
        # Format columns
        display_df['Stock Price'] = display_df['Stock Price'].apply(lambda x: f"${x:.2f}")
        display_df['Strike'] = display_df['Strike'].apply(lambda x: f"${x:.2f}")
        display_df['Delta'] = display_df['Delta'].apply(lambda x: f"{x:.3f}")
        display_df['Premium'] = display_df['Premium'].apply(lambda x: f"${x:.2f}")
        display_df['Cost/Contract'] = display_df['Cost/Contract'].apply(lambda x: f"${x:,.0f}")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Add action buttons for each LEAP
        st.write("")
        st.markdown("**Select a LEAP to purchase:**")
        
        # Create selection dropdown
        leap_options = [f"{r['symbol']} ${r['strike']:.2f} exp {r['expiration']} (${r['cost_per_contract']:,.0f})" 
                       for r in st.session_state.pmcc_leap_scan_results]
        
        selected_leap_idx = st.selectbox(
            "Choose LEAP",
            range(len(leap_options)),
            format_func=lambda x: leap_options[x],
            key="pmcc_selected_leap_to_buy"
        )
        
        if selected_leap_idx is not None:
            selected_leap = st.session_state.pmcc_leap_scan_results[selected_leap_idx]
            
            col1, col2 = st.columns(2)
            with col1:
                num_contracts = st.number_input(
                    "Number of Contracts",
                    min_value=1,
                    max_value=10,
                    value=1,
                    step=1,
                    key="pmcc_num_contracts"
                )
            
            with col2:
                total_cost = selected_leap['cost_per_contract'] * num_contracts
                st.metric("Total Cost", f"${total_cost:,.0f}")
            
            st.write("")
            if st.button("💰 Buy LEAP (Submit Order)", type="primary", use_container_width=True, key="pmcc_buy_leap"):
                try:
                    with st.status("Submitting LEAP buy order...", expanded=True) as status:
                        from utils.pmcc_orders import submit_leap_buy_order
                        
                        st.write(f"💰 Buying {num_contracts} contract(s) of {selected_leap['symbol']}")
                        st.write(f"💵 Limit Price: ${selected_leap['price']:.2f} per contract")
                        st.write(f"📄 Total Cost: ${total_cost:,.0f}")
                        
                        # Submit order via Tastytrade API
                        result = submit_leap_buy_order(
                            api,
                            selected_account,
                            selected_leap['option_symbol'],
                            num_contracts,
                            selected_leap['price'],
                            order_type='Limit'
                        )
                        
                        if result['success']:
                            status.update(label=f"✅ Order submitted successfully! Order ID: {result.get('order_id', 'N/A')}", state="complete")
                            st.success(f"✅ {result['message']}")
                            st.info(f"📊 Order ID: {result.get('order_id', 'N/A')}")
                            st.info(f"🕒 Status: {result.get('status', 'Pending')}")
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
            if st.button("🔍 Scan Short Calls", type="primary", use_container_width=True, key="pmcc_scan_short"):
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
                display_df['Strike'] = display_df['Strike'].apply(lambda x: f"${x:.2f}")
                display_df['Delta'] = display_df['Delta'].apply(lambda x: f"{x:.3f}")
                display_df['Premium'] = display_df['Premium'].apply(lambda x: f"${x:.0f}")
                display_df['Distance %'] = display_df['Distance %'].apply(lambda x: f"{x:.1f}%")
                display_df['Above LEAP'] = display_df['Above LEAP'].apply(lambda x: f"${x:.2f}")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
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
                    if st.button("💰 Sell Short Call (Submit Order)", type="primary", use_container_width=True, key="pmcc_sell_short"):
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
                                    st.balloons()
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
    st.markdown('<p style="color: #9ca3af; font-size: 14px; margin-bottom: 2rem;">Track your trading performance and analyze results</p>', unsafe_allow_html=True)
    
    # Premium Performance Metrics
    if selected_account:
        try:
            # Get account balances and positions
            balances = api.get_account_balances(selected_account)
            positions = api.get_positions(selected_account)
            
            if balances:
                # Safely get NLV
                nlv = 0
                try:
                    nlv = float(balances.get('net-liquidating-value', 0) or 0)
                except (ValueError, TypeError):
                    nlv = 0
                
                # Count positions
                total_positions = len(positions) if positions else 0
                stock_positions = len([p for p in positions if p.get('instrument-type') == 'Equity']) if positions else 0
                option_positions = len([p for p in positions if p.get('instrument-type') == 'Equity Option']) if positions else 0
                
                # Calculate total P/L from positions - with comprehensive error handling
                total_pl = 0
                if positions:
                    for p in positions:
                        try:
                            pl_value = p.get('realized-day-gain-effect', 0)
                            if pl_value is not None and pl_value != 'None':
                                total_pl += float(pl_value)
                        except (ValueError, TypeError):
                            continue
            
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
        except Exception as e:
            st.error(f"Error loading performance metrics: {str(e)}")
    
    # Monthly Premium Summary (ALL ACCOUNTS - not filtered by dropdown)
    from utils.monthly_premium import render_monthly_premium_summary
    render_monthly_premium_summary(api, all_accounts=True)
    
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