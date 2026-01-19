"""
Market hours utility functions with real-time market status check
"""

from datetime import datetime
import pytz
import requests

def is_market_actually_open():
    """
    Check if market is ACTUALLY open by querying Yahoo Finance for real-time data.
    This accounts for holidays and early closures.
    
    Returns:
        bool: True if market is actively trading, False otherwise
    """
    try:
        # Query Yahoo Finance for SPY (S&P 500 ETF) - highly liquid, always trades when market is open
        url = "https://query1.finance.yahoo.com/v8/finance/chart/SPY"
        params = {
            'interval': '1m',
            'range': '1d'
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we have current trading data
            if 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                meta = result.get('meta', {})
                
                # Check market state from Yahoo Finance
                market_state = meta.get('marketState', 'CLOSED')
                trading_period = meta.get('currentTradingPeriod', {})
                
                # Market states: REGULAR, PRE, POST, CLOSED
                # We only consider REGULAR as "open"
                if market_state == 'REGULAR':
                    return True
                    
        return False
        
    except Exception as e:
        # If API fails, fall back to time-based check
        return False


def get_market_status():
    """
    Check if US stock market is currently open (accounts for holidays)
    
    Returns:
        dict: {
            'is_open': bool,
            'status': str ('open', 'closing_soon', 'closed'),
            'message': str,
            'icon': str (emoji),
            'color': str ('green', 'yellow', 'red')
        }
    """
    # Get current time in Eastern Time
    et_tz = pytz.timezone('US/Eastern')
    now_et = datetime.now(et_tz)
    
    # Market hours: 9:30 AM - 4:00 PM ET, Monday-Friday
    market_open_time = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close_time = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    closing_soon_time = now_et.replace(hour=15, minute=0, second=0, microsecond=0)  # Last hour
    
    # Check if it's a weekday (0 = Monday, 6 = Sunday)
    is_weekday = now_et.weekday() < 5
    
    # Check if we're in normal trading hours
    is_during_hours = market_open_time <= now_et < market_close_time
    is_closing_soon = closing_soon_time <= now_et < market_close_time
    
    # If it's a weekday and during trading hours, check if market is ACTUALLY open (not a holiday)
    if is_weekday and is_during_hours:
        actually_open = is_market_actually_open()
        
        if actually_open:
            if is_closing_soon:
                return {
                    'is_open': True,
                    'status': 'closing_soon',
                    'message': f'Market closing soon (closes at 4:00 PM ET)',
                    'icon': '🟡',
                    'color': 'yellow',
                    'current_time_et': now_et.strftime('%I:%M %p ET')
                }
            else:
                return {
                    'is_open': True,
                    'status': 'open',
                    'message': f'Market is open (9:30 AM - 4:00 PM ET)',
                    'icon': '🟢',
                    'color': 'green',
                    'current_time_et': now_et.strftime('%I:%M %p ET')
                }
        else:
            # It's during normal hours but market is closed (holiday)
            return {
                'is_open': False,
                'status': 'closed',
                'message': 'Market is closed (Holiday)',
                'icon': '🔴',
                'color': 'red',
                'current_time_et': now_et.strftime('%I:%M %p ET')
            }
    else:
        # Outside normal trading hours or weekend
        if not is_weekday:
            return {
                'is_open': False,
                'status': 'closed',
                'message': 'Market is closed (Weekend)',
                'icon': '🔴',
                'color': 'red',
                'current_time_et': now_et.strftime('%I:%M %p ET')
            }
        else:
            if now_et < market_open_time:
                return {
                    'is_open': False,
                    'status': 'closed',
                    'message': f'Market opens at 9:30 AM ET',
                    'icon': '🔴',
                    'color': 'red',
                    'current_time_et': now_et.strftime('%I:%M %p ET')
                }
            else:
                return {
                    'is_open': False,
                    'status': 'closed',
                    'message': f'Market is closed (opens tomorrow at 9:30 AM ET)',
                    'icon': '🔴',
                    'color': 'red',
                    'current_time_et': now_et.strftime('%I:%M %p ET')
                }
