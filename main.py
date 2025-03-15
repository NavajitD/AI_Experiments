import streamlit as st
import requests
import json
import datetime
import pandas as pd
import google.generativeai as genai
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime

# Set the API key directly in the script
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "AIzaSyAqMFvXnZ4JLeYqySr1rkY5Ooc5pYdPmrc"  

# Retrieve the API key
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY is not set")

# Initialize Gemini model
gemini_model = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=api_key
)

# Function to get category prediction from Gemini model
def get_category_prediction(expense_name):
    prompt = f"""
    Classify the following expense into one of these categories:
    - Food
    - Groceries
    - Transportation
    - Housing
    - Utilities
    - Healthcare
    - Entertainment
    - Shopping
    - Personal Care
    - Education
    - Travel
    - Gifts
    - Investments
    - Insurance
    - Miscellaneous
    
    Expense: {expense_name}
    
    Return only the category name, nothing else.
    """
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

# Function to submit data to Google Apps Script
def submit_to_google_apps_script(data):
    # Replace with your deployed Google Apps Script web app URL
    apps_script_url = "https://script.google.com/macros/s/AKfycbxgFJ7IPoAN2uoOWW8Da6qGMsQ-mhfHvnZYGbfBrfDuuF6rdVEl0Q7NhN_oMaDVfu8Eqw/exec"
    
    try:
        response = requests.post(
            apps_script_url,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Function to get billing cycle based on date
def get_billing_cycle(date_obj):
    day = date_obj.day
    
    if day < 16:
        # Previous billing cycle
        start_month = (date_obj.replace(day=1) - datetime.timedelta(days=1)).replace(day=25)
        end_month = date_obj.replace(day=25)
    else:
        # Next billing cycle
        start_month = date_obj.replace(day=25)
        end_month = (date_obj.replace(day=28) + datetime.timedelta(days=4)).replace(day=25)
    
    start_month_str = start_month.strftime("%b")
    end_month_str = end_month.strftime("%b")
    
    return f"{start_month_str} 25 - {end_month_str} 25"

# Main app function
def main():
    # Set page config
    st.set_page_config(
        page_title="Expense Tracker",
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
    st.title("Expense Tracker")
    
    # Form to capture expense details
    with st.form("expense_form"):
        # Expense name
        expense_name = st.text_input("Expense Name", key="expense_name")
        
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
            "Food", "Groceries", "Transportation", "Housing", "Utilities",
            "Healthcare", "Entertainment", "Shopping", "Personal Care",
            "Education", "Travel", "Gifts", "Investments", "Insurance", "Miscellaneous"
        ]
        
        # Default to predicted category if available
        default_category = st.session_state.get('predicted_category', categories[0]) if expense_name else categories[0]
        category = st.selectbox("Category", categories, index=categories.index(default_category) if default_category in categories else 0)
        
        # Amount in Rupees
        amount = st.number_input("Amount (₹)", min_value=0.0, step=0.01, format="%.2f")
        
        # Date with calendar component
        today = datetime.now().date()
        date = st.date_input("Date", value=today)
        
        # Month and Year (auto-filled based on date)
        month = date.strftime("%B")
        year = date.year
        
        # Payment method
        payment_methods = ["Cash", "UPI", "Debit Card", "Credit Card", "Net Banking", "Other"]
        payment_method = st.selectbox("Payment Method", payment_methods)
        
        # Billing cycle (if Credit Card is selected)
        billing_cycle = ""
        if payment_method == "Credit Card":
            billing_cycle = get_billing_cycle(date)
            st.info(f"Billing Cycle: {billing_cycle}")
        
        # Shared expense
        shared = st.checkbox("Shared Expense", value=False)
        
        # Submit button
        submitted = st.form_submit_button("Add Expense")
        
        if submitted:
            if not expense_name:
                st.error("Please enter an expense name.")
            elif amount <= 0:
                st.error("Amount must be greater than 0.")
            else:
                # Prepare data for submission
                data = {
                    "expenseName": expense_name,
                    "category": category,
                    "amount": amount,
                    "date": date.strftime("%Y-%m-%d"),
                    "month": month,
                    "year": year,
                    "paymentMethod": payment_method,
                    "billingCycle": billing_cycle,
                    "shared": shared
                }
                
                # Submit to Google Apps Script
                with st.spinner("Adding expense..."):
                    response = submit_to_google_apps_script(data)
                    
                    if response["status"] == "success":
                        st.success("Expense added successfully!")
                        # Clear form fields
                        st.session_state['expense_name'] = ""
                        st.session_state['predicted_category'] = ""
                        st.session_state['category_predicted'] = ""
                        st.experimental_rerun()
                    else:
                        st.error(f"Error: {response['message']}")

if __name__ == "__main__":
    main()
