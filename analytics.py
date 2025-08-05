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
            
            # Filter data based on selection (moved earlier to use in metrics)
            filtered_df = df.copy()
            
            # Apply month filter if not "All"
            if selected_month != "All":
                selected_month_num = list(calendar.month_name).index(selected_month)
                filtered_df = filtered_df[filtered_df['month'] == selected_month_num]
                
            # Apply year filter if not "All"
            if selected_year != "All":
                filtered_df = filtered_df[filtered_df['year'] == selected_year]
            
            # Create period label for metrics
            if selected_month != "All" and selected_year != "All":
                period_label = f"{selected_month} {selected_year}"
                metric_title = f"Total Spent - {selected_month}"
            elif selected_month != "All":
                period_label = f"{selected_month} (All Years)"
                metric_title = f"Total Spent - {selected_month}"
            elif selected_year != "All":
                period_label = f"All Months {selected_year}"
                metric_title = f"Total Spent - {selected_year}"
            else:
                period_label = "All Time"
                metric_title = "Total Spent - All Time"
            
            # Create layout with three columns for the metrics
            col1, col2, col3 = st.columns(3)
            
            # 1. Dynamic tracker of total amount spent based on selected filters
            with col1:
                total_spent = filtered_df['amount'].sum() if not filtered_df.empty else 0
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">{metric_title}</div>
                    <div class="metric-value">₹{total_spent:,.2f}</div>
                    <div>{period_label}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # Average daily expense based on filtered data
            with col2:
                if not filtered_df.empty:
                    # Get the earliest and latest dates in filtered data
                    first_expense_date = filtered_df['date'].min().date()
                    last_expense_date = filtered_df['date'].max().date()
                    
                    # Calculate inclusive date range
                    days_in_range = (last_expense_date - first_expense_date).days + 1
                    
                    # Safety check to avoid division by zero
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
                
            # Top spending category (skip Rent/Maintenance if it's the highest)
            with col3:
                if not filtered_df.empty:
                    category_amounts = filtered_df.groupby('category')['amount'].sum().sort_values(ascending=False)
                    
                    # Check if top category is Rent/Maintenance and get next highest if so
                    if len(category_amounts) > 0:
                        top_category = category_amounts.index[0]
                        top_amount = category_amounts.iloc[0]
                        
                        # If top category is Rent/Maintenance and there are other categories, show the next one
                        if top_category == "Rent/Maintenance" and len(category_amounts) > 1:
                            top_category = category_amounts.index[1]
                            top_amount = category_amounts.iloc[1]
                            category_note = "(Next highest after Rent)"
                        else:
                            category_note = ""
                    
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">Top Spending Category</div>
                        <div class="metric-value">{top_category}</div>
                        <div>₹{top_amount:,.2f} {category_note}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">Top Spending Category</div>
                        <div class="metric-value">No Data</div>
                        <div>No expenses for {period_label}</div>
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
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Add some space before the trends section
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Trends section header
            st.markdown("<hr style='margin: 30px 0;'>", unsafe_allow_html=True)
            st.header("📊 Expense Analysis")
            
            # Create sub-tabs for different trend visualizations
            trend_tabs = st.tabs(["Category Breakdown", "Trends Over Time", "Payment Methods", "Expense Themes"])
            
            with trend_tabs[0]:
                # NEW: Category breakdown view
                st.subheader("💳 Spend by Category")
                
                if not filtered_df.empty:
                    # Aggregate expenses by category
                    category_totals = filtered_df.groupby('category')['amount'].sum().reset_index()
                    category_totals = category_totals.sort_values('amount', ascending=False)
                    
                    # Calculate percentages
                    total = category_totals['amount'].sum()
                    category_totals['percentage'] = (category_totals['amount'] / total * 100).round(1)
                    
                    # Create horizontal bar chart for better category name visibility
                    fig_category = px.bar(
                        category_totals, 
                        x='amount', 
                        y='category',
                        orientation='h',
                        title=f'Spending by Category - {selected_month if selected_month != "All" else "All Months"} {selected_year if selected_year != "All" else "All Years"}',
                        labels={'amount': 'Amount (₹)', 'category': 'Category'},
                        text='amount'
                    )
                    
                    # Customize the theme to match dark mode and improve mobile responsiveness
                    fig_category.update_layout(
                        template='plotly_dark',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=40, b=20),
                        height=max(400, len(category_totals) * 30),  # Dynamic height based on number of categories
                        yaxis={'categoryorder': 'total ascending'},  # Sort categories by value
                        autosize=True,
                    )
                    
                    # Format text on bars
                    fig_category.update_traces(
                        texttemplate='₹%{text:,.0f}',
                        textposition='outside'
                    )
                    
                    st.plotly_chart(fig_category, use_container_width=True)
                    
                    # Show detailed table
                    st.subheader("📋 Category Details")
                    
                    # Format the table for better display
                    display_df = category_totals.copy()
                    display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}")
                    display_df['percentage'] = display_df['percentage'].apply(lambda x: f"{x}%")
                    display_df.columns = ['Category', 'Amount', 'Percentage']
                    display_df.index = range(1, len(display_df) + 1)
                    
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info(f"No expense data available for the selected filters")
            
            with trend_tabs[1]:
                # ENHANCED: Toggle between weekly and monthly trends
                st.subheader("📈 Trends Over Time")
                
                # Add toggle for weekly vs monthly view
                view_type = st.radio(
                    "Select View",
                    options=["Weekly", "Monthly"],
                    horizontal=True,
                    help="Weekly view shows weeks within selected month. Monthly view shows months within selected year."
                )
                
                if view_type == "Weekly":
                    # Weekly view (existing functionality with some modifications)
                    if selected_month == "All":
                        st.info("Please select a specific month to view weekly trends")
                    else:
                        # Filter to selected month and year
                        if selected_year != "All":
                            monthly_df = filtered_df[(filtered_df['month'] == list(calendar.month_name).index(selected_month)) & 
                                                   (filtered_df['year'] == selected_year)]
                        else:
                            monthly_df = filtered_df[filtered_df['month'] == list(calendar.month_name).index(selected_month)]
                        
                        if not monthly_df.empty:
                            # Create day-of-month based week aggregation
                            weekly_category = monthly_df.groupby(['year', 'month', 'day_week', 'category'])['amount'].sum().reset_index()
                            
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
                            
                            # Create the line chart
                            week_labels = weekly_category['week_label'].unique()
                            
                            fig_weekly = px.line(
                                weekly_category, 
                                x='week_label', 
                                y='amount', 
                                color='category',
                                markers=True,
                                title=f'Weekly Expenses by Category - {selected_month} {selected_year if selected_year != "All" else "All Years"}',
                                labels={'amount': 'Amount (₹)', 'week_label': 'Week', 'category': 'Category'},
                                category_orders={'week_label': week_labels}
                            )
                            
                            # Customize the theme
                            fig_weekly.update_layout(
                                template='plotly_dark',
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
                                margin=dict(l=20, r=20, t=40, b=20),
                                height=500,
                                autosize=True,
                            )
                            
                            fig_weekly.update_traces(
                                line=dict(width=1),
                                marker=dict(size=12)
                            )
                            
                            st.plotly_chart(fig_weekly, use_container_width=True)
                        else:
                            st.info(f"No expense data available for {selected_month} {selected_year if selected_year != 'All' else ''}")
                
                else:  # Monthly view
                    # Monthly trends - show monthly aggregation
                    if selected_year != "All":
                        yearly_df = filtered_df[filtered_df['year'] == selected_year]
                        title_suffix = f" - {selected_year}"
                    else:
                        yearly_df = filtered_df
                        title_suffix = " - All Years"
                    
                    if not yearly_df.empty:
                        # Create monthly aggregation by category
                        monthly_category = yearly_df.groupby(['year', 'month', 'month_name', 'category'])['amount'].sum().reset_index()
                        
                        # Create month labels
                        monthly_category['month_label'] = monthly_category.apply(
                            lambda x: f"{x['month_name'][:3]} {x['year']}", axis=1
                        )
                        
                        # Sort by year and month
                        monthly_category['sort_key'] = monthly_category.apply(
                            lambda x: f"{x['year']:04d}{x['month']:02d}", axis=1
                        )
                        monthly_category = monthly_category.sort_values('sort_key')
                        
                        # Create the line chart
                        month_labels = monthly_category['month_label'].unique()
                        
                        fig_monthly = px.line(
                            monthly_category, 
                            x='month_label', 
                            y='amount', 
                            color='category',
                            markers=True,
                            title=f'Monthly Expenses by Category{title_suffix}',
                            labels={'amount': 'Amount (₹)', 'month_label': 'Month', 'category': 'Category'},
                            category_orders={'month_label': month_labels}
                        )
                        
                        # Customize the theme
                        fig_monthly.update_layout(
                            template='plotly_dark',
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
                            margin=dict(l=20, r=20, t=40, b=20),
                            height=500,
                            autosize=True,
                        )
                        
                        fig_monthly.update_traces(
                            line=dict(width=1),
                            marker=dict(size=12)
                        )
                        
                        st.plotly_chart(fig_monthly, use_container_width=True)
                    else:
                        st.info(f"No expense data available for the selected filters")
                
            with trend_tabs[2]:
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
                    
                    # Create donut chart with payment method names as labels
                    fig_donut = go.Figure(data=[go.Pie(
                        labels=payment_totals['paymentMethod'],  # Use payment method names directly
                        values=payment_totals['amount'],
                        hole=0.5,
                        textinfo='label',  # Show the label text instead of just percentage
                        hovertemplate='%{label}<br>Amount: ₹%{value:.2f}<br>%{percent}<extra></extra>',  # Removed "trace 0" with <extra></extra>
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
            
            with trend_tabs[3]:
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
                    
                    # Create pie chart for themes with theme names as labels
                    fig_theme = go.Figure(data=[go.Pie(
                        labels=theme_totals['theme'],  # Use theme names directly
                        values=theme_totals['amount'],
                        hole=0.4,
                        textinfo='label',  # Show the label text instead of just percentage
                        hovertemplate='%{label}<br>Amount: ₹%{value:.2f}<br>%{percent}<extra></extra>',  # Removed "trace 0" with <extra></extra>
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
