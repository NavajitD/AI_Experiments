import streamlit as st
import requests
import json
from datetime import datetime, timedelta

# Set page config as the first Streamlit command
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="✦",
    layout="wide"
)

# Initialize session state variables
if 'debug_mode' not in st.session_state:
    st.session_state['debug_mode'] = False

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

# Function to reset the form
def reset_form():
    for key in list(st.session_state.keys()):
        if key not in ['debug_mode'] and key.endswith('_input'):
            if key in st.session_state:
                del st.session_state[key]
    st.rerun()

# Main app
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
        
        # Expense name input - OUTSIDE form
        expense_name = st.text_input("Expense name", key="expense_name_input")
        
        # All possible categories
        categories = [
            "Bike", "Auto/Cab", "Public transport", "Groceries", "Eating out", "Party", "Household supplies", "Education", "Gift", 
            "Cinema", "Entertainment", "Rent/Maintenance", "Furniture", "Services", "Electricity", "Internet", "Investment", "Insurance", 
            "Medical expenses", "Flights", "Travel", "Clothes", "Gas", "Phone", "Miscellaneous"
        ]
        
        # Shared expense checkbox - OUTSIDE form
        shared = st.checkbox("Shared expense", key="shared_input")
        
        # Form for the inputs - USING DYNAMIC KEY APPROACH
        with st.form(key="expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                category = st.selectbox("Category", categories, key="category_input")
                
                # Payment method
                payment_methods = ["Cred UPI", "Credit card", "GPay UPI", "Pine Perks", "Cash", "Debit card", "Net Banking"]
                payment_method = st.selectbox("Payment method", payment_methods, key="payment_method_input")
            
            with col2:
                amount = st.number_input("Amount (₹)", min_value=0.0, step=0.01, format="%.2f", key="amount_input")
                
                # Date with calendar component
                today = datetime.now().date()
                date = st.date_input("Date", value=today, key="date_input")
            
            # Split options (conditionally shown)
            if shared:
                st.write("Split options")
                split_col1, split_col2 = st.columns(2)
                
                with split_col1:
                    split_between = st.number_input(
                        "Split between (number of people)", 
                        min_value=1, 
                        value=2, 
                        step=1, 
                        key="split_between_input"
                    )
                
                with split_col2:
                    # Calculate split amount - this will be recalculated on every form interaction
                    calculated_split = round(amount / split_between, 2) if amount > 0 and split_between > 0 else 0.0
                    
                    # Use a dynamic key that depends on amount and split_between values
                    # This forces Streamlit to recreate the widget with updated defaults when these values change
                    dynamic_key = f"split_amount_{amount}_{split_between}"
                    
                    split_amount = st.number_input(
                        "Split Amount (₹)", 
                        min_value=0.0, 
                        value=calculated_split,  # This will update as amount/split_between change
                        format="%.2f", 
                        key=dynamic_key
                    )
                    
                    # Store the value in our standard session state key for consistency
                    st.session_state['split_amount_input'] = split_amount
                
                # Display calculation formula to make it clear
                if amount > 0 and split_between > 1:
                    st.info(f"Split Amount = {amount:.2f} ÷ {split_between} = {calculated_split:.2f}")
            
            # Billing cycle (if Credit Card is selected)
            if payment_method == "Credit card":
                billing_cycle = get_billing_cycle(date)
                st.markdown(f"""
                <div class="info-box">
                    <strong>Billing Cycle:</strong> {billing_cycle}
                </div>
                """, unsafe_allow_html=True)
            
            # Add a spacer before submit button
            st.write("")
            
            # Submit button at the very end of the form
            submitted = st.form_submit_button("Add expense")
        
        # Handle form submission outside the form
        if submitted:
            if not expense_name:
                st.error("Please enter an expense name.")
            elif amount <= 0:
                st.error("Amount must be greater than 0.")
            else:
                # Calculate the final amount based on split options if shared
                final_amount = amount
                original_amount = amount
                
                if shared:
                    # Get split values - for split_amount, get from dynamic key or session state
                    split_between = st.session_state.get('split_between_input', 1)
                    
                    # Try to find the dynamic key value in session state
                    dynamic_key = f"split_amount_{amount}_{split_between}"
                    split_amount = st.session_state.get(dynamic_key, 0.0)
                    
                    # If not found in dynamic key, try the standard key
                    if split_amount == 0.0:
                        split_amount = st.session_state.get('split_amount_input', 0.0)
                    
                    # If still not found, calculate it
                    if split_amount == 0.0 and amount > 0 and split_between > 1:
                        split_amount = round(amount / split_between, 2)
                    
                    # Use the split amount for the final amount
                    final_amount = split_amount
                
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
                    "shared": "Yes" if shared else "No",
                    "billingCycle": get_billing_cycle(date) if payment_method == "Credit card" else "",
                    "timeStamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Add split details if this is a shared expense
                if shared:
                    data["splitBetween"] = split_between
                    data["splitAmount"] = split_amount
                
                # Submit to Google Apps Script
                with st.spinner("Adding expense..."):
                    response = submit_to_google_apps_script(data)
                    
                    if response.get("status") == "success":
                        st.success("Expense added successfully!")
                        # Reset form
                        reset_form()
                    else:
                        st.error(f"Error: {response.get('message', 'Unknown error')}")
                        st.error("Please check the Debug tab for more information.")
    
    with tab2:
        st.title("Trends")
        st.write("Analytics will be shown here.")
    
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
