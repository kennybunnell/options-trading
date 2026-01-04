#!/bin/bash

# ============================================
# Auto-Sync & Watch Script
# ============================================
# This script runs in the background and:
# 1. Checks GitHub for updates every 30 seconds
# 2. Auto-pulls if changes are detected
# 3. Streamlit will auto-reload when files change
#
# Usage: 
#   ./watch_and_sync.sh &    # Run in background
#   Or: nohup ./watch_and_sync.sh &  # Keep running after logout
# ============================================

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔄 Starting auto-sync watcher...${NC}"
echo -e "${YELLOW}Checking for GitHub updates every 30 seconds${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

while true; do
    # Fetch latest from GitHub
    git fetch origin main --quiet 2>/dev/null
    
    # Check if local is behind remote
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] 📥 New changes detected, pulling...${NC}"
        
        # Stash any local changes (shouldn't be any, but just in case)
        git stash --quiet 2>/dev/null || true
        
        # Pull latest changes
        git pull origin main --quiet
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Successfully synced with GitHub${NC}"
            echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Streamlit will auto-reload${NC}"
            
            # Clear cache
            find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        else
            echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠ Pull failed${NC}"
        fi
    fi
    
    # Wait 30 seconds before next check
    sleep 30
done
