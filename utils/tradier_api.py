import os
import requests
from datetime import datetime, timedelta

class TradierAPI:
    def __init__(self):
        self.api_key = os.getenv("TRADIER_API_KEY", "")
        self.sandbox = os.getenv("TRADIER_SANDBOX", "false").lower() == "true"
        
        if self.sandbox:
            self.base_url = "https://sandbox.tradier.com/v1"
            print("🧪 Using Tradier SANDBOX environment" )
        else:
            self.base_url = "https://api.tradier.com/v1"
            print("💰 Using Tradier PRODUCTION environment" )
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    def get_option_chains(self, symbol, min_dte=0, max_dte=60):
        """Get option chains for a symbol within a DTE range"""
        try:
            # Calculate date range
            today = datetime.now()
            min_date = (today + timedelta(days=min_dte)).strftime('%Y-%m-%d')
            max_date = (today + timedelta(days=max_dte)).strftime('%Y-%m-%d')
            
            # Get option expirations
            exp_url = f"{self.base_url}/markets/options/expirations"
            exp_params = {
                "symbol": symbol,
                "includeAllRoots": "true",
                "strikes": "false"
            }
            
            exp_response = requests.get(exp_url, headers=self.headers, params=exp_params)
            
            if exp_response.status_code != 200:
                return None
            
            exp_data = exp_response.json()
            
            if 'expirations' not in exp_data or not exp_data['expirations']:
                return None
            
            expirations = exp_data['expirations'].get('date', [])
            if isinstance(expirations, str):
                expirations = [expirations]
            
            # Filter expirations by DTE range
            filtered_expirations = []
            for exp_date_str in expirations:
                exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
                if min_date <= exp_date_str <= max_date:
                    filtered_expirations.append(exp_date_str)
            
            if not filtered_expirations:
                return None
            
            # Get chains for each expiration (Tradier requires one at a time)
            all_options = []
            
            for exp_date in filtered_expirations:
                chain_url = f"{self.base_url}/markets/options/chains"
                chain_params = {
                    "symbol": symbol,
                    "expiration": exp_date,  # Single expiration only
                    "greeks": "true"
                }
                
                chain_response = requests.get(chain_url, headers=self.headers, params=chain_params)
                
                if chain_response.status_code == 200:
                    chain_data = chain_response.json()
                    
                    if 'options' in chain_data and chain_data['options']:
                        options = chain_data['options'].get('option', [])
                        if isinstance(options, dict):
                            options = [options]
                        all_options.extend(options)
            
            if not all_options:
                return None
            
            # Get underlying price
            quote_url = f"{self.base_url}/markets/quotes"
            quote_params = {"symbols": symbol}
            quote_response = requests.get(quote_url, headers=self.headers, params=quote_params)
            
            underlying_price = None
            if quote_response.status_code == 200:
                quote_data = quote_response.json()
                if 'quotes' in quote_data and 'quote' in quote_data['quotes']:
                    quote = quote_data['quotes']['quote']
                    underlying_price = quote.get('last', 0)
            
            return {
                'options': all_options,
                'underlying_price': underlying_price
            }
            
        except Exception as e:
            print(f"Error fetching option chains for {symbol}: {str(e)}")
            return None
    
    def filter_put_options(self, chain_data, min_delta=0.10, max_delta=0.30):
        """Filter PUT options by delta range"""
        if not chain_data or not chain_data.get('options'):
            return []
        
        options = chain_data['options']
        if isinstance(options, dict):
            options = [options]
        
        filtered = []
        for option in options:
            # Only PUTs
            if option.get('option_type') != 'put':
                continue
            
            # Check delta
            greeks = option.get('greeks', {})
            if not greeks:
                continue
            
            delta = greeks.get('delta')
            if delta is None:
                continue
            
            # Delta for puts is negative, so we take absolute value
            abs_delta = abs(delta)
            
            if min_delta <= abs_delta <= max_delta:
                filtered.append(option)
        
        return filtered





