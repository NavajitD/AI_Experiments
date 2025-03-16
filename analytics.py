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
    """Fetch expense data from Google Sheets with enhanced error handling"""
    try:
        logger.info(f"Attempting to fetch data from {FETCH_SCRIPT_URL}")
        response = requests.get(FETCH_SCRIPT_URL, timeout=10)
        
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response content sample: {response.text[:200]}...")

        if response.status_code != 200:
            st.error(f"HTTP Error {response.status_code}: {response.reason}")
            logger.error(f"Failed to fetch data. Status: {response.status_code}, Response: {response.text}")
            return []

        try:
            json_data = response.json()
            logger.info(f"Successfully parsed JSON response. Data keys: {json_data.keys()}")
        except json.JSONDecodeError as e:
            st.error("Invalid JSON response from server")
            logger.error(f"JSON Decode Error: {str(e)}")
            logger.error(f"Raw response content: {response.text}")
            return []

        if 'data' not in json_data:
            st.error("Unexpected data format: 'data' key missing")
            logger.error(f"Missing 'data' key in response. Full response: {json_data}")
            return []

        logger.info(f"Successfully fetched {len(json_data['data'])} records")
        return json_data.get('data', [])

    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
        logger.error(f"Request Exception: {str(e)}", exc_info=True)
        return []
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return []

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
    """Main analytics function with error boundaries"""
    try:
        logger.info("Starting analytics processing")
        raw_data = fetch_expense_data()
        
        if not raw_data:
            st.info("No expense data available yet!")
            logger.info("No data available for analytics")
            return
            
        logger.info(f"Processing {len(raw_data)} records")
        df = process_data(pd.DataFrame(raw_data))
        
        if df.empty:
            st.warning("No valid data available for visualization")
            logger.warning("Processed DataFrame is empty")
            return

        current_month = datetime.now().strftime('%b %Y')
        current_month_df = df[df['month_year'] == current_month]
        current_month_total = current_month_df['amount'].sum()
        
        display_current_month_total(current_month_total)
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.plotly_chart(create_monthly_trend_chart(df), use_container_width=True)
        
        with col2:
            if not current_month_df.empty:
                st.plotly_chart(create_payment_method_chart(current_month_df), use_container_width=True)
            else:
                st.info("No expenses recorded for current month yet!")
                
        logger.info("Analytics processing completed successfully")
        
    except Exception as e:
        st.error(f"Analytics failed: {str(e)}")
        logger.error(f"Analytics fatal error: {str(e)}", exc_info=True)
