"""
Discovery Module for Options Trading
Finds high-potential stocks based on options volume, IV, VIX correlation, and unusual activity
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import time


def get_sp500_tickers() -> List[str]:
    """
    Get list of S&P 500 tickers from Wikipedia
    Returns a list of stock symbols
    """
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'wikitable sortable'})
        
        tickers = []
        for row in table.findAll('tr')[1:]:
            ticker = row.findAll('td')[0].text.strip()
            tickers.append(ticker)
        
        return tickers
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        # Fallback to a curated list of highly liquid stocks
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B',
            'JPM', 'V', 'UNH', 'XOM', 'JNJ', 'WMT', 'MA', 'PG', 'HD', 'CVX',
            'MRK', 'ABBV', 'KO', 'PEP', 'COST', 'AVGO', 'TMO', 'MCD', 'CSCO',
            'ACN', 'ABT', 'LIN', 'ADBE', 'DHR', 'NKE', 'VZ', 'TXN', 'NEE',
            'ORCL', 'CRM', 'PM', 'WFC', 'DIS', 'BMY', 'RTX', 'UPS', 'QCOM',
            'INTC', 'HON', 'INTU', 'AMD', 'BA', 'AMGN', 'CAT', 'GE', 'IBM',
            'AMAT', 'NOW', 'SBUX', 'LOW', 'SPGI', 'ELV', 'GS', 'PLD', 'BLK',
            'DE', 'AXP', 'SYK', 'GILD', 'MDLZ', 'TJX', 'BKNG', 'ADI', 'MMC',
            'C', 'VRTX', 'LRCX', 'AMT', 'REGN', 'ADP', 'CVS', 'MO', 'CI',
            'ISRG', 'ZTS', 'PGR', 'SO', 'DUK', 'CB', 'SCHW', 'ETN', 'NOC',
            'SLB', 'BDX', 'EQIX', 'ITW', 'BSX', 'MMM', 'CME', 'EOG', 'PNC'
        ]


def get_options_volume(symbol: str) -> Optional[Dict]:
    """
    Get options volume and related data for a symbol
    Returns dict with volume, IV, and other metrics
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Get basic info
        info = ticker.info
        
        # Get current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        
        # Get options dates
        options_dates = ticker.options
        if not options_dates:
            return None
        
        # Get nearest expiration options chain
        nearest_exp = options_dates[0]
        opt_chain = ticker.option_chain(nearest_exp)
        
        # Calculate total options volume (calls + puts)
        calls_volume = opt_chain.calls['volume'].sum()
        puts_volume = opt_chain.puts['volume'].sum()
        total_volume = calls_volume + puts_volume
        
        # Get average implied volatility
        calls_iv = opt_chain.calls['impliedVolatility'].mean()
        puts_iv = opt_chain.puts['impliedVolatility'].mean()
        avg_iv = (calls_iv + puts_iv) / 2
        
        # Get open interest
        calls_oi = opt_chain.calls['openInterest'].sum()
        puts_oi = opt_chain.puts['openInterest'].sum()
        total_oi = calls_oi + puts_oi
        
        # Calculate bid-ask spread (average of ATM options)
        atm_calls = opt_chain.calls[
            (opt_chain.calls['strike'] >= current_price * 0.95) &
            (opt_chain.calls['strike'] <= current_price * 1.05)
        ]
        
        if len(atm_calls) > 0:
            avg_spread = ((atm_calls['ask'] - atm_calls['bid']) / atm_calls['bid']).mean()
        else:
            avg_spread = 0
        
        return {
            'symbol': symbol,
            'price': current_price,
            'options_volume': int(total_volume),
            'calls_volume': int(calls_volume),
            'puts_volume': int(puts_volume),
            'avg_iv': avg_iv,
            'open_interest': int(total_oi),
            'avg_spread_pct': avg_spread * 100,
            'nearest_expiration': nearest_exp
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error fetching options data for {symbol}: {e}")
        print(f"Full traceback: {error_details}")
        return None


def calculate_iv_percentile(symbol: str, days: int = 252) -> Optional[float]:
    """
    Calculate IV percentile (current IV vs. historical range)
    Returns percentile (0-100)
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Get historical volatility
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        hist = ticker.history(start=start_date, end=end_date)
        
        if len(hist) < 30:
            return None
        
        # Calculate historical volatility (rolling 30-day)
        hist['returns'] = hist['Close'].pct_change()
        hist['volatility'] = hist['returns'].rolling(window=30).std() * np.sqrt(252)
        
        # Get current IV
        options_dates = ticker.options
        if not options_dates:
            return None
        
        opt_chain = ticker.option_chain(options_dates[0])
        current_iv = opt_chain.calls['impliedVolatility'].mean()
        
        # Calculate percentile
        volatilities = hist['volatility'].dropna()
        if len(volatilities) == 0:
            return None
        
        percentile = (volatilities < current_iv).sum() / len(volatilities) * 100
        
        return percentile
        
    except Exception as e:
        print(f"Error calculating IV percentile for {symbol}: {e}")
        return None


def calculate_vix_correlation(symbol: str, days: int = 30) -> Optional[float]:
    """
    Calculate correlation between stock and VIX over specified period
    Returns correlation coefficient (-1 to 1)
    """
    try:
        # Get stock data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days * 2)  # Extra buffer
        
        stock = yf.Ticker(symbol)
        stock_hist = stock.history(start=start_date, end=end_date)
        
        # Get VIX data
        vix = yf.Ticker('^VIX')
        vix_hist = vix.history(start=start_date, end=end_date)
        
        if len(stock_hist) < 20 or len(vix_hist) < 20:
            return None
        
        # Calculate daily returns
        stock_returns = stock_hist['Close'].pct_change().dropna()
        vix_returns = vix_hist['Close'].pct_change().dropna()
        
        # Remove timezone info to allow date matching
        stock_returns.index = stock_returns.index.tz_localize(None)
        vix_returns.index = vix_returns.index.tz_localize(None)
        
        # Align dates
        common_dates = stock_returns.index.intersection(vix_returns.index)
        if len(common_dates) < 20:
            return None
        
        stock_returns = stock_returns.loc[common_dates]
        vix_returns = vix_returns.loc[common_dates]
        
        # Calculate correlation
        correlation = stock_returns.corr(vix_returns)
        
        return correlation
        
    except Exception as e:
        print(f"Error calculating VIX correlation for {symbol}: {e}")
        return None


def detect_unusual_activity(symbol: str, lookback_days: int = 20) -> Optional[Dict]:
    """
    Detect unusual options activity by comparing current volume to average
    Returns dict with current volume, average volume, and multiplier
    """
    try:
        ticker = yf.Ticker(symbol)
        options_dates = ticker.options
        
        if not options_dates or len(options_dates) < 2:
            return None
        
        # Get current day options volume
        current_chain = ticker.option_chain(options_dates[0])
        current_volume = (
            current_chain.calls['volume'].sum() + 
            current_chain.puts['volume'].sum()
        )
        
        # Estimate average volume (simplified - would need historical options data for accuracy)
        # For now, use open interest as a proxy for typical activity
        avg_oi = (
            current_chain.calls['openInterest'].mean() + 
            current_chain.puts['openInterest'].mean()
        ) / 2
        
        # If current volume is significantly higher than typical OI, it's unusual
        if avg_oi > 0:
            multiplier = current_volume / avg_oi
        else:
            multiplier = 1.0
        
        return {
            'current_volume': int(current_volume),
            'avg_proxy': int(avg_oi),
            'multiplier': multiplier,
            'is_unusual': multiplier >= 2.0
        }
        
    except Exception as e:
        print(f"Error detecting unusual activity for {symbol}: {e}")
        return None


def run_discovery_scan(
    min_options_volume: int = 5000,
    min_iv_percentile: float = 50.0,
    min_vix_correlation: float = 0.3,
    unusual_activity_threshold: float = 2.0,
    max_stocks: int = 100,
    progress_callback=None,
    log_callback=None
) -> tuple:
    """
    Run comprehensive discovery scan across S&P 500 stocks
    Returns tuple: (DataFrame with all discovery metrics, log_lines list)
    """
    
    log_lines = []
    log_lines.append("=" * 80)
    log_lines.append("DISCOVERY SCAN LOG")
    log_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_lines.append("")
    log_lines.append("FILTER SETTINGS:")
    log_lines.append(f"  Min Options Volume: {min_options_volume:,}")
    log_lines.append(f"  Min IV Percentile: {min_iv_percentile}%")
    log_lines.append(f"  Min VIX Correlation: {min_vix_correlation}")
    log_lines.append(f"  Unusual Activity Threshold: {unusual_activity_threshold}x")
    log_lines.append(f"  Max Stocks to Scan: {max_stocks}")
    log_lines.append("")
    log_lines.append("=" * 80)
    log_lines.append("")
    
    if log_callback:
        log_callback("Fetching S&P 500 tickers...")
    log_lines.append("Fetching S&P 500 tickers...")
    
    tickers = get_sp500_tickers()[:max_stocks]  # Limit for performance
    log_lines.append(f"Retrieved {len(tickers)} tickers")
    log_lines.append("")
    
    results = []
    stats = {
        'total_scanned': 0,
        'no_options_data': 0,
        'filtered_volume': 0,
        'filtered_iv': 0,
        'filtered_vix': 0,
        'filtered_unusual': 0,
        'passed_all_filters': 0
    }
    
    for i, symbol in enumerate(tickers):
        stats['total_scanned'] += 1
        
        # Add delay to avoid Yahoo Finance rate limiting
        if i > 0:  # Don't delay before first request
            time.sleep(2.0)  # 2 second delay between requests
        
        # Longer pause every 15 stocks to avoid rate limiting
        if i > 0 and i % 15 == 0:
            log_lines.append(f"  ⏸️  Pausing for 10 seconds to avoid rate limiting...")
            time.sleep(10)
        
        if progress_callback:
            progress_callback(f"Scanning {symbol}... ({i+1}/{len(tickers)})", (i+1) / len(tickers))
        
        log_lines.append(f"--- {symbol} ({i+1}/{len(tickers)}) ---")
        
        # Get options volume data
        opt_data = get_options_volume(symbol)
        if not opt_data:
            log_lines.append(f"  ❌ No options data available")
            log_lines.append("")
            stats['no_options_data'] += 1
            continue
        
        log_lines.append(f"  Options Volume: {opt_data['options_volume']:,}")
        log_lines.append(f"  Current Price: ${opt_data['price']:.2f}")
        log_lines.append(f"  Avg IV: {opt_data['avg_iv']*100:.1f}%")
        
        # Skip if volume too low
        if opt_data['options_volume'] < min_options_volume:
            log_lines.append(f"  ❌ FILTERED: Volume {opt_data['options_volume']:,} < {min_options_volume:,}")
            log_lines.append("")
            stats['filtered_volume'] += 1
            continue
        
        # Calculate IV percentile
        iv_pct = calculate_iv_percentile(symbol)
        if iv_pct is not None:
            log_lines.append(f"  IV Percentile: {iv_pct:.1f}%")
        else:
            log_lines.append(f"  IV Percentile: N/A")
        
        # Calculate VIX correlation
        vix_corr = calculate_vix_correlation(symbol)
        if vix_corr is not None:
            log_lines.append(f"  VIX Correlation: {vix_corr:.2f}")
        else:
            log_lines.append(f"  VIX Correlation: N/A")
        
        # Detect unusual activity
        unusual = detect_unusual_activity(symbol)
        if unusual:
            log_lines.append(f"  Volume Multiplier: {unusual['multiplier']:.1f}x")
            log_lines.append(f"  Unusual Activity: {unusual['is_unusual']}")
        else:
            log_lines.append(f"  Unusual Activity: N/A")
        
        # Apply filters and log reasons
        filter_passed = True
        
        if iv_pct is not None and iv_pct < min_iv_percentile:
            log_lines.append(f"  ❌ FILTERED: IV Percentile {iv_pct:.1f}% < {min_iv_percentile}%")
            stats['filtered_iv'] += 1
            filter_passed = False
        
        # Use absolute value for VIX correlation (strength regardless of direction)
        if vix_corr is not None and abs(vix_corr) < min_vix_correlation:
            log_lines.append(f"  ❌ FILTERED: |VIX Correlation| {abs(vix_corr):.2f} < {min_vix_correlation}")
            stats['filtered_vix'] += 1
            filter_passed = False
        
        if unusual and unusual['multiplier'] < unusual_activity_threshold:
            log_lines.append(f"  ❌ FILTERED: Volume Multiplier {unusual['multiplier']:.1f}x < {unusual_activity_threshold}x")
            stats['filtered_unusual'] += 1
            filter_passed = False
        
        if not filter_passed:
            log_lines.append("")
            continue
        
        # Passed all filters!
        log_lines.append(f"  ✅ PASSED ALL FILTERS")
        log_lines.append("")
        stats['passed_all_filters'] += 1
        
        # Compile results
        result = {
            'Symbol': symbol,
            'Price': opt_data['price'],
            'Options Volume': opt_data['options_volume'],
            'Calls Volume': opt_data['calls_volume'],
            'Puts Volume': opt_data['puts_volume'],
            'Avg IV': opt_data['avg_iv'] * 100,  # Convert to percentage
            'IV Percentile': iv_pct if iv_pct else 0,
            'Open Interest': opt_data['open_interest'],
            'Avg Spread %': opt_data['avg_spread_pct'],
            'VIX Correlation': vix_corr if vix_corr else 0,
            'Volume Multiplier': unusual['multiplier'] if unusual else 1.0,
            'Unusual Activity': unusual['is_unusual'] if unusual else False
        }
        
        results.append(result)
    
    # Add summary to log
    log_lines.append("")
    log_lines.append("=" * 80)
    log_lines.append("SUMMARY STATISTICS:")
    log_lines.append(f"  Total Stocks Scanned: {stats['total_scanned']}")
    log_lines.append(f"  No Options Data: {stats['no_options_data']}")
    log_lines.append(f"  Filtered by Volume: {stats['filtered_volume']}")
    log_lines.append(f"  Filtered by IV Percentile: {stats['filtered_iv']}")
    log_lines.append(f"  Filtered by VIX Correlation: {stats['filtered_vix']}")
    log_lines.append(f"  Filtered by Unusual Activity: {stats['filtered_unusual']}")
    log_lines.append(f"  PASSED ALL FILTERS: {stats['passed_all_filters']}")
    log_lines.append("")
    log_lines.append("=" * 80)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    if len(df) == 0:
        return df, log_lines
    
    # Sort by options volume (descending)
    df = df.sort_values('Options Volume', ascending=False)
    
    return df, log_lines