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

# Sidebar
with st.sidebar:
    st.header("📊 Options Trading")
    
    # Account selector
    st.subheader("💼 Select Account")
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
    else:
        st.error("No accounts found")
        selected_account = None
    
    st.divider()
    
    # Navigation
    st.subheader("📍 Navigation")
    page = st.radio(
        "Go to",
        ["Home", "Analysis Dashboard", "CSP Dashboard", "CC Dashboard", "Performance", "Settings"],
        label_visibility="collapsed"
    )

# Main content area
if page == "Home":
    st.title("🏠 Home Dashboard")
    
    if selected_account:
        st.subheader(f"Account: {selected_display}")
        
        # Get account balances
        balances = api.get_account_balances(selected_account)
        
        if balances:
            col1, col2, col3 = st.columns(3)
            
            nlv = float(balances.get('net-liquidating-value', 0))
            cash = float(balances.get('cash-balance', 0))
            buying_power = float(balances.get('derivative-buying-power', 0))
            
            with col1:
                st.metric("Net Liquidating Value", f"${nlv:,.2f}")
            with col2:
                st.metric("Cash Balance", f"${cash:,.2f}")
            with col3:
                st.metric("Buying Power", f"${buying_power:,.2f}")
        
        st.divider()
        
        # CSP Ladder Manager
        render_csp_ladder_manager(api, selected_account)
        
        st.divider()
        
        # Get positions
        st.subheader("📊 Current Positions")
        positions = api.get_positions(selected_account)
        
        if positions:
            st.write(f"You have {len(positions)} open positions")
            # TODO: Display positions in a nice table
        else:
            st.info("No open positions")

elif page == "Analysis Dashboard":
    st.title("🔬 Stock Analysis Dashboard")
    st.write("Scan stocks for CSP opportunities based on technical indicators")
    
    # Read stock universe
    try:
        with open('stock_universe.txt', 'r') as f:
            stock_universe = [line.strip() for line in f if line.strip()]
    except Exception as e:
        st.error(f"❌ Could not read stock_universe.txt: {str(e)}")
        st.stop()
    
    st.info(f"📋 Stock Universe: {len(stock_universe)} symbols")
    
    # ========== STOCK UNIVERSE MANAGER ==========
    st.divider()
    
    with st.expander("⚙️ Manage Stock Universe", expanded=False):
        st.markdown("""
        **Manage your Stock Universe file:**
        
        - **View:** See all stocks currently in universe
        - **Clear:** Remove all stocks (start fresh)
        - **Replace:** Upload new CSV to replace entire universe
        - **Download:** Backup current universe
        """)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("👁️ View Universe", key="view_universe"):
                st.write(f"**Current Stock Universe ({len(stock_universe)} stocks):**")
                if len(stock_universe) <= 100:
                    st.text_area("Symbols:", "\n".join(stock_universe), height=300)
                else:
                    st.text_area("First 100 symbols:", "\n".join(stock_universe[:100]), height=300)
                    st.info(f"Showing first 100 of {len(stock_universe)} total stocks")
        
        with col2:
            if st.button("🗑️ Clear Universe", type="secondary", key="clear_universe"):
                if st.session_state.get('confirm_clear_universe', False):
                    with open('stock_universe.txt', 'w') as f:
                        f.write('')
                    st.success("✅ Stock Universe cleared! Refresh page to see changes.")
                    st.session_state['confirm_clear_universe'] = False
                else:
                    st.session_state['confirm_clear_universe'] = True
                    st.warning("⚠️ Click again to confirm clearing all stocks")
        
        with col3:
            # Replace universe with new CSV
            replace_file = st.file_uploader(
                "Replace Universe",
                type=['csv', 'txt'],
                help="Upload CSV or TXT to replace entire universe",
                key="replace_universe_uploader"
            )
            
            if replace_file is not None:
                try:
                    import pandas as pd
                    
                    if replace_file.name.endswith('.csv'):
                        df = pd.read_csv(replace_file)
                        symbol_col = None
                        for col in df.columns:
                            if col.lower() in ['symbol', 'ticker', 'stock']:
                                symbol_col = col
                                break
                        
                        if symbol_col:
                            new_symbols = df[symbol_col].dropna().unique().tolist()
                            new_symbols = [str(s).strip().upper() for s in new_symbols if str(s).strip()]
                        else:
                            st.error("❌ No 'Symbol' or 'Ticker' column found")
                            new_symbols = []
                    else:  # TXT file
                        content = replace_file.read().decode('utf-8')
                        new_symbols = [line.strip().upper() for line in content.split('\n') if line.strip()]
                    
                    if new_symbols:
                        with open('stock_universe.txt', 'w') as f:
                            for symbol in new_symbols:
                                f.write(f"{symbol}\n")
                        st.success(f"✅ Replaced universe with {len(new_symbols)} stocks! Refresh page.")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        with col4:
            # Download current universe
            if len(stock_universe) > 0:
                universe_txt = "\n".join(stock_universe)
                st.download_button(
                    label="💾 Download",
                    data=universe_txt,
                    file_name="stock_universe_backup.txt",
                    mime="text/plain",
                    key="download_universe"
                )
    
    # ========== CSV IMPORT SECTION ==========
    st.divider()
    
    with st.expander("📄 Import Stocks from TradingView CSV", expanded=False):
        st.markdown("""
        **Import a list of stocks from TradingView or other screeners:**
        
        1. Export your TradingView screener results to CSV
        2. Upload the CSV file below
        3. Stocks will be added to **Stock Universe** for analysis
        4. After analysis, move vetted stocks to **Watchlist** for CSP scanning
        
        **CSV Format:** Must have a column named "Symbol" or "Ticker"
        
        **🔄 Workflow:** Discovery → Stock Universe → Analysis → Watchlist → CSP Dashboard
        """)
        
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Upload CSV with stock symbols",
            key="csv_import_uploader"
        )
        
        if uploaded_file is not None:
            try:
                import pandas as pd
                import io
                
                # Read CSV
                df = pd.read_csv(uploaded_file)
                
                # Find symbol column (case insensitive)
                symbol_col = None
                for col in df.columns:
                    if col.lower() in ['symbol', 'ticker', 'stock']:
                        symbol_col = col
                        break
                
                if symbol_col is None:
                    st.error("❌ No 'Symbol' or 'Ticker' column found in CSV")
                else:
                    symbols = df[symbol_col].dropna().unique().tolist()
                    symbols = [str(s).strip().upper() for s in symbols if str(s).strip()]
                    
                    st.success(f"✅ Found {len(symbols)} unique symbols in CSV")
                    
                    # Show preview
                    st.write("**Preview (first 20):**")
                    st.write(", ".join(symbols[:20]) + ("..." if len(symbols) > 20 else ""))
                    
                    st.info("👉 **Next Step:** These stocks will be added to Stock Universe for technical analysis")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("➕ Add to Stock Universe", type="primary", key="add_csv_to_universe"):
                            # Read existing stock universe
                            universe_path = "stock_universe.txt"
                            existing_symbols = set()
                            
                            if os.path.exists(universe_path):
                                with open(universe_path, 'r') as f:
                                    existing_symbols = set(line.strip().upper() for line in f if line.strip())
                            
                            # Add new symbols
                            new_symbols = [s for s in symbols if s not in existing_symbols]
                            
                            if new_symbols:
                                with open(universe_path, 'a') as f:
                                    for symbol in new_symbols:
                                        f.write(f"{symbol}\n")
                                
                                st.success(f"✅ Added {len(new_symbols)} new symbols to Stock Universe!")
                                st.info(f"📊 {len(existing_symbols)} symbols were already in Stock Universe")
                                st.info("🔄 Refresh page to see updated count")
                            else:
                                st.info("📊 All symbols already in Stock Universe")
                    
                    with col2:
                        if st.button("💾 Download Symbols as TXT", key="download_csv_symbols"):
                            symbols_text = "\n".join(symbols)
                            st.download_button(
                                label="💾 Download",
                                data=symbols_text,
                                file_name="imported_symbols.txt",
                                mime="text/plain"
                            )
                    
            except Exception as e:
                st.error(f"❌ Error reading CSV: {e}")
    
    # ========== END CSV IMPORT SECTION ==========
    st.divider()
    
    # ========== DISCOVERY SCANNER (REMOVED) ==========
    # The Discovery Scanner has been removed from the UI due to Yahoo Finance rate limiting.
    # REASON: Yahoo Finance API returns 429 "Too Many Requests" errors when scanning stocks
    # ALTERNATIVE: Use TradingView CSV Import instead (works perfectly!)
    # CODE BACKUP: Saved in /home/ubuntu/discovery_section_backup.txt
    # TO RESTORE: Contact developer or check backup file
    # LAST UPDATED: 2026-01-01
    # ========== END DISCOVERY SCANNER ==========
    
    st.divider()
    
    # Quick Presets
    st.subheader("⚡ Quick Presets")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🟢 Conservative", use_container_width=True):
            st.session_state.min_csp_score = 60
            st.session_state.max_rsi = 40
            st.session_state.max_bb = 40
            st.session_state.max_52w = 40
            st.session_state.min_price = 20.0
            st.session_state.max_price = 300.0
            st.session_state.min_avg_volume = 1000000  # NEW: 1M+ volume
            st.session_state.max_spread = 2.0  # NEW: ≤2% spread
            st.session_state.max_support_dist = 15.0  # NEW: ≤15% above support
            st.rerun()
    
    with col2:
        if st.button("🟡 Medium", use_container_width=True):
            st.session_state.min_csp_score = 40
            st.session_state.max_rsi = 55
            st.session_state.max_bb = 55
            st.session_state.max_52w = 55
            st.session_state.min_price = 10.0
            st.session_state.max_price = 500.0
            st.session_state.min_avg_volume = 500000  # NEW: 500K+ volume
            st.session_state.max_spread = 3.0  # NEW: ≤3% spread
            st.session_state.max_support_dist = 25.0  # NEW: ≤25% above support
            st.rerun()
    
    with col3:
        if st.button("🔴 Aggressive", use_container_width=True):
            st.session_state.min_csp_score = 20
            st.session_state.max_rsi = 70
            st.session_state.max_bb = 70
            st.session_state.max_52w = 70
            st.session_state.min_price = 5.0
            st.session_state.max_price = 1000.0
            st.session_state.min_avg_volume = 100000  # NEW: 100K+ volume
            st.session_state.max_spread = 5.0  # NEW: ≤5% spread
            st.session_state.max_support_dist = 50.0  # NEW: ≤50% above support
            st.rerun()
    
    with col4:
        if st.button("🟦 Pass All", use_container_width=True, help="Pass all stocks without filtering"):
            st.session_state.min_csp_score = 0
            st.session_state.max_rsi = 100
            st.session_state.max_bb = 100
            st.session_state.max_52w = 100
            st.session_state.min_price = 0.01
            st.session_state.max_price = 10000.0
            st.session_state.min_avg_volume = 0  # NEW: No limit
            st.session_state.max_spread = 100.0  # NEW: No limit
            st.session_state.max_support_dist = 1000.0  # NEW: No limit
            st.rerun()
    
    with st.expander("📘 Preset Explanations"):
        st.markdown("""
        **🟢 Conservative (High Quality)**
        - Min CSP Score: 60 (only high-scoring opportunities)
        - Max RSI: 40 (oversold to neutral)
        - Max BB%: 40% (lower band area)
        - Max 52W%: 40% (near 52-week lows)
        - Price Range: $20-$300
        - Expected: 5-15 results in normal markets
        
        **🟡 Medium (Balanced)**
        - Min CSP Score: 40 (good balance)
        - Max RSI: 55 (neutral range)
        - Max BB%: 55% (middle range)
        - Max 52W%: 55% (middle range)
        - Price Range: $10-$500
        - Expected: 15-30 results
        
        **🔴 Aggressive (More Opportunities)**
        - Min CSP Score: 20 (more permissive)
        - Max RSI: 70 (allow overbought)
        - Max BB%: 70% (allow upper band)
        - Max 52W%: 70% (allow near highs)
        - Price Range: $5-$1000
        - Expected: 30-50+ results
        
        **🟦 Pass All (No Filtering)**
        - Min CSP Score: 0 (accept all)
        - Max RSI: 100 (no limit)
        - Max BB%: 100% (no limit)
        - Max 52W%: 100% (no limit)
        - Price Range: $0.01-$10,000
        - Expected: ALL stocks in universe
        - **Use Case:** You already vetted stocks in TradingView, just want to pass them through
        """)
    
    st.divider()
    
    # Custom Filters
    st.subheader("🔍 Custom Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        min_csp_score = st.number_input(
            "Min CSP Score",
            min_value=0,
            max_value=100,
            value=st.session_state.get('min_csp_score', 20),
            step=5
        )
    
    with col2:
        max_rsi = st.number_input(
            "Max RSI",
            min_value=0,
            max_value=100,
            value=st.session_state.get('max_rsi', 70),
            step=5
        )
    
    with col3:
        max_bb = st.number_input(
            "Max BB %",
            min_value=0,
            max_value=100,
            value=st.session_state.get('max_bb', 70),
            step=5
        )
    
    with col4:
        max_52w = st.number_input(
            "Max 52W %",
            min_value=0,
            max_value=100,
            value=st.session_state.get('max_52w', 70),
            step=5
        )
    
    col5, col6, col7 = st.columns(3)
    
    with col5:
        min_price = st.number_input(
            "Min Stock Price $",
            min_value=0.0,
            max_value=10000.0,
            value=st.session_state.get('min_price', 5.0),
            step=5.0
        )
    
    with col6:
        max_price = st.number_input(
            "Max Stock Price $",
            min_value=0.0,
            max_value=10000.0,
            value=st.session_state.get('max_price', 1000.0),
            step=50.0
        )
    
    with col7:
        limit_results = st.number_input(
            "Limit Results",
            min_value=10,
            max_value=200,
            value=50,
            step=10
        )
    
    # Removed "Scan All Stocks" checkbox - always scan all stocks by default
    # Users can limit results with "Limit Results" filter above
    
    if st.button("🔍 Scan for Opportunities", type="primary", use_container_width=True):
        from utils.yahoo_finance import get_technical_indicators
        from utils.scoring import calculate_csp_readiness_score
        
        symbols_to_scan = stock_universe  # Always scan all stocks
        
        with st.status(f"Scanning {len(symbols_to_scan)} stocks... This may take {len(symbols_to_scan)//2} seconds", expanded=True) as status:
            opportunities = []
            
            progress_bar = st.progress(0)
            
            for idx, symbol in enumerate(symbols_to_scan):
                st.write(f"Processing {symbol}... ({idx+1}/{len(symbols_to_scan)})")
                
                indicators = get_technical_indicators(symbol)
                
                if indicators:
                    score = calculate_csp_readiness_score(indicators)
                    
                    # Apply filters
                    min_avg_volume = st.session_state.get('min_avg_volume', 0)
                    max_spread = st.session_state.get('max_spread', 100.0)
                    max_support_dist = st.session_state.get('max_support_dist', 1000.0)
                    
                    if (score >= min_csp_score and
                        (indicators['rsi'] is None or indicators['rsi'] <= max_rsi) and
                        (indicators['bb_percent'] is None or indicators['bb_percent'] <= max_bb) and
                        (indicators['week_52_percent'] is None or indicators['week_52_percent'] <= max_52w) and
                        min_price <= indicators['current_price'] <= max_price and
                        (indicators.get('avg_volume') is None or indicators.get('avg_volume') >= min_avg_volume) and
                        (indicators.get('bid_ask_spread') is None or indicators.get('bid_ask_spread') <= max_spread) and
                        (indicators.get('support_distance') is None or indicators.get('support_distance') <= max_support_dist)):
                        
                        # Color coding functions
                        def color_rsi(val):
                            if val is None:
                                return "⚪ N/A"
                            if val < 30:
                                return f"🟢 {val:.1f}"
                            elif val <= 70:
                                return f"🟡 {val:.1f}"
                            else:
                                return f"🔴 {val:.1f}"
                        
                        def color_bb(val):
                            if val is None:
                                return "⚪ N/A"
                            if val <= 40:
                                return f"🟢 {val:.1f}%"
                            elif val <= 60:
                                return f"🟡 {val:.1f}%"
                            else:
                                return f"🔴 {val:.1f}%"
                        
                        def color_52w(val):
                            if val is None:
                                return "⚪ N/A"
                            if val <= 40:
                                return f"🟢 {val:.1f}%"
                            elif val <= 60:
                                return f"🟡 {val:.1f}%"
                            else:
                                return f"🔴 {val:.1f}%"
                        
                        def color_score(val):
                            if val >= 70:
                                return f"🟢 {val:.1f}"
                            elif val >= 40:
                                return f"🟡 {val:.1f}"
                            else:
                                return f"🔴 {val:.1f}"
                        
                        # NEW: Color coding for volume
                        def color_volume(val):
                            if val is None:
                                return "⚪ N/A"
                            if val >= 1000000:  # 1M+
                                return f"🟢 {val/1000000:.1f}M"
                            elif val >= 500000:  # 500K+
                                return f"🟡 {val/1000:.0f}K"
                            else:
                                return f"🔴 {val/1000:.0f}K"
                        
                        # NEW: Color coding for bid-ask spread
                        def color_spread(val):
                            if val is None:
                                return "⚪ N/A"
                            if val <= 1.0:  # ≤1% spread
                                return f"🟢 {val:.2f}%"
                            elif val <= 3.0:  # 1-3% spread
                                return f"🟡 {val:.2f}%"
                            else:  # >3% spread
                                return f"🔴 {val:.2f}%"
                        
                        # NEW: Color coding for support distance
                        def color_support(val):
                            if val is None:
                                return "⚪ N/A"
                            if val <= 10:  # Within 10% of support
                                return f"🟢 {val:.1f}%"
                            elif val <= 25:  # 10-25% above support
                                return f"🟡 {val:.1f}%"
                            else:  # >25% above support
                                return f"🔴 {val:.1f}%"
                        
                        opportunities.append({
                            'Select': False,
                            'Symbol': symbol,
                            'Price': f"${indicators['current_price']:.2f}",
                            'CSP Score': color_score(score),
                            'RSI': color_rsi(indicators['rsi']),
                            'BB %': color_bb(indicators['bb_percent']),
                            '52W %': color_52w(indicators['week_52_percent']),
                            'MA %': f"{indicators['ma_percent']:.1f}" if indicators['ma_percent'] else "N/A",
                            'Avg Vol': color_volume(indicators.get('avg_volume')),  # NEW
                            'Spread %': color_spread(indicators.get('bid_ask_spread')),  # NEW
                            'Support %': color_support(indicators.get('support_distance')),  # NEW
                            '_score_raw': score,
                            '_symbol_raw': symbol,
                            '_avg_volume_raw': indicators.get('avg_volume'),  # NEW - for filtering
                            '_spread_raw': indicators.get('bid_ask_spread'),  # NEW - for filtering
                            '_support_raw': indicators.get('support_distance'),  # NEW - for filtering
                        })
                
                progress_bar.progress((idx + 1) / len(symbols_to_scan))
            
            status.update(label=f"✅ Scan complete!", state="complete")
        
        if opportunities:
            # Sort by score
            opportunities.sort(key=lambda x: x['_score_raw'], reverse=True)
            
            # Limit results
            opportunities = opportunities[:limit_results]
            
            # STORE IN SESSION STATE IMMEDIATELY
            st.session_state.scan_results = pd.DataFrame(opportunities)
            st.session_state.has_results = True
            
            st.rerun()
        else:
            st.warning("⚠️ No opportunities found matching your criteria")
            st.info("💡 Try using the 'Aggressive' preset or lowering the filter values")
    
    # Display results if they exist in session state
    if st.session_state.get('has_results', False) and 'scan_results' in st.session_state:
        df = st.session_state.scan_results
        
        st.success(f"✅ Found {len(df)} opportunities!")
        
        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Found", len(df))
        with col2:
            avg_score = df['_score_raw'].mean()
            st.metric("Avg Score", f"{avg_score:.1f}")
        with col3:
            max_score = df['_score_raw'].max()
            st.metric("Max Score", f"{max_score:.1f}")
        with col4:
            high_score_count = (df['_score_raw'] >= 70).sum()
            st.metric("High Score (≥70)", high_score_count)
        
        # CSP Score Explanation
        with st.expander("📊 CSP Score Explanation & Legend"):
            st.markdown("""
            ### CSP Readiness Score Formula
            
            **Score = (RSI Score × 40%) + (BB% Score × 30%) + (52W% Score × 30%)**
            
            #### Component Scoring:
            
            **RSI (40% weight - Most Important)**
            - 100 pts: RSI < 30 (Deeply oversold - BEST)
            - 80 pts: RSI 30-35 (Oversold)
            - 60 pts: RSI 35-40 (Slightly oversold)
            - 40 pts: RSI 40-50 (Neutral)
            - 20 pts: RSI 50-70 (Neutral to overbought)
            - 0 pts: RSI > 70 (Overbought - AVOID)
            
            **Bollinger Band % (30% weight)**
            - 100 pts: BB% 0-20% (Very near lower band - BEST)
            - 80 pts: BB% 20-30% (Near lower band)
            - 60 pts: BB% 30-40% (Below middle)
            - 40 pts: BB% 40-50% (Middle range)
            - 20 pts: BB% 50-60% (Above middle)
            - 0 pts: BB% > 60% (Near upper band - AVOID)
            
            **52-Week % (30% weight)**
            - 100 pts: 52W% 0-20% (Near 52-week lows - BEST)
            - 80 pts: 52W% 20-30% (Below average)
            - 60 pts: 52W% 30-40% (Lower range)
            - 40 pts: 52W% 40-50% (Middle range)
            - 20 pts: 52W% 50-60% (Upper range)
            - 0 pts: 52W% > 60% (Near 52-week highs - AVOID)
            
            #### Color Legend:
            - 🟢 Green = Good for CSP (oversold, near lows, lower band)
            - 🟡 Yellow = Neutral/Medium
            - 🔴 Red = Avoid for CSP (overbought, near highs, upper band)
            """)
        
        # Selection controls
        st.subheader("📋 Select Stocks for Watchlist")
        
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
        
        with col1:
            if st.button("✅ Select All", use_container_width=True):
                st.session_state.scan_results['Select'] = True
                st.rerun()
        
        with col2:
            if st.button("❌ Clear Selection", use_container_width=True):
                st.session_state.scan_results['Select'] = False
                st.rerun()
        
        with col3:
            selected_count = st.session_state.scan_results['Select'].sum()
            st.metric("Selected", selected_count)
        
        # Display editable table
        edited_df = st.data_editor(
            st.session_state.scan_results,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select stocks to add to watchlist",
                    default=False,
                ),
                "Symbol": st.column_config.TextColumn("Symbol", disabled=True),
                "Price": st.column_config.TextColumn("Price", disabled=True),
                "CSP Score": st.column_config.TextColumn("↓ CSP Score", disabled=True),
                "RSI": st.column_config.TextColumn("RSI", disabled=True),
                "BB %": st.column_config.TextColumn("BB %", disabled=True),
                "52W %": st.column_config.TextColumn("52W %", disabled=True),
                "MA %": st.column_config.TextColumn("MA %", disabled=True),
                "Avg Vol": st.column_config.TextColumn("Avg Vol", disabled=True),  # NEW
                "Spread %": st.column_config.TextColumn("Spread %", disabled=True),  # NEW
                "Support %": st.column_config.TextColumn("Support %", disabled=True),  # NEW
                "_score_raw": None,  # Hide
                "_symbol_raw": None,  # Hide
                "_avg_volume_raw": None,  # NEW - Hide
                "_spread_raw": None,  # NEW - Hide
                "_support_raw": None,  # NEW - Hide
            },
            disabled=["Symbol", "Price", "CSP Score", "RSI", "BB %", "52W %", "MA %", "Avg Vol", "Spread %", "Support %"],
            hide_index=True,
            use_container_width=True,
            height=600,
            key="stock_selector"
        )
        
        # Update session state with manual checkbox changes
        st.session_state.scan_results = edited_df
        
        # Add to watchlist section
        st.divider()
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            selected_rows = edited_df[edited_df['Select'] == True]
            selected_count = len(selected_rows)
            
            if st.button(
                f"➕ Add {selected_count} to Watchlist" if selected_count > 0 else "➕ Add to Watchlist",
                disabled=selected_count == 0,
                type="primary",
                use_container_width=True
            ):
                # Read current watchlist
                try:
                    with open('watchlist.txt', 'r') as f:
                        current_watchlist = set(line.strip() for line in f if line.strip())
                except:
                    current_watchlist = set()
                
                # Add selected symbols
                new_symbols = selected_rows['_symbol_raw'].tolist()
                updated_watchlist = current_watchlist.union(set(new_symbols))
                
                # Write back
                with open('watchlist.txt', 'w') as f:
                    for symbol in sorted(updated_watchlist):
                        f.write(f"{symbol}\n")
                
                new_count = len(updated_watchlist) - len(current_watchlist)
                st.success(f"✅ Added {new_count} new symbols to watchlist! Total: {len(updated_watchlist)}")
                st.balloons()
                
                # Clear selections after adding
                st.session_state.scan_results['Select'] = False
                st.rerun()
        
        with col2:
            # Download CSV
            csv = df.drop(columns=['Select', '_score_raw', '_symbol_raw']).to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"stock_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

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
    
    # Watchlist Management Section
    st.subheader("📝 Watchlist Management")
    
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
                    
                    # Calculate spread percentage
                    mid = (bid + ask) / 2
                    spread_pct = ((ask - bid) / mid * 100) if mid > 0 else 999
                    
                    opp = {
                        'Symbol': symbol,
                        'Strike': strike,
                        'Current Price': underlying_price,
                        'Expiration': expiration,
                        'DTE': dte,
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
        
        # Format IV Rank and Spread % with colored emoji indicators (like CC Dashboard)
        display_df = st.session_state.csp_opportunities.copy()
        
        # Format IV Rank with emoji indicators
        def format_iv_rank(val):
            if val is None or (isinstance(val, float) and val != val):  # Check for None or NaN
                return "N/A"
            if val > 75:
                return f"🟢 {val:.0f}%"  # Green = High IV (good for selling)
            elif val < 25:
                return f"🔴 {val:.0f}%"  # Red = Low IV (bad for selling)
            else:
                return f"🟡 {val:.0f}%"  # Yellow = Medium IV
        
        # Format Spread % with emoji indicators
        def format_spread(val):
            if val is None or (isinstance(val, float) and val != val):  # Check for None or NaN
                return "N/A"
            if val <= 1.0:  # ≤1% spread
                return f"🟢 {val:.1f}%"  # Green = Tight spread (good)
            elif val <= 3.0:  # 1-3% spread
                return f"🟡 {val:.1f}%"  # Yellow = Medium spread
            else:  # >3% spread
                return f"🔴 {val:.1f}%"  # Red = Wide spread (bad)
        
        # Apply formatting to display columns
        if 'IV Rank' in display_df.columns:
            display_df['IV Rank'] = display_df['IV Rank'].apply(format_iv_rank)
        if 'Spread %' in display_df.columns:
            display_df['Spread %'] = display_df['Spread %'].apply(format_spread)
        
        # Display editable table (but encourage using buttons instead of editing cells)
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
            disabled=[col for col in st.session_state.csp_opportunities.columns if col not in ['Select', 'Qty']],
            hide_index=True,
            use_container_width=True,
            height=600,
            key="csp_selector"
        )
        
        # Update session state
        st.session_state.csp_opportunities = edited_df
        
        st.divider()
        
        # Order Summary Card
        selected_rows = edited_df[edited_df['Select'] == True]
        
        if len(selected_rows) > 0:
            st.subheader("💰 Order Summary")
            
            # Calculate totals accounting for quantities
            total_contracts = selected_rows['Qty'].sum()
            total_premium = (selected_rows['Bid'] * selected_rows['Qty'] * 100).sum()  # Each contract = 100 shares
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
                order_details = selected_rows[['Symbol', 'Qty', 'Strike', 'Expiration', 'DTE', 'Bid', 'Premium %', 'Weekly %', 'Delta']]
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
                                    option_symbol = f"{row['Symbol']}{exp_date.strftime('%y%m%d')}P{int(row['Strike']*1000):08d}"
                                    qty = int(row['Qty'])  # Get quantity from row
                                    
                                    if dry_run:
                                        # DRY RUN - Just simulate
                                        st.write(f"🧪 [DRY RUN] Would submit: {qty}x {option_symbol} @ ${row['Bid']:.2f}")
                                        success_count += 1
                                    else:
                                        # LIVE - Actually submit
                                        result = api.submit_csp_order(
                                            account_number=selected_account,
                                            symbol=option_symbol,
                                            quantity=qty,  # Use quantity from row
                                            price=row['Bid']
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
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📞 Covered Calls Dashboard")
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
        
        # Position Breakdown Metrics
        st.write("### 📊 Position Summary")
        
        # Calculate total eligible contracts (shares / 100)
        total_eligible_contracts = sum([h.get('max_contracts', 0) for h in holdings])
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Positions", breakdown.get('total_positions', 0))
        with col2:
            st.metric("Stock Positions", breakdown.get('stock_positions', 0))
        with col3:
            st.metric("Existing Calls", breakdown.get('existing_calls', 0))
        with col4:
            st.metric("Eligible for CC", breakdown.get('eligible_positions', 0))
        with col5:
            st.metric("💼 Eligible Contracts", total_eligible_contracts)
        
        st.write("")
        
        # Show friendly message if account has no stock positions
        if breakdown.get('stock_positions', 0) == 0:
            st.info("📊 This account has no stock positions. Stock positions are required to write covered calls.")
            st.stop()
        

        # TABLE 2: Eligible Positions (Selectable)
        if holdings:
            st.write("### ✅ Table 2: Eligible Positions for New Covered Calls")
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
            display_opp = opp_df[['Select', 'Qty', 'symbol', 'strike', 'expiration', 'dte', 'delta', 'premium', 'weekly_return_pct', 'rsi', 'iv_rank', 'spread_pct', 'open_interest', 'volume', 'max_contracts']].copy()
            
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
            display_opp.columns = ['Select', 'Qty', 'Symbol', 'Strike', 'Expiration', 'DTE', 'Delta', 'Premium', 'Weekly %', 'RSI', 'IV Rank', 'Spread %', 'OI', 'Volume', 'max_contracts', 'Available', 'Available_Display']
            
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
            
            # Apply formatting
            display_opp['Strike'] = display_opp['Strike'].apply(lambda x: f"${x:.2f}")
            display_opp['Delta'] = display_opp['Delta'].apply(lambda x: f"{x:.3f}")
            display_opp['Premium'] = display_opp['Premium'].apply(lambda x: f"${x:.2f}")
            display_opp['Weekly %'] = display_opp['Weekly %'].apply(lambda x: f"{x:.2f}%")
            display_opp['RSI'] = display_opp['RSI'].apply(format_rsi)
            display_opp['IV Rank'] = display_opp['IV Rank'].apply(format_iv_rank)
            display_opp['Spread %'] = display_opp['Spread %'].apply(format_spread)
            
            # Reorder columns to put Available after Qty (use display version with emoji)
            display_opp = display_opp[['Select', 'Qty', 'Available_Display', 'Symbol', 'Strike', 'Expiration', 'DTE', 'Delta', 'Premium', 'Weekly %', 'RSI', 'IV Rank', 'Spread %', 'OI', 'Volume']]
            
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
    st.title("📊 Performance Dashboard")
    
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