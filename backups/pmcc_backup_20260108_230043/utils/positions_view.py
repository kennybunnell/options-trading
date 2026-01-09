"""
Positions View - Mirrors Tastytrade's positions table
Shows all positions (stocks, options, CSPs, CCs) in a comprehensive table
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import re


def parse_option_symbol(symbol: str) -> dict:
    """Parse OCC option symbol to extract components"""
    try:
        clean_symbol = symbol.replace(' ', '')
        match = re.match(r'([A-Z]+)(\d{6})([CP])(\d+)', clean_symbol)
        if match:
            underlying = match.group(1)
            date_str = match.group(2)
            option_type = 'CALL' if match.group(3) == 'C' else 'PUT'
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
        return (exp_date - datetime.now()).days
    except:
        return 0


def render_positions_view(api, selected_account):
    """
    Render comprehensive positions view mirroring Tastytrade
    Shows all positions: stocks, options, CSPs, CCs
    """
    
    st.header("📊 All Positions")
    
    # Refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh", type="primary", key="refresh_positions_view"):
            st.rerun()
    
    # Fetch positions
    with st.spinner("Loading positions..."):
        positions = api.get_positions(selected_account)
    
    if not positions:
        st.info("No positions found")
        return
    
    # Process positions
    position_data = []
    
    for pos in positions:
        instrument_type = pos.get('instrument-type', '')
        symbol = pos.get('symbol', '')
        quantity = float(pos.get('quantity', 0))
        quantity_direction = pos.get('quantity-direction', '')
        
        # Determine if short
        is_short = quantity_direction.lower() == 'short' if quantity_direction else quantity < 0
        
        # Common fields
        avg_price = float(pos.get('average-open-price', 0))
        mark = float(pos.get('mark', 0))
        mark_price = float(pos.get('mark-price', 0))
        current_price = mark if mark != 0 else mark_price
        
        if instrument_type == 'Equity':
            # Stock position
            qty = int(quantity)
            cost_basis = avg_price * abs(qty)
            market_value = current_price * abs(qty)
            pl = market_value - cost_basis
            pl_pct = (pl / cost_basis * 100) if cost_basis != 0 else 0
            
            position_data.append({
                'Type': 'Stock',
                'Symbol': symbol,
                'Qty': qty,
                'Avg Price': avg_price,
                'Current': current_price,
                'Cost Basis': cost_basis,
                'Market Value': market_value,
                'P/L': pl,
                'P/L %': pl_pct,
                'Strike': None,
                'Exp': None,
                'DTE': None,
                'Option Type': None,
                'Direction': 'Long' if qty > 0 else 'Short'
            })
        
        elif instrument_type == 'Equity Option':
            # Option position
            parsed = parse_option_symbol(symbol)
            if not parsed:
                continue
            
            multiplier = int(float(pos.get('multiplier', 100)))
            qty = int(abs(quantity))
            
            # For short options (sold), avg_price is premium received (positive)
            # For long options (bought), avg_price is premium paid (positive)
            # Current price is what it would cost to close
            
            if is_short:
                # Short option (sold): we received premium
                premium_received = avg_price * qty * multiplier
                cost_to_close = current_price * qty * multiplier
                pl = premium_received - cost_to_close
                pl_pct = (pl / premium_received * 100) if premium_received != 0 else 0
                direction = 'Short'
            else:
                # Long option (bought): we paid premium
                premium_paid = avg_price * qty * multiplier
                current_value = current_price * qty * multiplier
                pl = current_value - premium_paid
                pl_pct = (pl / premium_paid * 100) if premium_paid != 0 else 0
                direction = 'Long'
            
            dte = calculate_dte(parsed['expiration'])
            
            # Determine strategy
            if is_short and parsed['option_type'] == 'PUT':
                strategy = 'CSP'
            elif is_short and parsed['option_type'] == 'CALL':
                strategy = 'CC'
            else:
                strategy = parsed['option_type']
            
            position_data.append({
                'Type': strategy,
                'Symbol': parsed['underlying'],
                'Qty': qty if not is_short else -qty,
                'Avg Price': avg_price,
                'Current': current_price,
                'Cost Basis': premium_received if is_short else premium_paid,
                'Market Value': cost_to_close if is_short else current_value,
                'P/L': pl,
                'P/L %': pl_pct,
                'Strike': parsed['strike'],
                'Exp': parsed['expiration'],
                'DTE': dte,
                'Option Type': parsed['option_type'],
                'Direction': direction
            })
    
    if not position_data:
        st.info("No positions to display")
        return
    
    # Create DataFrame
    df = pd.DataFrame(position_data)
    
    # Sort by Type (Stock, CSP, CC, etc.)
    type_order = {'Stock': 1, 'CSP': 2, 'CC': 3, 'PUT': 4, 'CALL': 5}
    df['sort_order'] = df['Type'].map(type_order)
    df = df.sort_values(['sort_order', 'Symbol']).drop('sort_order', axis=1)
    
    # Summary metrics
    total_positions = len(df)
    stock_positions = len(df[df['Type'] == 'Stock'])
    csp_positions = len(df[df['Type'] == 'CSP'])
    cc_positions = len(df[df['Type'] == 'CC'])
    total_pl = df['P/L'].sum()
    
    # Display summary
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Positions", total_positions)
    with col2:
        st.metric("Stocks", stock_positions)
    with col3:
        st.metric("CSPs", csp_positions)
    with col4:
        st.metric("CCs", cc_positions)
    with col5:
        delta_color = "normal" if total_pl >= 0 else "inverse"
        st.metric("Total P/L", f"${total_pl:,.2f}", delta=f"{total_pl:+,.2f}")
    
    st.write("")
    
    # Filter options
    with st.expander("🔍 Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_type = st.multiselect(
                "Position Type",
                options=['Stock', 'CSP', 'CC', 'PUT', 'CALL'],
                default=['Stock', 'CSP', 'CC', 'PUT', 'CALL']
            )
        with col2:
            filter_direction = st.multiselect(
                "Direction",
                options=['Long', 'Short'],
                default=['Long', 'Short']
            )
        with col3:
            show_expired = st.checkbox("Show Expired", value=False)
    
    # Apply filters
    filtered_df = df[df['Type'].isin(filter_type) & df['Direction'].isin(filter_direction)]
    
    if not show_expired:
        filtered_df = filtered_df[(filtered_df['DTE'].isna()) | (filtered_df['DTE'] >= 0)]
    
    # Format display DataFrame
    display_df = filtered_df.copy()
    
    # Format columns
    display_df['Avg Price'] = display_df['Avg Price'].apply(lambda x: f"${x:.2f}")
    display_df['Current'] = display_df['Current'].apply(lambda x: f"${x:.2f}")
    display_df['Cost Basis'] = display_df['Cost Basis'].apply(lambda x: f"${x:,.2f}")
    display_df['Market Value'] = display_df['Market Value'].apply(lambda x: f"${x:,.2f}")
    display_df['P/L'] = display_df['P/L'].apply(lambda x: f"${x:,.2f}")
    display_df['P/L %'] = display_df['P/L %'].apply(lambda x: f"{x:+.1f}%")
    
    # Format Strike and DTE
    display_df['Strike'] = display_df['Strike'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "—")
    display_df['DTE'] = display_df['DTE'].apply(lambda x: f"{int(x)}d" if pd.notna(x) else "—")
    display_df['Exp'] = display_df['Exp'].apply(lambda x: x if pd.notna(x) else "—")
    
    # Select columns to display
    display_columns = ['Type', 'Symbol', 'Qty', 'Strike', 'Exp', 'DTE', 'Avg Price', 'Current', 'P/L', 'P/L %', 'Direction']
    display_df = display_df[display_columns]
    
    # Display table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Export button
    st.write("")
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Export to CSV",
        data=csv,
        file_name=f"positions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=False
    )
