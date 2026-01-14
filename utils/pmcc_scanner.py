"""
PMCC Scanner Utilities
Scan for LEAP call options and short call opportunities for Poor Man's Covered Calls
Enhanced with technical indicators and value filters
"""

import os
import requests
from datetime import datetime, timedelta


def get_technical_indicators_for_pmcc(symbol):
    """
    Get technical indicators for PMCC filtering
    Uses the yahoo_finance module for RSI, MA%, etc.
    """
    try:
        from utils.yahoo_finance import get_technical_indicators
        indicators = get_technical_indicators(symbol)
        return indicators
    except Exception as e:
        print(f"Error getting technical indicators for {symbol}: {str(e)}")
        return None


def calculate_extrinsic_value(option_price, underlying_price, strike, option_type='call'):
    """
    Calculate extrinsic (time) value of an option
    
    For ITM calls: Extrinsic = Option Price - (Underlying Price - Strike)
    For OTM calls: Extrinsic = Option Price (all extrinsic)
    
    Returns extrinsic value and extrinsic as % of option price
    """
    if option_type == 'call':
        intrinsic = max(0, underlying_price - strike)
    else:
        intrinsic = max(0, strike - underlying_price)
    
    extrinsic = option_price - intrinsic
    extrinsic_pct = (extrinsic / option_price * 100) if option_price > 0 else 0
    
    return extrinsic, extrinsic_pct


def calculate_capital_efficiency(leap_cost, underlying_price):
    """
    Calculate capital efficiency - how much LEAP costs vs 100 shares
    
    Returns efficiency as a percentage
    Lower % = more capital efficient (LEAP costs less than shares)
    """
    shares_cost = underlying_price * 100
    if shares_cost <= 0:
        return 100.0
    
    efficiency = (leap_cost / shares_cost) * 100
    return efficiency


def calculate_pmcc_score(option_data, technical_indicators=None):
    """
    Calculate a composite PMCC score based on multiple factors
    
    Scoring factors:
    - Delta (higher = more stock-like, better for PMCC)
    - Extrinsic % (lower = better, less time premium)
    - Capital Efficiency (lower = better)
    - Bid-Ask Spread (lower = better liquidity)
    - RSI (30-70 range preferred)
    - MA% (above MA preferred for uptrend)
    
    Returns score 0-100 (higher = better candidate)
    """
    score = 0
    max_score = 100
    
    # Delta score (25 points max) - higher delta = better
    delta = option_data.get('delta', 0)
    if delta >= 0.85:
        score += 25
    elif delta >= 0.80:
        score += 20
    elif delta >= 0.75:
        score += 15
    elif delta >= 0.70:
        score += 10
    else:
        score += 5
    
    # Extrinsic % score (20 points max) - lower = better
    extrinsic_pct = option_data.get('extrinsic_pct', 50)
    if extrinsic_pct <= 5:
        score += 20
    elif extrinsic_pct <= 10:
        score += 15
    elif extrinsic_pct <= 15:
        score += 10
    elif extrinsic_pct <= 20:
        score += 5
    
    # Capital Efficiency score (20 points max) - lower = better
    efficiency = option_data.get('capital_efficiency', 100)
    if efficiency <= 50:
        score += 20
    elif efficiency <= 60:
        score += 15
    elif efficiency <= 70:
        score += 10
    elif efficiency <= 80:
        score += 5
    
    # Bid-Ask Spread score (15 points max) - lower = better
    spread_pct = option_data.get('bid_ask_spread_pct', 10)
    if spread_pct <= 1:
        score += 15
    elif spread_pct <= 2:
        score += 12
    elif spread_pct <= 3:
        score += 9
    elif spread_pct <= 5:
        score += 6
    elif spread_pct <= 7:
        score += 3
    
    # Technical indicators (20 points max)
    if technical_indicators:
        # RSI score (10 points) - prefer 30-70 range
        rsi = technical_indicators.get('rsi')
        if rsi is not None:
            if 40 <= rsi <= 60:
                score += 10  # Ideal neutral zone
            elif 30 <= rsi <= 70:
                score += 7   # Acceptable range
            elif 25 <= rsi <= 75:
                score += 4   # Extended but ok
            # Oversold/overbought = 0 points
        
        # MA% score (10 points) - prefer above MA (uptrend)
        ma_pct = technical_indicators.get('ma_percent')
        if ma_pct is not None:
            if ma_pct > 5:
                score += 10  # Strong uptrend
            elif ma_pct > 0:
                score += 7   # Above MA
            elif ma_pct > -5:
                score += 4   # Near MA
            # Below MA = 0 points
    
    return min(score, max_score)


def scan_leap_options(tradier_api, symbols, dte_min=270, dte_max=450, delta_min=0.70, delta_max=0.90, min_oi=50,
                      max_bid_ask_spread=5.0, max_extrinsic_pct=15.0, max_iv=100.0,
                      require_above_ma=False, min_rsi=30, max_rsi=70,
                      min_capital_efficiency=0.0, max_capital_efficiency=85.0,
                      include_technical=True):
    """
    Scan for LEAP call options across multiple symbols with enhanced filtering
    
    Args:
        tradier_api: TradierAPI instance
        symbols: List of ticker symbols to scan
        dte_min: Minimum days to expiration (default 270 = 9 months)
        dte_max: Maximum days to expiration (default 450 = 15 months)
        delta_min: Minimum delta (default 0.70 for deep ITM)
        delta_max: Maximum delta (default 0.90)
        min_oi: Minimum open interest for liquidity (default 50)
        max_bid_ask_spread: Maximum bid-ask spread % (default 5.0)
        max_extrinsic_pct: Maximum extrinsic value % (default 15.0)
        max_iv: Maximum implied volatility % (default 100.0)
        require_above_ma: Require price above 50-day MA (default False)
        min_rsi: Minimum RSI (default 30)
        max_rsi: Maximum RSI (default 70)
        min_capital_efficiency: Minimum capital efficiency % (default 0.0)
        max_capital_efficiency: Maximum capital efficiency % (default 85.0)
        include_technical: Include technical indicators in results (default True)
    
    Returns:
        List of LEAP opportunities with details
    """
    results = []
    
    # Pre-fetch technical indicators for all symbols if needed
    technical_cache = {}
    if include_technical or require_above_ma or min_rsi > 0 or max_rsi < 100:
        for symbol in symbols:
            try:
                indicators = get_technical_indicators_for_pmcc(symbol)
                if indicators:
                    technical_cache[symbol] = indicators
            except Exception as e:
                print(f"Could not get technical indicators for {symbol}: {e}")
    
    for symbol in symbols:
        try:
            # Check technical filters first (before expensive option chain call)
            tech_indicators = technical_cache.get(symbol)
            
            if require_above_ma and tech_indicators:
                ma_pct = tech_indicators.get('ma_percent')
                if ma_pct is not None and ma_pct < 0:
                    print(f"  {symbol}: Skipped - below 50-day MA ({ma_pct:.1f}%)")
                    continue
            
            if tech_indicators:
                rsi = tech_indicators.get('rsi')
                if rsi is not None:
                    if rsi < min_rsi:
                        print(f"  {symbol}: Skipped - RSI too low ({rsi:.1f} < {min_rsi})")
                        continue
                    if rsi > max_rsi:
                        print(f"  {symbol}: Skipped - RSI too high ({rsi:.1f} > {max_rsi})")
                        continue
            
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
                
                # Calculate bid-ask spread %
                if bid and bid > 0:
                    bid_ask_spread_pct = ((ask - bid) / bid) * 100
                else:
                    bid_ask_spread_pct = 100  # Very wide spread
                
                # Filter by bid-ask spread
                if bid_ask_spread_pct > max_bid_ask_spread:
                    continue
                
                # Calculate extrinsic value
                strike = option.get('strike', 0)
                extrinsic, extrinsic_pct = calculate_extrinsic_value(price, underlying_price, strike, 'call')
                
                # Filter by extrinsic %
                if extrinsic_pct > max_extrinsic_pct:
                    continue
                
                # Get IV
                iv = greeks.get('mid_iv', 0) * 100 if greeks.get('mid_iv') else 0
                
                # Filter by IV
                if iv > max_iv and max_iv < 200:
                    continue
                
                # Calculate cost per contract
                cost_per_contract = price * 100
                
                # Calculate capital efficiency
                capital_efficiency = calculate_capital_efficiency(cost_per_contract, underlying_price)
                
                # Filter by capital efficiency
                if capital_efficiency < min_capital_efficiency or capital_efficiency > max_capital_efficiency:
                    continue
                
                # Calculate breakeven
                breakeven = strike + price
                breakeven_pct = ((breakeven - underlying_price) / underlying_price) * 100
                
                # Calculate max loss (cost of LEAP)
                max_loss = cost_per_contract
                
                # Build result entry
                result = {
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
                    'breakeven_pct': breakeven_pct,
                    'max_loss': max_loss,
                    'gamma': greeks.get('gamma', 0),
                    'theta': greeks.get('theta', 0),
                    'vega': greeks.get('vega', 0),
                    'iv': iv,
                    'extrinsic': extrinsic,
                    'extrinsic_pct': extrinsic_pct,
                    'bid_ask_spread_pct': bid_ask_spread_pct,
                    'capital_efficiency': capital_efficiency,
                }
                
                # Add technical indicators if available
                if tech_indicators:
                    result['rsi'] = tech_indicators.get('rsi')
                    result['ma_percent'] = tech_indicators.get('ma_percent')
                    result['bb_percent'] = tech_indicators.get('bb_percent')
                    result['week_52_percent'] = tech_indicators.get('week_52_percent')
                
                # Calculate PMCC score
                result['pmcc_score'] = calculate_pmcc_score(result, tech_indicators)
                
                results.append(result)
        
        except Exception as e:
            print(f"Error scanning {symbol}: {str(e)}")
            continue
    
    # Sort by PMCC score (highest first), then by delta
    results.sort(key=lambda x: (-x.get('pmcc_score', 0), -x['delta']))
    
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
