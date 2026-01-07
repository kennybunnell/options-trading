# Covered Calls utility functions - Refactored for flexible workflow

from datetime import datetime, timedelta
import streamlit as st

def get_eligible_stock_positions(api, account_number):
    """
    Fetch stock positions that are eligible for covered calls
    
    Filters out:
    - Stocks with existing short call positions (already have covered calls)
    - Short positions (negative quantity)
    - Non-equity positions
    
    Returns:
        Tuple: (holdings, breakdown_info)
        - holdings: List of dict with symbol, quantity, avg_cost, current_price, etc.
        - breakdown_info: Dict with position counts at each filtering step
    """
    try:
        # Get all positions
        all_positions = api.get_positions(account_number)
        
        if not all_positions:
            # Return empty holdings and breakdown for accounts with no positions
            return [], {
                'total_positions': 0,
                'stock_positions': 0,
                'stock_symbols': [],
                'existing_calls': 0,
                'covered_symbols': [],
                'short_call_details': [],
                'eligible_positions': 0,
                'eligible_symbols': []
            }
        
        # Find all stock positions (long only)
        stock_positions = []
        for position in all_positions:
            if position.get('instrument-type') == 'Equity':
                quantity = int(position.get('quantity', 0))
                if quantity > 0:  # Long positions only
                    stock_positions.append(position)
        
        # Find existing short call positions and count contracts per symbol
        short_calls = {}  # Dict: symbol -> number of contracts sold
        short_call_details = []  # For display purposes
        for position in all_positions:
            if position.get('instrument-type') == 'Equity Option':
                quantity = int(position.get('quantity', 0))
                if quantity < 0:  # Short positions
                    option_type = position.get('option-type', '').lower()
                    if option_type == 'call':
                        underlying = position.get('underlying-symbol')
                        contracts_sold = abs(quantity)
                        short_calls[underlying] = short_calls.get(underlying, 0) + contracts_sold
                        
                        # Collect details for display
                        expiration_date = position.get('expiration-date', 'Unknown')
                        
                        # Calculate days to expiration
                        try:
                            exp_dt = datetime.strptime(expiration_date, '%Y-%m-%d')
                            dte = (exp_dt - datetime.now()).days
                        except:
                            dte = 0
                        
                        # Get premium collected (cost basis)
                        try:
                            cost_effect = float(position.get('cost-effect', 0))
                            premium_collected = abs(cost_effect) * abs(quantity) * 100  # Per contract
                        except:
                            premium_collected = 0
                        
                        # Get current option price to calculate P/L
                        try:
                            option_symbol = position.get('symbol', '')
                            option_quote = api.get_quote(option_symbol) if option_symbol else None
                            current_value = float(option_quote.get('last', 0)) if option_quote else 0
                            current_value_total = current_value * abs(quantity) * 100
                        except:
                            current_value = 0
                            current_value_total = 0
                        
                        # Calculate P/L and % recognized
                        pl = premium_collected - current_value_total
                        pct_recognized = (pl / premium_collected * 100) if premium_collected > 0 else 0
                        
                        # Find shares owned for this stock
                        shares_owned = 0
                        for sp in stock_positions:
                            if sp.get('symbol') == underlying:
                                shares_owned = int(sp.get('quantity', 0))
                                break
                        
                        short_call_details.append({
                            'symbol': underlying,
                            'shares': shares_owned,
                            'contracts': abs(quantity),
                            'strike': float(position.get('strike-price', 0)),
                            'expiration': expiration_date,
                            'dte': dte,
                            'premium_collected': premium_collected,
                            'current_value': current_value_total,
                            'pl': pl,
                            'pct_recognized': pct_recognized,
                            'option_symbol': position.get('symbol', '')
                        })
        
        # Don't filter out stocks with existing calls - just reduce available shares
        # All stock positions are eligible, but max_contracts will be reduced
        eligible_positions = stock_positions
        
        # Format holdings
        holdings = []
        for position in eligible_positions:
            symbol = position.get('symbol')
            quantity = int(position.get('quantity', 0))
            
            # Safely parse numeric values
            try:
                cost_basis = float(position.get('cost-effect', 0))
            except (ValueError, TypeError):
                cost_basis = 0
            
            try:
                average_open_price = float(position.get('average-open-price', 0))
            except (ValueError, TypeError):
                average_open_price = 0
            
            # Get current price (optional - will fetch during option chain scan if needed)
            try:
                quote = api.get_quote(symbol)
                current_price = float(quote.get('last', 0)) if quote else 0
            except:
                current_price = 0
            
            # Calculate available shares (total shares - shares already covered)
            existing_contracts = short_calls.get(symbol, 0)
            shares_covered = existing_contracts * 100
            available_shares = quantity - shares_covered
            max_new_contracts = max(0, available_shares // 100)  # Can't be negative
            
            # Add to holdings even if current_price is 0 (will fetch later)
            holdings.append({
                'symbol': symbol,
                'quantity': quantity,
                'existing_contracts': existing_contracts,
                'shares_covered': shares_covered,
                'available_shares': available_shares,
                'avg_cost': average_open_price,
                'current_price': current_price if current_price > 0 else average_open_price,  # Use avg_cost as fallback
                'market_value': (current_price if current_price > 0 else average_open_price) * quantity,
                'unrealized_pl': (current_price - average_open_price) * quantity if current_price > 0 else 0,
                'unrealized_pl_pct': ((current_price - average_open_price) / average_open_price * 100) if (average_open_price > 0 and current_price > 0) else 0,
                'max_contracts': max_new_contracts
            })
        
        # Create breakdown info
        breakdown = {
            'total_positions': len(all_positions),
            'stock_positions': len(stock_positions),
            'stock_symbols': [p.get('symbol') for p in stock_positions],
            'existing_calls': len(short_calls),  # Number of unique symbols with calls
            'covered_symbols': list(short_calls.keys()),
            'short_call_details': short_call_details,  # Full details with expiration
            'eligible_positions': len([h for h in holdings if h['max_contracts'] > 0]),  # Only count if has available contracts
            'eligible_symbols': [h['symbol'] for h in holdings if h['max_contracts'] > 0]
        }
        
        return holdings, breakdown
        
    except Exception as e:
        st.error(f"Error fetching eligible positions: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return [], {}


def pre_scan_covered_calls(api, tradier_api, holdings, min_prescan_delta=0.10, max_prescan_delta=0.50, min_dte=7, max_dte=14):
    """
    Pre-scan option chains for covered call opportunities WITH DETAILED LOGGING
    """
    opportunities = []
    
    st.write(f"📊 **Starting scan of {len(holdings)} stocks...**")
    st.write(f"🎯 Pre-scan filters: Delta {min_prescan_delta:.2f}-{max_prescan_delta:.2f}, DTE {min_dte}-{max_dte}")
    st.write("")
    
    for idx, holding in enumerate(holdings, 1):
        symbol = holding['symbol']
        quantity = holding['quantity']
        current_price = holding['current_price']
        
        st.write(f"**[{idx}/{len(holdings)}] {symbol}** - ${current_price:.2f}, {quantity} shares")
        
        if current_price <= 0:
            st.warning(f"  ⚠️ Skipping {symbol}: Invalid price ${current_price}")
            continue
        
        try:
            # Get option chain from Tradier (includes greeks!)
            st.write(f"  🔍 Fetching option chain and indicators...")
            
            # Fetch RSI and IV Rank for this stock
            rsi = tradier_api.get_rsi(symbol)
            iv_rank = tradier_api.get_iv_rank(symbol)
            
            tradier_chain = tradier_api.get_option_chains(symbol, min_dte=min_dte, max_dte=max_dte)
            
            if not tradier_chain or not tradier_chain.get('options'):
                st.warning(f"  ⚠️ No option chain data returned for {symbol}")
                continue
            
            st.write(f"  ✅ Got option chain data (RSI: {rsi if rsi else 'N/A'}, IV Rank: {iv_rank if iv_rank else 'N/A'})")
            
            # Convert Tradier format to grouped by expiration
            from collections import defaultdict
            expirations_dict = defaultdict(lambda: defaultdict(dict))
            
            for option in tradier_chain['options']:
                if option.get('option_type') != 'call':
                    continue  # Only calls for covered calls
                
                exp_date = option.get('expiration_date')
                strike = float(option.get('strike', 0))
                
                # Get greeks
                greeks = option.get('greeks', {})
                delta = greeks.get('delta', 0) if greeks else 0
                
                # Store call data
                expirations_dict[exp_date][strike] = {
                    'strike-price': strike,
                    'call': {
                        'delta': abs(delta),  # Make positive for calls
                        'bid': float(option.get('bid', 0)),
                        'ask': float(option.get('ask', 0)),
                        'volume': int(option.get('volume', 0)),
                        'open-interest': int(option.get('open_interest', 0))
                    }
                }
            
            # Convert to list format expected by rest of code
            expirations = []
            for exp_date, strikes_dict in expirations_dict.items():
                strikes = [strike_data for strike, strike_data in sorted(strikes_dict.items())]
                expirations.append({
                    'expiration-date': exp_date,
                    'strikes': strikes
                })
            
            if not expirations:
                st.warning(f"  ⚠️ No expirations found for {symbol}")
                continue
            
            st.write(f"  📅 Found {len(expirations)} expiration dates")
            
            # Filter expirations by DTE
            today = datetime.now().date()
            valid_expirations = 0
            total_strikes_checked = 0
            opportunities_found = 0
            
            for exp_data in expirations:
                exp_date_str = exp_data.get('expiration-date')
                
                if not exp_date_str:
                    continue
                
                try:
                    exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
                    dte = (exp_date - today).days
                    
                    # Filter by DTE range
                    if not (min_dte <= dte <= max_dte):
                        continue
                    
                    valid_expirations += 1
                    
                    # Get call strikes
                    strikes = exp_data.get('strikes', [])
                    
                    if not strikes:
                        continue
                    
                    st.write(f"    📊 {exp_date_str} (DTE {dte}): {len(strikes)} strikes")
                    
                    otm_count = 0
                    dict_count = 0
                    call_data_count = 0
                    
                    for strike_data in strikes:
                        # Skip if strike_data is not a dict (API returned invalid data)
                        if not isinstance(strike_data, dict):
                            continue
                        
                        dict_count += 1
                        
                        strike = float(strike_data.get('strike-price', 0))
                        total_strikes_checked += 1
                        
                        # Only OTM calls (strike > current price)
                        if strike <= current_price:
                            continue
                        
                        otm_count += 1
                        
                        # Get call option data
                        call_data = strike_data.get('call')
                        
                        if not call_data:
                            if otm_count == 1:
                                st.write(f"      ⚠️ First OTM strike ${strike:.2f} has no call data")
                            continue
                        
                        call_data_count += 1
                        
                        # Skip if call_data is not a dict (API returned invalid data)
                        if not isinstance(call_data, dict):
                            continue
                        
                        # Extract option data
                        delta = abs(float(call_data.get('delta', 0)))
                        bid = float(call_data.get('bid', 0))
                        ask = float(call_data.get('ask', 0))
                        mid = (bid + ask) / 2
                        volume = int(call_data.get('volume', 0))
                        open_interest = int(call_data.get('open-interest', 0))
                        
                        # Debug: Show first OTM call for each stock
                        if call_data_count == 1:  # First one with call data
                            st.write(f"      🔍 First OTM call: ${strike:.2f} Δ{delta:.3f} bid ${bid:.2f} ask ${ask:.2f}")
                            st.write(f"      🔍 Delta range check: {min_prescan_delta:.2f} <= {delta:.3f} <= {max_prescan_delta:.2f} = {min_prescan_delta <= delta <= max_prescan_delta}")
                            st.write(f"      🔍 Bid check: bid {bid:.2f} > 0 = {bid > 0}")
                        
                        # Filter by pre-scan delta range
                        if not (min_prescan_delta <= delta <= max_prescan_delta):
                            continue
                        
                        # Skip if no bid
                        if bid <= 0:
                            if opportunities_found == 0:
                                st.write(f"      ⚠️ No bid price available")
                            continue
                        
                        # Calculate metrics
                        premium_per_share = mid  # Use mid-price for better fill rate
                        return_pct = (premium_per_share / current_price) * 100
                        weekly_return = (return_pct / dte) * 7 if dte > 0 else 0
                        
                        # Calculate max contracts
                        max_contracts = quantity // 100
                        
                        if max_contracts <= 0:
                            continue
                        
                        # Calculate bid-ask spread
                        spread_pct = ((ask - bid) / mid * 100) if mid > 0 else 999
                        
                        # Distance OTM
                        distance_otm_pct = ((strike - current_price) / current_price) * 100
                        
                        opportunities.append({
                            'symbol': symbol,
                            'current_price': current_price,
                            'strike': strike,
                            'expiration': exp_date_str,
                            'dte': dte,
                            'delta': delta,
                            'bid': bid,
                            'ask': ask,
                            'mid': mid,
                            'premium': mid * 100,  # Per contract - use mid price
                            'return_pct': return_pct,
                            'weekly_return': weekly_return,
                            'weekly_return_pct': weekly_return,  # Add this for display
                            'volume': volume,
                            'open_interest': open_interest,
                            'spread_pct': spread_pct,
                            'rsi': rsi,  # Stock RSI
                            'iv_rank': iv_rank,  # IV Rank
                            'shares_owned': quantity,
                            'max_contracts': max_contracts,
                            'distance_otm': distance_otm_pct
                        })
                        
                        opportunities_found += 1
                        st.write(f"      ✅ ${strike:.2f} Δ{delta:.3f} bid ${bid:.2f} ({weekly_return:.2f}% weekly)")
                    
                    # Debug summary for this expiration
                    st.write(f"      🔍 Debug: {dict_count} valid dicts, {otm_count} OTM, {call_data_count} with call data, {opportunities_found} opportunities")
                
                except Exception as e:
                    st.warning(f"    ⚠️ Error parsing expiration {exp_date_str}: {str(e)}")
                    continue
            
            st.write(f"  📈 {symbol} summary: {valid_expirations} valid expirations, {total_strikes_checked} strikes checked, {opportunities_found} opportunities found")
            st.write("")
        
        except Exception as e:
            st.error(f"  ❌ Error scanning {symbol}: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            continue
    
    st.write("---")
    st.write(f"🎯 **TOTAL OPPORTUNITIES FOUND: {len(opportunities)}**")
    st.write("")
    
    return opportunities


def filter_opportunities(opportunities, min_return_pct=0.0, max_delta=1.0):
    """
    Filter opportunities client-side (no API calls)
    
    Args:
        opportunities: List of opportunities from pre_scan
        min_return_pct: Minimum weekly return %
        max_delta: Maximum delta
    
    Returns:
        Filtered list of opportunities
    """
    filtered = []
    
    for opp in opportunities:
        # Apply filters
        if opp['weekly_return'] < min_return_pct:
            continue
        
        if opp['delta'] > max_delta:
            continue
        
        filtered.append(opp)
    
    return filtered


def calculate_covered_call_metrics(opportunity, contracts=1):
    """
    Calculate metrics for a covered call trade
    
    Args:
        opportunity: Opportunity dict
        contracts: Number of contracts to sell
    
    Returns:
        Dict with calculated metrics
    """
    premium_total = opportunity['premium'] * contracts
    shares_required = contracts * 100
    stock_value = opportunity['current_price'] * shares_required
    
    # Return on stock value
    return_on_stock = (premium_total / stock_value) * 100
    
    # Annualized return
    dte = opportunity['dte']
    annualized_return = (return_on_stock / dte) * 365 if dte > 0 else 0
    
    # Break-even (stock can drop this much and still profit)
    breakeven_drop = (opportunity['premium'] / opportunity['current_price']) * 100
    
    # Max profit (if assigned)
    intrinsic_gain = (opportunity['strike'] - opportunity['current_price']) * shares_required
    max_profit = premium_total + intrinsic_gain
    max_profit_pct = (max_profit / stock_value) * 100
    
    return {
        'premium_total': premium_total,
        'shares_required': shares_required,
        'stock_value': stock_value,
        'return_on_stock': return_on_stock,
        'annualized_return': annualized_return,
        'breakeven_drop': breakeven_drop,
        'max_profit': max_profit,
        'max_profit_pct': max_profit_pct
    }


def format_covered_call_order(opportunity, contracts, account_number):
    """
    Format covered call order for submission
    
    Args:
        opportunity: Opportunity dict
        contracts: Number of contracts to sell
        account_number: Account number
    
    Returns:
        Order dict for API submission
    """
    symbol = opportunity['symbol']
    strike = opportunity['strike']
    expiration = opportunity['expiration']
    price = opportunity['bid']  # Use bid price
    
    # Format option symbol (OCC format)
    # Example: AAPL260110C00180000 (AAPL, 2026-01-10, Call, $180 strike)
    exp_formatted = expiration.replace('-', '')[2:]  # YYMMDD
    strike_formatted = f"{int(strike * 1000):08d}"  # 8 digits, 3 decimals
    option_symbol = f"{symbol}{exp_formatted}C{strike_formatted}"
    
    order = {
        'account_number': account_number,
        'symbol': option_symbol,
        'underlying_symbol': symbol,
        'quantity': contracts,
        'side': 'sell_to_open',
        'order_type': 'limit',
        'price': price,
        'duration': 'day',
        'option_type': 'call',
        'strike': strike,
        'expiration': expiration
    }
    
    return order

def get_active_covered_calls(api, account_number):
    """
    Get active covered call positions for monitoring with P/L tracking
    
    Returns:
        List of dict with detailed CC position info including:
        - symbol, strike, expiration, dte
        - premium_collected, current_value, pl, pl_pct
        - status (BTC/Hold/Monitor/ITM/Expiring)
        - stock_price, shares_owned
    """
    try:
        # Get all positions
        all_positions = api.get_positions(account_number)
        
        if not all_positions:
            return []
        
        # Find stock positions for reference
        stock_positions = {}
        for position in all_positions:
            if position.get('instrument-type') == 'Equity':
                quantity = int(position.get('quantity', 0))
                if quantity > 0:
                    symbol = position.get('symbol')
                    stock_positions[symbol] = {
                        'quantity': quantity,
                        'price': float(position.get('close-price', 0))
                    }
        
        # Find all short call positions
        active_calls = []
        for position in all_positions:
            if position.get('instrument-type') == 'Equity Option':
                quantity = int(position.get('quantity', 0))
                if quantity < 0:  # Short positions
                    option_type = position.get('option-type', '').lower()
                    if option_type == 'call':
                        underlying = position.get('underlying-symbol')
                        strike = float(position.get('strike-price', 0))
                        expiration_date = position.get('expiration-date', 'Unknown')
                        option_symbol = position.get('symbol', '')
                        
                        # Calculate DTE
                        try:
                            exp_dt = datetime.strptime(expiration_date, '%Y-%m-%d')
                            dte = (exp_dt - datetime.now()).days
                        except:
                            dte = 0
                        
                        # Get premium collected (cost basis)
                        try:
                            cost_effect = float(position.get('cost-effect', 0))
                            premium_collected = abs(cost_effect) * abs(quantity) * 100
                        except:
                            premium_collected = 0
                        
                        # Get current option price (ask price for buy-back)
                        try:
                            option_quote = api.get_quote(option_symbol) if option_symbol else None
                            current_ask = float(option_quote.get('ask', 0)) if option_quote else 0
                            current_value_total = current_ask * abs(quantity) * 100
                        except:
                            current_ask = 0
                            current_value_total = 0
                        
                        # Calculate P/L
                        pl = premium_collected - current_value_total
                        pl_pct = (pl / premium_collected * 100) if premium_collected > 0 else 0
                        
                        # Get stock info
                        stock_price = stock_positions.get(underlying, {}).get('price', 0)
                        shares_owned = stock_positions.get(underlying, {}).get('quantity', 0)
                        
                        # Determine status
                        if pl_pct >= 80:
                            status = 'BTC'  # Buy to Close
                            status_emoji = '🟢'
                        elif pl_pct >= 50:
                            status = 'Hold'
                            status_emoji = '🟡'
                        elif pl_pct >= 0:
                            status = 'Monitor'
                            status_emoji = '🟠'
                        else:
                            status = 'Monitor'
                            status_emoji = '🟠'
                        
                        # Check if ITM
                        if stock_price > strike:
                            status = 'ITM'
                            status_emoji = '🔴'
                        
                        # Check if expiring soon
                        if dte <= 3:
                            status = 'Expiring'
                            status_emoji = '⚠️'
                        
                        active_calls.append({
                            'symbol': underlying,
                            'option_symbol': option_symbol,
                            'strike': strike,
                            'expiration': expiration_date,
                            'dte': dte,
                            'quantity': abs(quantity),
                            'premium_collected': premium_collected,
                            'current_ask': current_ask,
                            'current_value': current_value_total,
                            'pl': pl,
                            'pl_pct': pl_pct,
                            'status': status,
                            'status_emoji': status_emoji,
                            'stock_price': stock_price,
                            'shares_owned': shares_owned
                        })
        
        return active_calls
        
    except Exception as e:
        st.error(f"Error fetching active covered calls: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return []
