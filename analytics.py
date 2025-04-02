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
FETCH_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwISgM-mNsc6fZmKki2ImDKhsePg_Ixbcku3Ofw9_feNE9OuDUEDamLylrwK5kLB7vGZg/exec"

# Add custom CSS for better mobile responsiveness
st.markdown("""
<style>
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .metric-container {
            padding: 8px;
            margin-bottom: 12px;
        }
        
        .metric-value {
            font-size: 20px !important;
        }
        
        .metric-label {
            font-size: 14px !important;
        }
    }
    
    /* Fix for metric values that weren't displaying properly */
    .metric-container {
        background-color: rgba(28, 28, 28, 0.2);
        border-radius: 5px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    .metric-label {
        font-size: 16px;
        color: #c0c0c0;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: white;
        margin-bottom: 5px;
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

def get_week_number(date_obj):
    return date_obj.isocalendar()[1]

def get_day_of_month_week(date_obj):
    """Group by the day of month, creating weekly ranges that start on the 1st"""
    day = date_obj.day
    # Create week ranges: 1-7, 8-14, 15-21, 22-28, 29-end of month
    if day <= 7:
        return "01-07"
    elif day <= 14:
        return "08-14"
    elif day <= 21:
        return "15-21"
    elif day <= 28:
        return "22-28"
    else:
        # Get the last day of the month
        last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
        return f"29-{last_day}"

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
            df['year'] = df['date'].apply(lambda x: x.year)
            df['month'] = df['date'].apply(lambda x: x.month)
            df['month_name'] = df['date'].apply(lambda x: calendar.month_name[x.month])
            # Create day-of-month based week ranges (1-7, 8-14, etc.)
            df['day_week'] = df['date'].apply(get_day_of_month_week)
            
            # Get unique months for the filter
            month_options = sorted(df['month_name'].unique(), 
                                  key=lambda x: list(calendar.month_name).index(x) if x in calendar.month_name else 0)
            year_options = sorted(df['year'].unique())
            
            # Get current month data
            now = datetime.now()
            current_month = now.month
            current_year = now.year
            
            # Create layout with three columns for the metrics
            col1, col2, col3 = st.columns(3)
            
            # Ensure the DataFrame is properly populated before accessing
            df_current_month = df[(df['month'] == current_month) & (df['year'] == current_year)]
            
            # 1. Dynamic tracker of total amount spent in current month till date
            with col1:
                total_spent = df_current_month['amount'].sum() if not df_current_month.empty else 0
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Total Spent This Month</div>
                    <div class="metric-value">₹{total_spent:,.2f}</div>
                    <div>Month to Date: {calendar.month_name[current_month]} {current_year}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Average daily expense - FIX: Calculate date span correctly
            with col2:
                if not df_current_month.empty:
                    # Get all unique dates that have expenses
                    unique_dates = df_current_month['date'].dt.date.unique()
                    
                    # Count the number of unique dates
                    days_passed = len(unique_dates)
                    
                    # Debugging to check the dates
                    logger.debug(f"Unique expense dates: {unique_dates}")
                    logger.debug(f"Number of days with expenses: {days_passed}")
                    
                    # Safety check to avoid division by zero
                    if days_passed < 1:
                        days_passed = 1
                else:
                    days_passed = 1  # Default if no data
                    
                avg_daily = total_spent / days_passed if days_passed > 0 else 0
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Average Daily Expense</div>
                    <div class="metric-value">₹{avg_daily:,.2f}</div>
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
                        <div>₹{top_amount:,.2f}</div>
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
            
            # 2. Week-wise graph of amount spent per category with month filter
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.subheader("Weekly Expense Trends by Category")
            
            # Add month and year filters for the weekly chart
            filter_col1, filter_col2 = st.columns([1, 1])
            
            # FIX: Default selection should always be current month/year, even if no data exists
            current_month_name = calendar.month_name[current_month]
            
            with filter_col1:
                if current_month_name not in month_options and len(month_options) > 0:
                    selected_month = st.selectbox(
                        "Select Month", 
                        options=[current_month_name] + list(month_options),
                        index=0  # Force current month to be default
                    )
                else:
                    # Use the current month if it exists in the options
                    selected_month = st.selectbox(
                        "Select Month", 
                        options=month_options if month_options else [current_month_name],
                        index=month_options.index(current_month_name) if current_month_name in month_options else 0
                    )
            
            with filter_col2:
                if current_year not in year_options and len(year_options) > 0:
                    selected_year = st.selectbox(
                        "Select Year",
                        options=[current_year] + list(year_options),
                        index=0  # Force current year to be default
                    )
                else:
                    # Use current year if it exists in options
                    selected_year = st.selectbox(
                        "Select Year",
                        options=year_options if year_options else [current_year],
                        index=year_options.index(current_year) if current_year in year_options else 0
                    )
            
            # Filter data based on selection
            selected_month_num = list(calendar.month_name).index(selected_month)
            filtered_df = df[(df['month'] == selected_month_num) & (df['year'] == selected_year)]
            
            # Create day-of-month based week aggregation for the filtered data
            weekly_category = filtered_df.groupby(['year', 'month', 'day_week', 'category'])['amount'].sum().reset_index()
            
            if not weekly_category.empty:
                # Create week labels showing the day range in the month
                weekly_category['week_label'] = weekly_category['day_week'].apply(
                    lambda x: f"{x} {calendar.month_name[weekly_category['month'].iloc[0]][:3]}"
                )
                
                # Create a sort key based on the day range
                # This assumes the day_week format is like "01-07", "08-14", etc.
                weekly_category['sort_key'] = weekly_category['day_week'].apply(
                    lambda x: int(x.split('-')[0])  # Sort by the first day in the range
                )
                
                # Sort by the combined key for proper chronological order
                weekly_category = weekly_category.sort_values('sort_key')
                
                # Create the line chart with Plotly using category_orders to enforce order
                week_labels = weekly_category['week_label'].unique()
                
                fig_weekly = px.line(
                    weekly_category, 
                    x='week_label', 
                    y='amount', 
                    color='category',
                    markers=True,
                    title=f'Weekly Expenses by Category - {selected_month} {selected_year}',
                    labels={'amount': 'Amount (₹)', 'week_label': 'Week', 'category': 'Category'},
                    category_orders={'week_label': week_labels}  # Enforce order of week labels
                )
                
                # Customize the theme to match dark mode and improve mobile responsiveness
                fig_weekly.update_layout(
                    template='plotly_dark',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=500,
                    # Improve responsiveness
                    autosize=True,
                )
                
                # Make the chart more mobile-friendly
                fig_weekly.update_traces(
                    line=dict(width=2),
                    marker=dict(size=8)
                )
                
                st.plotly_chart(fig_weekly, use_container_width=True)
            else:
                st.info(f"No expense data available for {selected_month} {selected_year}")
            
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
                lambda x: f"{x['paymentMethod']}: ₹{x['amount']:,.2f} ({x['percentage']}%)", axis=1
            )
            
            # Create donut chart
            fig_donut = go.Figure(data=[go.Pie(
                labels=payment_totals['label'],
                values=payment_totals['amount'],
                hole=0.5,
                textinfo='percent',
                marker_colors=px.colors.qualitative.Set3
            )])
            
            # Customize the theme to match dark mode and improve mobile responsiveness
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
                ),
                # Improve responsiveness
                autosize=True,
            )
            
            st.plotly_chart(fig_donut, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Add expander for debugging data
            with st.expander("🔧 Debug Data Preview", expanded=False):
                st.json(raw_data[:3] if raw_data else {})
                st.write("Data shape:", df.shape)
                if not df.empty:
                    st.write("Date range:", df['date'].min(), "to", df['date'].max())
                    # Add detailed date debugging info for current month
                    if not df_current_month.empty:
                        st.write("Current month unique dates:", df_current_month['date'].dt.date.unique())
                        st.write("Number of days with expenses:", len(df_current_month['date'].dt.date.unique()))
                    
    except Exception as e:
        logger.error(f"💣 Analytics failure: {str(e)}", exc_info=True)
        st.error(f"""
        🚨 Critical Error:
        We've hit an unexpected problem: {str(e)}
        Please screenshot this error and contact support.
        """)
