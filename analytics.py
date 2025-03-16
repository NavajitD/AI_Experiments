import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime

# Google Apps Script URL for fetching data
FETCH_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbygEKgEV6irH-nnJci-2YWsFVLOZokSpyVpaxACU14JcekHyiMSU2UltkDvw7aIaINYng/exec"

def fetch_expense_data():
    """Fetch expense data from Google Sheets"""
    try:
        response = requests.get(FETCH_SCRIPT_URL)
        if response.status_code == 200:
            return response.json().get('data', [])
        return []
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return []

def process_data(df):
    """Process data for analytics"""
    # Convert to datetime
    df['date'] = pd.to_datetime(df['date'])
    df['month_year'] = df['date'].dt.to_period('M').dt.strftime('%b %Y')
    
    # Convert amount to float
    df['amount'] = df['amount'].astype(float)
    return df

def create_monthly_trend_chart(df):
    """Create monthly category trend chart"""
    # Pivot data for monthly category breakdown
    monthly_data = df.groupby(['month_year', 'category'])['amount'].sum().reset_index()
    pivot_df = monthly_data.pivot(index='month_year', columns='category', values='amount').fillna(0)
    
    # Create line chart
    fig = px.line(
        pivot_df, 
        x=pivot_df.index, 
        y=pivot_df.columns,
        title="Monthly Expense Trends by Category",
        labels={'value': 'Amount (₹)', 'variable': 'Category'},
        height=400
    )
    
    # Style the chart
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

def create_payment_method_chart(current_month_df):
    """Create payment method breakdown for current month"""
    # Calculate percentages and amounts
    pm_data = current_month_df.groupby('paymentMethod')['amount'].agg(['sum', 'count'])
    pm_data['percentage'] = (pm_data['sum'] / pm_data['sum'].sum()) * 100
    pm_data = pm_data.reset_index().sort_values('sum', ascending=False)
    
    # Create bar chart
    fig = px.bar(
        pm_data,
        x='paymentMethod',
        y='sum',
        text=pm_data.apply(lambda x: f"₹{x['sum']:,.0f}<br>({x['percentage']:.1f}%)", axis=1),
        title="Current Month Payment Method Breakdown",
        height=400
    )
    
    # Style the chart
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        xaxis_title=None,
        yaxis_title='Amount (₹)',
        hovermode="x unified"
    )
    fig.update_traces(
        marker_color='#FF4B4B',
        textposition='outside',
        textfont_size=14
    )
    
    return fig

def display_current_month_total(current_month_total):
    """Display current month total in big numbers"""
    st.markdown(f"""
    <div class="glass-card" style="text-align: center; margin: 20px 0; padding: 30px">
        <h3 style="margin: 0; color: #FF4B4B">Current Month Total</h3>
        <div style="font-size: 3.5rem; font-weight: 700; margin: 10px 0">
            ₹{current_month_total:,.0f}
        </div>
        <div style="font-size: 1.2rem; color: rgba(255,255,255,0.7)">
            Spent so far in {datetime.now().strftime('%B')}
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_analytics():
    """Main analytics function"""
    # Fetch and process data
    raw_data = fetch_expense_data()
    if not raw_data:
        st.info("No expense data available yet!")
        return
    
    df = process_data(pd.DataFrame(raw_data))
    
    # Get current month data
    current_month = datetime.now().strftime('%b %Y')
    current_month_df = df[df['month_year'] == current_month]
    current_month_total = current_month_df['amount'].sum()
    
    # Display current month total
    display_current_month_total(current_month_total)
    
    # Create layout columns
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Monthly trend chart
        st.plotly_chart(create_monthly_trend_chart(df), use_container_width=True)
    
    with col2:
        # Payment method chart
        if not current_month_df.empty:
            st.plotly_chart(create_payment_method_chart(current_month_df), use_container_width=True)
        else:
            st.info("No expenses recorded for current month yet!")
