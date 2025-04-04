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
if 'show_split_options' not in st.session_state:
    st.session_state['show_split_options'] = False

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

def reset_form():
    st.session_state['reset_form'] = True
    st.session_state['predicted_category'] = ""
    st.session_state['category_predicted'] = ""
    st.session_state['form_submitted'] = False
    st.session_state['show_split_options'] = False
    # Reset date input to today's date
    if 'date_input' in st.session_state:
        st.session_state['date_input'] = datetime.now().date()
    # We can't directly set expense_name_input, but we'll use reset_form flag
    # to handle this in the UI

# Callback for shared expense checkbox
def on_shared_expense_change():
    st.session_state['show_split_options'] = st.session_state.shared_input

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

# Function to calculate final amount based on split options
def calculate_final_amount(original_amount, split_between, split_amount):
    # If split amount is provided, use it directly
    if split_amount > 0:
        return split_amount
    
    # If split between is provided, divide the original amount
    if split_between > 1:
        return original_amount / split_between
    
    # If neither is properly set, return the original amount
    return original_amount

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
                        <h3 class="title-font">Add Expense</h3>
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
                        "Cinema", "Entertainment", "Rent/Maintenance", "Furniture", "Services", "Electricity", "Internet", "Investment", "Insurance", 
                        "Medical expenses", "Flights", "Travel", "Clothes", "Gas", "Phone", "Miscellaneous"
                    ]
                    
                    # Default to predicted category if available
                    default_category = st.session_state.get('predicted_category', categories[0]) if expense_name else categories[0]
                    default_index = categories.index(default_category) if default_category in categories else 0
                    
                    # Form for the rest of the inputs
                    with st.form(key="expense_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            category = st.selectbox("Category", categories, index=default_index, key="category_input")
                            
                            # Payment method
                            payment_methods = ["Cred UPI", "Credit card", "GPay UPI", "Pine Perks", "Cash", "Debit card", "Net Banking"]
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
                        
                        # Shared expense with on_change callback
                        shared = st.checkbox("Shared expense", value=False, key="shared_input", on_change=on_shared_expense_change)
                        
                        # Show split options if shared expense is checked
                        if shared:
                            split_col1, split_col2 = st.columns(2)
                            
                            with split_col1:
                                # Only allow natural numbers for split between
                                split_between = st.number_input(
                                    "Split between (number of people)", 
                                    min_value=1, 
                                    max_value=100, 
                                    value=2, 
                                    step=1,
                                    help="Enter the total number of people sharing this expense",
                                    key="split_between_input"
                                )
                            
                            with split_col2:
                                split_amount = st.number_input(
                                    "Split amount (your share in ₹)", 
                                    min_value=0.0, 
                                    max_value=float(amount) if amount > 0 else 1000000.0,
                                    value=0.0 if amount <= 0 else round(amount / 2, 2),
                                    step=0.01,
                                    format="%.2f",
                                    help="Enter your portion of the expense (this will override the split calculation)",
                                    key="split_amount_input"
                                )
                            
                            # Display the effective amount to be recorded
                            effective_amount = calculate_final_amount(amount, split_between, split_amount)
                            
                            if split_amount > 0:
                                st.info(f"Your share of ₹{amount:.2f} will be recorded as: ₹{split_amount:.2f}")
                            elif split_between > 1:
                                st.info(f"Your share of ₹{amount:.2f} will be recorded as: ₹{amount / split_between:.2f}")
                
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
                        # Calculate the final amount based on split options if this is a shared expense
                        final_amount = st.session_state['amount_input']
                        original_amount = st.session_state['amount_input']
                        
                        if st.session_state['shared_input']:
                            split_between = st.session_state.get('split_between_input', 1)
                            split_amount = st.session_state.get('split_amount_input', 0.0)
                            
                            final_amount = calculate_final_amount(original_amount, split_between, split_amount)
                        
                        # Prepare data for submission
                        data = {
                            "expenseName": expense_name,
                            "category": st.session_state['category_input'],
                            "amount": final_amount,  # Send the calculated split amount
                            "originalAmount": original_amount,  # Include the original amount for reference
                            "date": st.session_state['date_input'].strftime("%Y-%m-%d"),
                            "month": st.session_state['date_input'].strftime("%B"),
                            "year": st.session_state['date_input'].year,
                            "paymentMethod": st.session_state['payment_method_input'],
                            "shared": "Yes" if st.session_state['shared_input'] else "No",
                            "billingCycle": billing_cycle if st.session_state['payment_method_input'] == "Credit card" else "",
                            "timeStamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Add split details if this is a shared expense
                        if st.session_state['shared_input']:
                            data["splitBetween"] = st.session_state.get('split_between_input', 1)
                            data["splitAmount"] = st.session_state.get('split_amount_input', 0.0)
                        
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
        analytics.show_analytics()
    
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
