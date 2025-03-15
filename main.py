import os
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
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
            st.info("Using credentials from secrets")
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", 
                        "https://www.googleapis.com/auth/drive"]
            )
        else:
            # Path to your service account JSON file
            credentials_path = "service_account_credentials.json"
            
            if not os.path.exists(credentials_path):
                st.error(f"Service account credentials file not found at: {os.path.abspath(credentials_path)}")
                return None
            
            st.info(f"Using credentials from file: {os.path.abspath(credentials_path)}")    
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/spreadsheets", 
                        "https://www.googleapis.com/auth/drive"]
            )
        
        # Authenticate and create the client
        client = gspread.authorize(credentials)
        st.success("Successfully connected to Google services")
        return client
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Function to add data to Google Sheets - UPDATED SHEET URL
def add_to_gsheets(data):
    # Updated Google Sheet URL
    sheet_url = "https://docs.google.com/spreadsheets/d/1ysIiU5zEl2vdA28Drs_jInyH2htWej7XzaxRYWfy1dU/edit?usp=sharing"
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

# Dark mode animation with calming colors
def dark_mode_animation():
    animation_placeholder = st.empty()
    
    # Initialize animation state
    if 'animation_frame' not in st.session_state:
        st.session_state.animation_frame = 0
        st.session_state.animation_direction = 1
        st.session_state.last_update = time.time()
    
    # Update animation frame
    current_time = time.time()
    if current_time - st.session_state.last_update > 0.1:  # Update every 100ms
        st.session_state.animation_frame += st.session_state.animation_direction * 0.5  # Slower transition
        if st.session_state.animation_frame >= 100:
            st.session_state.animation_direction = -1
        elif st.session_state.animation_frame <= 0:
            st.session_state.animation_direction = 1
        st.session_state.last_update = current_time
    
    # Calculate animation parameters
    frame = st.session_state.animation_frame / 100
    
    # Dark mode colors with cool/calm hues (blues, purples)
    hue1 = 220 + (frame * 40)  # Deep blue to purple range
    hue2 = 260 + (frame * 20)  # Purple to indigo range
    
    # Create a subtle gradient background
    css = f"""
    <style>
    .stApp {{
        background: linear-gradient(
            135deg,
            hsla({hue1}, 70%, 10%, 1),
            hsla({hue2}, 60%, 15%, 1)
        );
        background-size: 300% 300%;
        animation: gradient 15s ease infinite;
    }}
    
    @keyframes gradient {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    
    /* Dark mode form styling */
    div.stTextInput input, div.stNumberInput input, div.stDateInput input, div.stSelectbox, div.stRadio {{
        background-color: rgba(30, 30, 40, 0.6) !important;
        color: #e0e0e0 !important;
        border: 1px solid rgba(80, 100, 175, 0.5) !important;
        border-radius: 8px !important;
    }}
    
    div.stTextInput input:focus, div.stNumberInput input:focus, div.stDateInput input:focus {{
        border-color: rgba(100, 149, 237, 0.8) !important;
        box-shadow: 0 0 10px rgba(100, 149, 237, 0.3) !important;
    }}
    
    /* Glowing text effect for important elements */
    .glow-text {{
        color: rgba(150, 200, 255, 0.9);
        text-shadow: 0 0 10px rgba(150, 180, 255, 0.5);
    }}
    
    /* Buttons styling */
    .stButton button {{
        background: linear-gradient(45deg, rgba(60, 80, 160, 0.8), rgba(80, 100, 180, 0.8)) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
    }}
    
    .stButton button:hover {{
        background: linear-gradient(45deg, rgba(80, 100, 180, 0.9), rgba(100, 120, 200, 0.9)) !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3) !important;
        transform: translateY(-2px) !important;
    }}
    
    /* Form container with glassmorphism effect */
    .form-container {{
        background-color: rgba(20, 25, 35, 0.7) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        padding: 20px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(80, 120, 200, 0.18) !important;
        margin-bottom: 20px !important;
    }}
    
    /* Info and success boxes */
    div.stAlert {{
        background-color: rgba(30, 35, 50, 0.8) !important;
        border: 1px solid rgba(80, 120, 200, 0.5) !important;
        color: #e0e0e0 !important;
    }}
    
    /* JSON output styling */
    div.element-container div.stJson {{
        background-color: rgba(25, 30, 40, 0.8) !important;
        border: 1px solid rgba(80, 120, 200, 0.3) !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }}
    
    /* Date picker styling */
    div.st-bd, div.st-cs {{
        background-color: rgba(30, 35, 45, 0.9) !important;
        color: #e0e0e0 !important;
    }}
    
    /* Custom info cards */
    .info-card {{
        background-color: rgba(30, 40, 60, 0.6) !important;
        border-radius: 8px !important;
        padding: 10px 15px !important;
        border-left: 4px solid rgba(100, 149, 237, 0.7) !important;
        margin-bottom: 12px !important;
        color: #d0d0e0 !important;
    }}
    
    /* Custom success card */
    .success-card {{
        background-color: rgba(20, 40, 30, 0.7) !important;
        border-radius: 8px !important;
        padding: 15px !important;
        border-left: 4px solid rgba(80, 220, 100, 0.7) !important;
        margin: 15px 0 !important;
        color: #d0e0d0 !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    }}
    
    /* Custom error card */
    .error-card {{
        background-color: rgba(40, 20, 20, 0.7) !important;
        border-radius: 8px !important;
        padding: 15px !important;
        border-left: 4px solid rgba(220, 80, 80, 0.7) !important;
        margin: 15px 0 !important;
        color: #e0d0d0 !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    }}
    
    /* Custom header styling */
    .section-header {{
        color: #a0c4ff !important;
        margin-bottom: 20px !important;
        padding-bottom: 10px !important;
        border-bottom: 1px solid rgba(100, 149, 237, 0.3) !important;
    }}
    </style>
    """
    
    animation_placeholder.markdown(css, unsafe_allow_html=True)

# Define expense categories with icons
expense_categories = [
    "Housing", "Utilities", "Groceries", "Dining Out", "Transportation",
    "Healthcare", "Entertainment", "Shopping", "Personal Care", 
    "Education", "Travel", "Gifts & Donations", "Insurance",
    "Investments", "Debt Payments", "Miscellaneous"
]

# Category icons mapping (continued)
category_icons = {
    "Housing": "🏠", "Utilities": "⚡", "Groceries": "🛒", "Dining Out": "🍽️", 
    "Transportation": "🚗", "Healthcare": "⚕️", "Entertainment": "🎬", 
    "Shopping": "🛍️", "Personal Care": "💆", "Education": "📚",
    "Travel": "✈️", "Gifts & Donations": "🎁", "Insurance": "🔒",
    "Investments": "📈", "Debt Payments": "💳", "Miscellaneous": "🔄"
}

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

# Run dark mode animation
dark_mode_animation()

# App title with a glow effect
st.markdown("""
<h1 style='text-align: center; color: #a0c4ff; text-shadow: 0 0 10px rgba(100, 149, 237, 0.7);'>
    💰 Dark Mode Expense Tracker
</h1>
<p style='text-align: center; color: #d0d0e0;'>Track your expenses with AI-powered categorization</p>
""", unsafe_allow_html=True)

# Wrapper for the form with custom styling
st.markdown("""
<div class="form-container">
</div>
""", unsafe_allow_html=True)

with st.form("expense_form"):
    # Expense name input
    expense_name = st.text_input("Expense Name", key="expense_name")
    
    # Initialize category if needed
    if 'predicted_category' not in st.session_state:
        st.session_state.predicted_category = "Miscellaneous"
    
    # Predict category button
    col1, col2 = st.columns([2, 1])
    with col1:
        category_index = expense_categories.index(st.session_state.predicted_category) if st.session_state.predicted_category in expense_categories else 0
        category = st.selectbox("Category", expense_categories, index=category_index, format_func=lambda x: f"{category_icons.get(x, '')} {x}")
    
    with col2:
        predict_button = st.form_submit_button("🔍 Predict")
        
        # Update category if button is clicked and expense name is provided
        if predict_button and expense_name:
            with st.spinner("✨ AI predicting category..."):
                st.session_state.predicted_category = predict_category(expense_name)
    
    # Amount input with decimal support
    amount = st.number_input("Amount (₹)", min_value=0.0, step=0.01, format="%.2f")
    
    # Date input with current date as default
    today = datetime.now().date()
    date = st.date_input("Date", value=today)
    
    # Automatically fill month and year based on date
    month = calendar.month_name[date.month]
    year = date.year
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div class='info-card'>Month: {month}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='info-card'>Year: {year}</div>", unsafe_allow_html=True)
    
    # Payment method with icons
    payment_icons = {
        "Cash": "💵", "Debit Card": "💳", "Credit Card": "💳", 
        "UPI": "📱", "Net Banking": "🏦", "Mobile Wallet": "📲",
        "Bank Transfer": "🔄", "Other": "❓"
    }
    
    payment_method = st.selectbox(
        "Payment Method", 
        payment_methods,
        format_func=lambda x: f"{payment_icons.get(x, '')} {x}"
    )
    
    # Billing cycle for credit card
    if payment_method == "Credit Card":
        billing_cycle = get_billing_cycle(date)
        st.markdown(f"<div class='success-card'>Billing Cycle: {billing_cycle}</div>", unsafe_allow_html=True)
    
    # Shared expense toggle with better styling
    shared = st.radio(
        "Shared Expense?", 
        ["No", "Yes"], 
        index=0,
        horizontal=True
    )
    
    # Optional note field
    note = st.text_area("Note (Optional)", "", height=80)
    
    # Submit button with icon
    submitted = st.form_submit_button("💾 Save Expense")
    
    if submitted:
        if not expense_name:
            st.markdown(f"<div class='error-card'>Please enter an expense name</div>", unsafe_allow_html=True)
        elif amount <= 0:
            st.markdown(f"<div class='error-card'>Please enter a valid amount</div>", unsafe_allow_html=True)
        else:
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
                "Note": note,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if payment_method == "Credit Card":
                expense_data["Billing Cycle"] = billing_cycle
            
            # Add to Google Sheets
            with st.spinner("Saving to Google Sheets..."):
                success, message = add_to_gsheets(expense_data)
                
            if success:
                st.markdown(f"<div class='success-card'>✅ Expense saved successfully!</div>", unsafe_allow_html=True)
                # Show the data in a cleaner format
                st.json(expense_data)
                # Clear the form
                st.rerun()
            else:
                st.markdown(f"<div class='error-card'>❌ Failed: {message}</div>", unsafe_allow_html=True)
                st.markdown("<div class='info-card'>Here's the data that would have been saved:</div>", unsafe_allow_html=True)
                st.json(expense_data)

# Footer with credits
st.markdown("""
<div style='text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(100, 149, 237, 0.3); color: #a0a0a0;'>
    ✨ Powered by AI • Navajit D 2025
</div>
""", unsafe_allow_html=True)



    
