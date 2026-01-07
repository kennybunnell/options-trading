"""Cash Secured Puts (CSP) utilities"""

from datetime import datetime
import re

def get_existing_csp_positions(api, account_number):
    """
    Fetch existing short put positions (cash-secured puts)
    
    Returns:
        Dict: {
            'short_puts': {symbol: contracts_sold},
            'short_put_details': [list of position details]
        }
    """
    try:
        all_positions = api.get_positions(account_number)
        
        if not all_positions:
            return {
                'short_puts': {},
                'short_put_details': []
            }
        
        short_puts = {}  # Dict: symbol -> number of contracts sold
        short_put_details = []  # For display purposes
        
        print("\n=== DEBUG: Scanning for existing short puts (CSPs) ===")
        for position in all_positions:
            if position.get('instrument-type') == 'Equity Option':
                quantity = int(position.get('quantity', 0))
                symbol = position.get('symbol', 'UNKNOWN')
                option_type_field = position.get('option-type', '').lower()
                underlying = position.get('underlying-symbol', 'UNKNOWN')
                
                # Parse option type from symbol if not in field (OCC format)
                # Example: SOFI  260206P00030000 -> 'P' means Put
                option_type = option_type_field
                if not option_type:
                    # Find 'P' in the symbol using regex
                    match = re.search(r'\d{6}([CP])\d{8}', symbol)
                    if match:
                        type_char = match.group(1)
                        if type_char == 'P':
                            option_type = 'put'
                        elif type_char == 'C':
                            option_type = 'call'
                
                print(f"Found option: {symbol}, Type: {option_type}, Qty: {quantity}, Underlying: {underlying}")
                
                # Check if it's a short put
                if option_type == 'put':
                    # Tastytrade may return positive quantity for short positions
                    quantity_direction = position.get('quantity-direction', '')
                    is_short = (quantity < 0) or (quantity_direction == 'Short')
                    
                    if is_short or quantity > 0:  # Assume positive quantity for options means short
                        contracts_sold = abs(quantity)
                        short_puts[underlying] = short_puts.get(underlying, 0) + contracts_sold
                        print(f"  ✅ SHORT PUT: {underlying} - {contracts_sold} contracts")
                        
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
                        
                        # Calculate collateral required (strike * 100 * contracts)
                        strike = float(position.get('strike-price', 0))
                        collateral_required = strike * 100 * abs(quantity)
                        
                        short_put_details.append({
                            'symbol': underlying,
                            'contracts': abs(quantity),
                            'strike': strike,
                            'expiration': expiration_date,
                            'dte': dte,
                            'premium_collected': premium_collected,
                            'current_value': current_value_total,
                            'pl': pl,
                            'pct_recognized': pct_recognized,
                            'collateral_required': collateral_required,
                            'option_symbol': position.get('symbol', '')
                        })
        
        print(f"\n=== DEBUG: Total short puts found: {short_puts} ===")
        print(f"Short put details count: {len(short_put_details)}\n")
        
        return {
            'short_puts': short_puts,
            'short_put_details': short_put_details
        }
        
    except Exception as e:
        print(f"Error in get_existing_csp_positions: {str(e)}")
        return {
            'short_puts': {},
            'short_put_details': []
        }
