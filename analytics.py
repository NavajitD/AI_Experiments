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
FETCH_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx1HZs60TbbLxHmX1HQKpDiM_aGuGewhT4azBzuvoIqnvp3pEG-nhWe-hz-nK78YXnPkw/exec"

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
                
            # Display raw data preview for debugging (only in expander)
            with st.expander("🔧 Debug Data Preview"):
                st.write("First 3 records from server:")
                st.json(raw_data[:3])
                
            # Actual analytics visualization code
            import pandas as pd
            import plotly.express as px
            
            # Convert raw data to pandas DataFrame
            df = pd.DataFrame(raw_data)
            
            # Convert amount to numeric
            df['amount'] = pd.to_numeric(df['amount'])
            
            # Show expense distribution by category
            st.subheader("Expense Distribution by Category")
            category_totals = df.groupby('category')['amount'].sum().reset_index()
            fig = px.pie(category_totals, values='amount', names='category', 
                         title='Expenses by Category')
            st.plotly_chart(fig)
            
            # Show monthly trends
            st.subheader("Monthly Expense Trends")
            monthly_totals = df.groupby(['month', 'year'])['amount'].sum().reset_index()
            monthly_totals['month_year'] = monthly_totals['month'] + ' ' + monthly_totals['year'].astype(str)
            fig2 = px.bar(monthly_totals, x='month_year', y='amount',
                          title='Monthly Expenses')
            st.plotly_chart(fig2)
            
            # Show payment method breakdown
            st.subheader("Payment Method Analysis")
            payment_totals = df.groupby('paymentMethod')['amount'].sum().reset_index()
            fig3 = px.bar(payment_totals, x='paymentMethod', y='amount',
                          title='Expenses by Payment Method')
            st.plotly_chart(fig3)
            
    except Exception as e:
        logger.error(f"💣 Analytics failure: {str(e)}", exc_info=True)
        st.error("""
        🚨 Critical Error:
        We've hit an unexpected problem. To help resolve this:
        1. Screenshot this error
        2. Check the script URL directly
        3. Contact support with these details
        """)
