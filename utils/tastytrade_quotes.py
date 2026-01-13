"""
Tastytrade Quote Fetching using the official SDK

This module uses the official tastytrade Python SDK to fetch option quotes,
which handles the API calls correctly.
"""

import os
import streamlit as st

def get_option_quotes_sdk(option_symbols, show_debug=True):
    """
    Get quotes for multiple option symbols using the tastytrade SDK
    
    Args:
        option_symbols: List of option symbols (OCC format)
        show_debug: Whether to show debug info in UI
        
    Returns:
        dict mapping symbol to quote data {bid, ask, mid, last}
    """
    if not option_symbols:
        return {}
    
    quotes = {}
    debug_messages = []
    
    try:
        # Try to import the SDK
        try:
            from tastytrade import Session
            from tastytrade.market_data import get_market_data_by_type
            debug_messages.append("✅ tastytrade SDK imported successfully")
        except ImportError as e:
            debug_messages.append(f"❌ tastytrade SDK not installed: {e}")
            if show_debug:
                with st.expander("🔧 SDK Debug Info", expanded=True):
                    for msg in debug_messages:
                        st.write(msg)
            return {}
        
        # Get credentials from environment or Streamlit secrets
        username = os.getenv('TASTYTRADE_USERNAME')
        password = os.getenv('TASTYTRADE_PASSWORD')
        
        debug_messages.append(f"ENV username: {'✅ Found' if username else '❌ Not found'}")
        debug_messages.append(f"ENV password: {'✅ Found' if password else '❌ Not found'}")
        
        # Try Streamlit secrets if env vars not set
        if not username or not password:
            try:
                username = st.secrets.get('TASTYTRADE_USERNAME')
                password = st.secrets.get('TASTYTRADE_PASSWORD')
                debug_messages.append(f"Secrets username: {'✅ Found' if username else '❌ Not found'}")
                debug_messages.append(f"Secrets password: {'✅ Found' if password else '❌ Not found'}")
            except Exception as e:
                debug_messages.append(f"Secrets error: {e}")
        
        if not username or not password:
            debug_messages.append("❌ Tastytrade credentials not found in env or secrets")
            if show_debug:
                with st.expander("🔧 SDK Debug Info", expanded=True):
                    for msg in debug_messages:
                        st.write(msg)
            return {}
        
        debug_messages.append(f"Username: {username[:3]}***")
        
        # Create session using the SDK
        # Cache the session in Streamlit session state
        if 'tastytrade_sdk_session' not in st.session_state:
            debug_messages.append("Creating new Tastytrade SDK session...")
            try:
                st.session_state.tastytrade_sdk_session = Session(username, password)
                debug_messages.append("✅ SDK Session created successfully")
            except Exception as e:
                debug_messages.append(f"❌ SDK Session creation failed: {e}")
                if show_debug:
                    with st.expander("🔧 SDK Debug Info", expanded=True):
                        for msg in debug_messages:
                            st.write(msg)
                return {}
        else:
            debug_messages.append("✅ Using cached SDK session")
        
        session = st.session_state.tastytrade_sdk_session
        
        # Debug: log the symbols being requested
        debug_messages.append(f"Requesting quotes for {len(option_symbols)} symbols")
        
        # Fetch quotes using the SDK
        try:
            market_data = get_market_data_by_type(
                session,
                options=option_symbols
            )
            debug_messages.append(f"✅ API call successful, got {len(market_data)} items")
        except Exception as e:
            debug_messages.append(f"❌ API call failed: {e}")
            import traceback
            debug_messages.append(f"Traceback: {traceback.format_exc()}")
            if show_debug:
                with st.expander("🔧 SDK Debug Info", expanded=True):
                    for msg in debug_messages:
                        st.write(msg)
            return {}
        
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
            debug_messages.append(f"Quote for {sym[:10]}...: bid=${quotes[sym]['bid']:.2f}, ask=${quotes[sym]['ask']:.2f}")
        
        debug_messages.append(f"✅ Returning {len(quotes)} quotes")
        
        if show_debug:
            with st.expander("🔧 SDK Debug Info", expanded=False):
                for msg in debug_messages:
                    st.write(msg)
        
        return quotes
        
    except Exception as e:
        debug_messages.append(f"❌ Unexpected error: {e}")
        import traceback
        debug_messages.append(f"Traceback: {traceback.format_exc()}")
        if show_debug:
            with st.expander("🔧 SDK Debug Info", expanded=True):
                for msg in debug_messages:
                    st.write(msg)
        return {}


def clear_sdk_session():
    """Clear the cached SDK session (useful if credentials change)"""
    if 'tastytrade_sdk_session' in st.session_state:
        del st.session_state.tastytrade_sdk_session
