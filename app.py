import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Options Trading Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("💰 Options Trading Dashboard")

# Sidebar navigation
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select Page",
        ["🏠 Home", "📊 CSP Dashboard", "📈 CC Dashboard", "⚙️ Settings"]
    )

# Main content based on page selection
if page == "🏠 Home":
    st.write("## Welcome to Your Options Trading Dashboard!")
    
    st.write("""
    This professional web application helps you:
    - 📊 Find the best **cash-secured put** opportunities
    - 📈 Manage **covered call** positions  
    - 🚀 Submit orders to **Tastytrade** with one click
    - 📉 Track your portfolio performance
    """)
    
    # Check API credentials
    st.write("---")
    st.write("### 🔑 API Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if os.getenv("TASTYTRADE_USERNAME"):
            st.success("✅ Tastytrade: Configured")
        else:
            st.error("❌ Tastytrade: Not configured")
    
    with col2:
        if os.getenv("TRADIER_API_KEY") and os.getenv("TRADIER_API_KEY") != "not_configured":
            st.success("✅ Tradier: Configured")
        else:
            st.warning("⚠️ Tradier: Not configured")
    
    with col3:
        st.success("✅ Yahoo Finance: Ready")
    
    st.write("---")
    st.info("👈 Use the sidebar to navigate to CSP or CC Dashboard")

elif page == "📊 CSP Dashboard":
    st.write("## 📊 Cash-Secured Puts Dashboard")
    st.info("🚧 Coming soon!")

elif page == "📈 CC Dashboard":
    st.write("## 📈 Covered Calls Dashboard")
    st.info("🚧 Coming soon!")

elif page == "⚙️ Settings":
    st.write("## ⚙️ Settings")
    st.write("### API Credentials Status")
    
    if os.getenv("TASTYTRADE_USERNAME"):
        st.success(f"✅ Tastytrade: Connected as `{os.getenv('TASTYTRADE_USERNAME')}`")
        accounts = os.getenv("TASTYTRADE_ACCOUNTS", "").split(",")
        st.write(f"**Accounts:** {len(accounts)} configured")
    else:
        st.error("❌ Tastytrade: Not configured")

# Footer
st.write("---")
st.caption("Built with ❤️ using Streamlit | Options Trading Dashboard v1.0")
