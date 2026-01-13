import os
import requests
import math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        
        # Cache for RSI and IV Rank data (persists for session)
        self._indicators_cache = {}
        self._quotes_cache = {}
    
    def clear_cache(self):
        """Clear all cached data"""
        self._indicators_cache = {}
        self._quotes_cache = {}
    
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
            
            # Get underlying price from cache or fetch
            underlying_price = self._quotes_cache.get(symbol)
            if underlying_price is None:
                quote_url = f"{self.base_url}/markets/quotes"
                quote_params = {"symbols": symbol}
                quote_response = requests.get(quote_url, headers=self.headers, params=quote_params)
                
                if quote_response.status_code == 200:
                    quote_data = quote_response.json()
                    if 'quotes' in quote_data and 'quote' in quote_data['quotes']:
                        quote = quote_data['quotes']['quote']
                        underlying_price = quote.get('last', 0)
                        self._quotes_cache[symbol] = underlying_price
            
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

    def get_indicators(self, symbol, rsi_period=14, bb_period=20):
        """
        Get RSI, IV Rank, and Bollinger %B with a SINGLE API call (365 days of history).
        Results are cached for the session.
        
        Returns:
            dict: {'rsi': float, 'iv_rank': float, 'bb_pct_b': float} or all None
        """
        # Check cache first
        if symbol in self._indicators_cache:
            return self._indicators_cache[symbol]
        
        result = {'rsi': None, 'iv_rank': None, 'bb_pct_b': None}
        
        try:
            # Single API call for 365 days of history (enough for both RSI and IV Rank)
            url = f"{self.base_url}/markets/history"
            params = {
                "symbol": symbol,
                "interval": "daily",
                "start": (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                "end": datetime.now().strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code != 200:
                self._indicators_cache[symbol] = result
                return result
            
            data = response.json()
            
            if 'history' not in data or not data['history']:
                self._indicators_cache[symbol] = result
                return result
            
            history = data['history'].get('day', [])
            if not history:
                self._indicators_cache[symbol] = result
                return result
            
            # Extract close prices
            closes = [float(d['close']) for d in history if 'close' in d]
            
            # Calculate RSI (needs at least rsi_period + 1 days)
            if len(closes) >= rsi_period + 1:
                deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
                gains = [d if d > 0 else 0 for d in deltas]
                losses = [-d if d < 0 else 0 for d in deltas]
                
                avg_gain = sum(gains[-rsi_period:]) / rsi_period
                avg_loss = sum(losses[-rsi_period:]) / rsi_period
                
                if avg_loss == 0:
                    result['rsi'] = 100
                else:
                    rs = avg_gain / avg_loss
                    result['rsi'] = round(100 - (100 / (1 + rs)), 2)
            
            # Calculate IV Rank (needs at least 30 days for rolling volatility)
            if len(closes) >= 30:
                returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
                
                # Calculate rolling 30-day volatility
                volatilities = []
                window = 30
                for i in range(window, len(returns)):
                    window_returns = returns[i-window:i]
                    mean_return = sum(window_returns) / len(window_returns)
                    variance = sum((r - mean_return)**2 for r in window_returns) / len(window_returns)
                    vol = math.sqrt(variance) * math.sqrt(252) * 100  # Annualized
                    volatilities.append(vol)
                
                if volatilities:
                    current_iv = volatilities[-1]
                    iv_high = max(volatilities)
                    iv_low = min(volatilities)
                    
                    if iv_high == iv_low:
                        result['iv_rank'] = 50
                    else:
                        result['iv_rank'] = round(((current_iv - iv_low) / (iv_high - iv_low)) * 100, 1)
            
            # Calculate Bollinger Band %B (needs at least bb_period days)
            # %B = (Price - Lower Band) / (Upper Band - Lower Band)
            # %B < 0 = below lower band, %B > 1 = above upper band
            # %B = 0.5 = at middle band (SMA)
            if len(closes) >= bb_period:
                # Calculate 20-day SMA (middle band)
                sma = sum(closes[-bb_period:]) / bb_period
                
                # Calculate standard deviation
                variance = sum((p - sma) ** 2 for p in closes[-bb_period:]) / bb_period
                std_dev = math.sqrt(variance)
                
                # Calculate bands (2 standard deviations)
                upper_band = sma + (2 * std_dev)
                lower_band = sma - (2 * std_dev)
                
                # Calculate %B
                current_price = closes[-1]
                if upper_band != lower_band:
                    bb_pct_b = (current_price - lower_band) / (upper_band - lower_band)
                    result['bb_pct_b'] = round(bb_pct_b, 2)
                else:
                    result['bb_pct_b'] = 0.5  # At middle if no volatility
            
            # Cache the result
            self._indicators_cache[symbol] = result
            return result
            
        except Exception as e:
            print(f"Error getting indicators for {symbol}: {e}")
            self._indicators_cache[symbol] = result
            return result
    
    def get_rsi(self, symbol, period=14):
        """Get RSI for a symbol (uses cached combined indicator fetch)"""
        indicators = self.get_indicators(symbol, rsi_period=period)
        return indicators.get('rsi')
    
    def get_iv_rank(self, symbol):
        """Get IV Rank for a symbol (uses cached combined indicator fetch)"""
        indicators = self.get_indicators(symbol)
        return indicators.get('iv_rank')
    
    def get_batch_quotes(self, symbols):
        """
        Get quotes for multiple symbols in a single API call.
        Tradier supports up to 100 symbols per request.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            dict: {symbol: price} mapping
        """
        if not symbols:
            return {}
        
        results = {}
        
        # Tradier allows up to 100 symbols per request
        batch_size = 100
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            
            # Check cache first
            uncached = [s for s in batch if s not in self._quotes_cache]
            
            if uncached:
                try:
                    url = f"{self.base_url}/markets/quotes"
                    params = {"symbols": ",".join(uncached)}
                    response = requests.get(url, headers=self.headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'quotes' in data and 'quote' in data['quotes']:
                            quotes = data['quotes']['quote']
                            if isinstance(quotes, dict):
                                quotes = [quotes]
                            
                            for quote in quotes:
                                symbol = quote.get('symbol')
                                price = quote.get('last', 0)
                                if symbol:
                                    self._quotes_cache[symbol] = price
                except Exception as e:
                    print(f"Error fetching batch quotes: {e}")
            
            # Return from cache
            for symbol in batch:
                results[symbol] = self._quotes_cache.get(symbol)
        
        return results
    
    def prefetch_indicators(self, symbols, max_workers=10):
        """
        Prefetch RSI and IV Rank for multiple symbols in parallel.
        Uses ThreadPoolExecutor for concurrent API calls.
        
        Args:
            symbols: List of stock symbols
            max_workers: Maximum number of concurrent threads (default 10)
            
        Returns:
            dict: {symbol: {'rsi': float, 'iv_rank': float}}
        """
        results = {}
        
        # Filter out already cached symbols
        uncached = [s for s in symbols if s not in self._indicators_cache]
        
        if not uncached:
            # All cached, return from cache
            return {s: self._indicators_cache.get(s, {'rsi': None, 'iv_rank': None}) for s in symbols}
        
        def fetch_single(symbol):
            return symbol, self.get_indicators(symbol)
        
        # Fetch uncached symbols in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_single, s): s for s in uncached}
            
            for future in as_completed(futures):
                try:
                    symbol, indicators = future.result()
                    results[symbol] = indicators
                except Exception as e:
                    symbol = futures[future]
                    print(f"Error prefetching indicators for {symbol}: {e}")
                    results[symbol] = {'rsi': None, 'iv_rank': None}
        
        # Combine with cached results
        for symbol in symbols:
            if symbol not in results:
                results[symbol] = self._indicators_cache.get(symbol, {'rsi': None, 'iv_rank': None})
        
        return results

    def prefetch_option_chains(self, symbols, min_dte=0, max_dte=60, max_workers=5):
        """
        Prefetch option chains for multiple symbols in parallel.
        Uses ThreadPoolExecutor for concurrent API calls.
        
        Args:
            symbols: List of stock symbols
            min_dte: Minimum days to expiration
            max_dte: Maximum days to expiration
            max_workers: Maximum number of concurrent threads (default 5 to avoid rate limits)
            
        Returns:
            dict: {symbol: chain_data} mapping
        """
        results = {}
        
        def fetch_single(symbol):
            return symbol, self.get_option_chains(symbol, min_dte=min_dte, max_dte=max_dte)
        
        # Fetch all symbols in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_single, s): s for s in symbols}
            
            for future in as_completed(futures):
                try:
                    symbol, chain_data = future.result()
                    results[symbol] = chain_data
                except Exception as e:
                    symbol = futures[future]
                    print(f"Error prefetching option chain for {symbol}: {e}")
                    results[symbol] = None
        
        return results

    def get_option_quote(self, option_symbol):
        """
        Get current quote for an option symbol
        
        Args:
            option_symbol (str): Full option symbol (e.g., 'AAPL  260116C00255000')
            
        Returns:
            dict: Quote data with bid, ask, last, etc.
        """
        try:
            # Tradier uses a different endpoint for quotes
            url = f"{self.base_url}/markets/quotes"
            params = {"symbols": option_symbol, "greeks": "false"}
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'quotes' in data and 'quote' in data['quotes']:
                    quote = data['quotes']['quote']
                    
                    # Handle single quote vs array of quotes
                    if isinstance(quote, list):
                        quote = quote[0] if len(quote) > 0 else None
                    
                    if quote:
                        return quote
                
                return None
            else:
                return None
                
        except Exception as e:
            print(f"Error getting option quote for {option_symbol}: {str(e)}")
            return None
