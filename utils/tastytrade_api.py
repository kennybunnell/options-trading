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