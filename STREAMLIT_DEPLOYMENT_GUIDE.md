# Streamlit Cloud Deployment Guide

## 🚀 Quick Start - Deploy Your Dashboard to Streamlit Cloud

Follow these steps to deploy your Options Trading Dashboard to Streamlit Cloud and access it from anywhere.

---

## 📋 Prerequisites

- ✅ GitHub account (kennybunnell)
- ✅ Repository: `kennybunnell/options-trading`
- ✅ Tastytrade credentials ready

---

## 🌐 Step-by-Step Deployment

### Step 1: Sign Up for Streamlit Cloud

1. Go to **https://share.streamlit.io/**
2. Click **"Sign up"** or **"Continue with GitHub"**
3. Authorize Streamlit to access your GitHub repositories
4. You'll be redirected to the Streamlit Cloud dashboard

---

### Step 2: Create a New App

1. Click the **"New app"** button (top right)
2. Fill in the deployment settings:

   **Repository:**
   - Select: `kennybunnell/options-trading`
   
   **Branch:**
   - Select: `main`
   
   **Main file path:**
   - Enter: `app.py`
   
   **App URL (optional):**
   - Customize your URL (e.g., `kennybunnell-options-trading`)
   - Default will be: `https://kennybunnell-options-trading.streamlit.app`

3. **Don't click Deploy yet!** → Click **"Advanced settings"** first

---

### Step 3: Configure Secrets (Environment Variables)

In the **Advanced settings** section, you'll see a **"Secrets"** text area. Copy and paste this format:

```toml
# Tastytrade API Credentials
TASTYTRADE_USERNAME = "your_actual_username"
TASTYTRADE_PASSWORD = "your_actual_password"
TASTYTRADE_DEFAULT_ACCOUNT = "5WZ77313"

# Optional: Tradier API (if you use it)
TRADIER_API_KEY = "your_tradier_key_if_you_have_one"
```

**Important:** Replace the values with your actual credentials!

**Where to find your credentials:**
- Check your local `.env` file in the repo
- Or check your Codespace environment variables

---

### Step 4: Deploy!

1. Click **"Deploy!"** button
2. Wait 2-3 minutes while Streamlit Cloud:
   - Clones your repository
   - Installs dependencies from `requirements.txt`
   - Starts your app
3. You'll see a build log - watch for any errors

---

### Step 5: Access Your Dashboard

Once deployed (status shows "Running"):
- **Your URL:** `https://[your-app-name].streamlit.app`
- **Always accessible** from any device
- **Auto-updates** when you push to GitHub main branch

---

## 🔒 Security & Access Control

### Option 1: Built-in Email Authentication (Recommended)

1. In your Streamlit Cloud dashboard, click on your app
2. Go to **Settings** → **Sharing**
3. Enable **"Restrict viewing access"**
4. Add your email address (only you can access)
5. Can add additional emails for team members

### Option 2: Password Protection in Code

If you want a simple password prompt, I can add authentication code to your app.

---

## 🔄 Updating Your Dashboard

**Automatic Updates:**
Whenever you push changes to GitHub:
```bash
git add .
git commit -m "Update dashboard"
git push origin main
```

Streamlit Cloud will **automatically redeploy** your app (takes ~1-2 minutes).

---

## 🐛 Troubleshooting

### Issue: App won't start

**Check the logs:**
1. Go to Streamlit Cloud dashboard
2. Click on your app
3. Click "Manage app" → "Logs"
4. Look for error messages

**Common issues:**
- Missing environment variables (check Secrets)
- Missing dependencies (check requirements.txt)
- Python syntax errors (test locally first)

### Issue: Can't connect to Tastytrade API

**Check:**
1. Secrets are set correctly (no typos)
2. Username/password are correct
3. Account number is correct
4. Tastytrade API is accessible from Streamlit Cloud servers

### Issue: App is slow

**Causes:**
- Fetching too much data from API
- Not using Streamlit caching
- Large data processing

**Solutions:**
- Use `@st.cache_data` decorator (already implemented)
- Limit API calls
- Optimize data processing

---

## 📊 Monitoring Your App

### View App Analytics

1. Go to Streamlit Cloud dashboard
2. Click on your app
3. See:
   - **Usage stats** (viewers, sessions)
   - **Resource usage** (CPU, memory)
   - **Logs** (errors, warnings)

### App Status

- **Running** (green) - App is live and accessible
- **Sleeping** (yellow) - App is idle (wakes up when accessed)
- **Error** (red) - App crashed (check logs)

---

## 💰 Pricing

### Free Tier (Public Repos)
- ✅ **1 app** deployment
- ✅ Unlimited viewers
- ✅ Community support
- ⚠️ Repository must be **public**

### Paid Tier ($20/month)
- ✅ **Unlimited apps**
- ✅ **Private repositories**
- ✅ More resources (CPU, memory)
- ✅ Priority support
- ✅ Custom domains

**For your use case:**
- If your repo is **public** → Free tier works
- If your repo is **private** → Need paid tier ($20/month)

---

## 🔐 Making Your Repo Private (Optional)

If you want to keep your code private:

1. Go to GitHub repo settings
2. Scroll to "Danger Zone"
3. Click "Change visibility" → "Make private"
4. Confirm

**Note:** You'll need Streamlit Cloud paid plan ($20/month) for private repos.

---

## 🎯 Next Steps After Deployment

### 1. Test Everything

- ✅ Home Dashboard loads
- ✅ CSP Ladder Manager shows correct buying power
- ✅ Performance Dashboard loads
- ✅ Stock Basis & Returns shows positions
- ✅ Recovery Tracker displays correctly
- ✅ All API calls work

### 2. Bookmark Your URL

Add to your browser bookmarks for quick access.

### 3. Mobile Access

Your dashboard works on mobile! Just visit the URL on your phone.

### 4. Share (Optional)

If you want to share with others:
- Add their emails in Streamlit Cloud settings
- Or disable access restrictions (not recommended for financial data)

---

## 🚀 Future: Migrate to GCP

When you're ready to move to Google Cloud Platform:

### Why GCP?

- More control over environment
- Better performance
- Custom domain support
- Integration with other GCP services
- No vendor lock-in

### Migration Steps (Future)

1. **Create GCP project**
2. **Deploy to Cloud Run** (easiest) or **Compute Engine**
3. **Set up Cloud SQL** for data storage (optional)
4. **Configure custom domain**
5. **Set up SSL certificate**
6. **Configure authentication** (OAuth, etc.)

I can help you with GCP deployment when you're ready!

---

## 📞 Need Help?

If you run into issues during deployment:

1. Check the Streamlit Cloud logs
2. Test locally first (`streamlit run app.py`)
3. Verify all secrets are set correctly
4. Check GitHub repo has latest code

---

## ✅ Deployment Checklist

Before deploying, make sure:

- [ ] Latest code pushed to GitHub main branch
- [ ] `requirements.txt` includes all dependencies
- [ ] `.streamlit/config.toml` exists (for theme/settings)
- [ ] You have your Tastytrade credentials ready
- [ ] You've signed up for Streamlit Cloud
- [ ] You've authorized Streamlit to access your GitHub

After deploying:

- [ ] App status shows "Running"
- [ ] You can access the URL
- [ ] Home Dashboard loads correctly
- [ ] API calls work (check positions load)
- [ ] No errors in logs

---

## 🎉 You're All Set!

Once deployed, you'll have:

✅ **24/7 access** to your dashboard from any device
✅ **Automatic updates** when you push to GitHub
✅ **Professional URL** to share (if desired)
✅ **No need to keep Codespace running**

Start using your dashboard on Monday, Jan 6 for your CSP ladder strategy! 🚀📈
