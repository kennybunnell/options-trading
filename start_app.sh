#!/bin/bash

# ============================================
# Auto-Reload Streamlit Startup Script
# ============================================
# This script:
# 1. Pulls latest changes from GitHub
# 2. Starts Streamlit with auto-reload enabled
# 3. Watches for file changes and auto-restarts
#
# Usage: ./start_app.sh
# ============================================

set -e  # Exit on error

echo "========================================"
echo "🚀 Starting Options Trading Dashboard"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Pull latest changes from GitHub
echo -e "${BLUE}📥 Pulling latest changes from GitHub...${NC}"
git pull origin main

# Check if pull was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully pulled latest changes${NC}"
else
    echo -e "${YELLOW}⚠ Git pull failed or no changes to pull${NC}"
fi

# Clear Python cache
echo -e "${BLUE}🧹 Clearing Python cache...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✓ Cache cleared${NC}"

# Check if Streamlit is already running
if pgrep -f "streamlit run" > /dev/null; then
    echo -e "${YELLOW}⚠ Streamlit is already running. Stopping it...${NC}"
    pkill -f "streamlit run"
    sleep 2
fi

# Start Streamlit with auto-reload
echo -e "${BLUE}🎯 Starting Streamlit...${NC}"
echo ""
echo -e "${GREEN}Dashboard will be available at:${NC}"
echo -e "${GREEN}  Local: http://localhost:8501${NC}"
echo -e "${GREEN}  Network: Check terminal output below${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo "========================================"
echo ""

# Run Streamlit with auto-reload enabled
streamlit run app.py \
    --server.runOnSave true \
    --server.fileWatcherType auto \
    --browser.gatherUsageStats false \
    --theme.base dark
