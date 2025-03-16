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
FETCH_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwZ8Ltcz5n-kEI3b7zBJU9eH0K8KdiBveCEk6-XczwMOc8I-uxopyCp75S8HR-d2Bvsig/exec"

def fetch_expense_data():
    """Fetch and validate data with enhanced diagnostics"""
    try:
        # Add cache busting to prevent stale responses
        timestamp = int(datetime.now().timestamp())
        url = f"{FETCH_SCRIPT_URL}?cache={timestamp}"
        
        logger.info(f"🔍 Attempting to fetch data from: {url}")
        response = requests.get(url, timeout=15)
        
        # Log raw response details
        logger.debug(f"📄 Response status: {response.status_code}")
        logger.debug(f"🔖 Response headers: {dict(response.headers)}")
        logger.debug(f"📝 First 500 characters of response:\n{response.text[:500]}")

        # Check for common error patterns
        if response.status_code == 401:
            logger.error("🔒 Authentication required")
            st.error("Authorization needed - check script permissions")
            return []

        if "text/html" in response.headers.get('Content-Type', ''):
            logger.error("🖥️ Received HTML response instead of JSON")
            st.error("""
            ❗ Script Configuration Issue Detected:
            1. Open the script URL directly in your browser
            2. Ensure you see JSON data, not a login page
            3. Redeploy the script with:
               - Execute as: Me
               - Access: Anyone, even anonymous
            """)
            return []

        try:
            data = response.json()
            logger.info(f"✅ Successfully parsed {len(data.get('data', []))} records")
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {str(e)}")
            st.error(f"""
            🛠️ Data Format Issue Detected:
            Server response isn't valid JSON. Common causes:
            1. Script is returning HTML/error messages
            2. Incorrect data structure from Google Sheets
            3. Authorization requirements
            
            🔗 Test the script directly: {FETCH_SCRIPT_URL}
            """)
            return []

        # Validate response structure
        if 'data' not in data:
            logger.error(f"🔍 Missing 'data' key in response. Keys found: {data.keys()}")
            st.error("""
            📛 Unexpected Response Structure:
            The script should return {{"data": [...]}}
            Verify your Google Apps Script code:
            function doGet() {{
              return ContentService
                .createTextOutput(JSON.stringify({{ data: yourData }}))
                .setMimeType(ContentService.MimeType.JSON);
            }}
            """)
            return []

        return data['data']

    except requests.exceptions.SSLError:
        logger.error("🔒 SSL Certificate verification failed")
        st.error("Security connection failed - check system date/time")
        return []
        
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}", exc_info=True)
        st.error("""
        🌐 Network Issue Detected:
        1. Check your internet connection
        2. Try refreshing the page
        3. If using VPN, ensure proper connectivity
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
