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

# Define expense theme categorization
def categorize_theme(category):
    """Map each expense category to its theme"""
    cost_of_living = ['Bike', 'Public transport', 'Groceries', 'Household supplies', 
                      'Rent/Maintenance', 'Furniture', 'Services', 'Electricity', 
                      'Internet', 'Insurance', 'Medical expenses', 'Gas', 'Phone']
    
    going_out = ['Auto/Cab', 'Eating out', 'Party', 'Cinema', 'Entertainment', 
                'Liquor', 'Travel', 'Games/Sports']
    
    incidentals = ['Education', 'Gift', 'Investment', 'Flights', 'Clothes']
    
    if category in cost_of_living:
        return "Cost of living"
    elif category in going_out:
        return "Going out"
    elif category in incidentals:
        return "Incidentals"
    else:
        return "Other"

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
        st.caption("Track and analyze your spending patterns")
        
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
            
            # Add expense theme categorization
            df['theme'] = df['category'].apply(categorize_theme)
            
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
                
            # Average daily expense - FIX: Calculate based on actual expense date range
            with col2:
                if not df_current_month.empty:
                    # Get the earliest date with an expense this month
                    first_expense_date = df_current_month['date'].min().date()
                    
                    # For the end date, use the latest transaction date instead of today
                    # This ensures we count all days with transactions
                    last_expense_date = df_current_month['date'].max().date()
                    today_date = now.date()
                    
                    # Calculate inclusive date range (first day to last day inclusive)
                    # Add 1 to include both start and end dates in the count
                    days_in_range = (last_expense_date - first_expense_date).days + 1
                    
                    # Safety check to avoid division by zero and ensure minimum of 1 day
                    if days_in_range < 1:
                        days_in_range = 1
                else:
                    days_in_range = 1  # Default if no data
                    
                avg_daily = total_spent / days_in_range if days_in_range > 0 else 0
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Average Daily Expense</div>
                    <div class="metric-value">₹{avg_daily:,.2f}</div>
                    <div>Based on {days_in_range} days</div>
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
            
            # Add space before filters
            st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
            
            # Add filters without header
            filter_col1, filter_col2 = st.columns([1, 1])
            
            # Add "All" option for month and year filters
            with filter_col1:
                month_options_with_all = ["All"] + sorted(month_options, 
                                  key=lambda x: list(calendar.month_name).index(x) if x in calendar.month_name else 0)
                current_month_name = calendar.month_name[current_month]
                
                selected_month = st.selectbox(
                    "Select Month", 
                    options=month_options_with_all,
                    index=month_options_with_all.index(current_month_name) if current_month_name in month_options_with_all else 0
                )
            
            with filter_col2:
                year_options_with_all = ["All"] + sorted(year_options)
                
                selected_year = st.selectbox(
                    "Select Year",
                    options=year_options_with_all,
                    index=year_options_with_all.index(current_year) if current_year in year_options_with_all[1:] else 0
                )
            
            # Filter data based on selection
            filtered_df = df.copy()
            
            # Apply month filter if not "All"
            if selected_month != "All":
                selected_month_num = list(calendar.month_name).index(selected_month)
                filtered_df = filtered_df[filtered_df['month'] == selected_month_num]
                
            # Apply year filter if not "All"
            if selected_year != "All":
                filtered_df = filtered_df[filtered_df['year'] == selected_year]
            
            # Create day-of-month based week aggregation for the filtered data
            weekly_category = filtered_df.groupby(['year', 'month', 'day_week', 'category'])['amount'].sum().reset_index()
            
            if not weekly_category.empty:
                # Create week labels showing the day range in the month
                weekly_category['week_label'] = weekly_category.apply(
                    lambda x: f"{x['day_week']} {calendar.month_name[x['month']][:3]} {x['year']}", axis=1
                )
                
                # Create a sort key based on year, month, and day range
                weekly_category['sort_key'] = weekly_category.apply(
                    lambda x: f"{x['year']:04d}{x['month']:02d}{int(x['day_week'].split('-')[0]):02d}", axis=1
                )
                
                # Sort by the combined key for proper chronological order
                weekly_category = weekly_category.sort_values('sort_key')
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Add some space before the trends section
            st.markdown("<br>", unsafe_allow_html=True)
            

            
            # Trends section header
            st.markdown("<hr style='margin: 30px 0;'>", unsafe_allow_html=True)
            st.header("📊 Expense Trends")
            
            # Create sub-tabs for different trend visualizations
            trend_tabs = st.tabs(["Weekly Category Trends", "Payment Methods", "Expense Themes"])
            
            with trend_tabs[0]:
                # 2. Week-wise graph of amount spent per category (original line chart)
                if not weekly_category.empty:
                    # Create the line chart with Plotly using category_orders to enforce order
                    week_labels = weekly_category['week_label'].unique()
                    
                    fig_weekly = px.line(
                        weekly_category, 
                        x='week_label', 
                        y='amount', 
                        color='category',
                        markers=True,
                        title=f'Weekly Expenses by Category - {selected_month if selected_month != "All" else "All Months"} {selected_year if selected_year != "All" else "All Years"}',
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
                    
                    # Make the chart more mobile-friendly with bigger dots and thinner lines
                    fig_weekly.update_traces(
                        line=dict(width=1),  # Thinner lines
                        marker=dict(size=12)  # Bigger dots
                    )
                    
                    st.plotly_chart(fig_weekly, use_container_width=True)
                else:
                    st.info(f"No expense data available for the selected filters")
                
            with trend_tabs[1]:
                # 3. Donut chart of spend distribution by payment methods
                if not filtered_df.empty:
                    payment_totals = filtered_df.groupby('paymentMethod')['amount'].sum().reset_index()
                    
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
                        textinfo='label',  # Changed from 'percent' to 'label'
                        textposition='inside',  # Ensure text is positioned inside the slices
                        insidetextorientation='radial',  # Orient text radially for better readability
                        marker_colors=px.colors.qualitative.Set3
                    )])
                    
                    # Customize the theme to match dark mode and improve mobile responsiveness
                    fig_donut.update_layout(
                        template='plotly_dark',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=40, b=20),
                        height=500,
                        title=f'Payment Method Distribution - {selected_month if selected_month != "All" else "All Months"} {selected_year if selected_year != "All" else "All Years"}',
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
                else:
                    st.info(f"No expense data available for the selected filters")
            
            with trend_tabs[2]:
                # 4. NEW: Pie chart of expense themes
                if not filtered_df.empty:
                    # Aggregate expenses by theme
                    theme_totals = filtered_df.groupby('theme')['amount'].sum().reset_index()
                    
                    # Calculate percentages
                    theme_total = theme_totals['amount'].sum()
                    theme_totals['percentage'] = (theme_totals['amount'] / theme_total * 100).round(1)
                    
                    # Add percentage to labels
                    theme_totals['label'] = theme_totals.apply(
                        lambda x: f"{x['theme']}: ₹{x['amount']:,.2f} ({x['percentage']}%)", axis=1
                    )
                    
                    # Define custom colors for each theme - improved color palette
                    theme_colors = {
                        "Cost of living": "#7986CB",  # Indigo-blue
                        "Going out": "#FF8A65",       # Orange
                        "Incidentals": "#4DB6AC",     # Teal
                        "Other": "#9E9E9E"            # Grey
                    }
                    
                    # Extract colors in the same order as themes
                    color_sequence = [theme_colors.get(theme, "#9E9E9E") for theme in theme_totals['theme']]
                    
                    # Create pie chart for themes
                    fig_theme = go.Figure(data=[go.Pie(
                        labels=theme_totals['label'],
                        values=theme_totals['amount'],
                        hole=0.4,
                        textinfo='label',  # Changed from 'percent' to 'label'
                        textposition='inside',  # Ensure text is positioned inside the slices
                        insidetextorientation='radial',  # Orient text radially for better readability
                        marker_colors=color_sequence
                    )])
                    
                    # Customize the theme to match dark mode and improve mobile responsiveness
                    fig_theme.update_layout(
                        template='plotly_dark',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=40, b=20),
                        height=500,
                        title=f'Expense Distribution by Theme - {selected_month if selected_month != "All" else "All Months"} {selected_year if selected_year != "All" else "All Years"}',
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
                    
                    st.plotly_chart(fig_theme, use_container_width=True)
                    
                    # Add theme category details as an expander
                    with st.expander("What's included in each theme?", expanded=False):
                        st.markdown(f"""
                        <div style='margin: 10px 0;'>
                            <p><b>Cost of living:</b> Bike, Public transport, Groceries, Household supplies, Rent/Maintenance, Furniture, Services, Electricity, Internet, Insurance, Medical expenses, Gas, Phone</p>
                            <p><b>Going out:</b> Auto/Cab, Eating out, Party, Cinema, Entertainment, Liquor, Travel, Games/Sports</p>
                            <p><b>Incidentals:</b> Education, Gift, Investment, Flights, Clothes</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info(f"No expense data available for the selected filters")
            
            # Add expander for debugging data
            with st.expander("🔧 Debug Data Preview", expanded=False):
                st.json(raw_data[:3] if raw_data else {})
                st.write("Data shape:", df.shape)
                if not df.empty:
                    st.write("Date range:", df['date'].min(), "to", df['date'].max())
                    
    except Exception as e:
        logger.error(f"💣 Analytics failure: {str(e)}", exc_info=True)
        st.error(f"""
        🚨 Critical Error:
        We've hit an unexpected problem: {str(e)}
        Please screenshot this error and contact support.
        """)
