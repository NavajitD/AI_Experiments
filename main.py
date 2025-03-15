import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Set the API key directly in the script
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "AIzaSyAqMFvXnZ4JLeYqySr1rkY5Ooc5pYdPmrc"  

# Retrieve the API key
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY is not set")

# Initialize Gemini model
Model_Gemini = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=api_key
)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import json
import time
import numpy as np

def predict_category(expense_name):
    """Use Gemini to predict the expense category based on expense name"""
    if not Model_Gemini:
        return "Miscellaneous"
        
    prompt = f"""
    Given the expense name '{expense_name}', classify it into one of the following categories:
    - Housing (rent, mortgage, maintenance)
    - Utilities (electricity, water, gas, internet)
    - Groceries
    - Dining Out
    - Transportation (fuel, public transit, vehicle maintenance)
    - Healthcare (medical bills, medicines, insurance)
    - Entertainment (movies, events, subscriptions)
    - Shopping (clothing, electronics, household items)
    - Personal Care (haircuts, cosmetics)
    - Education (tuition, books, courses)
    - Travel
    - Gifts & Donations
    - Insurance
    - Investments
    - Debt Payments
    - Miscellaneous
    
    Return only the category name, nothing else.
    """
    
    try:
        response = Model_Gemini.generate_content(prompt)
        category = response.text.strip()
        # Ensure the predicted category is in our list
        if category not in expense_categories:
            category = "Miscellaneous"
        return category
    except Exception as e:
        st.error(f"Error predicting category: {str(e)}")
        return "Miscellaneous"

def get_billing_cycle(date):
    """Determine credit card billing cycle based on date"""
    # Convert to datetime if it's a date object
    if not isinstance(date, datetime):
        date = datetime.combine(date, datetime.min.time())
        
    if date.day < 16:
        # Previous billing cycle
        # Handle month rollover properly
        if date.month == 1:  # January
            prev_month = 12
            prev_year = date.year - 1
        else:
            prev_month = date.month - 1
            prev_year = date.year
            
        # Create start and end dates
        cycle_start = datetime(prev_year, prev_month, 25)
        cycle_end = datetime(date.year, date.month, 25)
    else:
        # Next billing cycle
        # Handle month rollover properly
        if date.month == 12:  # December
            next_month = 1
            next_year = date.year + 1
        else:
            next_month = date.month + 1
            next_year = date.year
            
        # Create start and end dates
        cycle_start = datetime(date.year, date.month, 25)
        cycle_end = datetime(next_year, next_month, 25)
        
    return f"{cycle_start.strftime('%b %d')} - {cycle_end.strftime('%b %d')}"

# Create a native Streamlit animation function
def native_animation():
    # Create a placeholder for the animation
    animation_placeholder = st.empty()
    
    # Initialize animation state
    if 'animation_frame' not in st.session_state:
        st.session_state.animation_frame = 0
        st.session_state.animation_direction = 1
        st.session_state.last_update = time.time()
    
    # Update animation frame
    current_time = time.time()
    if current_time - st.session_state.last_update > 0.1:  # Update every 100ms
        st.session_state.animation_frame += st.session_state.animation_direction
        if st.session_state.animation_frame >= 100:
            st.session_state.animation_direction = -1
        elif st.session_state.animation_frame <= 0:
            st.session_state.animation_direction = 1
        st.session_state.last_update = current_time
    
    # Calculate animation parameters
    frame = st.session_state.animation_frame / 100
    hue = (frame * 360) % 360  # Cycle through colors
    
    # Create a gradient background
    css = f"""
    <style>
    .stApp {{
        background: linear-gradient(
            {(hue+180) % 360}deg,
            hsla({hue}, 70%, 90%, 0.8),
            hsla({(hue+120) % 360}, 70%, 90%, 0.8)
        );
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }}
    @keyframes gradient {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    </style>
    """
    
    animation_placeholder.markdown(css, unsafe_allow_html=True)
    
    # Return to ensure the function runs in the app flow
    return None

# Define expense categories
expense_categories = [
    "Housing", "Utilities", "Groceries", "Dining Out", "Transportation",
    "Healthcare", "Entertainment", "Shopping", "Personal Care", 
    "Education", "Travel", "Gifts & Donations", "Insurance",
    "Investments", "Debt Payments", "Miscellaneous"
]

# Define payment methods
payment_methods = [
    "Cash", "Debit Card", "Credit Card", "UPI", "Net Banking", 
    "Mobile Wallet", "Bank Transfer", "Other"
]

# Configure page
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Run our native animation instead of using streamlit_particles
native_animation()

# App UI - adding some extra styling to make it stand out from the background
st.markdown("""
<style>
    .main-container {
        background-color: rgba(255, 255, 255, 0.85);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stForm {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# App title with a glow effect
st.markdown("""
<h1 style='text-align: center; color: #1E3A8A; text-shadow: 0 0 10px rgba(100, 149, 237, 0.5);'>
    ✨ Expense Tracker
</h1>
""", unsafe_allow_html=True)

with st.form("expense_form"):
    # Expense name input
    expense_name = st.text_input("Expense Name", key="expense_name")
    
    # Initialize category if needed
    if 'predicted_category' not in st.session_state:
        st.session_state.predicted_category = "Miscellaneous"
    
    # Predict category button
    predict_button = st.form_submit_button("Predict Category")
    
    # Update category if button is clicked and expense name is provided
    if predict_button and expense_name:
        with st.spinner("Predicting category..."):
            st.session_state.predicted_category = predict_category(expense_name)
    
    # Category dropdown with predicted value
    category_index = expense_categories.index(st.session_state.predicted_category) if st.session_state.predicted_category in expense_categories else 0
    category = st.selectbox("Category", expense_categories, index=category_index)
    
    # Amount input with decimal support for paise
    amount = st.number_input("Amount (₹)", min_value=0.0, step=0.01, format="%.2f")
    
    # Date input with current date as default
    today = datetime.now().date()
    date = st.date_input("Date", value=today)
    
    # Automatically fill month and year based on date
    month = calendar.month_name[date.month]
    year = date.year
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Month: {month}")
    with col2:
        st.info(f"Year: {year}")
    
    # Payment method
    payment_method = st.selectbox("Payment Method", payment_methods)
    
    # Billing cycle for credit card
    if payment_method == "Credit Card":
        billing_cycle = get_billing_cycle(date)
        st.success(f"Billing Cycle: {billing_cycle}")
    
    # Shared expense
    shared = st.radio("Shared Expense?", ["No", "Yes"], index=0)
    
    # Submit button
    submitted = st.form_submit_button("Save Expense")
    
    if submitted:
        # In a real app, you would save this data to a database
        expense_data = {
            "Expense Name": expense_name,
            "Category": category,
            "Amount": f"₹{amount:.2f}",
            "Date": date.strftime("%Y-%m-%d"),
            "Month": month,
            "Year": year,
            "Payment Method": payment_method,
            "Shared": shared == "Yes"  # Convert to boolean
        }
        
        if payment_method == "Credit Card":
            expense_data["Billing Cycle"] = billing_cycle
        
        # Display success message and data
        st.success("Expense saved successfully!")
        st.json(expense_data)
        
        # In a real app, you would add code here to save to a database

# Add expander with info about the app
with st.expander("About this app"):
    st.write("""
    This expense tracker uses AI to automatically categorize your expenses.
    It also calculates credit card billing cycles and provides a beautiful
    dynamic color-changing background animation.
    """)
