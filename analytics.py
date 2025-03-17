import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import logging

# Configure advanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Google Apps Script URL
FETCH_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx1HZs60TbbLxHmX1HQKpDiM_aGuGewhT4azBzuvoIqnvp3pEG-nhWe-hz-nK78YXnPkw/exec"

# Custom CSS for dark theme
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .css-1d391kg, .css-12oz5g7 {
        background-color: #161B22;
    }
    .metric-container {
        background-color: #161B22;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #00CED1;
    }
    .metric-label {
        font-size: 14px;
        color: #A0A0A0;
    }
    .chart-container {
        background-color: #161B22;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

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

def get_week_number(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return date_obj.isocalendar()[1]

def get_week_label(year, week_num):
    # Get the first day of the week (Monday)
    first_day = datetime.strptime(f'{year}-W{week_num}-1', '%Y-W%W-%w')
    # Get the last day of the week (Sunday)
    last_day = first_day + timedelta(days=6)
    return f"{first_day.strftime('%d %b')} - {last_day.strftime('%d %b')}"

def show_analytics():
    """Main analytics function with dark theme and requested visualizations"""
    try:
        st.title("💰 Expense Analytics Dashboard")
        
        with st.spinner("🔍 Loading financial insights..."):
            raw_data = fetch_expense_data()
            
            if not raw_data:
                st.info("📭 No expense records found")
                return
                
            # Convert raw data to pandas DataFrame
            df = pd.DataFrame(raw_data)
            
            # Basic data cleaning and type conversion
            df['amount'] = pd.to_numeric(df['amount'])
            df['date'] = pd.to_datetime(df['date'])
            
            # Add week number for weekly analysis
            df['week'] = df['date'].apply(lambda x: x.isocalendar()[1])
            df['year'] = df['date'].apply(lambda x: x.year)
            df['month'] = df['date'].apply(lambda x: x.month)
            df['month_name'] = df['date'].apply(lambda x: calendar.month_name[x.month])
            
            # Get current month data
            now = datetime.now()
            current_month = now.month
            current_year = now.year
            df_current_month = df[(df['month'] == current_month) & (df['year'] == current_year)]
            
            # Create layout with three columns for the metrics
            col1, col2, col3 = st.columns(3)
            
            # 1. Dynamic tracker of total amount spent in current month till date
            with col1:
                total_spent = df_current_month['amount'].sum()
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Total Spent This Month</div>
                    <div class="metric-value">${total_spent:,.2f}</div>
                    <div>Month to Date: {calendar.month_name[current_month]} {current_year}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Average daily expense
            with col2:
                days_passed = min(now.day, calendar.monthrange(current_year, current_month)[1])
                avg_daily = total_spent / days_passed if days_passed > 0 else 0
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Average Daily Expense</div>
                    <div class="metric-value">${avg_daily:,.2f}</div>
                    <div>Based on {days_passed} days</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Top spending category
            with col3:
                if not df_current_month.empty:
                    top_category = df_current_month.groupby('category')['amount'].sum().idxmax()
                    top_amount = df_current_month.groupby('category')['amount'].sum().max()
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">Top Spending Category</div>
                        <div class="metric-value">{top_category}</div>
                        <div>${top_amount:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="metric-container">
                        <div class="metric-label">Top Spending Category</div>
                        <div class="metric-value">No Data</div>
                        <div>No expenses recorded this month</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 2. Week-wise graph of amount spent per category
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.subheader("Weekly Expense Trends by Category")
            
            # Create week-category aggregation
            weekly_category = df.groupby(['year', 'week', 'category'])['amount'].sum().reset_index()
            
            # Create week labels
            weekly_category['week_label'] = weekly_category.apply(
                lambda x: get_week_label(x['year'], x['week']), axis=1
            )
            
            # Sort by year and week for proper chronological order
            weekly_category = weekly_category.sort_values(['year', 'week'])
            
            # Create the line chart with Plotly
            fig_weekly = px.line(
                weekly_category, 
                x='week_label', 
                y='amount', 
                color='category',
                markers=True,
                title='Weekly Expenses by Category',
                labels={'amount': 'Amount ($)', 'week_label': 'Week', 'category': 'Category'}
            )
            
            # Customize the theme to match dark mode
            fig_weekly.update_layout(
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
                margin=dict(l=20, r=20, t=40, b=20),
                height=500
            )
            
            st.plotly_chart(fig_weekly, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # 3. Donut chart of spend distribution by payment methods
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.subheader("Payment Method Distribution")
            
            # Aggregate by payment method
            payment_totals = df.groupby('paymentMethod')['amount'].sum().reset_index()
            
            # Calculate percentages
            total = payment_totals['amount'].sum()
            payment_totals['percentage'] = (payment_totals['amount'] / total * 100).round(1)
            
            # Add percentage to labels
            payment_totals['label'] = payment_totals.apply(
                lambda x: f"{x['paymentMethod']}: ${x['amount']:,.2f} ({x['percentage']}%)", axis=1
            )
            
            # Create donut chart
            fig_donut = go.Figure(data=[go.Pie(
                labels=payment_totals['label'],
                values=payment_totals['amount'],
                hole=0.5,
                textinfo='percent',
                marker_colors=px.colors.qualitative.Set3
            )])
            
            # Customize the theme to match dark mode
            fig_donut.update_layout(
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=40, b=20),
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.3,
                    xanchor="center",
                    x=0.5
                )
            )
            
            st.plotly_chart(fig_donut, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Add expander for debugging data
            with st.expander("🔧 Debug Data Preview", expanded=False):
                st.json(raw_data[:3])
                st.write("Data shape:", df.shape)
                st.write("Date range:", df['date'].min(), "to", df['date'].max())
                
    except Exception as e:
        logger.error(f"💣 Analytics failure: {str(e)}", exc_info=True)
        st.error(f"""
        🚨 Critical Error:
        We've hit an unexpected problem: {str(e)}
        Please screenshot this error and contact support.
        """)
