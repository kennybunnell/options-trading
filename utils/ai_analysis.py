"""
AI Stock Analysis Module
Uses OpenAI API to analyze stocks for earnings, news, and risks
"""

import streamlit as st
from openai import OpenAI

def analyze_stocks_with_ai(symbols):
    """
    Analyze a list of stock symbols using OpenAI API
    
    Args:
        symbols: List of stock ticker symbols
        
    Returns:
        dict: Analysis results with risk categorization
    """
    # Get API key from Streamlit secrets
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        client = OpenAI(api_key=api_key)
    except Exception as e:
        return {
            'error': f"OpenAI API key not found in secrets: {str(e)}",
            'full_analysis': f"❌ Error: OpenAI API key not configured. Please add OPENAI_API_KEY to .streamlit/secrets.toml",
            'safe_stocks': [],
            'caution_stocks': [],
            'avoid_stocks': [],
            'total_analyzed': 0
        }
    
    # Create prompt for batch analysis
    symbols_str = ", ".join(symbols)
    
    prompt = f"""Analyze these stocks for Cash-Secured Put (CSP) trading: {symbols_str}

For EACH stock, provide:
1. Full company name
2. Brief company description (what the company does, industry)
3. Specific upcoming earnings quarter (e.g., Q4 2024) and estimated week/date
4. Analyst recommendations (consensus: Buy/Hold/Sell, if known)
5. Any notable recent news or events
6. Risk assessment for selling puts (Low/Medium/High)
7. 3-sentence summary combining the above

Format your response EXACTLY like this for each stock:

**SYMBOL - Full Company Name**
Business: [Brief 1-sentence description of what the company does]
Earnings: [Specific quarter (e.g., Q1 2025) and estimated date/week (e.g., "Week of Feb 10, 2025" or "Mid-February 2025")]
Analyst Rating: [Consensus rating if known, e.g., "Buy (70% of analysts)" or "Hold" or "Data not available"]
News: [Recent notable events or "No major news"]
Risk: [Low/Medium/High] - [Brief reason]
Summary: [3 sentences covering: 1) Company overview, 2) Earnings timing and analyst sentiment, 3) CSP suitability]

---

Be specific with earnings dates/quarters. Focus on information relevant to CSP trading (assignment risk, volatility events, negative catalysts).
If you don't have exact data, provide best estimates based on typical patterns (e.g., "Typically reports Q4 in late January").
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",  # Fast and cost-effective
            messages=[
                {"role": "system", "content": "You are a financial analyst helping options traders assess stocks for Cash-Secured Put strategies. Provide concise, actionable analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more factual responses
            max_tokens=5000  # Increased for more detailed analysis per stock
        )
        
        analysis_text = response.choices[0].message.content
        
        # Parse the response to categorize stocks
        results = {
            'full_analysis': analysis_text,
            'safe_stocks': [],
            'caution_stocks': [],
            'avoid_stocks': [],
            'total_analyzed': len(symbols)
        }
        
        # Simple parsing to categorize by risk level
        lines = analysis_text.split('\n')
        current_symbol = None
        
        for line in lines:
            line = line.strip()
            
            # Detect stock symbol
            if line.startswith('**') and line.endswith('**'):
                current_symbol = line.strip('*')
            
            # Detect risk level
            elif line.startswith('Risk:') and current_symbol:
                if 'Low' in line:
                    results['safe_stocks'].append(current_symbol)
                elif 'Medium' in line:
                    results['caution_stocks'].append(current_symbol)
                elif 'High' in line:
                    results['avoid_stocks'].append(current_symbol)
                current_symbol = None  # Reset for next stock
        
        return results
        
    except Exception as e:
        return {
            'error': str(e),
            'full_analysis': f"❌ Error analyzing stocks: {str(e)}",
            'safe_stocks': [],
            'caution_stocks': [],
            'avoid_stocks': [],
            'total_analyzed': 0
        }


def get_ai_analysis_summary(results):
    """
    Generate a summary of AI analysis results
    
    Args:
        results: Dict from analyze_stocks_with_ai()
        
    Returns:
        str: Formatted summary text
    """
    if 'error' in results:
        return f"❌ Analysis failed: {results['error']}"
    
    summary = f"""
📊 **AI Analysis Complete**

Analyzed {results['total_analyzed']} stocks:
- ✅ Safe: {len(results['safe_stocks'])} stocks
- ⚠️ Caution: {len(results['caution_stocks'])} stocks  
- ❌ Avoid: {len(results['avoid_stocks'])} stocks

**Safe Stocks:** {', '.join(results['safe_stocks']) if results['safe_stocks'] else 'None'}

**Caution Stocks:** {', '.join(results['caution_stocks']) if results['caution_stocks'] else 'None'}

**Avoid Stocks:** {', '.join(results['avoid_stocks']) if results['avoid_stocks'] else 'None'}
"""
    
    return summary.strip()