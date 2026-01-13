"""
Tastytrade Quote Fetching using the official SDK

This module uses the official tastytrade Python SDK to fetch option quotes,
which handles the API calls correctly.
"""

import os
import streamlit as st

def get_option_quotes_sdk(option_symbols):
    """
    Get quotes for multiple option symbols using the tastytrade SDK
    
    Args:
        option_symbols: List of option symbols (OCC format)
        
    Returns:
        dict mapping symbol to quote data {bid, ask, mid, last}
    """
    if not option_symbols:
        return {}
    
    quotes = {}
    
    try:
        from tastytrade import Session
        from tastytrade.market_data import get_market_data_by_type
        
        # Get credentials from environment or Streamlit secrets
        username = os.getenv('TASTYTRADE_USERNAME')
        password = os.getenv('TASTYTRADE_PASSWORD')
        
        # Try Streamlit secrets if env vars not set
        if not username or not password:
            try:
                username = st.secrets.get('TASTYTRADE_USERNAME')
                password = st.secrets.get('TASTYTRADE_PASSWORD')
            except:
                pass
        
        if not username or not password:
            print("DEBUG: Tastytrade credentials not found")
            return {}
        
        # Create session using the SDK
        # Cache the session in Streamlit session state
        if 'tastytrade_sdk_session' not in st.session_state:
            print("DEBUG: Creating new Tastytrade SDK session")
            st.session_state.tastytrade_sdk_session = Session(username, password)
        
        session = st.session_state.tastytrade_sdk_session
        
        # Debug: log the symbols being requested
        print(f"DEBUG SDK: Requesting quotes for {len(option_symbols)} symbols")
        if option_symbols:
            print(f"DEBUG SDK: First symbol: '{option_symbols[0]}' (len={len(option_symbols[0])})")
            print(f"DEBUG SDK: All symbols: {option_symbols}")
        
        # Fetch quotes using the SDK
        # The SDK's get_market_data_by_type expects options in OCC format
        market_data = get_market_data_by_type(
            session,
            options=option_symbols
        )
        
        print(f"DEBUG SDK: Got {len(market_data)} market data items")
        
        # Parse the response
        for item in market_data:
            sym = item.symbol
            quotes[sym] = {
                'bid': float(item.bid) if item.bid else 0,
                'ask': float(item.ask) if item.ask else 0,
                'mid': float(item.mid) if item.mid else 0,
                'last': float(item.last) if item.last else 0,
                'mark': float(item.mark) if item.mark else 0,
            }
            print(f"DEBUG SDK: Quote for {sym}: bid={quotes[sym]['bid']}, ask={quotes[sym]['ask']}")
        
        print(f"DEBUG SDK: Returning {len(quotes)} quotes")
        return quotes
        
    except ImportError as e:
        print(f"DEBUG SDK: tastytrade SDK not installed: {e}")
        return {}
    except Exception as e:
        print(f"DEBUG SDK: Error fetching quotes: {e}")
        import traceback
        traceback.print_exc()
        return {}


def clear_sdk_session():
    """Clear the cached SDK session (useful if credentials change)"""
    if 'tastytrade_sdk_session' in st.session_state:
        del st.session_state.tastytrade_sdk_session
