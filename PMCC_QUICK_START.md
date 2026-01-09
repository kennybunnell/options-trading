# 🎯 PMCC Dashboard - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### **Step 1: Pull Latest Code**
```bash
cd /path/to/options-trading
git pull origin main
streamlit run app.py
```

### **Step 2: Navigate to PMCC Dashboard**
Click **"🎯 PMCC Dashboard"** in the left sidebar

---

## 📋 Basic Workflow

### **1. Add Tickers** 📝
- Import CSV from TradingView, OR
- Type ticker (e.g., AAPL) and click "➕ Add"

### **2. Scan for LEAPs** 🔍
- Choose preset: **Aggressive** / **Medium** / **Conservative**
- Click **"🔍 Scan for LEAPs"**
- Select LEAP from dropdown
- Choose quantity
- Click **"💰 Buy LEAP"**

### **3. Sell Short Calls** 💰
- Click **"🔍 Refresh PMCC Positions"** (fetches your LEAPs)
- Select LEAP from dropdown
- Click **"🔍 Scan Short Calls"**
- Select short call
- Click **"💰 Sell Short Call"**

### **4. Monitor Risk** ⚠️
- Check **Assignment Risk Alerts** section
- Watch for CRITICAL or HIGH risk warnings
- Click **"📧 Send Alert"** for email/SMS (if configured)

---

## 🎯 Strategy Cheat Sheet

### **LEAP Selection**
- **DTE**: 270-450 days (9-15 months)
- **Delta**: 0.70-0.90 (deep ITM)
- **Open Interest**: 50+ (liquidity)

### **Short Call Selection**
- **DTE**: 30-45 days (theta sweet spot)
- **Delta**: <0.30 (low assignment risk)
- **Strike**: ABOVE your LEAP strike
- **Premium**: $50+ per contract

### **ROI Targets**
- **Conservative**: 50% (half of LEAP cost)
- **Aggressive**: 100% (full LEAP cost)
- **Typical**: 3-6 short calls to hit 50%

---

## ⚠️ Risk Management

### **When to Roll**
- 🚨 **CRITICAL**: ITM with ≤7 DTE → Roll NOW
- ⚠️ **HIGH**: ITM with >7 DTE → Monitor closely
- ⚡ **MODERATE**: Within 5% of strike → Watch
- ✅ **LOW**: Safely OTM → Relax

### **Roll Strategy**
- Roll **UP** if bullish (higher strike)
- Roll **OUT** if neutral (later expiration)
- Roll **DOWN and OUT** if bearish (lower strike + later date)

---

## 📧 Enable Notifications (Optional)

Add to `.env` file:

```bash
NOTIFICATIONS_ENABLED=true
NOTIFICATION_EMAIL=your_email@gmail.com

# Gmail SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

**Gmail App Password**: Google Account → Security → 2FA → App Passwords

---

## 🔄 Rollback (If Needed)

```bash
# Revert to before PMCC
git checkout pmcc-scanner-complete

# Or restore from backup
cp backups/pmcc_backup_20260108_230043/app.py app.py
```

---

## 💡 Pro Tips

1. **Start Small**: Test with 1 LEAP on a low-cost ticker
2. **Track ROI**: Aim for 50% before LEAP expiration
3. **Set Alerts**: Enable notifications for peace of mind
4. **Roll Early**: Don't wait until expiration if ITM
5. **Take Profits**: Close short calls at 50% profit

---

## 📊 What You'll See

### **Active PMCC Positions**
- LEAP legs with cost basis and P/L
- Short calls with premiums collected
- ROI tracking (current % vs 50% target)

### **Assignment Risk Alerts**
- Real-time risk monitoring
- Color-coded warnings
- Actionable recommendations

### **Scan Results**
- LEAPs sorted by delta (highest first)
- Short calls sorted by premium (highest first)
- All key metrics in one table

---

## ✅ You're Ready!

Navigate to **🎯 PMCC Dashboard** and start scanning! 🚀
