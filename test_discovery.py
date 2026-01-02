"""
Discovery Module Component Testing Script
Tests each function individually to diagnose issues
"""

import sys
sys.path.append('/home/ubuntu')

from utils.discovery import (
    get_sp500_tickers,
    get_options_volume,
    calculate_iv_percentile,
    calculate_vix_correlation,
    detect_unusual_activity
)

print("=" * 80)
print("DISCOVERY MODULE COMPONENT TESTING")
print("=" * 80)
print()

# Test 1: Get S&P 500 Tickers
print("TEST 1: Fetching S&P 500 Tickers from Wikipedia")
print("-" * 80)
try:
    tickers = get_sp500_tickers()
    print(f"✅ SUCCESS: Retrieved {len(tickers)} tickers")
    print(f"First 10 tickers: {tickers[:10]}")
    print()
except Exception as e:
    print(f"❌ FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    print()

# Test 2: Get Options Volume for a known liquid stock (AAPL)
print("TEST 2: Fetching Options Data for AAPL (known liquid stock)")
print("-" * 80)
try:
    opt_data = get_options_volume('AAPL')
    if opt_data:
        print(f"✅ SUCCESS: Retrieved options data for AAPL")
        print(f"  Symbol: {opt_data['symbol']}")
        print(f"  Price: ${opt_data['price']:.2f}")
        print(f"  Options Volume: {opt_data['options_volume']:,}")
        print(f"  Calls Volume: {opt_data['calls_volume']:,}")
        print(f"  Puts Volume: {opt_data['puts_volume']:,}")
        print(f"  Avg IV: {opt_data['avg_iv']*100:.2f}%")
        print(f"  Open Interest: {opt_data['open_interest']:,}")
        print(f"  Avg Spread %: {opt_data['avg_spread_pct']:.2f}%")
        print(f"  Nearest Expiration: {opt_data['nearest_expiration']}")
        print()
    else:
        print(f"❌ FAILED: No options data returned for AAPL")
        print()
except Exception as e:
    print(f"❌ FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    print()

# Test 3: Calculate IV Percentile for AAPL
print("TEST 3: Calculating IV Percentile for AAPL")
print("-" * 80)
try:
    iv_pct = calculate_iv_percentile('AAPL')
    if iv_pct is not None:
        print(f"✅ SUCCESS: IV Percentile = {iv_pct:.1f}%")
        print()
    else:
        print(f"❌ FAILED: IV Percentile returned None")
        print()
except Exception as e:
    print(f"❌ FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    print()

# Test 4: Calculate VIX Correlation for AAPL
print("TEST 4: Calculating VIX Correlation for AAPL")
print("-" * 80)
try:
    vix_corr = calculate_vix_correlation('AAPL')
    if vix_corr is not None:
        print(f"✅ SUCCESS: VIX Correlation = {vix_corr:.3f}")
        print()
    else:
        print(f"❌ FAILED: VIX Correlation returned None")
        print()
except Exception as e:
    print(f"❌ FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    print()

# Test 5: Detect Unusual Activity for AAPL
print("TEST 5: Detecting Unusual Activity for AAPL")
print("-" * 80)
try:
    unusual = detect_unusual_activity('AAPL')
    if unusual:
        print(f"✅ SUCCESS: Unusual activity data retrieved")
        print(f"  Current Volume: {unusual['current_volume']:,}")
        print(f"  Avg Proxy: {unusual['avg_proxy']:,}")
        print(f"  Multiplier: {unusual['multiplier']:.2f}x")
        print(f"  Is Unusual: {unusual['is_unusual']}")
        print()
    else:
        print(f"❌ FAILED: No unusual activity data returned")
        print()
except Exception as e:
    print(f"❌ FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    print()

# Test 6: Test multiple stocks to see pattern
print("TEST 6: Testing Multiple High-Volume Stocks")
print("-" * 80)
test_symbols = ['AAPL', 'MSFT', 'TSLA', 'NVDA', 'SPY']
results = []

for symbol in test_symbols:
    print(f"\nTesting {symbol}...")
    try:
        opt_data = get_options_volume(symbol)
        if opt_data:
            print(f"  ✅ Options Volume: {opt_data['options_volume']:,}")
            print(f"  ✅ Price: ${opt_data['price']:.2f}")
            print(f"  ✅ Avg IV: {opt_data['avg_iv']*100:.1f}%")
            
            # Quick filter test
            if opt_data['options_volume'] >= 5000:
                print(f"  ✅ PASSES volume filter (>= 5,000)")
                results.append(symbol)
            else:
                print(f"  ❌ FAILS volume filter (< 5,000)")
        else:
            print(f"  ❌ No options data available")
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

print()
print(f"Stocks passing volume filter: {results}")
print()

# Test 7: Check yfinance installation and basic functionality
print("TEST 7: Checking yfinance Package")
print("-" * 80)
try:
    import yfinance as yf
    print(f"✅ yfinance is installed")
    
    # Test basic ticker fetch
    ticker = yf.Ticker("AAPL")
    info = ticker.info
    print(f"✅ Can fetch ticker info")
    print(f"  Symbol: {info.get('symbol', 'N/A')}")
    print(f"  Name: {info.get('longName', 'N/A')}")
    print(f"  Current Price: ${info.get('currentPrice', info.get('regularMarketPrice', 0)):.2f}")
    
    # Test options dates
    options_dates = ticker.options
    print(f"✅ Can fetch options dates: {len(options_dates)} expirations available")
    print(f"  First 5 dates: {options_dates[:5]}")
    
    # Test option chain
    if options_dates:
        chain = ticker.option_chain(options_dates[0])
        print(f"✅ Can fetch option chain")
        print(f"  Calls: {len(chain.calls)} contracts")
        print(f"  Puts: {len(chain.puts)} contracts")
    
    print()
    
except ImportError:
    print(f"❌ yfinance is NOT installed")
    print()
except Exception as e:
    print(f"❌ Error testing yfinance: {str(e)}")
    import traceback
    traceback.print_exc()
    print()

# Test 8: Check BeautifulSoup for Wikipedia scraping
print("TEST 8: Checking BeautifulSoup Package")
print("-" * 80)
try:
    from bs4 import BeautifulSoup
    import requests
    print(f"✅ BeautifulSoup is installed")
    
    # Test Wikipedia fetch
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    response = requests.get(url, timeout=10)
    print(f"✅ Can connect to Wikipedia")
    print(f"  Status Code: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'wikitable sortable'})
    if table:
        print(f"✅ Can parse S&P 500 table")
        rows = table.findAll('tr')[1:]
        print(f"  Found {len(rows)} rows")
    else:
        print(f"❌ Could not find S&P 500 table")
    
    print()
    
except ImportError as e:
    print(f"❌ Missing package: {str(e)}")
    print()
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    print()

# Summary
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("""
If all tests pass:
  ✅ All components are working correctly
  ✅ Issue is likely with filter settings being too strict

If some tests fail:
  ❌ Identify which component is failing
  ❌ Check error messages for root cause
  ❌ May need to adjust implementation or dependencies

Common Issues:
  1. No options data: Stock may not have options available
  2. IV Percentile None: Insufficient historical data
  3. VIX Correlation None: Insufficient price history
  4. Volume filter: Filters may be too strict for current market
""")
print("=" * 80)