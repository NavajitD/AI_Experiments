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
from datetime import datetime, timedelta, timezone
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Set API key directly in the code
os.environ["GOOGLE_API_KEY"] = "AIzaSyDRrTvYX6F7EJUK789Yz0IQcMMbjCRXwso"

# Initialize session state variables if they don't exist
if 'predicted_category' not in st.session_state:
    st.session_state['predicted_category'] = ""
if 'category_predicted' not in st.session_state:
    st.session_state['category_predicted'] = ""
if 'form_submitted' not in st.session_state:
    st.session_state['form_submitted'] = False
if 'reset_form' not in st.session_state:
    st.session_state['reset_form'] = False
if 'shared_percentage' not in st.session_state:
    st.session_state['shared_percentage'] = 50.0
if 'shared_amount' not in st.session_state:
    st.session_state['shared_amount'] = 0.0
# Force current date on every app load
if 'force_current_date' not in st.session_state or st.session_state['force_current_date'] != datetime.now().date():
    if 'date_input' in st.session_state:
        st.session_state['date_input'] = datetime.now().date()
    st.session_state['force_current_date'] = datetime.now().date()

# Callback for expense name change
def on_expense_name_change():
    # Only trigger prediction if there's text
    if st.session_state.expense_name_input:
        predict_category(st.session_state.expense_name_input)

# Function to predict category
def predict_category(expense_name):
    if expense_name and st.session_state.get('category_predicted') != expense_name:
        with st.spinner("Predicting category..."):
            try:
                predicted_category = get_category_prediction(expense_name)
                st.session_state['predicted_category'] = predicted_category
                st.session_state['category_predicted'] = expense_name
            except Exception as e:
                st.error(f"Error predicting category: {str(e)}")
                st.session_state['predicted_category'] = "Miscellaneous"

# Function to handle form submission
def handle_form_submit():
    st.session_state['form_submitted'] = True

# Calculate shared amount based on percentage
def calculate_shared_amount():
    if 'amount_input' in st.session_state and 'shared_percentage_input' in st.session_state:
        total_amount = st.session_state['amount_input']
        percentage = st.session_state['shared_percentage_input']
        st.session_state['shared_amount_input'] = round(total_amount * percentage / 100, 2)

# Calculate shared percentage based on amount
def calculate_shared_percentage():
    if 'amount_input' in st.session_state and 'shared_amount_input' in st.session_state:
        total_amount = st.session_state['amount_input']
        shared_amount = st.session_state['shared_amount_input']
        if total_amount > 0:
            st.session_state['shared_percentage_input'] = round(shared_amount / total_amount * 100, 2)

# Function to reset the form
def reset_form():
    st.session_state['reset_form'] = True
    st.session_state['predicted_category'] = ""
    st.session_state['category_predicted'] = ""
    st.session_state['form_submitted'] = False
    # Reset date input to today's date with timezone awareness
    if 'date_input' in st.session_state:
        st.session_state['date_input'] = datetime.now(timezone.utc).date()
    # Reset shared expense values
    if 'shared_input' in st.session_state:
        st.session_state['shared_input'] = False
    if 'shared_percentage_input' in st.session_state:
        st.session_state['shared_percentage_input'] = 50.0
    if 'shared_amount_input' in st.session_state:
        st.session_state['shared_amount_input'] = 0.0
    # We can't directly set expense_name_input, but we'll use reset_form flag
    # to handle this in the UI

# Function to get category prediction from Gemini model
def get_category_prediction(expense_name):
    api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
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
    apps_script_url = "https://script.google.com/macros/s/AKfycbwISgM-mNsc6fZmKki2ImDKhsePg_Ixbcku3Ofw9_feNE9OuDUEDamLylrwK5kLB7vGZg/exec"
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Convert data to JSON string
        json_data = json.dumps(data)
        
        # Log the data being sent for debugging
        if st.session_state['debug_mode']:
            st.write(f"Sending data: {json_data}")
        
        response = requests.post(
            apps_script_url,
            data=json_data,
            headers=headers
        )
        
        # Log the response for debugging
        if st.session_state['debug_mode']:
            st.write(f"Response status code: {response.status_code}")
            st.write(f"Response content: {response.text[:100]}")  # Show first 100 chars
        
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": "error", "message": "Failed to parse response JSON"}
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
    # Hide the debug outputs by default
    if 'debug_mode' not in st.session_state:
        st.session_state['debug_mode'] = False
    
    # CSS for premium dark theme design with animated background
    st.markdown("""
    <style>
    /* Your CSS styles here */
    </style>
    """, unsafe_allow_html=True)
    
    # Create tabs for the app
    tab1, tab2, tab3 = st.tabs(["New Expense", "Trends", "Debug"])
    
    with tab1:
        # Zen header
        st.markdown("""
        <div class="zen-header">
            <span class="zen-icon">💸</span>
            <h1>Small Expense Tracker</h1>
            <p>Track spending fast with clarity</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Handle form reset
        if st.session_state['reset_form']:
            # Clear the reset flag
            st.session_state['reset_form'] = False
            # We can't modify the expense_name_input directly, but we force a rerun
            # which will show empty widgets due to the cleared category_predicted
            st.rerun()
        
        # Create a container for the form
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Create a glass card for the form
                with st.container():
                    st.markdown("""
                    <div class="glass-card">
                        <h3 class="title-font">New Expense</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Expense name input with on_change callback
                    expense_name = st.text_input(
                        "Expense name", 
                        key="expense_name_input", 
                        on_change=on_expense_name_change
                    )
                    
                    # All possible categories
                    categories = [
                        "Bike", "Auto/Cab", "Public transport", "Groceries", "Eating out", "Party", "Household supplies", "Education", "Gift", 
                        "Cinema", "Entertainment", "Liquor", "Rent/Maintenance", "Furniture", "Services", "Electricity", "Internet", "Investment", "Insurance", 
                        "Medical expenses", "Flights", "Travel", "Clothes", "Games/Sports", "Gas", "Phone", "Miscellaneous"
                    ]
                    
                    # Default to predicted category if available
                    default_category = st.session_state.get('predicted_category', categories[0]) if expense_name else categories[0]
                    default_index = categories.index(default_category) if default_category in categories else 0
                    
                    # Create layout columns before the form
                    input_col1, input_col2 = st.columns(2)
                    
                    with input_col1:
                        category_input = st.selectbox(
                            "Category", 
                            categories, 
                            index=default_index, 
                            key="category_input_outside_form"
                        )
                        
                        # Payment method
                        payment_methods = ["Cred UPI", "Credit card", "GPay UPI", "Pine Perks", "Cash", "Debit card", "Net Banking"]
                        payment_method_input = st.selectbox(
                            "Payment method", 
                            payment_methods, 
                            key="payment_method_input_outside_form"
                        )
                    
                    with input_col2:
                        # Amount in Rupees
                        amount_input = st.number_input(
                            "Amount (₹)", 
                            min_value=0.0, 
                            step=0.01, 
                            format="%.2f", 
                            key="amount_input_outside_form"
                        )
                        
                        # Date input
                        date_cols = st.columns([3, 1])
                        with date_cols[0]:
                            # Get current date with timezone awareness
                            today = datetime.now(timezone.utc).date()
                            date_input = st.date_input("Date", value=today, key="date_input_outside_form")
                        with date_cols[1]:
                            if st.button("Today", key="today_button_outside_form"):
                                st.session_state['date_input_outside_form'] = datetime.now(timezone.utc).date()
                                st.rerun()
                    
                    # Month and Year (auto-filled based on date)
                    month = date_input.strftime("%B")
                    year = date_input.year
                    
                    # Billing cycle (if Credit Card is selected)
                    if payment_method_input == "Credit card":
                        billing_cycle = get_billing_cycle(date_input)
                        st.markdown(f"""
                        <div class="info-box">
                            <strong>Billing Cycle:</strong> {billing_cycle}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        billing_cycle = ""
                    
                    # Shared expense
                    shared_input = st.checkbox("Shared expense", value=False, key="shared_input_outside_form")
                    
                    # Show additional fields if shared expense is checked
                    if shared_input:
                        shared_cols = st.columns(2)
                        
                        with shared_cols[0]:
                            shared_percentage_input = st.number_input(
                                "Your share (%)", 
                                min_value=0.0, 
                                max_value=100.0, 
                                value=50.0, 
                                step=0.1, 
                                format="%.1f",
                                key="shared_percentage_input_outside_form",
                                # Calculate shared amount when percentage changes
                                on_change=lambda: setattr(
                                    st.session_state, 
                                    'shared_amount_input_outside_form', 
                                    round(st.session_state.amount_input_outside_form * st.session_state.shared_percentage_input_outside_form / 100, 2)
                                ) if 'amount_input_outside_form' in st.session_state else None
                            )
                        
                        with shared_cols[1]:
                            shared_amount_input = st.number_input(
                                "Your amount (₹)", 
                                min_value=0.0, 
                                max_value=float(amount_input) if amount_input else 0.0,
                                value=amount_input * 0.5 if amount_input else 0.0,
                                step=0.01, 
                                format="%.2f",
                                key="shared_amount_input_outside_form",
                                # Calculate percentage when amount changes
                                on_change=lambda: setattr(
                                    st.session_state,
                                    'shared_percentage_input_outside_form',
                                    round(st.session_state.shared_amount_input_outside_form / st.session_state.amount_input_outside_form * 100, 2)
                                ) if 'amount_input_outside_form' in st.session_state and st.session_state.amount_input_outside_form > 0 else None
                            )
                            
                        # Display the calculated amount that will be submitted
                        st.markdown(f"""
                        <div class="info-box">
                            <strong>Amount to record:</strong> ₹{shared_amount_input:.2f} ({shared_percentage_input:.1f}% of ₹{amount_input:.2f})
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Now use a form just for the submit button
                    with st.form(key="expense_submit_form"):
                        # Hidden fields to carry values from outside the form
                        # These don't need to be visible but will be submitted with the form
                        st.session_state['category_input'] = st.session_state.get('category_input_outside_form', default_category)
                        st.session_state['payment_method_input'] = st.session_state.get('payment_method_input_outside_form', payment_methods[0])
                        st.session_state['amount_input'] = st.session_state.get('amount_input_outside_form', 0.0)
                        st.session_state['date_input'] = st.session_state.get('date_input_outside_form', today)
                        st.session_state['shared_input'] = st.session_state.get('shared_input_outside_form', False)
                        st.session_state['shared_percentage_input'] = st.session_state.get('shared_percentage_input_outside_form', 50.0)
                        st.session_state['shared_amount_input'] = st.session_state.get('shared_amount_input_outside_form', 0.0)
                        
                        # Submit button with callback
                        submitted = st.form_submit_button("Add expense", on_click=handle_form_submit)
                
                # Handle form submission outside the form
                if st.session_state['form_submitted']:
                    if not expense_name:
                        st.error("Please enter an expense name.")
                        st.session_state['form_submitted'] = False
                    elif 'amount_input' not in st.session_state or st.session_state['amount_input'] <= 0:
                        st.error("Amount must be greater than 0.")
                        st.session_state['form_submitted'] = False
                    else:
                        # Calculate the final amount to submit
                        final_amount = st.session_state['amount_input']
                        if st.session_state['shared_input']:
                            final_amount = st.session_state['shared_amount_input']
                        
                        # Prepare data for submission
                        data = {
                            "expenseName": expense_name,
                            "category": st.session_state['category_input'],
                            "amount": final_amount,  # Use the shared amount if applicable
                            "originalAmount": st.session_state['amount_input'],  # Store the original amount
                            "date": st.session_state['date_input'].strftime("%Y-%m-%d"),
                            "month": st.session_state['date_input'].strftime("%B"),
                            "year": st.session_state['date_input'].year,
                            "paymentMethod": st.session_state['payment_method_input'],
                            "shared": "Yes" if st.session_state['shared_input'] else "No",
                            "sharedPercentage": st.session_state['shared_percentage_input'] if st.session_state['shared_input'] else 100,
                            "billingCycle": billing_cycle if st.session_state['payment_method_input'] == "Credit card" else "",
                            "timeStamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Toggle debug mode for this submission
                        st.session_state['debug_mode'] = True
                        
                        # Submit to Google Apps Script
                        with st.spinner("Adding expense..."):
                            response = submit_to_google_apps_script(data)
                            
                            if response.get("status") == "success":
                                st.success("Expense added successfully!")
                                # Reset form using our custom reset function
                                reset_form()
                            else:
                                st.error(f"Error: {response.get('message', 'Unknown error')}")
                                st.error("Please check the Debug tab for more information.")
                                st.session_state['form_submitted'] = False

    with tab2:
        # Create analytics view
        try:
            analytics.show_analytics()
        except Exception as e:
            st.error(f"Error loading analytics: {str(e)}")
            st.info("Please check that the analytics.py file exists and is properly configured.")
    
    with tab3:
        st.header("Debug Information")
        st.write("This tab shows debugging information when submitting expenses.")
        
        # Toggle for debug mode
        st.session_state['debug_mode'] = st.checkbox("Enable Debug Mode", value=st.session_state['debug_mode'])
        
        if st.button("Test Connection to Google Apps Script"):
            with st.spinner("Testing connection..."):
                test_data = {
                    "test": True,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                response = submit_to_google_apps_script(test_data)
                st.json(response)

if __name__ == "__main__":
    main()
