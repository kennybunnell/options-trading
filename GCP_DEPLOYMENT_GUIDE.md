# GCP Deployment Guide (Future)

## 🌐 Deploying Your Dashboard to Google Cloud Platform

This guide will help you deploy your Options Trading Dashboard to GCP when you're ready to move from Streamlit Cloud.

---

## 🎯 Why Deploy to GCP?

**Benefits:**
- ✅ **Full control** over infrastructure
- ✅ **Better performance** (dedicated resources)
- ✅ **Custom domain** support
- ✅ **Integration** with other GCP services
- ✅ **Scalability** (auto-scaling if needed)
- ✅ **Private by default** (no public repo required)

**Costs:**
- Cloud Run: ~$5-15/month (pay per use)
- Compute Engine: ~$10-30/month (always-on VM)
- Cloud SQL (optional): ~$10-20/month

---

## 🚀 Deployment Options on GCP

### Option 1: Cloud Run (Recommended - Easiest)

**Best for:** Serverless deployment, auto-scaling, pay-per-use

**Pros:**
- ✅ Fully managed (no server maintenance)
- ✅ Auto-scales to zero (save money when not in use)
- ✅ Built-in HTTPS
- ✅ Easy deployment from Docker

**Cons:**
- ⚠️ Cold starts (1-2 second delay if idle)
- ⚠️ Stateless (need external storage for data)

**Cost:** ~$5-15/month (based on usage)

---

### Option 2: Compute Engine (VM)

**Best for:** Always-on deployment, full control

**Pros:**
- ✅ Full control over environment
- ✅ No cold starts
- ✅ Can run background jobs
- ✅ Persistent storage

**Cons:**
- ⚠️ Need to manage server
- ⚠️ Pay for always-on (even when idle)
- ⚠️ Need to configure SSL manually

**Cost:** ~$10-30/month (e2-micro to e2-small instance)

---

### Option 3: App Engine

**Best for:** Simple deployment, managed platform

**Pros:**
- ✅ Fully managed
- ✅ Auto-scaling
- ✅ Built-in SSL

**Cons:**
- ⚠️ Less flexible than Compute Engine
- ⚠️ More expensive than Cloud Run

**Cost:** ~$15-30/month

---

## 📋 Prerequisites

Before deploying to GCP:

1. **GCP Account**
   - Sign up at https://cloud.google.com/
   - $300 free credits for new accounts

2. **Install Google Cloud SDK**
   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   gcloud init
   ```

3. **Enable APIs**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

4. **Set up billing**
   - Link a credit card (required even with free credits)

---

## 🐳 Option 1: Deploy to Cloud Run (Step-by-Step)

### Step 1: Create Dockerfile

Create `Dockerfile` in your repo:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose port
EXPOSE 8080

# Set environment variable for Streamlit
ENV PORT=8080

# Run Streamlit
CMD streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.serverAddress="0.0.0.0" \
    --browser.gatherUsageStats=false
```

### Step 2: Create .dockerignore

```
.git
.gitignore
.env
.streamlit/secrets.toml
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
```

### Step 3: Build and Deploy

```bash
# Set your GCP project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Build the container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/options-trading-dashboard

# Deploy to Cloud Run
gcloud run deploy options-trading-dashboard \
    --image gcr.io/$PROJECT_ID/options-trading-dashboard \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --set-env-vars TASTYTRADE_USERNAME=your_username \
    --set-env-vars TASTYTRADE_PASSWORD=your_password \
    --set-env-vars TASTYTRADE_DEFAULT_ACCOUNT=5WZ77313
```

### Step 4: Access Your App

After deployment:
- **URL:** `https://options-trading-dashboard-[hash]-uc.a.run.app`
- Copy this URL and bookmark it

### Step 5: Set Up Custom Domain (Optional)

```bash
# Map custom domain
gcloud run domain-mappings create \
    --service options-trading-dashboard \
    --domain trading.yourdomain.com \
    --region us-central1
```

---

## 🖥️ Option 2: Deploy to Compute Engine (Step-by-Step)

### Step 1: Create VM Instance

```bash
# Create e2-small instance (2GB RAM, 2 vCPUs)
gcloud compute instances create options-trading-vm \
    --zone=us-central1-a \
    --machine-type=e2-small \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --tags=http-server,https-server
```

### Step 2: Configure Firewall

```bash
# Allow HTTP/HTTPS traffic
gcloud compute firewall-rules create allow-streamlit \
    --allow tcp:8501 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server
```

### Step 3: SSH into VM and Set Up

```bash
# SSH into VM
gcloud compute ssh options-trading-vm --zone=us-central1-a

# Install dependencies
sudo apt update
sudo apt install -y python3-pip git

# Clone your repo
git clone https://github.com/kennybunnell/options-trading.git
cd options-trading

# Install Python packages
pip3 install -r requirements.txt

# Set environment variables
export TASTYTRADE_USERNAME="your_username"
export TASTYTRADE_PASSWORD="your_password"
export TASTYTRADE_DEFAULT_ACCOUNT="5WZ77313"

# Run Streamlit
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Step 4: Set Up as System Service (Always Running)

Create `/etc/systemd/system/streamlit-dashboard.service`:

```ini
[Unit]
Description=Streamlit Options Trading Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/options-trading
Environment="TASTYTRADE_USERNAME=your_username"
Environment="TASTYTRADE_PASSWORD=your_password"
Environment="TASTYTRADE_DEFAULT_ACCOUNT=5WZ77313"
ExecStart=/usr/local/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable streamlit-dashboard
sudo systemctl start streamlit-dashboard
sudo systemctl status streamlit-dashboard
```

### Step 5: Access Your App

- **URL:** `http://[VM-EXTERNAL-IP]:8501`
- Get external IP: `gcloud compute instances describe options-trading-vm --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'`

---

## 🔒 Security Best Practices

### 1. Use Secret Manager

Instead of environment variables, use GCP Secret Manager:

```bash
# Create secrets
echo -n "your_username" | gcloud secrets create tastytrade-username --data-file=-
echo -n "your_password" | gcloud secrets create tastytrade-password --data-file=-

# Grant access to Cloud Run
gcloud secrets add-iam-policy-binding tastytrade-username \
    --member=serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com \
    --role=roles/secretmanager.secretAccessor
```

### 2. Set Up Authentication

Add authentication to your Streamlit app using Google OAuth or custom auth.

### 3. Enable HTTPS

For Compute Engine, set up SSL with Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d trading.yourdomain.com
```

---

## 💰 Cost Estimation

### Cloud Run (Recommended)
- **CPU:** $0.00002400/vCPU-second
- **Memory:** $0.00000250/GiB-second
- **Requests:** $0.40/million requests
- **Estimated:** $5-15/month (light usage)

### Compute Engine (e2-small)
- **VM:** $13.34/month (730 hours)
- **Storage:** $2/month (20GB)
- **Estimated:** $15-20/month

### Additional Costs
- **Cloud SQL** (if needed): $10-20/month
- **Load Balancer** (if needed): $18/month
- **Cloud Storage** (if needed): $0.02/GB/month

---

## 🔄 CI/CD Pipeline (Optional)

Set up automatic deployment on GitHub push:

### Create `.github/workflows/deploy-gcp.yml`:

```yaml
name: Deploy to GCP Cloud Run

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v0
      with:
        project_id: ${{ secrets.GCP_PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}
    
    - name: Build and Deploy
      run: |
        gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/options-trading-dashboard
        gcloud run deploy options-trading-dashboard \
          --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/options-trading-dashboard \
          --platform managed \
          --region us-central1 \
          --allow-unauthenticated
```

---

## 📊 Monitoring & Logging

### View Logs

**Cloud Run:**
```bash
gcloud run services logs read options-trading-dashboard --region us-central1
```

**Compute Engine:**
```bash
sudo journalctl -u streamlit-dashboard -f
```

### Set Up Monitoring

1. Go to **Cloud Monitoring** in GCP Console
2. Create dashboards for:
   - CPU usage
   - Memory usage
   - Request count
   - Error rate

### Set Up Alerts

```bash
# Alert when CPU > 80%
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High CPU Alert" \
    --condition-threshold-value=0.8 \
    --condition-threshold-duration=300s
```

---

## 🚀 Next Steps After Deployment

1. **Test thoroughly** - Verify all features work
2. **Set up monitoring** - Track performance and errors
3. **Configure backups** - If using Cloud SQL
4. **Set up custom domain** - Point your domain to GCP
5. **Enable authentication** - Protect your dashboard
6. **Optimize costs** - Review usage and adjust resources

---

## 📞 When You're Ready

Let me know when you want to deploy to GCP and I'll help you:

1. Create the Dockerfile
2. Set up the deployment scripts
3. Configure CI/CD
4. Set up monitoring
5. Optimize for cost and performance

For now, use Streamlit Cloud - it's perfect for getting started quickly! 🚀
