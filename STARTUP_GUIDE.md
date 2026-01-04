# 🚀 Startup Scripts Guide

This guide explains how to use the auto-reload and auto-sync scripts for the Options Trading Dashboard.

---

## Quick Start (Recommended)

### Option 1: Simple Auto-Reload (Easiest)

Just run this once:

```bash
./start_app.sh
```

**What it does:**
- ✅ Pulls latest changes from GitHub
- ✅ Clears Python cache
- ✅ Starts Streamlit with auto-reload enabled
- ✅ Automatically reloads when you edit files locally

**When to use:** Daily development, making local changes

---

### Option 2: Auto-Sync + Auto-Reload (Best for Collaboration)

Run both scripts in separate terminals:

**Terminal 1:**
```bash
./start_app.sh
```

**Terminal 2:**
```bash
./watch_and_sync.sh
```

**What it does:**
- ✅ Everything from Option 1
- ✅ Checks GitHub for updates every 30 seconds
- ✅ Auto-pulls when changes are pushed from elsewhere (e.g., from Manus)
- ✅ Streamlit auto-reloads when files change

**When to use:** When working with Manus or collaborators who push to GitHub

---

## Detailed Usage

### `start_app.sh` - Main Startup Script

**Features:**
- Pulls latest from GitHub before starting
- Clears Python cache (`__pycache__`, `.pyc` files)
- Stops any existing Streamlit instances
- Starts Streamlit with auto-reload enabled
- Uses dark theme by default

**Usage:**
```bash
./start_app.sh
```

**Stop:** Press `Ctrl+C`

---

### `watch_and_sync.sh` - Auto-Sync Watcher

**Features:**
- Runs in background
- Checks GitHub every 30 seconds
- Auto-pulls when remote changes detected
- Stashes local changes if needed
- Clears cache after pulling

**Usage:**

Run in foreground (see output):
```bash
./watch_and_sync.sh
```

Run in background:
```bash
./watch_and_sync.sh &
```

Keep running after logout:
```bash
nohup ./watch_and_sync.sh > sync.log 2>&1 &
```

**Stop:**
```bash
# Find the process
ps aux | grep watch_and_sync

# Kill it
kill <PID>

# Or kill all watch scripts
pkill -f watch_and_sync
```

---

## Workflow Examples

### Scenario 1: Solo Development
```bash
# Just run the app
./start_app.sh

# Make changes to files
# Streamlit auto-reloads when you save
```

### Scenario 2: Working with Manus
```bash
# Terminal 1: Start the app
./start_app.sh

# Terminal 2: Start auto-sync
./watch_and_sync.sh

# Now when Manus pushes changes to GitHub:
# 1. watch_and_sync.sh detects and pulls them
# 2. Streamlit auto-reloads with the new code
# 3. You see updates immediately!
```

### Scenario 3: Codespace (Always Running)
```bash
# Start both in background
nohup ./start_app.sh > app.log 2>&1 &
nohup ./watch_and_sync.sh > sync.log 2>&1 &

# Check logs
tail -f app.log
tail -f sync.log

# Your dashboard stays running even if you close the browser
```

---

## Troubleshooting

### Streamlit won't start
```bash
# Kill any existing instances
pkill -f "streamlit run"

# Try again
./start_app.sh
```

### Git pull conflicts
```bash
# Reset to remote version (loses local changes!)
git reset --hard origin/main

# Or stash your changes first
git stash
git pull
git stash pop
```

### Port already in use
```bash
# Find what's using port 8501
lsof -i :8501

# Kill it
kill <PID>

# Or use a different port
streamlit run app.py --server.port 8502
```

### Cache issues
```bash
# Manual cache clear
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Restart Streamlit
./start_app.sh
```

---

## Configuration

### Change sync interval
Edit `watch_and_sync.sh` and change:
```bash
sleep 30  # Change to desired seconds
```

### Change Streamlit port
Edit `start_app.sh` and add:
```bash
streamlit run app.py --server.port 8502
```

### Disable dark theme
Edit `start_app.sh` and remove:
```bash
--theme.base dark
```

---

## Tips

1. **Use VS Code's integrated terminal** - Run scripts in split terminals
2. **Check sync.log** - See what's being pulled: `tail -f sync.log`
3. **Bookmark the URL** - Usually `http://localhost:8501`
4. **Use Codespace port forwarding** - Access from anywhere
5. **Stop before git operations** - Avoid conflicts during manual git commands

---

## Need Help?

- **Script not working?** Check file permissions: `ls -la *.sh`
- **Git issues?** Run `git status` to see what's wrong
- **Streamlit errors?** Check `app.log` or terminal output
- **Still stuck?** Ask Manus for help!
