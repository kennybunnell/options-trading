# Prosper Trading App - Current Status & Context

**Last Updated:** January 19, 2026  
**Repository:** https://github.com/kennybunnell/options-trading  
**Local Path:** `/home/ubuntu/projects/options-trading-7581daba/prosper-trading-app/`

---

## 📊 Application Overview

**Prosper Trading** is a professional options trading dashboard built with Python/Streamlit for analyzing and executing options strategies. The app connects to Tastytrade API for live trading and uses Yahoo Finance for technical analysis.

### Current Features

1. **Cash-Secured Puts (CSP) Dashboard**
   - Pull option chains from Tastytrade API
   - Dual scoring system (Primary + Secondary scores)
   - Smart recommendations with auto-selection
   - Interactive filters and sorting
   - Real-time summary card (premium, collateral, buying power)
   - One-click order submission to Tastytrade
   - Score-based selection buttons (100%, 95%+, 90%+, 85%+, 80%+, down to 40%)
   - Watchlist persistence in data/ directory

2. **Covered Calls (CC) Dashboard**
   - Pull existing positions from Tastytrade
   - Analyze covered call opportunities
   - Score and rank CC opportunities
   - Submit CC orders to Tastytrade
   - Score-based selection buttons (100% down to 40% in 5-point increments)
   - "Selected Only" toggle filter

3. **PMCC Dashboard (Poor Man's Covered Call)**
   - LEAPS-based covered call strategy
   - Notification system for alerts
   - Order submission capability

4. **Performance Dashboard**
   - Track trading performance
   - Analytics and metrics

5. **Technical Analysis Integration**
   - RSI (Relative Strength Index)
   - Bollinger Bands %
   - Moving Average %
   - 52-Week Range %

---

## 🏗️ Technical Architecture

### Tech Stack
- **Frontend:** Streamlit
- **Backend:** Python 3.11+
- **Data Processing:** Pandas, NumPy
- **Visualization:** Plotly
- **APIs:** 
  - Tastytrade API (primary - account data, option chains, order submission)
  - Yahoo Finance (technical indicators)
  - Tradier API (backup/alternative market data)

### Project Structure
```
prosper-trading-app/
├── app.py (5,684 lines - main Streamlit app)
├── utils/
│   ├── tastytrade_api.py (Tastytrade API integration)
│   ├── cash_secured_puts.py (CSP logic)
│   ├── covered_calls.py (CC logic)
│   ├── pmcc_scanner.py (PMCC logic)
│   ├── performance_dashboard.py (Performance tracking)
│   ├── yahoo_finance.py (Technical indicators)
│   ├── scoring.py (Options scoring system)
│   └── [25+ other utility modules]
├── assets/
│   ├── prosper_trading_banner.png (4.7MB)
│   └── prosper_trading_logo.png (5.0MB)
├── data/ (persistent data storage)
├── requirements.txt
└── Documentation files (README, guides, etc.)
```

---

## 📝 Recent Development History

### Last 5 Commits (as of Jan 19, 2026)
1. **47cf68f** (3 days ago) - Expand score filter buttons to 5-point increments (80-40) on both CC and CSP dashboards
2. **9c0d856** - Fix CSP watchlist persistence - save to data/ directory
3. **d121137** - Add Selected Only toggle to CC Dashboard (was missing)
4. **bb9138d** - Add score-based selection buttons to CSP Dashboard (100%, 95%+, 90%+, 85%+, 80%+)
5. **c438ec9** - Move score filter buttons to appear right above contracts table

### Recent Focus Areas
- Enhanced user experience with score-based filtering
- Improved data persistence (watchlists)
- UI/UX refinements for dashboard controls
- Bug fixes for format specifiers and display issues

---

## 🎯 Known Requirements & Preferences

### User Context
- **Non-coder:** Requires complete, ready-to-use code blocks with clear instructions
- **Multi-account trading:** Needs support for Traditional IRA, Cash, HELOC-funded, and LLC entity accounts
- **Full Wheel Strategy:** Must support CSPs → assignment → covered calls workflow
- **Tastytrade exclusive:** All order execution must go through Tastytrade API

### Development Workflow
1. Set context properly at the start
2. Provide complete code blocks (not partial)
3. Deliver code as downloadable .txt files for reliability
4. Include version numbers in code headers
5. Always include a final confirmation step before live order execution
6. Maintain credential persistence (no manual re-entry)

---

## 🚀 Deployment Status

- **Development:** Local Streamlit app
- **Deployment Options Available:**
  - Streamlit Cloud (see STREAMLIT_DEPLOYMENT_GUIDE.md)
  - Google Cloud Platform (see GCP_DEPLOYMENT_GUIDE.md)
  - Devcontainer setup available (.devcontainer/)

---

## 📋 Next Steps / Roadmap

### Immediate Priorities
- [TO BE DETERMINED BY USER]

### Future Enhancements
- Enhanced PMCC tracking and management
- Additional technical indicators
- Advanced portfolio analytics
- Multi-account view and management
- Automated trade execution based on criteria

---

## 🔧 Setup & Configuration

### Environment Variables Required
Create `.env` file with:
- `TASTYTRADE_USERNAME`
- `TASTYTRADE_PASSWORD`
- `TRADIER_API_KEY` (optional backup)

### Installation
```bash
cd /home/ubuntu/projects/options-trading-7581daba/prosper-trading-app
pip install -r requirements.txt
streamlit run app.py
```

---

## 📚 Documentation Files

- `README` - Project overview
- `STARTUP_GUIDE.md` - Getting started
- `CSP_QUICK_START.md` - CSP dashboard guide
- `PMCC_QUICK_START.md` - PMCC dashboard guide
- `CSP_DASHBOARD_RESTORATION_SUMMARY.md` - CSP feature history
- `PMCC_DASHBOARD_COMPLETE.md` - PMCC implementation details
- `STREAMLIT_DEPLOYMENT_GUIDE.md` - Cloud deployment
- `GCP_DEPLOYMENT_GUIDE.md` - GCP deployment

---

## 💡 Session Continuity Notes

**For Future Sessions:**
1. Repository is stored in persistent project directory
2. No need to reclone - just navigate to `/home/ubuntu/projects/options-trading-7581daba/prosper-trading-app/`
3. Always check `git status` for uncommitted changes before starting work
4. Update this file with new developments and next steps
5. Reference previous task: "prosper trading ROI calculator" for additional context

---

## ⚠️ Important Notes

- App uses session state extensively for UI persistence
- Tastytrade API requires active session token management
- Technical indicators fetched from Yahoo Finance may have rate limits
- Order submission includes celebration effects (balloons + cha-ching sound)
- All monetary values displayed with proper formatting and emoji indicators

---

**End of Status Document**
