"""
PMCC Order Submission Utilities
Handle buy-to-open for LEAPs and sell-to-open for short calls via Tastytrade API
"""

import requests


def submit_leap_buy_order(tastytrade_api, account_number, option_symbol, quantity, price, order_type='Limit'):
    """
    Submit a buy-to-open order for a LEAP call option
    
    Args:
        tastytrade_api: TastytradeAPI instance
        account_number: Account number
        option_symbol: Full option symbol from Tradier (e.g., 'AAPL250117C00150000')
        quantity: Number of contracts to buy
        price: Limit price per contract (or None for market order)
        order_type: 'Limit' or 'Market'
    
    Returns:
        dict: Order response with success status
    """
    try:
        if not tastytrade_api._is_token_valid():
            tastytrade_api._authenticate()
        
        # Parse option symbol to extract components
        # Tradier format: SYMBOL + YYMMDD + C/P + STRIKE (8 digits in cents)
        # Example: AAPL250117C00150000 = AAPL Jan 17 2025 Call $150
        
        # Extract underlying (variable length, before date)
        # Find where the date starts (6 digits YYMMDD)
        import re
        match = re.match(r'([A-Z]+)(\d{6})([CP])(\d{8})', option_symbol)
        
        if not match:
            return {
                'success': False,
                'message': f'Invalid option symbol format: {option_symbol}'
            }
        
        underlying = match.group(1)
        exp_date = match.group(2)  # YYMMDD
        option_type = match.group(3)  # C or P
        strike_cents = match.group(4)  # Strike in cents (8 digits)
        
        # Format for Tastytrade (needs spaces for padding)
        # Tastytrade format: SYMBOL(6 chars padded) + YYMMDD + C/P + STRIKE(8 digits)
        tastytrade_symbol = f"{underlying.ljust(6)}{exp_date}{option_type}{strike_cents}"
        
        # Build order payload
        url = f'{tastytrade_api.base_url}/accounts/{account_number}/orders'
        headers = tastytrade_api._get_headers()
        
        # Determine time in force
        time_in_force = 'Day' if order_type == 'Limit' else 'Day'
        
        # Build legs
        legs = [
            {
                'instrument-type': 'Equity Option',
                'symbol': tastytrade_symbol,
                'quantity': quantity,
                'action': 'Buy to Open'
            }
        ]
        
        # Build order
        order_payload = {
            'time-in-force': time_in_force,
            'order-type': order_type,
            'legs': legs
        }
        
        # Add price for limit orders
        if order_type == 'Limit' and price is not None:
            order_payload['price'] = str(price)
            order_payload['price-effect'] = 'Debit'
        
        print(f"\n=== LEAP BUY ORDER DEBUG ===")
        print(f"Account: {account_number}")
        print(f"Original Symbol: {option_symbol}")
        print(f"Tastytrade Symbol: {tastytrade_symbol}")
        print(f"Quantity: {quantity}")
        print(f"Price: ${price}")
        print(f"Order Type: {order_type}")
        print(f"Payload: {order_payload}")
        
        response = requests.post(url, headers=headers, json=order_payload)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            data = response.json()
            order_data = data.get('data', {}).get('order', {})
            
            return {
                'success': True,
                'message': 'LEAP buy order submitted successfully',
                'order_id': order_data.get('id'),
                'status': order_data.get('status'),
                'symbol': tastytrade_symbol,
                'quantity': quantity,
                'price': price
            }
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            
            return {
                'success': False,
                'message': f'Order failed: {error_msg}',
                'status_code': response.status_code,
                'full_response': error_data
            }
    
    except Exception as e:
        import traceback
        return {
            'success': False,
            'message': f'Exception: {str(e)}',
            'traceback': traceback.format_exc()
        }


def submit_short_call_order(tastytrade_api, account_number, option_symbol, quantity, price, order_type='Limit'):
    """
    Submit a sell-to-open order for a short call against a LEAP
    
    Args:
        tastytrade_api: TastytradeAPI instance
        account_number: Account number
        option_symbol: Full option symbol from Tradier
        quantity: Number of contracts to sell
        price: Limit price per contract (or None for market order)
        order_type: 'Limit' or 'Market'
    
    Returns:
        dict: Order response with success status
    """
    try:
        if not tastytrade_api._is_token_valid():
            tastytrade_api._authenticate()
        
        # Parse option symbol
        import re
        match = re.match(r'([A-Z]+)(\d{6})([CP])(\d{8})', option_symbol)
        
        if not match:
            return {
                'success': False,
                'message': f'Invalid option symbol format: {option_symbol}'
            }
        
        underlying = match.group(1)
        exp_date = match.group(2)
        option_type = match.group(3)
        strike_cents = match.group(4)
        
        # Format for Tastytrade
        tastytrade_symbol = f"{underlying.ljust(6)}{exp_date}{option_type}{strike_cents}"
        
        # Build order payload
        url = f'{tastytrade_api.base_url}/accounts/{account_number}/orders'
        headers = tastytrade_api._get_headers()
        
        time_in_force = 'Day'
        
        legs = [
            {
                'instrument-type': 'Equity Option',
                'symbol': tastytrade_symbol,
                'quantity': quantity,
                'action': 'Sell to Open'
            }
        ]
        
        order_payload = {
            'time-in-force': time_in_force,
            'order-type': order_type,
            'legs': legs
        }
        
        if order_type == 'Limit' and price is not None:
            order_payload['price'] = str(price)
            order_payload['price-effect'] = 'Credit'
        
        print(f"\n=== SHORT CALL ORDER DEBUG ===")
        print(f"Account: {account_number}")
        print(f"Original Symbol: {option_symbol}")
        print(f"Tastytrade Symbol: {tastytrade_symbol}")
        print(f"Quantity: {quantity}")
        print(f"Price: ${price}")
        print(f"Order Type: {order_type}")
        print(f"Payload: {order_payload}")
        
        response = requests.post(url, headers=headers, json=order_payload)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            data = response.json()
            order_data = data.get('data', {}).get('order', {})
            
            return {
                'success': True,
                'message': 'Short call order submitted successfully',
                'order_id': order_data.get('id'),
                'status': order_data.get('status'),
                'symbol': tastytrade_symbol,
                'quantity': quantity,
                'price': price
            }
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            
            return {
                'success': False,
                'message': f'Order failed: {error_msg}',
                'status_code': response.status_code,
                'full_response': error_data
            }
    
    except Exception as e:
        import traceback
        return {
            'success': False,
            'message': f'Exception: {str(e)}',
            'traceback': traceback.format_exc()
        }
