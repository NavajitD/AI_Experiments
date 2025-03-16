import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import analytics

# Initialize session state variables if they don't exist
if 'predicted_category' not in st.session_state:
    st.session_state['predicted_category'] = ""
if 'category_predicted' not in st.session_state:
    st.session_state['category_predicted'] = ""


# Function to get category prediction from Gemini model
def get_category_prediction(expense_name):
    # Set the API key directly in the script
    if "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = "AIzaSyAqMFvXnZ4JLeYqySr1rkY5Ooc5pYdPmrc"  
    
    # Retrieve the API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set")
    
    # Initialize Gemini model
    model = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=api_key
    )
    try:
        prompt = f"""
        Classify the following expense into one of these categories:
        - Bike
        - Auto/Cab
        - Public transport
        - Groceries
        - Eating out
        - Party
        - Household supplies
        - Education
        - Gift
        - Cinema
        - Entertainment
        - Liquor
        - Rent/Maintenance
        - Furniture
        - Services
        - Electricity
        - Internet
        - Investment
        - Insurance
        - Medical expenses
        - Flights
        - Travel
        - Clothes
        - Games/Sports
        - Gas
        - Phone
        
        Expense: {expense_name}
        
        Return only the category name, nothing else.
        """
        response = model.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        st.error(f"Error with Gemini API: {str(e)}")
        return "Miscellaneous"

# Function to submit data to Google Apps Script
def submit_to_google_apps_script(data):
    # Replace with your deployed Google Apps Script web app URL
    apps_script_url = "https://script.google.com/macros/s/AKfycbx1HZs60TbbLxHmX1HQKpDiM_aGuGewhT4azBzuvoIqnvp3pEG-nhWe-hz-nK78YXnPkw/exec"
    
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            apps_script_url,
            data=json.dumps(data),
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": f"HTTP Status: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Function to get billing cycle based on date
def get_billing_cycle(date_obj):
    day = date_obj.day
    
    if day < 16:
        # Previous billing cycle
        last_month = date_obj.replace(day=1) - timedelta(days=1)
        start_month = last_month.replace(day=25)
        end_month = date_obj.replace(day=25)
    else:
        # Next billing cycle
        start_month = date_obj.replace(day=25)
        next_month = date_obj.replace(day=28) + timedelta(days=4)
        end_month = next_month.replace(day=25)
    
    start_month_str = start_month.strftime("%b")
    end_month_str = end_month.strftime("%b")
    
    return f"{start_month_str} 25 - {end_month_str} 25"

# Function to create a zen card
def create_zen_card(content_function, title=""):
    with st.container():
        st.markdown(f"""
        <div class="zen-card">
            <h3>{title}</h3>
            <div class="card-content">
                {content_function()}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Main app function
def main():
    # Set page config
    st.set_page_config(
        page_title="Expense Tracker",
        page_icon="✦",
        layout="wide"
    )
    
    # CSS for premium dark theme design with animated background
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&family=Hind:wght@300;400;500;600&display=swap');
    
    * {
        transition: all 0.3s ease;
    }
    
    h1, h2, h3, h4, .title-font {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
        letter-spacing: 0.5px !important;
    }
    
    p, span, div, label, input, select, option {
        font-family: 'Hind', sans-serif !important;
        letter-spacing: 0.2px !important;
    }
    
    /* Premium blue colors */
    :root {
        --royal-blue: #2D5AFE;
        --royal-blue-light: #5B7FFF;
        --royal-blue-dark: #1E40AF;
        --royal-accent: #B69E66;
        --dark-bg: #121220;
        --dark-card: #1A1A2E;
        --text-primary: #FFFFFF;
        --text-secondary: #B5C9E0;
    }
    
    /* Animated background */
    @keyframes gradientAnimation {
        0% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
        100% {
            background-position: 0% 50%;
        }
    }
    
    .stApp {
        position: relative;
        color: var(--text-primary);
        background: var(--dark-bg);
        overflow: hidden;
    }
    
    .stApp::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(
            125deg,
            rgba(18, 18, 32, 0.98) 0%,
            rgba(26, 26, 46, 0.98) 25%,
            rgba(30, 64, 175, 0.02) 50%,
            rgba(26, 26, 46, 0.98) 75%,
            rgba(18, 18, 32, 0.98) 100%
        );
        background-size: 400% 400%;
        animation: gradientAnimation 30s ease infinite;
        z-index: -2;
    }
    
    .stApp::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 20%, rgba(45, 90, 254, 0.08) 0%, transparent 45%),
            radial-gradient(circle at 80% 80%, rgba(182, 158, 102, 0.08) 0%, transparent 45%);
        z-index: -1;
    }
    
    /* Zen card effect */
    .zen-card {
        background: var(--dark-card);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 28px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .zen-card::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(45, 90, 254, 0.3), transparent);
        z-index: 1;
    }
    
    .zen-card h3 {
        color: var(--royal-blue-light);
        font-weight: 600;
        margin-bottom: 20px;
        border-bottom: 1px solid rgba(45, 90, 254, 0.15);
        padding-bottom: 12px;
        text-transform: uppercase;
        font-size: 1.1rem;
    }
    
    /* Glass card effect */
    .glass-card {
        background: rgba(26, 26, 46, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border: 1px solid rgba(45, 90, 254, 0.1);
        padding: 28px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        position: relative;
        overflow: hidden;
    }
    
    /* Form styling */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox select {
        border-radius: 8px !important;
        border: 1px solid rgba(45, 90, 254, 0.2) !important;
        background: rgba(18, 18, 32, 0.7) !important;
        backdrop-filter: blur(5px) !important;
        padding: 12px 16px !important;
        color: var(--text-primary) !important;
        box-shadow: none !important;
        font-family: 'Hind', sans-serif !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stSelectbox select:focus {
        border-color: var(--royal-blue) !important;
        box-shadow: 0 0 0 1px rgba(45, 90, 254, 0.2) !important;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 8px !important;
        background: var(--royal-blue) !important;
        color: #FFFFFF !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(45, 90, 254, 0.3) !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        overflow: hidden !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        font-size: 14px !important;
    }
    
    .stButton>button:hover {
        background: var(--royal-blue-light) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(45, 90, 254, 0.4) !important;
    }
    
    /* Custom labels */
    label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        margin-bottom: 8px !important;
        letter-spacing: 0.5px !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.9rem !important;
    }
    
    /* Success and error messages */
    .success-message {
        background: rgba(52, 211, 153, 0.1);
        border-left: 3px solid #34D399;
        padding: 14px 18px;
        border-radius: 6px;
        color: #34D399;
        margin: 16px 0;
        font-family: 'Hind', sans-serif;
    }
    
    .error-message {
        background: rgba(239, 68, 68, 0.1);
        border-left: 3px solid #EF4444;
        padding: 14px 18px;
        border-radius: 6px;
        color: #EF4444;
        margin: 16px 0;
        font-family: 'Hind', sans-serif;
    }
    
    /* Info box */
    .info-box {
        background: rgba(45, 90, 254, 0.05);
        border-left: 3px solid var(--royal-blue);
        padding: 14px 18px;
        border-radius: 6px;
        color: var(--text-secondary);
        margin: 16px 0;
        font-family: 'Hind', sans-serif;
    }
    
    /* Header */
    .zen-header {
        text-align: center;
        margin-bottom: 40px;
        padding: 35px 0;
    }
    
    .zen-header h1 {
        color: #FFFFFF;
        font-size: 2.2rem;
        margin-bottom: 12px;
        letter-spacing: 2px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        text-transform: uppercase;
    }
    
    .zen-header p {
        color: var(--royal-accent);
        font-size: 1.1rem;
        max-width: 600px;
        margin: 0 auto;
        font-weight: 400;
        letter-spacing: 0.5px;
    }
    
    /* Icon styling */
    .zen-icon {
        font-size: 1.8rem;
        color: var(--royal-blue);
        margin-bottom: 18px;
        display: inline-block;
    }
    
    /* Custom checkbox */
    .stCheckbox {
        border-radius: 6px;
        padding: 10px;
        background: rgba(45, 90, 254, 0.05);
        margin: 12px 0;
    }

    .stCheckbox label {
        color: var(--text-secondary) !important;
    }
    
    /* Streamlit elements overall customization */
    .stProgress .st-emotion-cache-11s8ty4 {
        background-color: rgba(45, 90, 254, 0.1) !important;
    }
    
    .stProgress .st-emotion-cache-11s8ty4 > div {
        background: var(--royal-blue) !important;
    }
    
    /* Analytics customizations */
    .stPlotlyChart {
        background: rgba(26, 26, 46, 0.7);
        border-radius: 8px;
        padding: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow
    
    /* Pandas dataframe styling */
    .dataframe {
        border-collapse: collapse;
        font-family: 'Orbi', 'Montserrat', sans-serif;
        font-size: 0.9rem;
    }
    
    .dataframe th {
        background-color: rgba(126, 206, 255, 0.1);
        color: #7ECEFF;
        padding: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .dataframe td {
        padding: 8px 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        color: #E0E0E0;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: rgba(30, 30, 46, 0.3);
    }
    
    /* Streamlit sidebar */
    .css-1d391kg, .css-12oz5g7 {
        background-color: #262636 !important;
    }
    
    /* Streamlit expander */
    .st-emotion-cache-1xw8zd0 {
        background-color: #262636 !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
    }
    
    /* Streamlit tabs */
    .st-emotion-cache-k7vsyb {
        background-color: rgba(126, 206, 255, 0.1) !important;
        color: #7ECEFF !important;
    }
    
    .st-emotion-cache-k7vsyb:hover {
        background-color: rgba(126, 206, 255, 0.2) !important;
    }
    
    .st-emotion-cache-1cypcdb {
        border-color: #7ECEFF !important;
        color: #7ECEFF !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .zen-card, .glass-card {
            padding: 16px;
        }
        
        .zen-header h1 {
            font-size: 1.8rem !important;
        }
        
        .zen-header p {
            font-size: 0.9rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Zen header
    st.markdown("""
    <div class="zen-header">
        <span class="zen-icon">💸</span>
        <h1>Small Expense Tracker</h1>
        <p>Track spending fast with clarity</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a container for the form
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Create a glass card for the form
            with st.container():
                st.markdown("""
                <div class="glass-card">
                    <h3 class="title-font">New Expense</h3>
                """, unsafe_allow_html=True)
                
                # Form to capture expense details
                with st.form(key="expense_form"):
                    # Expense name
                    expense_name = st.text_input("Expense name", key="expense_name_input")
                    
                    # Category with Gemini prediction
                    if expense_name and st.session_state.get('category_predicted') != expense_name:
                        with st.spinner("Predicting category..."):
                            try:
                                predicted_category = get_category_prediction(expense_name)
                                st.session_state['predicted_category'] = predicted_category
                                st.session_state['category_predicted'] = expense_name
                            except Exception as e:
                                st.error(f"Error predicting category: {str(e)}")
                                st.session_state['predicted_category'] = "Miscellaneous"
                    
                    # All possible categories
                    categories = [
                        "Bike", "Auto/Cab", "Public transport", "Groceries", "Eating out", "Party", "Household supplies", "Education", "Gift", 
                        "Cinema", "Entertainment", "Liquor", "Rent/Maintenance", "Furniture", "Services", "Electricity", "Internet", "Investment", "Insurance", 
                        "Medical expenses", "Flights", "Travel", "Clothes", "Games/Sports", "Gas", "Phone"
                    ]
                    
                    # Default to predicted category if available
                    default_category = st.session_state.get('predicted_category', categories[0]) if expense_name else categories[0]
                    default_index = categories.index(default_category) if default_category in categories else 0
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        category = st.selectbox("Category", categories, index=default_index, key="category_input")
                        
                        # Payment method
                        payment_methods = ["Cred UPI", "Credit card", "GPay UPI", "Cash", "Debit card", "Net Banking"]
                        payment_method = st.selectbox("Payment method", payment_methods, key="payment_method_input")
                    
                    with col2:
                        # Amount in Rupees
                        amount = st.number_input("Amount (₹)", min_value=0.0, step=0.01, format="%.2f", key="amount_input")
                        
                        # Date with calendar component
                        today = datetime.now().date()
                        date = st.date_input("Date", value=today, key="date_input")
                    
                    # Month and Year (auto-filled based on date)
                    month = date.strftime("%B")
                    year = date.year
                    
                    # Billing cycle (if Credit Card is selected)
                    if payment_method == "Credit card":
                        billing_cycle = get_billing_cycle(date)
                        st.markdown(f"""
                        <div class="info-box">
                            <strong>Billing Cycle:</strong> {billing_cycle}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        billing_cycle = ""
                    
                    # Shared expense
                    shared = st.checkbox("Shared expense", value=False, key="shared_input")
            
                    # Data preparation
                    data = {
                        "expenseName": expense_name,
                        "category": category,
                        "amount": amount,
                        "date": date.strftime("%Y-%m-%d"),
                        "month": month,
                        "year": year,
                        "paymentMethod": payment_method,
                        "shared": "Yes" if shared else "No",
                        "billingCycle": billing_cycle,
                        "timeStamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Submit button
                    submitted = st.form_submit_button("Add expense")
                    
                    if submitted:
                        if not expense_name:
                            st.error("Please enter an expense name.")
                        elif amount <= 0:
                            st.error("Amount must be greater than 0.")
                        else:
                            # Submit to Google Apps Script
                            with st.spinner("Adding expense..."):
                                response = submit_to_google_apps_script(data)
                                
                                if response["status"] == "success":
                                    st.success("Expense added successfully!")
                                    # Reset form logic here
                                else:
                                    st.error(f"Error: {response['message']}")                       
    # Show analytics after the form
    analytics.show_analytics()

if __name__ == "__main__":
    main()
