# CSP Dashboard Quick Start Guide

## 🚀 Getting Started

### 1. Start the Application
```bash
cd /home/ubuntu/options-trading-github
streamlit run app.py
```

### 2. Navigate to CSP Dashboard
Click **"CSP Dashboard"** in the sidebar

---

## 📋 Workflow

### Step 1: Build Your Watchlist

**Option A: Import from TradingView**
1. Export your TradingView screener as CSV
2. Click "Upload TradingView CSV" in the CSP Dashboard
3. Choose "Replace" or "Append" mode
4. Click "✅ Replace/Append Watchlist"

**Option B: Manual Entry**
1. Enter ticker symbol in the text box
2. Click "➕ Add to Watchlist"

**View Watchlist:**
- Click "👁️ View/Edit Watchlist" to see all symbols
- Check boxes and click "🗑️ Remove Selected" to delete symbols

---

### Step 2: Scan for CSP Opportunities

1. Click **"🔄 Fetch Opportunities"** button
2. Wait for scan to complete (progress bar shows status)
3. Review results in the opportunities table

**What the Scanner Does:**
- Fetches option chains for all watchlist symbols
- Filters PUT options by delta (0.05 - 0.50)
- Calculates premium at MID price: `(bid + ask) / 2`
- Computes ROI and annualized return
- Gets technical indicators (IV Rank, RSI)
- Displays results sorted by annualized return

**Scan Results Include:**
- Symbol, Strike, Expiration, DTE
- Delta, IV Rank, Spread %
- Premium (at MID price)
- Collateral Required
- ROI and Annualized Return
- Volume and Open Interest

---

### Step 3: Select Opportunities

1. Check the boxes next to opportunities you want to trade
2. Review the metrics:
   - **High Annualized Return** = Better income potential
   - **Low Delta** = Lower assignment risk
   - **High IV Rank** = Premium is elevated
   - **Low Spread %** = Better liquidity

**Recommended Criteria:**
- Delta: 0.10 - 0.30 (10-30% probability of assignment)
- IV Rank: > 50 (premium is above average)
- Spread %: < 10% (tight bid-ask spread)
- Volume: > 100 (good liquidity)
- Open Interest: > 500 (established market)

---

### Step 4: Submit Orders (DRY RUN FIRST!)

**Dry Run (Test Mode):**
1. Select opportunities (checkboxes)
2. Click "Submit Selected Orders"
3. **Enable "Dry Run Mode"** toggle
4. Click "✅ Confirm & Submit Orders"
5. Review results (should show success simulation)

**Live Orders:**
1. Select opportunities (checkboxes)
2. Click "Submit Selected Orders"
3. **Disable "Dry Run Mode"** toggle
4. Review order summary:
   - Total Premium to collect
   - Total Collateral required
   - Individual order details
5. Click "✅ Confirm & Submit Orders"
6. Wait for confirmation
7. Page auto-refreshes to show new positions

**Order Details:**
- **Order Type**: Sell-to-Open PUT
- **Price**: MID price `(bid + ask) / 2`
- **Quantity**: Calculated based on available buying power
- **Collateral**: `strike × 100 × contracts`

---

### Step 5: Monitor Positions

**Existing CSP Positions Table:**
- Shows all current short put positions
- Displays P/L, % Recognized, DTE
- Updates after each order submission

**Working Orders Monitor:**
- Shows pending orders
- Displays order status (working, filled, rejected)
- Ability to cancel pending orders

---

## 📊 Understanding the Metrics

### Premium
- Amount you collect for selling the put
- Calculated at MID price: `(bid + ask) / 2`
- Example: Bid $2.00, Ask $2.10 → Premium = $2.05

### Collateral Required
- Cash needed to secure the put
- Formula: `strike × 100 × contracts`
- Example: $50 strike, 1 contract → $5,000 collateral

### ROI (Return on Investment)
- Premium as % of collateral
- Formula: `(premium / collateral) × 100`
- Example: $100 premium, $5,000 collateral → 2% ROI

### Annualized Return
- ROI projected over a full year
- Formula: `(ROI / DTE) × 365`
- Example: 2% ROI, 30 DTE → 24.3% annualized

### Delta
- Probability of option expiring in-the-money
- 0.10 delta = 10% chance of assignment
- 0.30 delta = 30% chance of assignment
- Lower delta = safer, but lower premium

### IV Rank
- Implied volatility percentile (0-100)
- High IV Rank (>50) = Premium is elevated
- Low IV Rank (<50) = Premium is below average
- Sell puts when IV Rank is high

### Spread %
- Bid-ask spread as % of mid price
- Formula: `((ask - bid) / mid) × 100`
- Low spread (<10%) = Good liquidity
- High spread (>20%) = Poor liquidity, avoid

---

## ⚠️ Risk Management

### Position Sizing
- Don't use more than 5% of account on one position
- Diversify across multiple symbols
- Keep cash reserve for assignments

### Delta Selection
- **Conservative**: 0.05 - 0.15 delta (5-15% assignment risk)
- **Moderate**: 0.15 - 0.25 delta (15-25% assignment risk)
- **Aggressive**: 0.25 - 0.40 delta (25-40% assignment risk)

### DTE (Days to Expiration)
- **Short-term**: 7-21 DTE (higher theta decay)
- **Mid-term**: 30-45 DTE (balanced risk/reward)
- **Long-term**: 60-90 DTE (lower management frequency)

### Assignment Risk
If the stock drops below your strike:
1. You'll be assigned 100 shares per contract
2. You'll pay: `strike × 100 × contracts`
3. You keep the premium collected
4. You now own the stock at the strike price

**To Avoid Assignment:**
- Buy back the put before expiration (buy-to-close)
- Roll the put to a later expiration (close + reopen)
- Let it expire if the stock stays above strike

---

## 🔧 Troubleshooting

### "No opportunities found"
- **Check watchlist**: Ensure you have symbols added
- **Check filters**: Default delta range is 0.05-0.50
- **Try different symbols**: Some stocks have no active options
- **Review scan log**: Click "View Detailed Scan Log" for reasons

### "Order submission failed"
- **Check buying power**: Ensure sufficient collateral available
- **Check market hours**: Orders only during 9:30 AM - 4:00 PM ET
- **Check API credentials**: Verify Tastytrade API is connected
- **Check option liquidity**: Avoid wide spreads (>20%)

### "Positions not updating"
- **Wait for fill**: Orders may take time to execute
- **Check Working Orders**: See if order is still pending
- **Manual refresh**: Press F5 to reload page
- **Check Tastytrade**: Verify order status in platform

---

## 💡 Pro Tips

### 1. Use High IV Rank
- Sell puts when IV Rank > 50
- Premium is elevated = better income
- Avoid selling when IV Rank < 30

### 2. Target 30-45 DTE
- Sweet spot for theta decay
- Not too short (gamma risk)
- Not too long (capital tied up)

### 3. Aim for 1-2% ROI
- 1% ROI in 30 days = 12% annualized
- 2% ROI in 30 days = 24% annualized
- Don't chase high returns with high delta

### 4. Manage Winners Early
- Close at 50% profit (buy-to-close)
- Don't wait for full expiration
- Redeploy capital into new trades

### 5. Roll Losers
- If stock drops, don't panic
- Roll to later expiration for credit
- Lower strike if needed (adjust down)

### 6. Diversify
- 5-10 different symbols minimum
- Different sectors (tech, finance, healthcare)
- Mix of high/low IV stocks

---

## 📈 Example Trade

**Setup:**
- Symbol: AAPL
- Current Price: $180
- Strike: $175 (5 points OTM)
- Expiration: 30 DTE
- Delta: 0.20 (20% assignment risk)
- Premium: $2.50 (MID price)
- IV Rank: 65 (elevated)

**Trade:**
- Sell 1 contract of AAPL $175 PUT
- Collect: $250 premium ($2.50 × 100)
- Collateral: $17,500 ($175 × 100)
- ROI: 1.43% ($250 / $17,500)
- Annualized: 17.4% (1.43% × 365 / 30)

**Outcomes:**
1. **Stock stays above $175**: Put expires worthless, keep $250
2. **Stock drops below $175**: Assigned 100 shares at $175, keep $250
3. **Close early at 50% profit**: Buy-to-close at $1.25, profit $125

---

## 📚 Additional Resources

- **Tastytrade Education**: https://www.tastytrade.com/learn
- **Options Playbook**: https://www.optionsplaybook.com/
- **IV Rank Explained**: Search "IV Rank vs IV Percentile"

---

## 🎯 Summary Checklist

- [ ] Build watchlist (TradingView import or manual)
- [ ] Click "Fetch Opportunities" to scan
- [ ] Review results (annualized return, delta, IV Rank)
- [ ] Select opportunities (checkboxes)
- [ ] Test with Dry Run Mode first
- [ ] Submit live orders (disable Dry Run)
- [ ] Monitor positions in "Existing CSP Positions"
- [ ] Manage winners at 50% profit
- [ ] Roll losers if needed

---

**Happy Trading! 🚀**
