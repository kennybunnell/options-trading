import requests
import os
from datetime import datetime, timedelta

class TastytradeAPI:
    def __init__(self):
        self.base_url = 'https://api.tastyworks.com'
        self.username = os.getenv('TASTYTRADE_USERNAME' )
        self.password = os.getenv('TASTYTRADE_PASSWORD')
        self.session_token = None
        self.token_expiry = None
        self._authenticate()
        
    def _is_token_valid(self):
        """Check if current token is still valid"""
        if not self.session_token or not self.token_expiry:
            return False
        
        # Refresh token 1 hour before expiry
        return datetime.now() < (self.token_expiry - timedelta(hours=1))
    
    def _authenticate(self):
        """Authenticate with Tastytrade API and get session token"""
        # Check if existing token is still valid
        if self._is_token_valid():
            return True
        
        try:
            url = f'{self.base_url}/sessions'
            payload = {
                'login': self.username,
                'password': self.password
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 201:
                data = response.json()
                self.session_token = data['data']['session-token']
                # Tastytrade tokens are valid for 24 hours
                self.token_expiry = datetime.now() + timedelta(hours=24)
                return True
            else:
                print(f"Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return False
    
    def _get_headers(self):
        """Get headers with valid session token"""
        # Ensure token is valid before making request
        if not self._is_token_valid():
            self._authenticate()
        
        return {
            'Authorization': self.session_token,
            'Content-Type': 'application/json'
        }
    
    def get_accounts(self):
        """Get all accounts"""
        try:
            url = f'{self.base_url}/customers/me/accounts'
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                data = response.json()
                return data['data']['items']
            return []
            
        except Exception as e:
            print(f"Error fetching accounts: {str(e)}")
            return []
    
    def get_account_balances(self, account_number):
        """Get account balances"""
        try:
            url = f'{self.base_url}/accounts/{account_number}/balances'
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                data = response.json()
                return data['data']
            return None
            
        except Exception as e:
            print(f"Error fetching balances: {str(e)}")
            return None
    
    def get_positions(self, account_number):
        """Get account positions"""
        try:
            url = f'{self.base_url}/accounts/{account_number}/positions'
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                data = response.json()
                return data['data']['items']
            return []
            
        except Exception as e:
            print(f"Error fetching positions: {str(e)}")
            return []
    
    def get_accounts_with_names(self):
        """Get accounts with their actual nicknames from Tastytrade"""
        accounts = self.get_accounts()
        
        result = []
        for acc in accounts:
            account_number = acc['account']['account-number']
            
            # Try to get nickname from various possible fields
            nickname = (
                acc['account'].get('nickname') or 
                acc['account'].get('name') or 
                acc['account'].get('account-nickname') or
                account_number
            )
            
            result.append({
                'account_number': account_number,
                'nickname': nickname,
                'display': f"{nickname} ({account_number})"
            })
        
        return result

    
    def get_quote(self, symbol):
        """
        Get current quote for a stock symbol
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            
        Returns:
            dict: Quote data with bid, ask, last, volume, etc.
        """
        try:
            if not self._is_token_valid():
                self._authenticate()
            
            url = f'{self.base_url}/market-data/by-type'
            headers = {'Authorization': self.session_token}
            params = {'equity': symbol}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    return data['data'][0]
                return None
            else:
                print(f"Get quote failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Get quote error: {str(e)}")
            return None
    
    def get_option_expirations(self, symbol):
        """
        Get available option expirations for a symbol
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            
        Returns:
            list: List of expiration dates
        """
        try:
            if not self._is_token_valid():
                self._authenticate()
            
            url = f'{self.base_url}/option-chains/{symbol}/nested'
            headers = {'Authorization': self.session_token}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                expirations = []
                
                if data.get('data') and data['data'].get('items'):
                    for item in data['data']['items']:
                        if item.get('expirations'):
                            for exp in item['expirations']:
                                exp_date = exp.get('expiration-date')
                                if exp_date:
                                    expirations.append(exp_date)
                
                return sorted(set(expirations))
            else:
                print(f"Get expirations failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Get expirations error: {str(e)}")
            return []
    
    def get_option_chain(self, symbol, expiration_date=None):
        """
        Get option chain for a symbol in nested format
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            expiration_date (str, optional): Specific expiration date (YYYY-MM-DD)
            
        Returns:
            dict: Nested option chain with format {'expirations': [...]}
                  Each expiration contains strikes with call/put data
        """
        try:
            if not self._is_token_valid():
                self._authenticate()
            
            url = f'{self.base_url}/option-chains/{symbol}/nested'
            headers = {'Authorization': self.session_token}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Return nested format that covered_calls.py expects
                if data.get('data') and data['data'].get('items'):
                    # Get the first item (the underlying stock)
                    item = data['data']['items'][0]
                    
                    if item.get('expirations'):
                        # Return in the format: {'expirations': [...]}
                        return {'expirations': item['expirations']}
                
                return None
            else:
                print(f"Get option chain failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Get option chain error: {str(e)}")
            return None
    def submit_covered_call_order(self, account_number, symbol, strike, expiration, quantity, order_type='Limit', price=None):
        """
        Submit a covered call order (sell to open call option)
        
        Args:
            account_number (str): Account number
            symbol (str): Underlying stock symbol (e.g., 'AAPL')
            strike (float): Strike price
            expiration (str): Expiration date in YYYY-MM-DD format
            quantity (int): Number of contracts to sell
            order_type (str): 'Limit' or 'Market' (default: 'Limit')
            price (float): Limit price per contract (required if order_type='Limit')
        
        Returns:
            dict: Order response with status and order ID, or None if failed
        """
        try:
            if not self._is_token_valid():
                self._authenticate()
            
            # Format expiration date (remove dashes for Tastytrade format)
            exp_formatted = expiration.replace('-', '')
            
            # Build option symbol (Tastytrade format: SYMBOL YYMMDD C/P STRIKE)
            # Example: AAPL  250117C00150000 (AAPL Jan 17 2025 Call $150)
            exp_short = exp_formatted[2:]  # Remove century (25 instead of 2025)
            strike_formatted = f"{int(strike * 1000):08d}"  # Strike in cents, 8 digits
            option_symbol = f"{symbol.ljust(6)}{exp_short}C{strike_formatted}"
            
            # Build order payload
            url = f'{self.base_url}/accounts/{account_number}/orders'
            headers = self._get_headers()
            
            print(f"\n=== ORDER SUBMISSION DEBUG ===")
            print(f"Account Number: {account_number}")
            print(f"URL: {url}")
            print(f"Symbol: {symbol}")
            print(f"Option Symbol: {option_symbol}")
            print(f"Quantity: {quantity}")
            print(f"============================\n")
            
            # Covered call = Sell to Open (STO) call option
            # NOTE: Tastytrade API does NOT support multi-leg covered call orders
            # The system will automatically check if you own the underlying shares
            # and treat this as covered if shares are available in the account
            legs = [{
                'instrument-type': 'Equity Option',
                'symbol': option_symbol,
                'action': 'Sell to Open',
                'quantity': quantity
            }]
            
            payload = {
                'time-in-force': 'Day',
                'order-type': order_type,
                'underlying-symbol': symbol,  # Required field
                'legs': legs
            }
            
            # Add price if limit order
            if order_type == 'Limit' and price is not None:
                payload['price'] = str(price)
                payload['price-effect'] = 'Credit'  # We receive credit for selling
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                data = response.json()
                return {
                    'success': True,
                    'order_id': data['data'].get('id'),
                    'status': data['data'].get('status'),
                    'message': f"Order submitted: {quantity} contracts of {symbol} ${strike} Call"
                }
            else:
                # Capture full error response for debugging
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    # Log full response for debugging
                    print(f"\n=== TASTYTRADE ORDER ERROR ===")
                    print(f"Status Code: {response.status_code}")
                    print(f"Full Response: {error_data}")
                    print(f"Payload Sent: {payload}")
                    print(f"Option Symbol: {option_symbol}")
                    print(f"==========================\n")
                except:
                    error_msg = response.text
                    print(f"Raw error: {response.text}")
                
                return {
                    'success': False,
                    'message': f"Order failed: {error_msg}",
                    'status_code': response.status_code,
                    'full_response': error_data if 'error_data' in locals() else response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Order error: {str(e)}"
            }
    
    def submit_covered_call_orders_batch(self, account_number, orders):
        """
        Submit multiple covered call orders
        
        Args:
            account_number (str): Account number
            orders (list): List of order dicts with keys: symbol, strike, expiration, quantity, price
        
        Returns:
            list: List of results for each order
        """
        results = []
        for order in orders:
            result = self.submit_covered_call_order(
                account_number=account_number,
                symbol=order['symbol'],
                strike=order['strike'],
                expiration=order['expiration'],
                quantity=order['quantity'],
                order_type='Limit',
                price=order.get('price')
            )
            results.append({
                **result,
                'symbol': order['symbol'],
                'strike': order['strike'],
                'quantity': order['quantity']
            })
        return results

    def buy_to_close_covered_call(self, account_number, option_symbol, quantity, price):
        """
        Submit a buy-to-close order for a covered call
        
        Args:
            account_number: Tastytrade account number
            option_symbol: Full option symbol from position
            quantity: Number of contracts to buy back
            price: Limit price per contract
        
        Returns:
            dict with 'success' (bool) and 'order_id' or 'message'
        """
        try:
            if not self._is_token_valid():
                self._authenticate()
            
            url = f'{self.base_url}/accounts/{account_number}/orders'
            headers = self._get_headers()
            
            # Extract underlying symbol from option symbol (first 6 chars, stripped)
            underlying_symbol = option_symbol[:6].strip()
            
            # Buy to Close (BTC) order
            legs = [{
                'instrument-type': 'Equity Option',
                'symbol': option_symbol,
                'action': 'Buy to Close',
                'quantity': quantity
            }]
            
            payload = {
                'time-in-force': 'Day',
                'order-type': 'Limit',
                'underlying-symbol': underlying_symbol,  # Required field
                'price': str(price),
                'price-effect': 'Debit',  # We pay to buy back
                'legs': legs
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                data = response.json()
                return {
                    'success': True,
                    'order_id': data['data'].get('id'),
                    'message': f"Buy-to-close order submitted for {quantity} contracts"
                }
            else:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                return {
                    'success': False,
                    'message': f"Order failed: {error_msg}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Exception: {str(e)}"
            }

    def submit_csp_order(self, account_number, symbol, quantity, price):
        """
        Submit a cash-secured put order (sell to open put option)
        
        Args:
            account_number (str): Account number
            symbol (str): Full option symbol in OCC format (e.g., 'AAPL  250117P00150000')
            quantity (int): Number of contracts to sell
            price (float): Limit price per contract
        
        Returns:
            dict: Order response with success status, or None if failed
        """
        try:
            if not self._is_token_valid():
                self._authenticate()
            
            # Extract underlying symbol from option symbol
            # OCC format: TICKER(6) + DATE(6) + C/P(1) + STRIKE(8)
            # Example: AAPL  250117P00150000
            underlying = symbol[:6].strip()
            
            # Build order payload
            url = f'{self.base_url}/accounts/{account_number}/orders'
            headers = self._get_headers()
            
            print(f"\n=== CSP ORDER SUBMISSION DEBUG ===")
            print(f"Account Number: {account_number}")
            print(f"URL: {url}")
            print(f"Underlying: {underlying}")
            print(f"Option Symbol: {symbol}")
            print(f"Quantity: {quantity}")
            print(f"Price: {price}")
            print(f"==================================\n")
            
            # Cash-secured put = Sell to Open (STO) put option
            # Tastytrade will automatically check buying power
            legs = [{
                'instrument-type': 'Equity Option',
                'symbol': symbol,
                'action': 'Sell to Open',
                'quantity': quantity
            }]
            
            payload = {
                'time-in-force': 'Day',
                'order-type': 'Limit',
                'underlying-symbol': underlying,
                'legs': legs,
                'price': str(price),
                'price-effect': 'Credit'  # We receive credit for selling
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                data = response.json()
                return {
                    'success': True,
                    'order_id': data['data'].get('id'),
                    'status': data['data'].get('status'),
                    'message': f"CSP order submitted: {quantity} contracts of {underlying}"
                }
            else:
                # Capture full error response for debugging
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    errors = error_data.get('error', {}).get('errors', [])
                    
                    # Log full response for debugging
                    print(f"\n=== TASTYTRADE CSP ORDER ERROR ===")
                    print(f"Status Code: {response.status_code}")
                    print(f"Error Message: {error_msg}")
                    print(f"Errors: {errors}")
                    print(f"Full Response: {error_data}")
                    print(f"Payload Sent: {payload}")
                    print(f"==================================\n")
                    
                    # Return detailed error for user
                    if errors:
                        error_details = '; '.join([e.get('message', '') for e in errors])
                        return {
                            'success': False,
                            'message': f"Order failed: {error_msg} - {error_details}",
                            'status_code': response.status_code
                        }
                    else:
                        return {
                            'success': False,
                            'message': f"Order failed: {error_msg}",
                            'status_code': response.status_code
                        }
                except:
                    error_msg = response.text
                    print(f"Raw error: {response.text}")
                    return {
                        'success': False,
                        'message': f"Order failed: {error_msg}",
                        'status_code': response.status_code
                    }
                
        except Exception as e:
            print(f"Exception in submit_csp_order: {str(e)}")
            return {
                'success': False,
                'message': f"Order error: {str(e)}"
            }

    def get_live_orders(self, account_number):
        """
        Get all live (working/pending) orders for an account
        
        Args:
            account_number: Account number to fetch orders from
            
        Returns:
            List of order dictionaries, or empty list if error
        """
        try:
            url = f'{self.base_url}/accounts/{account_number}/orders/live'
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                data = response.json()
                return data['data']['items']
            else:
                print(f"Error fetching live orders: {response.status_code}")
                print(f"Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"Exception in get_live_orders: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def cancel_order(self, account_number, order_id):
        """
        Cancel a working order
        
        Args:
            account_number: Account number
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f'{self.base_url}/accounts/{account_number}/orders/{order_id}'
            response = requests.delete(url, headers=self._get_headers())
            
            if response.status_code == 204 or response.status_code == 200:
                print(f"Order {order_id} canceled successfully")
                return True
            else:
                print(f"Error canceling order: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"Exception in cancel_order: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
