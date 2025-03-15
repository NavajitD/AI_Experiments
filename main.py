import os
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
pip install gspread
import pandas as pd
from datetime import datetime, timedelta
import calendar
import json
import time
import numpy as np
import gspread
from google.oauth2 import service_account
from gspread_dataframe import set_with_dataframe

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

# Function to connect to Google Sheets
def connect_to_gsheets():
    # Create a connection object
    try:
        # Either load credentials from secrets or from a JSON file
        if 'gcp_service_account' in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", 
                        "https://www.googleapis.com/auth/drive"]
            )
        else:
            # Path to your service account JSON file
            # You'll need to create this file and put it in the same directory as your script
            credentials_path = "service_account_credentials.json"
            
            if not os.path.exists(credentials_path):
                st.error("Service account credentials file not found. Please see the sidebar for setup instructions.")
                return None
                
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/spreadsheets", 
                        "https://www.googleapis.com/auth/drive"]
            )
        
        # Authenticate and create the client
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {str(e)}")
        return None

# Function to add data to Google Sheets
def add_to_gsheets(data):
    # Google Sheet URL or ID
    sheet_url = "https://docs.google.com/spreadsheets/d/1OLLl7WZzuqiKCEvQYhLs2YrONcvEszolbSQK4t2HJLc/edit?usp=sharing"
    sheet_id = sheet_url.split('/d/')[1].split('/')[0]
    
    client = connect_to_gsheets()
    if client is None:
        return False, "Failed to connect to Google Sheets. Check your credentials."
    
    try:
        # Open the spreadsheet
        spreadsheet = client.open_by_key(sheet_id)
        
        # Select the first worksheet or create one if it doesn't exist
        try:
            worksheet = spreadsheet.worksheet("Expenses")
        except:
            worksheet = spreadsheet.add_worksheet(title="Expenses", rows=1000, cols=20)
        
        # Get existing data
        try:
            existing_data = worksheet.get_all_records()
            # If it's empty, we need to create headers
            if not existing_data:
                headers = list(data.keys())
                worksheet.append_row(headers)
        except:
            # Create headers if there's an error (likely empty sheet)
            headers = list(data.keys())
            worksheet.append_row(headers)
        
        # Convert data to a list of values in the correct order
        # First get headers to ensure correct order
        headers = worksheet.row_values(1)
        row_values = [data.get(header, "") for header in headers]
        
        # Append the data
        worksheet.append_row(row_values)
        
        return True, "Data added to Google Sheets successfully."
    except Exception as e:
        return False, f"Error adding data to Google Sheets: {str(e)}"

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
        response = Model_Gemini.invoke(prompt)
        category = response.content.strip()
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
    billing_cycle = ""
    if payment_method == "Credit Card":
        billing_cycle = get_billing_cycle(date)
        st.success(f"Billing Cycle: {billing_cycle}")
    
    # Shared expense
    shared = st.radio("Shared Expense?", ["No", "Yes"], index=0)
    
    # Submit button
    submitted = st.form_submit_button("Save Expense")
    
    if submitted:
        # Format the data
        expense_data = {
            "Expense Name": expense_name,
            "Category": category,
            "Amount": amount,  # Store as number for calculations
            "Amount (₹)": f"₹{amount:.2f}",  # Formatted display
            "Date": date.strftime("%Y-%m-%d"),
            "Month": month,
            "Year": year,
            "Payment Method": payment_method,
            "Shared": shared == "Yes",  # Convert to boolean
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if payment_method == "Credit Card":
            expense_data["Billing Cycle"] = billing_cycle
        
        # Add to Google Sheets
        with st.spinner("Saving to Google Sheets..."):
            success, message = add_to_gsheets(expense_data)
            
        if success:
            st.success("✅ Expense saved successfully to Google Sheets!")
            st.json(expense_data)
        else:
            st.error(f"Failed to save to Google Sheets: {message}")
            st.info("Here's the data that would have been saved:")
            st.json(expense_data)

# Add expander with info about the app
with st.expander("About this app"):
    st.write("""
    This expense tracker uses AI to automatically categorize your expenses.
    It also calculates credit card billing cycles and saves all data to Google Sheets
    with a beautiful dynamic color-changing background animation.
    """)
