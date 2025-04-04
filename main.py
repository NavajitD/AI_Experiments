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
if 'debug_mode' not in st.session_state:
    st.session_state['debug_mode'] = False

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
    """Reset form fields without modifying widget-bound session state directly"""
    st.session_state['reset_form'] = True
    st.session_state['predicted_category'] = ""
    st.session_state['category_predicted'] = ""
    st.session_state['form_submitted'] = False
    st.session_state['show_split_options'] = False
    
    # Clear split related fields
    if 'split_between_input' in st.session_state:
        del st.session_state['split_between_input']
    if 'split_amount_input' in st.session_state:
        del st.session_state['split_amount_input']
    
    # Mark form for reset but don't directly modify widget values
    # This will be handled during the next rerun
    st.session_state['_form_reset_pending'] = True

# Function to update the split amount when either amount or split between changes
def update_split_amount():
    current_amount = st.session_state.get('amount_input', 0.0)
    current_split_between = st.session_state.get('split_between_input', 2)
    
    if current_amount > 0 and current_split_between > 0:
        new_split_amount = round(current_amount / current_split_between, 2)
        st.session_state['split_amount_input'] = new_split_amount

# Callback for when amount changes
def on_amount_change():
    # Update split amount if shared expense is checked
    if st.session_state.get('shared_input', False):
        update_split_amount()

# Function to handle showing/hiding split options
def toggle_split_options():
    # Update the shared expense flag
    st.session_state['show_split_options'] = st.session_state.shared_input
    
    # If turning on shared expense, initialize split amount
    if st.session_state.shared_input:
        update_split_amount()

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

# Main app function
def main():
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
        if st.session_state.get('reset_form', False):
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
                    
                    # Form for the inputs
                    with st.form(key="expense_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            category = st.selectbox("Category", categories, index=default_index, key="category_input")
                            
                            # Payment method
                            payment_methods = ["Cred UPI", "Credit card", "GPay UPI", "Pine Perks", "Cash", "Debit card", "Net Banking"]
                            payment_method = st.selectbox("Payment method", payment_methods, key="payment_method_input")
                        
                        with col2:
                            # Amount in Rupees with callback for shared expense calculation
                            amount = st.number_input("Amount (₹)", min_value=0.0, step=0.01, format="%.2f", key="amount_input", on_change=on_amount_change)
                            
                            # Date with calendar component
                            today = datetime.now().date()
                            date = st.date_input("Date", value=today, key="date_input")
                        
                        # Shared expense checkbox
                        shared = st.checkbox("Shared expense", value=False, key="shared_input", on_change=toggle_split_options)
                        
                        # Show split options if shared expense is checked
                        if st.session_state.get('shared_input', False):
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
                                    key="split_between_input",
                                    on_change=update_split_amount
                                )
                            
                            with split_col2:
                                # Get the current amount value for calculation
                                current_amount = st.session_state.get('amount_input', 0.0)
                                # Calculate default split amount
                                default_split = round(current_amount / split_between, 2) if current_amount > 0 and split_between > 0 else 0.0
                                
                                split_amount = st.number_input(
                                    "Split amount (your share in ₹)", 
                                    min_value=0.0, 
                                    max_value=float(current_amount) if current_amount > 0 else 1000000.0,
                                    value=st.session_state.get('split_amount_input', default_split),
                                    step=0.01,
                                    format="%.2f",
                                    help="Enter your portion of the expense (this will override the split calculation)",
                                    key="split_amount_input"
                                )
                            
                            # Display the effective amount to be recorded
                            if split_amount > 0:
                                st.info(f"Your share of ₹{current_amount:.2f} will be recorded as: ₹{split_amount:.2f}")
                            elif split_between > 1 and current_amount > 0:
                                calculated_amount = current_amount / split_between
                                st.info(f"Your share of ₹{current_amount:.2f} will be recorded as: ₹{calculated_amount:.2f}")
                        
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
                        
                        # Add spacer before submit button
                        st.write("")
                        
                        # Submit button at the very end of the form
                        submitted = st.form_submit_button("Add expense")
                    
                    # Handle form submission
                    if submitted:
                        if not expense_name:
                            st.error("Please enter an expense name.")
                        elif amount <= 0:
                            st.error("Amount must be greater than 0.")
                        else:
                            # Calculate the final amount based on split options if shared
                            final_amount = amount
                            original_amount = amount
                            
                            if st.session_state.get('shared_input', False):
                                # Get split values from the session state
                                split_between = st.session_state.get('split_between_input', 1)
                                split_amount = st.session_state.get('split_amount_input', 0.0)
                                
                                # Prioritize split amount if provided, otherwise use calculated split
                                if split_amount > 0:
                                    final_amount = split_amount
                                elif split_between > 1:
                                    final_amount = original_amount / split_between
                            
                            # Prepare data for submission
                            data = {
                                "expenseName": expense_name,
                                "category": category,
                                "amount": final_amount,  # Send the calculated split amount
                                "originalAmount": original_amount,  # Include the original amount for reference
                                "date": date.strftime("%Y-%m-%d"),
                                "month": date.strftime("%B"),
                                "year": date.year,
                                "paymentMethod": payment_method,
                                "shared": "Yes" if st.session_state.get('shared_input', False) else "No",
                                "billingCycle": billing_cycle if payment_method == "Credit card" else "",
                                "timeStamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            # Add split details if this is a shared expense
                            if st.session_state.get('shared_input', False):
                                data["splitBetween"] = split_between
                                data["splitAmount"] = split_amount
                            
                            # Submit to Google Apps Script
                            with st.spinner("Adding expense..."):
                                response = submit_to_google_apps_script(data)
                                
                                if response.get("status") == "success":
                                    st.success("Expense added successfully!")
                                    # Reset form using our custom reset function
                                    reset_form()
                                    # Force a rerun to clear the form
                                    st.rerun()
                                else:
                                    st.error(f"Error: {response.get('message', 'Unknown error')}")
                                    st.error("Please check the Debug tab for more information.")

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
