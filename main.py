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
        page_icon="🍃",
        layout="wide"
    )
    
    # CSS for zen design with muted red and yellow
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;500;600&family=Merriweather:wght@300;400;700&display=swap');
    
    * {
        font-family: 'Nunito', sans-serif;
        transition: all 0.3s ease;
    }
    
    h1, h2, .title-font {
        font-family: 'Merriweather', serif !important;
        font-weight: 400 !important;
        color: #8A3033 !important;
    }
    
    /* Soft background */
    .stApp {
        background: linear-gradient(135deg, #FFF8E1 0%, #FFFBF2 100%);
    }
    
    /* Zen card effect */
    .zen-card {
        background: #FFFAF0;
        border-radius: 8px;
        border: 1px solid rgba(138, 48, 51, 0.1);
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(138, 48, 51, 0.05);
    }
    
    .zen-card h3 {
        color: #8A3033;
        font-weight: 500;
        margin-bottom: 16px;
        border-bottom: 1px solid rgba(138, 48, 51, 0.1);
        padding-bottom: 8px;
    }
    
    /* Form styling */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox select {
        border-radius: 6px !important;
        border: 1px solid rgba(138, 48, 51, 0.2) !important;
        background: #FFFDF7 !important;
        padding: 8px 12px !important;
        color: #5D4037 !important;
        box-shadow: none !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stSelectbox select:focus {
        border-color: rgba(204, 143, 77, 0.6) !important;
        box-shadow: 0 0 0 1px rgba(204, 143, 77, 0.2) !important;
    }
    
    .stButton>button {
        border-radius: 6px !important;
        background: linear-gradient(90deg, #B56E70, #CC8F4D) !important;
        color: white !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(138, 48, 51, 0.1) !important;
    }
    
    .stButton>button:hover {
        background: linear-gradient(90deg, #A25E60, #BD803E) !important;
        box-shadow: 0 3px 6px rgba(138, 48, 51, 0.15) !important;
    }
    
    /* Custom labels */
    label {
        color: #8A3033 !important;
        font-weight: 500 !important;
        margin-bottom: 4px !important;
    }
    
    /* Success and error messages */
    .success-message {
        background: rgba(139, 195, 74, 0.1);
        border-left: 3px solid #8BC34A;
        padding: 10px 15px;
        border-radius: 4px;
        color: #558B2F;
        margin: 10px 0;
    }
    
    .error-message {
        background: rgba(138, 48, 51, 0.1);
        border-left: 3px solid #8A3033;
        padding: 10px 15px;
        border-radius: 4px;
        color: #8A3033;
        margin: 10px 0;
    }
    
    /* Custom info box */
    .info-box {
        background: rgba(204, 143, 77, 0.1);
        border-left: 3px solid #CC8F4D;
        padding: 10px 15px;
        border-radius: 4px;
        color: #996B39;
        margin: 10px 0;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .zen-card {
            padding: 16px;
        }
        
        h1 {
            font-size: 1.6rem !important;
        }
    }
    
    /* Header */
    .zen-header {
        text-align: center;
        margin-bottom: 30px;
        padding: 20px 0;
    }
    
    .zen-header h1 {
        color: #8A3033;
        font-size: 2rem;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
    }
    
    .zen-header p {
        color: #CC8F4D;
        font-size: 1rem;
        max-width: 600px;
        margin: 0 auto;
        font-weight: 300;
    }
    
    /* Icon styling */
    .zen-icon {
        font-size: 1.8rem;
        color: #CC8F4D;
        margin-bottom: 12px;
        display: inline-block;
    }
    
    /* Custom checkbox */
    .stCheckbox {
        border-radius: 4px;
        padding: 8px;
        background: rgba(204, 143, 77, 0.05);
        margin: 10px 0;
    }
    
    /* Tooltip customization */
    .stTooltip {
        color: #8A3033;
    }
    
    /* Streamlit elements overall customization */
    .stProgress .st-emotion-cache-11s8ty4 {
        background-color: rgba(204, 143, 77, 0.2) !important;
    }
    
    .stProgress .st-emotion-cache-11s8ty4 > div {
        background-color: #CC8F4D !important;
    }
    
    /* Analytics customizations */
    .stPlotlyChart {
        background: #FFFDF7;
        border-radius: 6px;
        padding: 4px;
        border: 1px solid rgba(138, 48, 51, 0.1);
    }
    
    /* Pandas dataframe styling */
    .dataframe {
        border-collapse: collapse;
        font-family: 'Nunito', sans-serif;
        font-size: 0.9rem;
    }
    
    .dataframe th {
        background-color: rgba(204, 143, 77, 0.1);
        color: #8A3033;
        padding: 8px;
        border: 1px solid rgba(138, 48, 51, 0.1);
    }
    
    .dataframe td {
        padding: 6px 8px;
        border: 1px solid rgba(138, 48, 51, 0.1);
        color: #5D4037;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: rgba(204, 143, 77, 0.03);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Zen header
    st.markdown("""
    <div class="zen-header">
        <span class="zen-icon">🍃</span>
        <h1>ZEN EXPENSE TRACKER</h1>
        <p>Mindfully manage your expenses</p>
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
