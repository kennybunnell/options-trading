def calculate_csp_readiness_score(indicators):
    """
    Calculate CSP Readiness Score (0-100)
    
    Weighting:
    - RSI: 40% (most important)
    - BB%: 30%
    - 52W%: 30%
    """
    if not indicators:
        return 0
    
    rsi = indicators.get('rsi')
    bb_pct = indicators.get('bb_percent')
    week_52_pct = indicators.get('week_52_percent')
    
    # RSI Score (40% weight)
    rsi_score = 0
    if rsi is not None:
        if rsi < 30:
            rsi_score = 100
        elif rsi < 35:
            rsi_score = 80
        elif rsi < 40:
            rsi_score = 60
        elif rsi < 50:
            rsi_score = 40
        elif rsi <= 70:
            rsi_score = 20
        else:
            rsi_score = 0
    
    # BB Score (30% weight)
    bb_score = 0
    if bb_pct is not None:
        if bb_pct <= 20:
            bb_score = 100
        elif bb_pct <= 30:
            bb_score = 80
        elif bb_pct <= 40:
            bb_score = 60
        elif bb_pct <= 50:
            bb_score = 40
        elif bb_pct <= 60:
            bb_score = 20
        else:
            bb_score = 0
    
    # 52W Score (30% weight)
    week_52_score = 0
    if week_52_pct is not None:
        if week_52_pct <= 20:
            week_52_score = 100
        elif week_52_pct <= 30:
            week_52_score = 80
        elif week_52_pct <= 40:
            week_52_score = 60
        elif week_52_pct <= 50:
            week_52_score = 40
        elif week_52_pct <= 60:
            week_52_score = 20
        else:
            week_52_score = 0
    
    # Calculate weighted score
    total_score = (rsi_score * 0.40) + (bb_score * 0.30) + (week_52_score * 0.30)
    
    return round(total_score, 1)

def get_score_breakdown(indicators):
    """Get detailed breakdown of score components"""
    if not indicators:
        return None
    
    rsi = indicators.get('rsi')
    bb_pct = indicators.get('bb_percent')
    week_52_pct = indicators.get('week_52_percent')
    
    breakdown = {
        'rsi_value': round(rsi, 1) if rsi else None,
        'bb_value': round(bb_pct, 1) if bb_pct else None,
        'week_52_value': round(week_52_pct, 1) if week_52_pct else None
    }
    
    return breakdown

