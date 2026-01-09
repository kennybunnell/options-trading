"""Working Orders Monitor - View and manage unfilled orders"""

import streamlit as st
import pandas as pd
from datetime import datetime

def render_working_orders_monitor(api, account_number, order_type='all'):
    """
    Display working (unfilled) orders with cancel and resubmit functionality
    
    Args:
        api: TastytradeAPI instance
        account_number: Account number to fetch orders from
        order_type: 'all', 'csp', or 'cc' to filter order types
    """
    st.subheader("📋 Working Orders Monitor")
    st.caption("View and manage orders that haven't filled yet")
    
    # Fetch working orders
    if st.button("🔄 Refresh Orders", use_container_width=False, key=f"refresh_orders_{order_type}"):
        st.rerun()
    
    try:
        # Get live orders (working/pending)
        orders = api.get_live_orders(account_number)
        
        if not orders or len(orders) == 0:
            st.info("✅ No working orders - all orders have been filled or canceled!")
            return
        
        # Debug: Print raw orders to see what we're getting
        print(f"\n=== Working Orders Debug (filter: {order_type}) ===")
        print(f"Total orders fetched: {len(orders)}")
        
        # Parse orders into displayable format
        order_data = []
        for order in orders:
            try:
                # Extract order details
                order_id = order.get('id', 'N/A')
                status = order.get('status', 'Unknown')
                time_in_force = order.get('time-in-force', 'N/A')
                
                # Get legs (option details)
                legs = order.get('legs', [])
                if not legs:
                    print(f"  Skipping order {order_id}: No legs")
                    continue
                
                leg = legs[0]  # Assume single-leg orders for now
                symbol = leg.get('symbol', 'UNKNOWN')
                action = leg.get('action', 'N/A')  # STO, BTO, STC, BTC, etc.
                quantity = leg.get('quantity', 0)
                
                print(f"  Order {order_id}: symbol={symbol}, action={action}, qty={quantity}, status={status}")
                
                # Filter out non-Live orders (Cancelled, Filled, etc.)
                if status != 'Live':
                    print(f"    Filtered out: Status is {status} (not Live)")
                    continue
                
                # Parse symbol to get underlying and option details
                # Format: TICKER  YYMMDDC########
                # Example: SOFI  260116P00030000
                underlying = symbol.split()[0] if ' ' in symbol else symbol[:4]
                
                # Determine if PUT or CALL by looking for P or C in the option symbol
                # The format is: TICKER YYMMDDC######## where C is P or C
                import re
                match = re.search(r'\d{6}([PC])\d{8}', symbol)
                if match:
                    option_char = match.group(1)
                    option_type = 'PUT' if option_char == 'P' else 'CALL'
                else:
                    option_type = 'UNKNOWN'
                    print(f"    Warning: Could not parse option type from symbol: {symbol}")
                
                # Normalize action (handle STO, Sell to Open, etc.)
                action_upper = action.upper()
                is_sell_to_open = 'STO' in action_upper or 'SELL TO OPEN' in action_upper or action_upper == 'SELL_TO_OPEN'
                
                # Filter by order type if specified
                if order_type == 'csp':
                    if option_type != 'PUT' or not is_sell_to_open:
                        print(f"    Filtered out: Not a CSP (type={option_type}, action={action})")
                        continue
                elif order_type == 'cc':
                    if option_type != 'CALL' or not is_sell_to_open:
                        print(f"    Filtered out: Not a CC (type={option_type}, action={action})")
                        continue
                
                print(f"    ✅ Included: {underlying} {option_type}")
                
                # Get price
                price = order.get('price', 0)
                
                # Get order time
                order_time_str = order.get('received-at', order.get('created-at', ''))
                if order_time_str:
                    try:
                        order_time = datetime.fromisoformat(order_time_str.replace('Z', '+00:00'))
                        time_display = order_time.strftime('%m/%d %H:%M')
                    except:
                        time_display = 'N/A'
                else:
                    time_display = 'N/A'
                
                order_data.append({
                    'order_id': order_id,
                    'Symbol': underlying,
                    'Type': option_type,
                    'Action': action,
                    'Qty': int(quantity),
                    'Limit Price': float(price),
                    'Status': status,
                    'Time': time_display,
                    'TIF': time_in_force,
                    'Full Symbol': symbol
                })
            
            except Exception as e:
                st.warning(f"Error parsing order: {str(e)}")
                continue
        
        if not order_data:
            st.info("✅ No working orders matching the filter!")
            return
        
        # Create DataFrame
        df = pd.DataFrame(order_data)
        
        # Add selection column
        df.insert(0, 'Select', False)
        
        # Display summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Working Orders", len(df))
        with col2:
            total_qty = df['Qty'].sum()
            st.metric("Total Contracts", int(total_qty))
        with col3:
            csp_count = len(df[df['Type'] == 'PUT'])
            cc_count = len(df[df['Type'] == 'CALL'])
            st.metric("CSP / CC", f"{csp_count} / {cc_count}")
        
        st.write("")
        
        # Initialize session state for selections if not exists
        session_key = f"working_orders_selections_{order_type}"
        if session_key not in st.session_state:
            st.session_state[session_key] = [False] * len(df)
        
        # Ensure session state matches current df length
        if len(st.session_state[session_key]) != len(df):
            st.session_state[session_key] = [False] * len(df)
        
        # Apply session state to df
        df['Select'] = st.session_state[session_key]
        
        # Add Select All / Deselect All buttons
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("✅ Select All", use_container_width=True, key=f"select_all_{order_type}"):
                st.session_state[session_key] = [True] * len(df)
                st.rerun()
        with col2:
            if st.button("⬜ Deselect All", use_container_width=True, key=f"deselect_all_{order_type}"):
                st.session_state[session_key] = [False] * len(df)
                st.rerun()
        
        st.write("")
        
        # Format display
        display_df = df[['Select', 'Symbol', 'Type', 'Action', 'Qty', 'Limit Price', 'Status', 'Time', 'TIF']].copy()
        display_df['Limit Price'] = display_df['Limit Price'].apply(lambda x: f"${x:.2f}")
        
        # Display table
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select orders to cancel or resubmit",
                    default=False,
                )
            },
            key=f"working_orders_editor_{order_type}"
        )
        
        # Update selections in both df and session state
        df['Select'] = edited_df['Select']
        st.session_state[session_key] = edited_df['Select'].tolist()
        
        # Action buttons
        selected_orders = df[df['Select'] == True]
        
        if len(selected_orders) > 0:
            st.write("")
            st.write(f"**Selected: {len(selected_orders)} order(s)**")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("❌ Cancel Selected", type="secondary", use_container_width=True, key=f"cancel_orders_{order_type}"):
                    with st.spinner("Canceling orders..."):
                        success_count = 0
                        failed_count = 0
                        
                        for idx, row in selected_orders.iterrows():
                            try:
                                result = api.cancel_order(account_number, row['order_id'])
                                if result:
                                    success_count += 1
                                    st.success(f"✅ Canceled: {row['Symbol']} {row['Type']}")
                                else:
                                    failed_count += 1
                                    st.error(f"❌ Failed to cancel: {row['Symbol']} {row['Type']}")
                            except Exception as e:
                                failed_count += 1
                                st.error(f"❌ Error canceling {row['Symbol']}: {str(e)}")
                        
                        if success_count > 0:
                            st.success(f"🎉 Canceled {success_count} order(s)!")
                            st.rerun()
                        if failed_count > 0:
                            st.warning(f"⚠️ {failed_count} order(s) failed to cancel")
            
            with col2:
                if st.button("🔄 Cancel & Resubmit @ Mid", type="primary", use_container_width=True, key=f"resubmit_orders_{order_type}"):
                    with st.spinner("Canceling and resubmitting orders at midpoint..."):
                        success_count = 0
                        failed_count = 0
                        
                        for idx, row in selected_orders.iterrows():
                            try:
                                # Step 1: Cancel the existing order
                                cancel_result = api.cancel_order(account_number, row['order_id'])
                                if not cancel_result:
                                    st.error(f"❌ Failed to cancel: {row['Symbol']} {row['Type']}")
                                    failed_count += 1
                                    continue
                                
                                st.success(f"✅ Canceled: {row['Symbol']} {row['Type']}")
                                
                                # Step 2: Get current quote for the symbol
                                full_symbol = row['Full Symbol']
                                quote = api.get_option_quote(full_symbol)
                                
                                if not quote or 'bid' not in quote or 'ask' not in quote:
                                    st.error(f"❌ Could not get quote for {row['Symbol']}")
                                    failed_count += 1
                                    continue
                                
                                bid = float(quote['bid'])
                                ask = float(quote['ask'])
                                mid_price = round((bid + ask) / 2, 2)
                                
                                st.info(f"📊 {row['Symbol']}: Bid=${bid:.2f}, Ask=${ask:.2f}, Mid=${mid_price:.2f}")
                                
                                # Step 3: Resubmit at midpoint
                                if row['Type'] == 'PUT':
                                    # CSP order
                                    result = api.submit_csp_order(
                                        account_number=account_number,
                                        symbol=full_symbol,
                                        quantity=int(row['Qty']),
                                        price=mid_price
                                    )
                                else:
                                    # CC order
                                    result = api.submit_covered_call_order(
                                        account_number=account_number,
                                        symbol=full_symbol,
                                        quantity=int(row['Qty']),
                                        price=mid_price
                                    )
                                
                                if result.get('success'):
                                    success_count += 1
                                    st.success(f"✅ Resubmitted: {row['Symbol']} @ ${mid_price:.2f}")
                                else:
                                    failed_count += 1
                                    st.error(f"❌ Failed to resubmit {row['Symbol']}: {result.get('message', 'Unknown error')}")
                                    
                            except Exception as e:
                                failed_count += 1
                                st.error(f"❌ Error with {row['Symbol']}: {str(e)}")
                        
                        if success_count > 0:
                            st.success(f"🎉 Successfully resubmitted {success_count} order(s) at midpoint!")
                            st.rerun()
                        if failed_count > 0:
                            st.warning(f"⚠️ {failed_count} order(s) failed to resubmit")   
            with col3:
                st.caption("💡 Tip: Cancel orders that aren't filling and resubmit from the opportunities table at midpoint price")
        
    except Exception as e:
        st.error(f"Error fetching orders: {str(e)}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())
