import streamlit as st
import requests
import json
from datetime import datetime
import logging

# Configure advanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Google Apps Script URL (same as yours)
FETCH_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyyvQylzEz7uxrpizadLThdrDl5z3fGG2kV7InhLissWKH2uw1uzPCfi6TzDLi_iRB8Hg/exec"

def fetch_expense_data():
    try:
        response = requests.get(FETCH_SCRIPT_URL, timeout=10)
        
        # Check for JSON errors
        try:
            response.json()
        except json.JSONDecodeError:
            if "Google Apps Script" in response.text:
                st.error("""
                🔧 Script Configuration Required:
                1. Open the script URL in browser
                2. Click 'Review Permissions'
                3. Choose your Google account
                4. Click 'Advanced' > 'Go to [Project Name]'
                5. Click 'Allow'
                """)
            return []
            
        return response.json().get('data', [])
        
    except Exception as e:
        st.error(f"""
        🚨 Connection Error:
        {str(e)}
        Verify the script is deployed as:
        - Execute as: Me
        - Who has access: Anyone
        """)
        return []

def show_analytics():
    """Main analytics function with enhanced diagnostics"""
    try:
        st.markdown("---")
        st.subheader("📊 Expense Analytics")
        
        with st.spinner("🔍 Loading financial insights..."):
            raw_data = fetch_expense_data()
            
            if not raw_data:
                st.info("📭 No expense records found")
                return
                
            # Display raw data preview for debugging
            with st.expander("🔧 Debug Data Preview"):
                st.write("First 3 records from server:")
                st.json(raw_data[:3])
                
            # Continue processing...
            
    except Exception as e:
        logger.error(f"💣 Analytics failure: {str(e)}", exc_info=True)
        st.error("""
        🚨 Critical Error:
        We've hit an unexpected problem. To help resolve this:
        1. Screenshot this error
        2. Check the script URL directly
        3. Contact support with these details
        """)
