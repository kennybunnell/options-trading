"""Cash Secured Puts (CSP) utilities"""

from datetime import datetime
import re

def parse_option_symbol(symbol: str):
    """Parse OCC option symbol to extract components"""
    try:
        clean_symbol = symbol.replace(' ', '')
        match = re.match(r'([A-Z]+)(\d{6})([CP])(\d+)', clean_symbol)
        if match:
            underlying = match.group(1)
            date_str = match.group(2)
            option_type = 'PUT' if match.group(3) == 'P' else 'CALL'
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
    except Exception as e:
        pass
    return None

def get_existing_csp_positions(api, account_number):
    """
    Fetch existing short put positions (cash-secured puts)
    
    Args:
        api: TastytradeAPI instance for position data
        account_number: Account number to fetch positions from
    
    Returns:
        Dict: {
            'short_puts': {symbol: contracts_sold},
            'short_put_details': [list of position details]
        }
    
    Note:
        All data comes from Tastytrade API (positions, cost basis, current value).
        Does NOT use Tradier API for quotes.
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
                
                # DEBUG: Print all available fields in position (only for first put found)
                if option_type == 'put' and len(short_put_details) == 0:
                    print(f"\n=== DEBUG: All available fields in Tastytrade position ===")
                    for key, value in position.items():
                        print(f"  {key}: {value}")
                    print(f"=== END DEBUG ===")
                
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
                        
                        # Parse option symbol to get strike, expiration, etc.
                        parsed = parse_option_symbol(symbol)
                        if not parsed:
                            print(f"  ⚠️ Could not parse option symbol: {symbol}")
                            continue
                        
                        strike = parsed['strike']
                        expiration_date = parsed['expiration']
                        
                        # Calculate days to expiration
                        try:
                            exp_dt = datetime.strptime(expiration_date, '%Y-%m-%d')
                            dte = (exp_dt - datetime.now()).days
                        except:
                            dte = 0
                        
                        # Get premium collected (cost basis) from average-open-price
                        try:
                            avg_open_price = float(position.get('average-open-price', 0))
                            premium_collected = avg_open_price * abs(quantity) * 100  # Price per share * contracts * 100
                        except:
                            premium_collected = 0
                        
                        # Get current market value from Tastytrade position data
                        # Tastytrade provides the current value in the position object
                        try:
                            # Try different possible field names for current price
                            current_price_per_contract = (
                                float(position.get('mark', 0)) or
                                float(position.get('mark-price', 0)) or
                                float(position.get('close-price', 0)) or
                                float(position.get('last-price', 0)) or
                                0
                            )
                            
                            # Total current value = price per share * contracts * 100 shares per contract
                            current_value_total = current_price_per_contract * abs(quantity) * 100
                            
                            print(f"  ✅ Got value from Tastytrade for {underlying}: ${current_price_per_contract:.2f}/contract, total=${current_value_total:.2f}")
                        except Exception as e:
                            print(f"  ⚠️ Error getting value from position data: {str(e)}")
                            current_value_total = 0
                        
                        # Calculate P/L and % recognized
                        pl = premium_collected - current_value_total
                        pct_recognized = (pl / premium_collected * 100) if premium_collected > 0 else 0
                        
                        # Collateral = strike * contracts * 100
                        collateral_required = strike * abs(quantity) * 100
                        
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
