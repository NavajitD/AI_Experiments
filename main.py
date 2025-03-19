import streamlit as st

# Set page config as the first Streamlit command
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="✦",
    layout="wide"
)

# Import analytics after setting page config
import analytics

# Rest of your imports
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Initialize session state variables if they don't exist
if 'predicted_category' not in st.session_state:
    st.session_state['predicted_category'] = ""
if 'category_predicted' not in st.session_state:
    st.session_state['category_predicted'] = ""

# Function to get category prediction from Gemini model
def get_category_prediction(expense_name):
    # Get API key from environment variable
    api_key = os.environ.get("GOOGLE_API_KEY")
    
    # Check if API key is available
    if not api_key:
        st.warning("Google API key not found. Please set the GOOGLE_API_KEY environment variable.")
        return "Miscellaneous"
    
    try:
        model = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=api_key
        )
        
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
        last_month = date_obj.replace(day=1) - timedelta(days=1)
        start_month = last_month.replace(day=25)
        end_month = date_obj.replace(day=25)
    else:
        start_month = date_obj.replace(day=25)
        next_month = date_obj.replace(day=28) + timedelta(days=4)
        end_month = next_month.replace(day=25)
    
    start_month_str = start_month.strftime("%b")
    end_month_str = end_month.strftime("%b")
    
    return f"{start_month_str} 25 - {end_month_str} 25"

# Main app function
def main():
    
    # CSS for premium dark theme design with animated background
    st.markdown("""
    <style>
    /* Your CSS styles here */
    </style>
    """, unsafe_allow_html=True)
    
    # Create tabs for the app
    tab1, tab2 = st.tabs(["New Expense", "Trends"])
    
    with tab1:
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
                    
                    # API key input (only show if not set)
                    if not os.environ.get("GOOGLE_API_KEY"):
                        api_key = st.text_input("Google API Key (required for category prediction)", type="password")
                        if api_key:
                            os.environ["GOOGLE_API_KEY"] = api_key
                    
                    # Form to capture expense details
                    with st.form(key="expense_form"):
                        # Expense name
                        expense_name = st.text_input("Expense name", key="expense_name_input")
                        
                        # Category with Gemini prediction
                        if expense_name and st.session_state.get('category_predicted') != expense_name:
                            if os.environ.get("GOOGLE_API_KEY"):
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
                            "Medical expenses", "Flights", "Travel", "Clothes", "Games/Sports", "Gas", "Phone", "Miscellaneous"
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
                                        st.session_state['predicted_category'] = ""
                                        st.session_state['category_predicted'] = ""
                                        st.experimental_rerun()
                                    else:
                                        st.error(f"Error: {response['message']}")    

    with tab2:
        # Create analytics view
        analytics.show_analytics()

if __name__ == "__main__":
    main()
