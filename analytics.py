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
    """Fetch expense data with detailed diagnostics"""
    try:
        logger.info(f"Fetching data from: {FETCH_SCRIPT_URL}")
        response = requests.get(FETCH_SCRIPT_URL, timeout=15)
        
        # Log raw response details
        logger.debug(f"Status Code: {response.status_code}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        logger.debug(f"First 200 chars: {response.text[:200]}")

        if response.status_code != 200:
            error_msg = f"Server Error: {response.status_code} - {response.reason}"
            logger.error(error_msg)
            st.error("Failed to connect to data source. Please try again later.")
            return []

        try:
            data = response.json()
            logger.info(f"Received {len(data.get('data', []))} records")
            return data.get('data', [])
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error: {str(e)}")
            logger.error(f"Raw Response: {response.text[:500]}")
            st.error("Data format error. Please check the data source.")
            return []

    except requests.exceptions.Timeout:
        logger.error("Request timed out after 15 seconds")
        st.error("Connection timeout. Please check your internet connection.")
        return []
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}", exc_info=True)
        st.error("Temporary data unavailability. Try refreshing the page.")
        return []

def validate_data_structure(df):
    """Ensure data matches expected schema"""
    required_columns = {
        'date': 'datetime64[ns]',
        'amount': 'float64',
        'category': 'object',
        'paymentMethod': 'object'
    }
    
    errors = []
    for col, dtype in required_items:
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
        elif not pd.api.types.is_dtype(df[col].dtype, dtype):
            errors.append(f"Invalid dtype for {col}: {df[col].dtype}")
    
    if errors:
        logger.error(f"Data validation failed: {', '.join(errors)}")
        st.error("Data source format mismatch. Contact support.")
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
