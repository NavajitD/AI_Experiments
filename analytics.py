import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Apps Script URL for fetching data
FETCH_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbygEKgEV6irH-nnJci-2YWsFVLOZokSpyVpaxACU14JcekHyiMSU2UltkDvw7aIaINYng/exec"

def fetch_expense_data():
    """Fetch and validate expense data with enhanced diagnostics"""
    try:
        # Add cache busting to avoid stale responses
        cache_buster = int(datetime.now().timestamp())
        url = f"{FETCH_SCRIPT_URL}?cache={cache_buster}"
        
        logger.info(f"Fetching data from: {url}")
        response = requests.get(url, timeout=15)
        
        # Log raw response details
        logger.debug(f"Status Code: {response.status_code}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        logger.debug(f"First 500 characters: {response.text[:500]}")
        
        # Check for common error patterns
        if "DOCTYPE html" in response.text:
            logger.error("Received HTML response instead of JSON")
            st.error("""
            🔌 Connection Issue Detected:
            - This usually means the data source is unavailable
            - Check if the Google Sheet is properly shared
            - Verify the script deployment permissions
            """)
            return []

        if response.status_code == 401:
            logger.error("Authentication required")
            st.error("🔐 Authorization needed - check script permissions")
            return []

        if 400 <= response.status_code < 500:
            logger.error(f"Client error: {response.status_code}")
            st.error("📛 Invalid request configuration")
            return []

        # Attempt JSON parsing with detailed diagnostics
        try:
            data = response.json()
            logger.info("Successfully parsed JSON response")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            logger.error(f"Full response: {response.text}")
            st.error("""
            🛠️ Data Format Mismatch:
            - The server response isn't valid JSON
            - Common causes:
              1. Incorrect script deployment
              2. Authorization requirements
              3. Script runtime errors
            - Check script execution logs in Google Cloud
            """)
            return []

        # Validate response structure
        if 'data' not in data:
            logger.error(f"Missing 'data' key in response: {data.keys()}")
            st.error("""
            🔍 Unexpected Data Structure:
            - The response format doesn't match expectations
            - Verify the Google Apps Script is returning:
              { data: [...] }
            """)
            return []

        logger.info(f"Received {len(data['data'])} valid records")
        return data['data']

    except requests.exceptions.SSLError:
        logger.error("SSL Certificate verification failed")
        st.error("🔒 Security connection failed - check system date/time")
        return []
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        st.error("""
        🌐 Network Issue Detected:
        - Check your internet connection
        - Try refreshing the page
        - If using VPN, ensure proper connectivity
        """)
        return []

def validate_response_structure(data):
    """Deep validation of response data structure"""
    if not isinstance(data, list):
        logger.error(f"Top-level data is not a list: {type(data)}")
        return False
        
    required_fields = {
        'date': str,
        'amount': (int, float),
        'category': str,
        'paymentMethod': str
    }
    
    for i, record in enumerate(data):
        if not isinstance(record, dict):
            logger.error(f"Record {i} is not a dictionary: {type(record)}")
            return False
            
        missing = [k for k in required_fields if k not in record]
        if missing:
            logger.error(f"Record {i} missing fields: {missing}")
            return False
            
        for field, types in required_fields.items():
            if not isinstance(record[field], types):
                logger.error(f"Record {i} field {field} has invalid type {type(record[field])}")
                return False
                
    return True

def process_data(df):
    """Process data for analytics with validation"""
    if df.empty:
        logger.warning("Empty DataFrame received for processing")
        return df

    required_columns = {'date', 'amount', 'category', 'paymentMethod'}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        logger.error(f"Data validation failed. Missing columns: {missing_columns}")
        return pd.DataFrame()

    try:
        # Date processing
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        invalid_dates = df[df['date'].isna()]
        if not invalid_dates.empty:
            st.warning(f"Found {len(invalid_dates)} records with invalid dates")
            logger.warning(f"Invalid dates found: {invalid_dates.to_dict('records')}")
            df = df.dropna(subset=['date'])

        df['month_year'] = df['date'].dt.to_period('M').dt.strftime('%b %Y')
        
        # Amount processing
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        invalid_amounts = df[df['amount'].isna()]
        if not invalid_amounts.empty:
            st.warning(f"Found {len(invalid_amounts)} records with invalid amounts")
            logger.warning(f"Invalid amounts found: {invalid_amounts.to_dict('records')}")
            df = df.dropna(subset=['amount'])

        return df

    except Exception as e:
        st.error(f"Data processing error: {str(e)}")
        logger.error(f"Data processing failed: {str(e)}", exc_info=True)
        return pd.DataFrame()

def create_monthly_trend_chart(df):
    """Create monthly category trend chart with error handling"""
    try:
        if df.empty:
            logger.warning("Empty DataFrame passed to monthly trend chart")
            return px.line(title="Monthly Trends (No Data)")
            
        monthly_data = df.groupby(['month_year', 'category'])['amount'].sum().reset_index()
        pivot_df = monthly_data.pivot(index='month_year', columns='category', values='amount').fillna(0)
        
        fig = px.line(
            pivot_df, 
            x=pivot_df.index, 
            y=pivot_df.columns,
            title="Monthly Expense Trends by Category",
            labels={'value': 'Amount (₹)', 'variable': 'Category'},
            height=400
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            xaxis_title=None,
            legend_title_text='Category',
            hovermode="x unified"
        )
        fig.update_traces(line=dict(width=2.5))
        
        return fig
        
    except Exception as e:
        st.error(f"Chart creation failed: {str(e)}")
        logger.error(f"Monthly trend chart error: {str(e)}", exc_info=True)
        return go.Figure()

def show_analytics():
    """Main analytics with fallback UI"""
    try:
        with st.spinner("Loading financial insights..."):
            raw_data = fetch_expense_data()
            
            if not raw_data:
                st.info("📭 No expense records found")
                return
                
            df = process_data(pd.DataFrame(raw_data))
            
            if df.empty:
                st.warning("⚠️ No valid data to display")
                return
                
            # Display core metrics
            st.subheader("💰 Spending Overview")
            display_current_month_total(df)
            
            # Create visualization section
            st.subheader("📈 Trend Analysis")
            col1, col2 = st.columns([3, 2])
            
            with col1:
                if not df.empty:
                    st.plotly_chart(create_monthly_trend_chart(df))
                else:
                    st.info("No historical data available")
                    
            with col2:
                current_data = get_current_month_data(df)
                if not current_data.empty:
                    st.plotly_chart(create_payment_method_chart(current_data))
                else:
                    st.info("No current month expenses")
                    
    except Exception as e:
        logger.error(f"Analytics Failure: {str(e)}", exc_info=True)
        st.error("""🚨 Failed to load analytics. 
            We're working to fix this! Try these steps:
            1. Refresh the page
            2. Check your internet connection
            3. Contact support if issue persists""")
