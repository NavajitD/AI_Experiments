import streamlit as st
import requests
import json
from datetime import datetime, timedelta

# Set page config - must be the first Streamlit command
st.set_page_config(page_title="Expense Tracker", page_icon="✦", layout="wide")

# Import analytics AFTER setting page config
# Using a function import to prevent code in analytics.py from running at import time
from analytics import show_analytics

# Initialize variables in session state
if 'debug_mode' not in st.session_state:
    st.session_state['debug_mode'] = False

# Function to get billing cycle
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

# Reset form fields
def reset_form():
    for key in list(st.session_state.keys()):
        if key not in ['debug_mode'] and key.endswith('_input'):
            if key in st.session_state:
                del st.session_state[key]

def main():
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["New Expense", "Trends", "Debug"])
    
    with tab1:
        # Header
        st.title("Small Expense Tracker")
        st.write("Track spending fast with clarity")
        
        # Basic input fields
        expense_name = st.text_input("Expense name", key="expense_name_input")
        
        # Categories
        categories = [
            "Miscellaneous", "Bike", "Auto/Cab", "Public transport", "Groceries", "Eating out", 
            "Party", "Household supplies", "Education", "Gift", "Cinema", "Entertainment", 
            "Rent/Maintenance", "Furniture", "Services", "Electricity", "Internet", "Investment", 
            "Insurance", "Medical expenses", "Flights", "Travel", "Clothes", "Gas", "Phone"
        ]
        
        # Create two columns for inputs
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox("Category", categories, key="category_input")
            payment_methods = ["Cred UPI", "Credit card", "GPay UPI", "Pine Perks", "Cash", "Debit card", "Net Banking"]
            payment_method = st.selectbox("Payment method", payment_methods, key="payment_method_input")
        
        with col2:
            amount = st.number_input("Amount (₹)", min_value=0.0, step=0.01, format="%.2f", key="amount_input")
            date = st.date_input("Date", value=datetime.now().date(), key="date_input")
        
        # Shared expense checkbox
        shared = st.checkbox("Shared expense", key="shared_input")
        
        # Show split options if shared expense is checked
        if shared:
            split_col1, split_col2 = st.columns(2)
            
            with split_col1:
                split_between = st.number_input("Split between (number of people)", min_value=1, value=2, step=1, key="split_between_input")
            
            with split_col2:
                # Calculate default split amount
                if amount > 0 and split_between > 0:
                    default_split = amount / split_between
                else:
                    default_split = 0.0
                
                split_amount = st.number_input("Split Amount (₹)", min_value=0.0, value=default_split, format="%.2f", key="split_amount_input")
            
            # Display calculation
            if amount > 0 and split_between > 1:
                st.info(f"Split Amount = {amount:.2f} ÷ {split_between} = {default_split:.2f}")
        
        # Credit card billing cycle
        if payment_method == "Credit card":
            billing_cycle = get_billing_cycle(date)
            st.info(f"Billing Cycle: {billing_cycle}")
        
        # Add expense button outside of any form
        if st.button("Add expense", use_container_width=True, key="add_expense_button"):
            if not expense_name:
                st.error("Please enter an expense name.")
            elif amount <= 0:
                st.error("Amount must be greater than 0.")
            else:
                # Calculate final amount
                final_amount = amount
                original_amount = amount
                
                if shared:
                    # Use split amount if provided
                    split_amount_value = st.session_state.get('split_amount_input', 0.0)
                    if split_amount_value > 0:
                        final_amount = split_amount_value
                
                # Prepare data for submission
                data = {
                    "expenseName": expense_name,
                    "category": category,
                    "amount": final_amount,
                    "originalAmount": original_amount,
                    "date": date.strftime("%Y-%m-%d"),
                    "month": date.strftime("%B"),
                    "year": date.year,
                    "paymentMethod": payment_method,
                    "shared": "Yes" if shared else "No",
                    "billingCycle": get_billing_cycle(date) if payment_method == "Credit card" else "",
                    "timeStamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Add split details if shared expense
                if shared:
                    data["splitBetween"] = split_between
                    data["splitAmount"] = split_amount_value
                
                # Submit to Google Apps Script
                with st.spinner("Adding expense..."):
                    response = submit_to_google_apps_script(data)
                    
                    if response.get("status") == "success":
                        st.success("Expense added successfully!")
                        reset_form()
                        st.rerun()
                    else:
                        st.error(f"Error: {response.get('message', 'Unknown error')}")
                        st.error("Please check the Debug tab for more information.")
    
    with tab2:
        # Call the analytics function
        show_analytics()
    
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
