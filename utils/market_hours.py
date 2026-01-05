"""
Market hours utility functions
"""

from datetime import datetime
import pytz

def get_market_status():
    """
    Check if US stock market is currently open
    
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
    
    # Check if market is open
    is_during_hours = market_open_time <= now_et < market_close_time
    is_closing_soon = closing_soon_time <= now_et < market_close_time
    
    if is_weekday and is_during_hours:
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
