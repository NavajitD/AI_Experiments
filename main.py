import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from datetime import datetime

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
    apps_script_url = "https://script.google.com/macros/s/AKfycbyfbV3TsTyNG69NZ2cBj4EFIALcds2sAvPKlrBUXSbN6qxJkk1C37fqoIXneuPubkihFA/exec"
    
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            apps_script_url,
            data=json.dumps(data),
            headers=headers
        )
        
        st.write("Response Status Code:", response.status_code)  # Debug
        st.write("Response Content:", response.text)  # Debug
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": f"HTTP Status: {response.status_code}"}
    except Exception as e:
        st.write(f"Exception: {str(e)}")  # Debug
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

# Main app function
def main():
    # Set page config
    st.set_page_config(
        page_title="Expense tracker",
        page_icon="💰",
        layout="wide"
    )
    
    # CSS for the trippy background animation
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
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
    </style>
    """, unsafe_allow_html=True)
    
    # App title
    st.title("Expense tracker")
    
    # Create a form key that will be used to clear the form
    form_key = "expense_form"
    
    # Form to capture expense details
    with st.form(form_key):
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
        category = st.selectbox("Category", categories, index=default_index, key="category_input")
        
        # Amount in Rupees
        amount = st.number_input("Amount (₹)", min_value=0.0, step=0.01, format="%.2f", key="amount_input")
        
        # Date with calendar component
        today = datetime.now().date()
        date = st.date_input("Date", value=today, key="date_input")
        
        # Month and Year (auto-filled based on date)
        month = date.strftime("%B")
        year = date.year
        
        # Payment method
        payment_methods = ["Cred UPI", "Credit card", "GPay UPI", "Cash", "Debit card", "Net Banking"]
        payment_method = st.selectbox("Payment method", payment_methods, key="payment_method_input")
        
        # Billing cycle (if Credit Card is selected)
        billing_cycle = ""
        if payment_method == "Credit card":
            billing_cycle = get_billing_cycle(date)
            st.info(f"Billing Cycle: {billing_cycle}")

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
