"""
Working Orders Monitor - View and manage unfilled orders with smart fill prices

Enhanced features:
- Smart fill price suggestions based on spread width and time working
- Auto-refresh capability
- Auto-replace mode for hands-off order management
- Cancel and replace in single action
"""

import streamlit as st
import pandas as pd
from datetime import datetime, time as dt_time
import pytz
import time


def is_market_open():
    """Check if the US stock market is currently open"""
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    
    # Check if it's a weekday (Monday=0, Sunday=6)
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Market hours: 9:30 AM - 4:00 PM ET
    market_open = dt_time(9, 30)
    market_close = dt_time(16, 0)
    current_time = now.time()
    
    return market_open <= current_time <= market_close


def is_safe_to_replace():
    """Check if it's safe to replace orders (not too close to market close)"""
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    
    # Don't replace after 3:55 PM ET
    cutoff = dt_time(15, 55)
    
    return is_market_open() and now.time() < cutoff


def get_market_status():
    """Get current market status as a string"""
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    
    if now.weekday() >= 5:
        return "🔴 Market Closed (Weekend)"
    
    current_time = now.time()
    market_open = dt_time(9, 30)
    market_close = dt_time(16, 0)
    
    if current_time < market_open:
        return f"🟡 Pre-Market (Opens 9:30 AM ET)"
    elif current_time > market_close:
        return "🔴 Market Closed (After Hours)"
    elif current_time > dt_time(15, 55):
        return "🟠 Market Closing Soon"
    else:
        return "🟢 Market Open"


def calculate_suggested_price(bid, ask, current_price=None, time_working_minutes=0):
    """
    Calculate a suggested fill price based on spread width and time working
    
    Returns:
        dict with suggested_price, strategy, and explanation
    """
    if bid is None or ask is None or bid <= 0 or ask <= 0:
        return {
            'suggested_price': None,
            'strategy': 'unknown',
            'explanation': 'Unable to calculate - missing bid/ask data'
        }
    
    spread = ask - bid
    mid = (bid + ask) / 2
    
    # Determine strategy based on spread width
    if spread <= 0.05:
        suggested = mid
        strategy = 'mid'
        explanation = f'Tight spread (${spread:.2f}) - using mid'
    elif spread <= 0.15:
        suggested = mid - 0.01
        strategy = 'mid-1¢'
        explanation = f'Medium spread (${spread:.2f}) - mid - $0.01'
    elif spread <= 0.30:
        suggested = bid + (spread * 0.60)
        strategy = '60%'
        explanation = f'Wide spread (${spread:.2f}) - 60% of spread'
    else:
        suggested = bid + (spread * 0.50)
        strategy = '50%'
        explanation = f'Very wide (${spread:.2f}) - 50% of spread'
    
    # Adjust for time working
    if time_working_minutes > 60:
        adjustment = min(0.03, spread * 0.10)
        suggested = max(bid + 0.01, suggested - adjustment)
        strategy += '+time'
    elif time_working_minutes > 30:
        adjustment = min(0.02, spread * 0.05)
        suggested = max(bid + 0.01, suggested - adjustment)
        strategy += '+time'
    
    suggested = round(suggested, 2)
    
    if suggested < bid:
        suggested = bid
    
    return {
        'suggested_price': suggested,
        'strategy': strategy,
        'explanation': explanation,
        'bid': bid,
        'ask': ask,
        'mid': round(mid, 2),
        'spread': round(spread, 2)
    }


def format_time_working(minutes):
    """Format time working as human-readable string"""
    if minutes < 1:
        return "Just now"
    elif minutes < 60:
        return f"{minutes}m"
    elif minutes < 1440:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"
    else:
        days = minutes // 1440
        hours = (minutes % 1440) // 60
        return f"{days}d {hours}h"


def render_working_orders_dashboard(api, account_number):
    """
    Render the enhanced Working Orders Dashboard with smart fill prices and auto-replace
    
    Args:
        api: TastytradeAPI instance
        account_number: Account number to fetch orders from
    """
    st.header("📋 Working Orders Dashboard")
    
    # Market status
    market_status = get_market_status()
    st.caption(f"Market Status: {market_status}")
    
    # Initialize session state
    if 'working_orders_data' not in st.session_state:
        st.session_state.working_orders_data = None
    if 'auto_replace_enabled' not in st.session_state:
        st.session_state.auto_replace_enabled = False
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None
    if 'replacement_counts' not in st.session_state:
        st.session_state.replacement_counts = {}  # Track replacements per order
    if 'auto_replace_log' not in st.session_state:
        st.session_state.auto_replace_log = []
    if 'working_orders_selected' not in st.session_state:
        st.session_state.working_orders_selected = set()  # Track selected order IDs
    if 'aggressive_fill_enabled' not in st.session_state:
        st.session_state.aggressive_fill_enabled = False
    
    # Control panel
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("🔄 Refresh Orders", use_container_width=True):
            st.session_state.working_orders_data = None
            st.rerun()
    
    with col2:
        auto_refresh = st.checkbox("⏱️ Auto-Refresh (60s)", value=False)
    
    with col3:
        if is_safe_to_replace():
            auto_replace = st.checkbox("🤖 Auto-Replace Mode", value=st.session_state.auto_replace_enabled)
            st.session_state.auto_replace_enabled = auto_replace
        else:
            st.checkbox("🤖 Auto-Replace Mode", value=False, disabled=True, help="Disabled - market closed or closing soon")
            st.session_state.auto_replace_enabled = False
    
    with col4:
        if st.session_state.last_refresh:
            st.caption(f"Last: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    # Second row of controls - Aggressive Fill Mode
    col_agg1, col_agg2 = st.columns([1, 3])
    with col_agg1:
        aggressive_fill = st.checkbox(
            "🚀 Aggressive Fill Mode", 
            value=st.session_state.aggressive_fill_enabled,
            help="Lower suggested prices to prioritize getting filled over best price"
        )
        st.session_state.aggressive_fill_enabled = aggressive_fill
    
    if st.session_state.aggressive_fill_enabled:
        with col_agg2:
            st.info("💨 Aggressive mode: Prices lowered by $0.01-0.02 to help orders fill faster")
    
    # Auto-replace warning/confirmation
    if st.session_state.auto_replace_enabled:
        st.warning("""
        ⚠️ **Auto-Replace Mode Active**
        - Orders will be replaced at suggested prices every 30 minutes
        - Stops at 3:55 PM ET or when all orders fill
        - Orders replaced 5+ times will be flagged for manual review
        """)
    
    # Fetch orders
    try:
        orders = api.get_live_orders(account_number)
        st.session_state.last_refresh = datetime.now()
        
        if not orders or len(orders) == 0:
            st.success("✅ No working orders - all orders have been filled or canceled!")
            return
        
        # Filter to only Live orders
        live_orders = [o for o in orders if o.get('status') == 'Live']
        
        if not live_orders:
            st.success("✅ No working orders - all orders have been filled or canceled!")
            return
        
        # Get quotes for all options
        option_symbols = []
        for order in live_orders:
            legs = order.get('legs', [])
            if legs:
                symbol = legs[0].get('symbol', '')
                if symbol:
                    option_symbols.append(symbol)
        
        # Fetch quotes using the tastytrade SDK
        quotes = {}
        if option_symbols:
            with st.spinner(f"Fetching quotes for {len(option_symbols)} options..."):
                try:
                    # Debug: show the symbols being requested
                    with st.expander("🔧 Debug: Option Symbols", expanded=False):
                        st.write(f"Requesting quotes for {len(option_symbols)} symbols:")
                        for sym in option_symbols[:6]:  # Show all symbols
                            st.code(f"'{sym}' (len={len(sym)})")
                        if len(option_symbols) > 6:
                            st.write(f"... and {len(option_symbols) - 6} more")
                    
                    # Try the SDK method first (more reliable)
                    try:
                        from utils.tastytrade_quotes import get_option_quotes_sdk
                        # SDK function now shows its own debug info
                        quotes = get_option_quotes_sdk(option_symbols, show_debug=True)
                        if quotes:
                            st.success(f"✅ Fetched quotes for {len(quotes)} options via SDK")
                    except ImportError as ie:
                        st.warning(f"SDK import failed: {ie}")
                        st.info("Falling back to direct API method...")
                        quotes = api.get_option_quotes_batch(option_symbols)
                    except Exception as sdk_error:
                        st.warning(f"SDK error: {sdk_error}")
                        st.info("Falling back to direct API method...")
                        quotes = api.get_option_quotes_batch(option_symbols)
                    
                    # Debug: show how many quotes were fetched
                    if len(quotes) == 0:
                        st.warning(f"No quotes returned for {len(option_symbols)} option symbols")
                        st.info("👆 Expand 'SDK Debug Info' above to see what happened")
                    elif len(quotes) < len(option_symbols):
                        st.info(f"Fetched quotes for {len(quotes)}/{len(option_symbols)} options")
                        
                except Exception as e:
                    st.warning(f"Could not fetch option quotes: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
        
        # Build display data
        order_data = []
        for order in live_orders:
            try:
                order_id = order.get('id', 'N/A')
                current_price = float(order.get('price', 0))
                time_in_force = order.get('time-in-force', 'Day')
                
                legs = order.get('legs', [])
                if not legs:
                    continue
                
                leg = legs[0]
                symbol = leg.get('symbol', '')
                quantity = int(leg.get('quantity', 0))
                action = leg.get('action', '')
                
                # Parse option symbol
                underlying = symbol[:6].strip() if len(symbol) > 6 else symbol
                
                # Determine option type
                import re
                match = re.search(r'\d{6}([PC])\d{8}', symbol)
                option_type = ''
                strike = 0
                expiration = ''
                
                if match:
                    option_char = match.group(1)
                    option_type = 'PUT' if option_char == 'P' else 'CALL'
                    
                    # Parse strike and expiration
                    try:
                        date_part = symbol[6:12]
                        strike_part = symbol[13:]
                        exp_year = int('20' + date_part[:2])
                        exp_month = int(date_part[2:4])
                        exp_day = int(date_part[4:6])
                        expiration = f"{exp_month}/{exp_day}"
                        strike = float(strike_part) / 1000
                    except:
                        pass
                
                # Calculate time working
                received_at = order.get('received-at', '')
                time_working_minutes = 0
                if received_at:
                    try:
                        received_dt = datetime.fromisoformat(received_at.replace('Z', '+00:00'))
                        now = datetime.now(pytz.UTC)
                        time_working_minutes = int((now - received_dt).total_seconds() / 60)
                    except:
                        pass
                
                # Get quote data
                quote = quotes.get(symbol, {})
                bid = float(quote.get('bid', 0)) if quote else 0
                ask = float(quote.get('ask', 0)) if quote else 0
                
                # Calculate suggested price
                price_calc = calculate_suggested_price(bid, ask, current_price, time_working_minutes)
                suggested_price = price_calc.get('suggested_price', current_price)
                strategy = price_calc.get('strategy', '-')
                mid = price_calc.get('mid', 0)
                spread = price_calc.get('spread', 0)
                
                # Apply aggressive fill adjustment if enabled
                if st.session_state.aggressive_fill_enabled and suggested_price and bid > 0:
                    # For orders working > 2 hours, go straight to ask
                    if time_working_minutes > 120:
                        aggressive_price = ask if ask > 0 else suggested_price
                        strategy = 'ask (aggressive)'
                    # For orders working > 1 hour, subtract $0.02
                    elif time_working_minutes > 60:
                        aggressive_price = max(bid, suggested_price - 0.02)
                        strategy = strategy + ' -$0.02'
                    # Otherwise subtract $0.01
                    else:
                        aggressive_price = max(bid, suggested_price - 0.01)
                        strategy = strategy + ' -$0.01'
                    
                    suggested_price = round(aggressive_price, 2)
                
                # Check replacement count
                replacement_count = st.session_state.replacement_counts.get(order_id, 0)
                needs_review = replacement_count >= 5
                
                # Determine if replacement is needed
                price_diff = abs(current_price - suggested_price) if suggested_price else 0
                needs_replacement = price_diff >= 0.01 and not needs_review
                
                # Check if this order was previously selected
                is_selected = order_id in st.session_state.working_orders_selected
                
                order_data.append({
                    'order_id': order_id,
                    'Select': is_selected,
                    'Symbol': underlying,
                    'Strike': strike,
                    'Exp': expiration,
                    'Type': option_type,
                    'Qty': quantity,
                    'Current': current_price,
                    'Bid': bid,
                    'Ask': ask,
                    'Mid': mid,
                    'Spread': spread,
                    'Suggested': suggested_price,
                    'Strategy': strategy,
                    'Time Working': format_time_working(time_working_minutes),
                    'time_minutes': time_working_minutes,
                    'TIF': time_in_force,
                    'Replacements': replacement_count,
                    'Needs Review': needs_review,
                    'Needs Replace': needs_replacement,
                    'full_symbol': symbol,
                    'raw_order': order
                })
                
            except Exception as e:
                st.warning(f"Error parsing order: {str(e)}")
                continue
        
        if not order_data:
            st.success("✅ No working orders to display!")
            return
        
        # Create DataFrame
        df = pd.DataFrame(order_data)
        
        # Summary metrics
        st.write("")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Working Orders", len(df))
        with col2:
            st.metric("Total Contracts", df['Qty'].sum())
        with col3:
            needs_replace = df['Needs Replace'].sum()
            st.metric("Need Replacement", int(needs_replace))
        with col4:
            needs_review = df['Needs Review'].sum()
            if needs_review > 0:
                st.metric("⚠️ Need Review", int(needs_review))
            else:
                st.metric("Need Review", 0)
        with col5:
            avg_time = df['time_minutes'].mean()
            st.metric("Avg Time Working", format_time_working(int(avg_time)))
        
        st.write("")
        
        # Display orders needing review
        review_orders = df[df['Needs Review'] == True]
        if len(review_orders) > 0:
            st.error(f"⚠️ {len(review_orders)} order(s) have been replaced 5+ times and need manual review:")
            for _, row in review_orders.iterrows():
                st.write(f"  • {row['Symbol']} ${row['Strike']} {row['Type']} - {row['Replacements']} replacements")
        
        # Display table
        display_cols = ['Select', 'Symbol', 'Strike', 'Exp', 'Type', 'Qty', 'Current', 'Bid', 'Mid', 'Ask', 'Suggested', 'Strategy', 'Time Working', 'TIF']
        display_df = df[display_cols].copy()
        
        # Format currency columns
        for col in ['Current', 'Bid', 'Mid', 'Ask', 'Suggested']:
            display_df[col] = display_df[col].apply(lambda x: f"${x:.2f}" if x else "-")
        
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", default=False),
                "Strike": st.column_config.NumberColumn("Strike", format="$%.0f"),
            },
            key="working_orders_table"
        )
        
        # Update selections and persist to session state
        df['Select'] = edited_df['Select']
        
        # Sync selections to session state
        new_selected = set()
        for idx, row in df.iterrows():
            if row['Select']:
                new_selected.add(row['order_id'])
        st.session_state.working_orders_selected = new_selected
        
        selected = df[df['Select'] == True]
        
        # Action buttons
        st.write("")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✅ Select All", use_container_width=True):
                # Add all order IDs to selected set
                for idx, row in df.iterrows():
                    st.session_state.working_orders_selected.add(row['order_id'])
                st.rerun()
        
        with col2:
            if st.button("⬜ Deselect All", use_container_width=True):
                st.session_state.working_orders_selected = set()
                st.rerun()
        
        with col3:
            replace_all_btn = st.button(
                f"🔄 Replace All to Suggested ({int(df['Needs Replace'].sum())})",
                use_container_width=True,
                type="primary",
                disabled=df['Needs Replace'].sum() == 0
            )
        
        with col4:
            if len(selected) > 0:
                cancel_btn = st.button(f"❌ Cancel Selected ({len(selected)})", use_container_width=True)
            else:
                st.button("❌ Cancel Selected (0)", use_container_width=True, disabled=True)
        
        # Handle Replace All
        if replace_all_btn:
            orders_to_replace = df[df['Needs Replace'] == True]
            if len(orders_to_replace) > 0:
                with st.spinner(f"Replacing {len(orders_to_replace)} orders..."):
                    success_count = 0
                    failed_count = 0
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, (idx, row) in enumerate(orders_to_replace.iterrows()):
                        progress_bar.progress((i + 1) / len(orders_to_replace))
                        status_text.text(f"Replacing {row['Symbol']} ${row['Strike']}...")
                        
                        try:
                            result = api.cancel_replace_order(
                                account_number,
                                row['order_id'],
                                row['Suggested'],
                                row['raw_order']
                            )
                            
                            if result.get('success'):
                                success_count += 1
                                # Increment replacement count
                                st.session_state.replacement_counts[row['order_id']] = row['Replacements'] + 1
                                st.session_state.auto_replace_log.append({
                                    'time': datetime.now().strftime('%H:%M:%S'),
                                    'symbol': row['Symbol'],
                                    'old_price': row['Current'],
                                    'new_price': row['Suggested'],
                                    'status': 'Success'
                                })
                            else:
                                failed_count += 1
                                st.session_state.auto_replace_log.append({
                                    'time': datetime.now().strftime('%H:%M:%S'),
                                    'symbol': row['Symbol'],
                                    'old_price': row['Current'],
                                    'new_price': row['Suggested'],
                                    'status': f"Failed: {result.get('message', 'Unknown')}"
                                })
                        except Exception as e:
                            failed_count += 1
                        
                        time.sleep(0.5)  # Rate limit buffer
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    if success_count > 0:
                        st.success(f"✅ Replaced {success_count} order(s) successfully!")
                    if failed_count > 0:
                        st.warning(f"⚠️ {failed_count} order(s) failed to replace")
                    
                    time.sleep(1)
                    st.rerun()
        
        # Handle Cancel Selected
        if len(selected) > 0 and 'cancel_btn' in dir() and cancel_btn:
            with st.spinner(f"Canceling {len(selected)} orders..."):
                success_count = 0
                for idx, row in selected.iterrows():
                    try:
                        result = api.cancel_order(account_number, row['order_id'])
                        if result:
                            success_count += 1
                    except:
                        pass
                
                if success_count > 0:
                    st.success(f"✅ Canceled {success_count} order(s)")
                    time.sleep(1)
                    st.rerun()
        
        # Replacement log
        if st.session_state.auto_replace_log:
            with st.expander("📜 Replacement Log"):
                log_df = pd.DataFrame(st.session_state.auto_replace_log[-20:])  # Last 20 entries
                st.dataframe(log_df, use_container_width=True, hide_index=True)
                if st.button("Clear Log"):
                    st.session_state.auto_replace_log = []
                    st.rerun()
        
        # Auto-refresh logic
        if auto_refresh:
            time.sleep(60)
            st.rerun()
        
    except Exception as e:
        st.error(f"Error fetching orders: {str(e)}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())


# Legacy function for backward compatibility
def render_working_orders_monitor(api, account_number, order_type='all'):
    """Legacy wrapper - redirects to new dashboard"""
    render_working_orders_dashboard(api, account_number)
