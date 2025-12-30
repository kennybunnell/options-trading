#!/bin/bash

echo "🚀 Starting Options Trading Dashboard..."
echo ""

# Install dependencies (in case of fresh start)
echo "📦 Checking dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "✅ Dependencies ready!"
echo ""

# Start Streamlit
echo "🌐 Starting Streamlit server..."
echo "📍 Once started, go to PORTS tab and make port 8501 PUBLIC"
echo ""

streamlit run app.py --server.headless=true
