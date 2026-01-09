"""
PMCC Scanner Utilities
Scan for LEAP call options and short call opportunities for Poor Man's Covered Calls
"""

import os
import requests
from datetime import datetime, timedelta


def scan_leap_options(tradier_api, symbols, dte_min=270, dte_max=450, delta_min=0.70, delta_max=0.90, min_oi=50):
    """
    Scan for LEAP call options across multiple symbols
    
    Args:
        tradier_api: TradierAPI instance
        symbols: List of ticker symbols to scan
        dte_min: Minimum days to expiration (default 270 = 9 months)
        dte_max: Maximum days to expiration (default 450 = 15 months)
        delta_min: Minimum delta (default 0.70 for deep ITM)
        delta_max: Maximum delta (default 0.90)
        min_oi: Minimum open interest for liquidity (default 50)
    
    Returns:
        List of LEAP opportunities with details
    """
    results = []
    
    for symbol in symbols:
        try:
            # Get option chains for this symbol with extended DTE range
            chain_data = tradier_api.get_option_chains(symbol, min_dte=dte_min, max_dte=dte_max)
            
            if not chain_data or not chain_data.get('options'):
                continue
            
            options = chain_data['options']
            underlying_price = chain_data.get('underlying_price', 0)
            
            if not underlying_price:
                continue
            
            # Filter for CALL options with target delta and liquidity
            for option in options:
                # Only CALL options
                if option.get('option_type') != 'call':
                    continue
                
                # Check greeks
                greeks = option.get('greeks', {})
                if not greeks:
                    continue
                
                delta = greeks.get('delta')
                if delta is None:
                    continue
                
                # Delta filter (calls have positive delta)
                if not (delta_min <= delta <= delta_max):
                    continue
                
                # Open interest filter
                open_interest = option.get('open_interest', 0)
                if open_interest < min_oi:
                    continue
                
                # Calculate DTE
                exp_date_str = option.get('expiration_date', '')
                if not exp_date_str:
                    continue
                
                exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
                dte = (exp_date - datetime.now()).days
                
                # Get pricing
                bid = option.get('bid', 0)
                ask = option.get('ask', 0)
                last = option.get('last', 0)
                
                # Use mid price or last
                if bid and ask:
                    price = (bid + ask) / 2
                elif last:
                    price = last
                else:
                    continue
                
                # Calculate cost per contract
                cost_per_contract = price * 100
                
                # Calculate breakeven
                strike = option.get('strike', 0)
                breakeven = strike + price
                
                # Calculate max loss (cost of LEAP)
                max_loss = cost_per_contract
                
                results.append({
                    'symbol': symbol,
                    'underlying_price': underlying_price,
                    'option_symbol': option.get('symbol', ''),
                    'strike': strike,
                    'expiration': exp_date_str,
                    'dte': dte,
                    'delta': delta,
                    'bid': bid,
                    'ask': ask,
                    'last': last,
                    'price': price,
                    'cost_per_contract': cost_per_contract,
                    'open_interest': open_interest,
                    'volume': option.get('volume', 0),
                    'breakeven': breakeven,
                    'max_loss': max_loss,
                    'gamma': greeks.get('gamma', 0),
                    'theta': greeks.get('theta', 0),
                    'vega': greeks.get('vega', 0),
                    'iv': option.get('greeks', {}).get('mid_iv', 0)
                })
        
        except Exception as e:
            print(f"Error scanning {symbol}: {str(e)}")
            continue
    
    # Sort by delta (highest first) then by DTE (longest first)
    results.sort(key=lambda x: (-x['delta'], -x['dte']))
    
    return results


def scan_short_call_opportunities(tradier_api, underlying_symbol, leap_strike, dte_min=30, dte_max=45, 
                                   delta_max=0.30, min_premium=50):
    """
    Scan for short call opportunities to sell against a LEAP position
    
    Args:
        tradier_api: TradierAPI instance
        underlying_symbol: Ticker symbol of the underlying
        leap_strike: Strike price of the owned LEAP (short call must be above this)
        dte_min: Minimum days to expiration (default 30)
        dte_max: Maximum days to expiration (default 45)
        delta_max: Maximum delta (default 0.30 for low assignment risk)
        min_premium: Minimum premium per contract in dollars (default $50)
    
    Returns:
        List of short call opportunities
    """
    results = []
    
    try:
        # Get option chains for short-term expirations
        chain_data = tradier_api.get_option_chains(underlying_symbol, min_dte=dte_min, max_dte=dte_max)
        
        if not chain_data or not chain_data.get('options'):
            return []
        
        options = chain_data['options']
        underlying_price = chain_data.get('underlying_price', 0)
        
        if not underlying_price:
            return []
        
        # Filter for CALL options above LEAP strike
        for option in options:
            # Only CALL options
            if option.get('option_type') != 'call':
                continue
            
            # Strike must be above LEAP strike (to avoid early assignment risk)
            strike = option.get('strike', 0)
            if strike <= leap_strike:
                continue
            
            # Check greeks
            greeks = option.get('greeks', {})
            if not greeks:
                continue
            
            delta = greeks.get('delta')
            if delta is None or delta > delta_max:
                continue
            
            # Calculate DTE
            exp_date_str = option.get('expiration_date', '')
            if not exp_date_str:
                continue
            
            exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
            dte = (exp_date - datetime.now()).days
            
            # Get pricing
            bid = option.get('bid', 0)
            ask = option.get('ask', 0)
            last = option.get('last', 0)
            
            # Use mid price or last
            if bid and ask:
                price = (bid + ask) / 2
            elif last:
                price = last
            else:
                continue
            
            # Calculate premium per contract
            premium_per_contract = price * 100
            
            # Filter by minimum premium
            if premium_per_contract < min_premium:
                continue
            
            # Calculate distance from current price
            distance_from_price = ((strike - underlying_price) / underlying_price) * 100
            
            # Calculate distance from LEAP strike
            distance_from_leap = strike - leap_strike
            
            # Open interest check
            open_interest = option.get('open_interest', 0)
            
            results.append({
                'symbol': underlying_symbol,
                'underlying_price': underlying_price,
                'option_symbol': option.get('symbol', ''),
                'strike': strike,
                'expiration': exp_date_str,
                'dte': dte,
                'delta': delta,
                'bid': bid,
                'ask': ask,
                'last': last,
                'price': price,
                'premium_per_contract': premium_per_contract,
                'open_interest': open_interest,
                'volume': option.get('volume', 0),
                'distance_from_price_pct': distance_from_price,
                'distance_from_leap': distance_from_leap,
                'gamma': greeks.get('gamma', 0),
                'theta': greeks.get('theta', 0),
                'vega': greeks.get('vega', 0),
                'iv': option.get('greeks', {}).get('mid_iv', 0)
            })
    
    except Exception as e:
        print(f"Error scanning short calls for {underlying_symbol}: {str(e)}")
        return []
    
    # Sort by premium (highest first)
    results.sort(key=lambda x: -x['premium_per_contract'])
    
    return results


def calculate_pmcc_roi(leap_cost, premiums_collected):
    """
    Calculate ROI for a PMCC position
    
    Args:
        leap_cost: Total cost of the LEAP contract
        premiums_collected: Total premiums collected from selling short calls
    
    Returns:
        ROI as a percentage
    """
    if leap_cost <= 0:
        return 0
    
    return (premiums_collected / leap_cost) * 100


def check_assignment_risk(underlying_price, short_call_strike, short_call_dte):
    """
    Check if a short call position is at risk of assignment
    
    Args:
        underlying_price: Current price of underlying
        short_call_strike: Strike price of short call
        short_call_dte: Days to expiration of short call
    
    Returns:
        Dict with risk level and message
    """
    # Calculate how far ITM the short call is
    distance_pct = ((short_call_strike - underlying_price) / underlying_price) * 100
    
    # Risk levels
    if underlying_price >= short_call_strike:
        # ITM - high risk
        if short_call_dte <= 7:
            return {
                'risk_level': 'CRITICAL',
                'color': 'red',
                'message': f'⚠️ CRITICAL: Short call is ITM with only {short_call_dte} DTE. Consider rolling or closing.'
            }
        else:
            return {
                'risk_level': 'HIGH',
                'color': 'orange',
                'message': f'⚠️ HIGH RISK: Short call is ITM. Monitor closely and consider rolling.'
            }
    elif distance_pct < 5:
        # Within 5% of strike - moderate risk
        return {
            'risk_level': 'MODERATE',
            'color': 'yellow',
            'message': f'⚡ MODERATE: Price is within 5% of strike. Watch for movement.'
        }
    else:
        # Safe - OTM with good distance
        return {
            'risk_level': 'LOW',
            'color': 'green',
            'message': f'✅ LOW RISK: Short call is safely OTM ({distance_pct:.1f}% away).'
        }
