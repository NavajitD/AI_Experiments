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

# Try to import streamlit_particles, but provide a fallback if it's not available
try:
    from streamlit_particles import particles
    particles_available = True
except ImportError:
    particles_available = False

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

# Particle animation configuration (only if library is available)
if particles_available:
    particle_options = {
        "particles": {
            "number": {
                "value": 80,
                "density": {
                    "enable": True,
                    "value_area": 800
                }
            },
            "color": {
                "value": "#ffffff"
            },
            "shape": {
                "type": "circle",
                "stroke": {
                    "width": 0,
                    "color": "#000000"
                },
            },
            "opacity": {
                "value": 0.5,
                "random": True,
            },
            "size": {
                "value": 3,
                "random": True,
            },
            "line_linked": {
                "enable": True,
                "distance": 150,
                "color": "#ffffff",
                "opacity": 0.4,
                "width": 1
            },
            "move": {
                "enable": True,
                "speed": 2,
                "direction": "none",
                "random": True,
                "straight": False,
                "out_mode": "out",
                "bounce": False,
            }
        },
        "interactivity": {
            "detect_on": "canvas",
            "events": {
                "onhover": {
                    "enable": True,
                    "mode": "grab"
                },
                "onclick": {
                    "enable": True,
                    "mode": "push"
                },
                "resize": True
            },
            "modes": {
                "grab": {
                    "distance": 140,
                    "line_linked": {
                        "opacity": 1
                    }
                },
                "push": {
                    "particles_nb": 4
                },
            }
        },
        "retina_detect": True
    }
    # Run background animation
    particles(particle_options, height="100vh", width="100%")
else:
    st.info("Install streamlit_particles for the animated background: `pip install streamlit-particles`")

# App UI
st.title("✨ Expense Tracker")

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
    interactive background animation.
    """)
