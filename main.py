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
    apps_script_url = "https://script.google.com/macros/s/AKfycbydCB4JxP6nJDSGcfW1vwvyuTP9yOrgM8Gd-tdpOEkTN_tD0R0m2lsISog1TC8x5YMs0A/exec"
    
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

# Function to create a glassmorphism card
def create_glass_card(content_function, title=""):
    with st.container():
        st.markdown(f"""
        <div class="glass-card">
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
        page_icon="💰",
        layout="wide"
    )
    
    # CSS for the enhanced design
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;700&family=Poppins:wght@300;400;500&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    h1, h2, .title-font {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }
    
    /* Animated background */
    .stApp {
        background: linear-gradient(-45deg, #7928ca, #ff0080, #00bfff, #00f2ea);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    
    @keyframes gradient {
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
    
    /* Glass card effect */
    .glass-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 20px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
    }
    
    /* Form styling */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox select {
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        background: rgba(255, 255, 255, 0.05) !important;
        padding: 10px !important;
        color: white !important;
    }
    
    .stButton>button {
        border-radius: 12px !important;
        background: linear-gradient(90deg, #ff0080, #7928ca) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Custom labels */
    label {
        color: white !important;
        font-weight: 500 !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Success and error messages */
    .success-message {
        background: rgba(46, 204, 113, 0.2);
        border-left: 4px solid #2ecc71;
        padding: 10px 15px;
        border-radius: 8px;
        color: white;
        margin: 10px 0;
    }
    
    .error-message {
        background: rgba(231, 76, 60, 0.2);
        border-left: 4px solid #e74c3c;
        padding: 10px 15px;
        border-radius: 8px;
        color: white;
        margin: 10px 0;
    }
    
    /* Custom info box */
    .info-box {
        background: rgba(52, 152, 219, 0.2);
        border-left: 4px solid #3498db;
        padding: 10px 15px;
        border-radius: 8px;
        color: white;
        margin: 10px 0;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .glass-card {
            padding: 15px;
        }
        
        h1 {
            font-size: 1.8rem !important;
        }
    }
    
    /* Animated icons */
    .icon-container {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    
    .icon {
        font-size: 3rem;
        animation: pulse 2s infinite;
        color: white;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
    }
    
    @keyframes pulse {
        0% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.1);
        }
        100% {
            transform: scale(1);
        }
    }
    
    /* Custom header */
    .custom-header {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .custom-header h1 {
        color: white;
        text-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        font-size: 3rem;
        margin-bottom: 10px;
    }
    
    .custom-header p {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1.2rem;
        max-width: 600px;
        margin: 0 auto;
    }
    
    /* Custom checkbox */
    .stCheckbox {
        border-radius: 10px;
        padding: 10px;
        background: rgba(255, 255, 255, 0.05);
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Custom header
    st.markdown("""
    <div class="custom-header">
        <div class="icon-container">
            <span class="icon">💰</span>
        </div>
        <h1>EXPENSE TRACKER</h1>
        <p>Track your expenses with our AI-powered system</p>
    </div>
    """, unsafe_allow_html=True)

    # Show analytics after the form
    analytics.show_analytics()
    
    # Create a container for the form
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Create a glass card for the form
            with st.container():
                st.markdown("""
                <div class="glass-card">
                    <h3 class="title-font">Add Expense</h3>
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
                                    

if __name__ == "__main__":
    main()
