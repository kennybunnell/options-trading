#!/usr/bin/env python3
"""Test script to debug option quote fetching"""

import os
import sys
sys.path.insert(0, '/home/ubuntu/options-trading')

from utils.tastytrade_api import TastytradeCertAPI

# Initialize API
api = TastytradeCertAPI()

# Get live orders first to see the symbol format
account = os.environ.get('TASTYTRADE_ACCOUNT', '5WV27135')
print(f"Fetching orders for account: {account}")

orders = api.get_live_orders(account)
print(f"\nFound {len(orders) if orders else 0} orders")

if orders:
    for order in orders[:3]:  # Just first 3
        legs = order.get('legs', [])
        if legs:
            symbol = legs[0].get('symbol', '')
            print(f"\nOrder symbol: '{symbol}'")
            print(f"  Symbol length: {len(symbol)}")
            print(f"  Symbol repr: {repr(symbol)}")
            
            # Try to get quote
            print(f"\n  Trying get_option_quote...")
            quote = api.get_option_quote(symbol)
            print(f"  Quote result: {quote}")
            
            if quote:
                print(f"  Keys in quote: {quote.keys()}")
                print(f"  bid-price: {quote.get('bid-price')}")
                print(f"  ask-price: {quote.get('ask-price')}")
                print(f"  bid: {quote.get('bid')}")
                print(f"  ask: {quote.get('ask')}")
