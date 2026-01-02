import pandas as pd
from datetime import datetime, timedelta
import time
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple in-memory cache
_cache = {}
_cache_duration = 3600  # 1 hour in seconds

def _get_cached_or_fetch(symbol, fetch_func):
    """Get data from cache or fetch if expired"""
    cache_key = f"{symbol}_{fetch_func.__name__}"
    
    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if time.time() - timestamp < _cache_duration:
            return data
    
    # Fetch new data
    data = fetch_func(symbol)
    
    if data is not None:
        _cache[cache_key] = (data, time.time())
    
    return data

def get_historical_data_tradier(symbol, days=365):
    """Get historical price data from Tradier API"""
    try:
        api_key = os.getenv('TRADIER_API_KEY', '')
        
        if not api_key:
            print(f"ERROR: TRADIER_API_KEY not set in environment")
            return None
        
        base_url = 'https://api.tradier.com/v1'
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f'{base_url}/markets/history'
        params = {
            'symbol': symbol,
            'interval': 'daily',
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Failed to get history for {symbol}: HTTP {response.status_code}")
            if response.status_code == 401:
                print(f"  Authentication failed. Check TRADIER_API_KEY")
            return None
        
        data = response.json()
        
        if not data.get('history') or not data['history'].get('day'):
            print(f"No historical data for {symbol}")
            return None
        
        # Convert to pandas DataFrame
        days_data = data['history']['day']
        
        # Handle single day response (dict) vs multiple days (list)
        if isinstance(days_data, dict):
            days_data = [days_data]
        
        df = pd.DataFrame(days_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df.sort_index()
        
        return df
        
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {str(e)}")
        return None

def get_quote_tradier(symbol):
    """Get current quote data from Tradier API"""
    try:
        api_key = os.getenv('TRADIER_API_KEY', '')
        
        if not api_key:
            return None
        
        base_url = 'https://api.tradier.com/v1'
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
        
        url = f'{base_url}/markets/quotes'
        params = {'symbols': symbol}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if 'quotes' in data and 'quote' in data['quotes']:
            return data['quotes']['quote']
        
        return None
        
    except Exception as e:
        print(f"Error fetching quote for {symbol}: {str(e)}")
        return None

def calculate_rsi(prices, period=14):
    """Calculate RSI (Relative Strength Index)"""
    try:
        if len(prices) < period:
            return None
            
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1]
    except Exception as e:
        print(f"Error calculating RSI: {str(e)}")
        return None

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands %"""
    try:
        if len(prices) < period:
            return None
            
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        current_price = prices.iloc[-1]
        bb_percent = ((current_price - lower_band.iloc[-1]) / 
                     (upper_band.iloc[-1] - lower_band.iloc[-1])) * 100
        
        return bb_percent
    except Exception as e:
        print(f"Error calculating Bollinger Bands: {str(e)}")
        return None

def calculate_ma_percent(prices, period=50):
    """Calculate % distance from moving average"""
    try:
        if len(prices) < period:
            return None
            
        ma = prices.rolling(window=period).mean().iloc[-1]
        current_price = prices.iloc[-1]
        
        ma_percent = ((current_price - ma) / ma) * 100
        
        return ma_percent
    except Exception as e:
        print(f"Error calculating MA: {str(e)}")
        return None

def calculate_52week_percent(prices):
    """Calculate position in 52-week range"""
    try:
        if len(prices) < 252:
            high_52w = prices.max()
            low_52w = prices.min()
        else:
            high_52w = prices.iloc[-252:].max()
            low_52w = prices.iloc[-252:].min()
        
        current_price = prices.iloc[-1]
        
        if high_52w == low_52w:
            return 50.0
        
        percent_52w = ((current_price - low_52w) / (high_52w - low_52w)) * 100
        
        return percent_52w
    except Exception as e:
        print(f"Error calculating 52-week %: {str(e)}")
        return None

def calculate_avg_volume(hist, period=30):
    """Calculate average daily volume over specified period"""
    try:
        if hist is None or hist.empty:
            return None
        
        if 'volume' not in hist.columns:
            return None
        
        # Get last N days of volume
        recent_volume = hist['volume'].tail(period)
        
        if len(recent_volume) == 0:
            return None
        
        avg_vol = recent_volume.mean()
        
        return int(avg_vol) if avg_vol > 0 else None
        
    except Exception as e:
        print(f"Error calculating average volume: {str(e)}")
        return None

def calculate_support_distance(prices):
    """Calculate distance from nearest support level (52-week low)"""
    try:
        if len(prices) < 252:
            low_52w = prices.min()
        else:
            low_52w = prices.iloc[-252:].min()
        
        current_price = prices.iloc[-1]
        
        if low_52w == 0:
            return None
        
        # % distance above 52-week low (support level)
        support_distance = ((current_price - low_52w) / low_52w) * 100
        
        return support_distance
        
    except Exception as e:
        print(f"Error calculating support distance: {str(e)}")
        return None

def calculate_bid_ask_spread(quote_data):
    """Calculate bid-ask spread percentage"""
    try:
        if not quote_data:
            return None
        
        bid = quote_data.get('bid', 0)
        ask = quote_data.get('ask', 0)
        
        if bid is None or ask is None or bid == 0:
            return None
        
        spread_pct = ((ask - bid) / bid) * 100
        
        return spread_pct
        
    except Exception as e:
        print(f"Error calculating bid-ask spread: {str(e)}")
        return None

def get_technical_indicators(symbol):
    """Get all technical indicators for a symbol using Tradier data"""
    
    def _fetch_indicators(sym):
        hist = get_historical_data_tradier(sym, days=365)
        
        if hist is None or hist.empty:
            return None
        
        prices = hist['close']
        
        # Get quote data for bid-ask spread
        quote_data = get_quote_tradier(sym)
        
        indicators = {
            'symbol': sym,
            'current_price': prices.iloc[-1],
            'rsi': calculate_rsi(prices),
            'bb_percent': calculate_bollinger_bands(prices),
            'ma_percent': calculate_ma_percent(prices),
            'week_52_percent': calculate_52week_percent(prices),
            'avg_volume': calculate_avg_volume(hist, period=30),  # NEW
            'support_distance': calculate_support_distance(prices),  # NEW
            'bid_ask_spread': calculate_bid_ask_spread(quote_data),  # NEW
        }
        
        return indicators
    
    return _get_cached_or_fetch(symbol, _fetch_indicators)

def test_tradier_indicators(symbols):
    """Test Tradier-based technical indicators"""
    print(f"\n{'='*60}")
    print(f"Testing Tradier Technical Indicators with {len(symbols)} symbols")
    print(f"{'='*60}\n")
    
    api_key = os.getenv('TRADIER_API_KEY', '')
    if not api_key:
        print("❌ ERROR: TRADIER_API_KEY not found in environment!")
        print("   Make sure .env file exists and contains TRADIER_API_KEY")
        return []
    else:
        print(f"✅ API Key loaded: {api_key[:10]}...{api_key[-4:]}\n")
    
    results = []
    
    for symbol in symbols:
        print(f"Testing {symbol}...")
        indicators = get_technical_indicators(symbol)
        
        if indicators:
            print(f"  ✅ Success!")
            print(f"     Price: ${indicators['current_price']:.2f}")
            print(f"     RSI: {indicators['rsi']:.1f}" if indicators['rsi'] else "     RSI: N/A")
            print(f"     BB%: {indicators['bb_percent']:.1f}%" if indicators['bb_percent'] else "     BB%: N/A")
            print(f"     MA%: {indicators['ma_percent']:.1f}%" if indicators['ma_percent'] else "     MA%: N/A")
            print(f"     52W%: {indicators['week_52_percent']:.1f}%" if indicators['week_52_percent'] else "     52W%: N/A")
            print(f"     Avg Volume: {indicators['avg_volume']:,}" if indicators['avg_volume'] else "     Avg Volume: N/A")
            print(f"     Support Dist: {indicators['support_distance']:.1f}%" if indicators['support_distance'] else "     Support Dist: N/A")
            print(f"     Bid-Ask Spread: {indicators['bid_ask_spread']:.2f}%" if indicators['bid_ask_spread'] else "     Bid-Ask Spread: N/A")
            results.append((symbol, True))
        else:
            print(f"  ❌ Failed")
            results.append((symbol, False))
        
        print()
        time.sleep(0.5)
    
    print(f"\n{'='*60}")
    print(f"Summary: {sum(1 for _, success in results if success)}/{len(symbols)} successful")
    print(f"{'='*60}\n")
    
    return results