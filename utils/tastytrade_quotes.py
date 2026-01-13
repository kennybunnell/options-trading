"""
Tastytrade Quote Fetching using direct REST API

This module fetches option quotes directly from the Tastytrade REST API
using username/password authentication (not OAuth SDK).
"""

import os
import requests
import streamlit as st
from datetime import datetime, timedelta


def get_tastytrade_session():
    """
    Get or create a Tastytrade session with username/password auth
    Returns session_token or None
    """
    # Check for cached session
    if 'tt_session_token' in st.session_state and 'tt_token_expiry' in st.session_state:
        if datetime.now() < st.session_state.tt_token_expiry:
            return st.session_state.tt_session_token
    
    # Get credentials
    username = os.getenv('TASTYTRADE_USERNAME')
    password = os.getenv('TASTYTRADE_PASSWORD')
    
    if not username or not password:
        try:
            username = st.secrets.get('TASTYTRADE_USERNAME')
            password = st.secrets.get('TASTYTRADE_PASSWORD')
        except:
            pass
    
    if not username or not password:
        return None
    
    # Authenticate
    try:
        url = 'https://api.tastyworks.com/sessions'
        payload = {
            'login': username,
            'password': password
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 201:
            data = response.json()
            token = data['data']['session-token']
            st.session_state.tt_session_token = token
            st.session_state.tt_token_expiry = datetime.now() + timedelta(hours=23)
            return token
        else:
            st.error(f"Auth failed: {response.status_code} - {response.text[:200]}")
            return None
            
    except Exception as e:
        st.error(f"Auth error: {e}")
        return None


def get_option_quotes_sdk(option_symbols, show_debug=True):
    """
    Get quotes for multiple option symbols using direct REST API
    
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
        # Get session token
        session_token = get_tastytrade_session()
        
        if not session_token:
            debug_messages.append("❌ Could not get Tastytrade session")
            if show_debug:
                with st.expander("🔧 Quote Debug Info", expanded=True):
                    for msg in debug_messages:
                        st.write(msg)
            return {}
        
        debug_messages.append("✅ Got Tastytrade session token")
        
        headers = {
            'Authorization': session_token,
            'Content-Type': 'application/json'
        }
        
        # Use the market-data/by-type endpoint
        url = 'https://api.tastyworks.com/market-data/by-type'
        
        debug_messages.append(f"Requesting quotes for {len(option_symbols)} symbols:")
        for i, sym in enumerate(option_symbols[:6]):
            debug_messages.append(f"  '{sym}' (len={len(sym)})")
        if len(option_symbols) > 6:
            debug_messages.append(f"  ... and {len(option_symbols) - 6} more")
        
        # Build params - use 'equity-option' parameter for each symbol
        params = [('equity-option', sym) for sym in option_symbols]
        
        debug_messages.append(f"API URL: {url}")
        debug_messages.append(f"Params: equity-option x {len(option_symbols)}")
        
        response = requests.get(url, headers=headers, params=params)
        
        debug_messages.append(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            debug_messages.append(f"Response keys: {list(data.keys())}")
            
            # The response should have 'data' key with 'items' array
            if 'data' in data:
                items = data['data']
                
                # Check if it's a dict with 'items' or directly an array
                if isinstance(items, dict) and 'items' in items:
                    items = items['items']
                elif not isinstance(items, list):
                    items = [items] if items else []
                
                debug_messages.append(f"Found {len(items)} items in response")
                
                if len(items) > 0:
                    # Log first item structure
                    first_item = items[0]
                    if isinstance(first_item, dict):
                        debug_messages.append(f"First item keys: {list(first_item.keys())[:10]}")
                    else:
                        debug_messages.append(f"First item type: {type(first_item)}")
                
                for item in items:
                    if isinstance(item, dict):
                        sym = item.get('symbol', '')
                        if sym:
                            quotes[sym] = {
                                'bid': float(item.get('bid', 0) or 0),
                                'ask': float(item.get('ask', 0) or 0),
                                'mid': float(item.get('mid', 0) or 0),
                                'last': float(item.get('last', 0) or 0),
                                'mark': float(item.get('mark', 0) or 0),
                            }
                            debug_messages.append(f"✅ {sym[:15]}: bid=${quotes[sym]['bid']:.2f}, ask=${quotes[sym]['ask']:.2f}")
                    else:
                        debug_messages.append(f"⚠️ Item is not a dict: {type(item)}")
            else:
                debug_messages.append(f"❌ No 'data' key in response")
                debug_messages.append(f"Response preview: {str(data)[:500]}")
        else:
            debug_messages.append(f"❌ API error: {response.status_code}")
            debug_messages.append(f"Response: {response.text[:500]}")
        
        debug_messages.append(f"Returning {len(quotes)} quotes")
        
        if show_debug:
            with st.expander("🔧 Quote Debug Info", expanded=len(quotes) == 0):
                for msg in debug_messages:
                    st.write(msg)
        
        return quotes
        
    except Exception as e:
        debug_messages.append(f"❌ Error: {e}")
        import traceback
        debug_messages.append(f"Traceback: {traceback.format_exc()}")
        if show_debug:
            with st.expander("🔧 Quote Debug Info", expanded=True):
                for msg in debug_messages:
                    st.write(msg)
        return {}


def clear_sdk_session():
    """Clear the cached session (useful if credentials change)"""
    if 'tt_session_token' in st.session_state:
        del st.session_state.tt_session_token
    if 'tt_token_expiry' in st.session_state:
        del st.session_state.tt_token_expiry
