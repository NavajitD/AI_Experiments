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
        page_title="Zen Expense Tracker",
        page_icon="💸",
        layout="wide"
    )
    
    # CSS for dark theme design
    st.markdown("""
    <style>
    @font-face {
        font-family: 'Sole Sans';
        src: url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&display=swap');
        font-weight: 400;
        font-style: normal;
    }
        
    @font-face {
        font-family: 'Orbi';
        src: url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&display=swap');
        font-weight: 400;
        font-style: normal;
    }
    
    * {
        font-family: 'Sole Sans', 'Montserrat', sans-serif;
        transition: all 0.3s ease;
    }
    
    h1, h2, h3, h4, .title-font {
        font-family: 'Sole Sans', 'Montserrat', sans-serif !important;
        font-weight: 500 !important;
        color: #E0E0E0 !important;
    }
    
    p, span, div, label, input, select, option {
        font-family: 'Orbi', 'Montserrat', sans-serif;
    }
    
    /* Dark theme background */
    .stApp {
        background: linear-gradient(135deg, #1E1E2E 0%, #282838 100%);
        color: #E0E0E0;
    }
    
    /* Zen card effect */
    .zen-card {
        background: #262636;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    
    .zen-card h3 {
        color: #7ECEFF;
        font-weight: 500;
        margin-bottom: 16px;
        border-bottom: 1px solid rgba(126, 206, 255, 0.2);
        padding-bottom: 12px;
    }
    
    /* Glass card effect */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    /* Form styling */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox select {
        border-radius: 8px !important;
        border: 1px solid rgba(126, 206, 255, 0.2) !important;
        background: rgba(30, 30, 46, 0.8) !important;
        padding: 10px 14px !important;
        color: #E0E0E0 !important;
        box-shadow: none !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stSelectbox select:focus {
        border-color: #7ECEFF !important;
        box-shadow: 0 0 0 1px rgba(126, 206, 255, 0.3) !important;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 8px !important;
        background: linear-gradient(90deg, #7ECEFF, #FF7EC6) !important;
        color: #1E1E2E !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(126, 206, 255, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(126, 206, 255, 0.4) !important;
    }
    
    /* Custom labels */
    label {
        color: #A5BCCC !important;
        font-weight: 500 !important;
        margin-bottom: 8px !important;
        letter-spacing: 0.5px !important;
    }
    
    /* Success and error messages */
    .success-message {
        background: rgba(80, 250, 123, 0.1);
        border-left: 3px solid #50FA7B;
        padding: 12px 16px;
        border-radius: 6px;
        color: #50FA7B;
        margin: 16px 0;
    }
    
    .error-message {
        background: rgba(255, 85, 85, 0.1);
        border-left: 3px solid #FF5555;
        padding: 12px 16px;
        border-radius: 6px;
        color: #FF5555;
        margin: 16px 0;
    }
    
    /* Info box */
    .info-box {
        background: rgba(139, 233, 253, 0.1);
        border-left: 3px solid #8BE9FD;
        padding: 12px 16px;
        border-radius: 6px;
        color: #8BE9FD;
        margin: 16px 0;
    }
    
    /* Header */
    .zen-header {
        text-align: center;
        margin-bottom: 40px;
        padding: 30px 0;
    }
    
    .zen-header h1 {
        color: #7ECEFF;
        font-size: 2.2rem;
        margin-bottom: 10px;
        letter-spacing: 1px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .zen-header p {
        color: #A5BCCC;
        font-size: 1.1rem;
        max-width: 600px;
        margin: 0 auto;
        font-weight: 300;
        letter-spacing: 0.5px;
    }
    
    /* Icon styling */
    .zen-icon {
        font-size: 2.2rem;
        color: #FF7EC6;
        margin-bottom: 16px;
        display: inline-block;
        text-shadow: 0 2px 8px rgba(255, 126, 198, 0.4);
    }
    
    /* Custom checkbox */
    .stCheckbox {
        border-radius: 6px;
        padding: 10px;
        background: rgba(126, 206, 255, 0.05);
        margin: 12px 0;
    }
    
    /* Tooltip customization */
    .stTooltip {
        color: #FF7EC6;
    }
    
    /* Streamlit elements overall customization */
    .stProgress .st-emotion-cache-11s8ty4 {
        background-color: rgba(126, 206, 255, 0.2) !important;
    }
    
    .stProgress .st-emotion-cache-11s8ty4 > div {
        background: linear-gradient(90deg, #7ECEFF, #FF7EC6) !important;
    }
    
    /* Analytics customizations */
    .stPlotlyChart {
        background: rgba(30, 30, 46, 0.5);
        border-radius: 8px;
        padding: 6px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    }
    
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
