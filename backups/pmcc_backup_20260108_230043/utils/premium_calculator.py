"""
Premium Calculator - Order-based calculation with roll detection
Correctly handles multi-leg orders and roll transactions
"""

from collections import defaultdict
from datetime import datetime


def calculate_premium_from_transactions(transactions):
    """
    Calculate premium from API transactions using order-based grouping.
    
    Groups transactions by timestamp (same order) and calculates NET per order.
    This correctly handles rolls (BTC + STO in same order) and multi-leg orders.
    
    Args:
        transactions: List of transaction dicts from Tastytrade API
        
    Returns:
        dict with premium breakdown and statistics
    """
    
    # Filter option transactions only
    option_txns = [t for t in transactions if t.get('instrument-type') == 'Equity Option']
    
    # Group transactions by executed-at timestamp (same order)
    by_timestamp = defaultdict(list)
    for t in option_txns:
        timestamp = t.get('executed-at', '')
        by_timestamp[timestamp].append(t)
    
    # Calculate premium by ORDER (not by transaction)
    orders = []
    total_credits = 0
    total_debits = 0
    zero_value_count = 0
    
    csp_orders = []
    cc_orders = []
    
    for timestamp, txn_list in by_timestamp.items():
        # Calculate net value for this order
        order_net = 0
        order_credits = 0
        order_debits = 0
        has_non_zero = False
        
        for t in txn_list:
            value = float(t.get('value', 0) or 0)
            effect = t.get('value-effect', '')
            
            if value > 0:
                has_non_zero = True
                
            if effect == 'Credit':
                order_credits += value
                order_net += value
            elif effect == 'Debit':
                order_debits += value
                order_net -= value
        
        # Skip orders with all $0 values (expirations, assignments)
        if not has_non_zero:
            zero_value_count += len(txn_list)
            continue
        
        total_credits += order_credits
        total_debits += order_debits
        
        # Determine if CSP or CC
        has_put = any('Put' in t.get('description', '') for t in txn_list)
        has_call = any('Call' in t.get('description', '') for t in txn_list)
        
        # Get underlying symbol
        underlying = txn_list[0].get('underlying-symbol', '')
        
        order_data = {
            'timestamp': timestamp,
            'underlying': underlying,
            'transactions': txn_list,
            'credits': order_credits,
            'debits': order_debits,
            'net': order_net,
            'is_put': has_put,
            'is_call': has_call,
            'is_multi_leg': len(txn_list) > 1
        }
        
        orders.append(order_data)
        
        # Categorize by type
        if has_put and not has_call:
            csp_orders.append(order_data)
        elif has_call and not has_put:
            cc_orders.append(order_data)
        else:
            # Mixed - assign to dominant
            put_count = sum(1 for t in txn_list if 'Put' in t.get('description', ''))
            call_count = sum(1 for t in txn_list if 'Call' in t.get('description', ''))
            if put_count > call_count:
                csp_orders.append(order_data)
            else:
                cc_orders.append(order_data)
    
    # Calculate CSP and CC totals
    csp_net = sum(o['net'] for o in csp_orders)
    cc_net = sum(o['net'] for o in cc_orders)
    
    csp_credits = sum(o['credits'] for o in csp_orders)
    csp_debits = sum(o['debits'] for o in csp_orders)
    cc_credits = sum(o['credits'] for o in cc_orders)
    cc_debits = sum(o['debits'] for o in cc_orders)
    
    # Calculate per-symbol breakdown
    csp_by_symbol = defaultdict(float)
    cc_by_symbol = defaultdict(float)
    
    for order in csp_orders:
        symbol = order['underlying']
        csp_by_symbol[symbol] += order['net']
    
    for order in cc_orders:
        symbol = order['underlying']
        cc_by_symbol[symbol] += order['net']
    
    # Count rolls (multi-leg orders with both BTC and STO)
    roll_count = 0
    for order in orders:
        if order['is_multi_leg']:
            actions = [t.get('action', '') for t in order['transactions']]
            has_btc = 'Buy to Close' in actions
            has_sto = 'Sell to Open' in actions
            if has_btc and has_sto:
                roll_count += 1
    
    return {
        'total_gross': total_credits,
        'total_buyback': total_debits,
        'total_net': total_credits - total_debits,
        
        'csp_gross': csp_credits,
        'csp_buyback': csp_debits,
        'csp_net': csp_net,
        
        'cc_gross': cc_credits,
        'cc_buyback': cc_debits,
        'cc_net': cc_net,
        
        'csp_by_symbol': dict(csp_by_symbol),
        'cc_by_symbol': dict(cc_by_symbol),
        
        'total_orders': len(orders),
        'csp_orders': len(csp_orders),
        'cc_orders': len(cc_orders),
        'roll_count': roll_count,
        'multi_leg_count': sum(1 for o in orders if o['is_multi_leg']),
        'single_leg_count': sum(1 for o in orders if not o['is_multi_leg']),
        
        'orders': orders,
        'csp_orders_list': csp_orders,
        'cc_orders_list': cc_orders
    }


def format_premium_summary(premium_data):
    """Format premium data as a readable summary string"""
    
    lines = []
    lines.append("=" * 70)
    lines.append("PREMIUM SUMMARY (Order-Based Calculation)")
    lines.append("=" * 70)
    lines.append("")
    
    lines.append("COVERED CALLS (CC):")
    lines.append(f"  Gross Credits:    ${premium_data['cc_gross']:>12,.2f}")
    lines.append(f"  Buyback Costs:    ${premium_data['cc_buyback']:>12,.2f}")
    lines.append(f"  NET CC Premium:   ${premium_data['cc_net']:>12,.2f}")
    lines.append(f"  Orders: {premium_data['cc_orders']}")
    lines.append("")
    
    lines.append("CASH SECURED PUTS (CSP):")
    lines.append(f"  Gross Credits:    ${premium_data['csp_gross']:>12,.2f}")
    lines.append(f"  Buyback Costs:    ${premium_data['csp_buyback']:>12,.2f}")
    lines.append(f"  NET CSP Premium:  ${premium_data['csp_net']:>12,.2f}")
    lines.append(f"  Orders: {premium_data['csp_orders']}")
    lines.append("")
    
    lines.append("=" * 70)
    lines.append("TOTAL:")
    lines.append(f"  Gross Credits:    ${premium_data['total_gross']:>12,.2f}")
    lines.append(f"  Buyback Costs:    ${premium_data['total_buyback']:>12,.2f}")
    lines.append(f"  NET PREMIUM:      ${premium_data['total_net']:>12,.2f}")
    lines.append("=" * 70)
    lines.append("")
    
    lines.append(f"Total Orders: {premium_data['total_orders']}")
    lines.append(f"  Single-leg: {premium_data['single_leg_count']}")
    lines.append(f"  Multi-leg: {premium_data['multi_leg_count']}")
    lines.append(f"  Rolls: {premium_data['roll_count']}")
    
    return "\n".join(lines)
