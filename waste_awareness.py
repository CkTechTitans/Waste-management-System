import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import pymongo
from pymongo import MongoClient
import base64
from io import BytesIO
from PIL import Image
from bson.objectid import ObjectId
import secrets
import hashlib

# MongoDB connection function (existing)
def connect_to_mongodb():
    try:
        # Replace with your actual MongoDB connection string
        client = MongoClient("mongodb://localhost:27017/")
        db = client["waste_management"]
        # Test the connection by executing a simple command
        client.admin.command('ping')
        return db
    except Exception as e:
        st.error(f"Error connecting to MongoDB: {e}")
        return None

# New admin authentication functions
def initialize_admin_accounts():
    """Initialize admin accounts if they don't exist"""
    db = connect_to_mongodb()
    if db is None:
        return
    
    admin_collection = db["admin_users"]
    
    # Create default admin if no admins exist
    if admin_collection.count_documents({}) == 0:
        # Generate a salt and hash the default password
        salt = secrets.token_hex(16)
        default_password = "admin123"  # You would change this in production
        password_hash = hashlib.sha256((default_password + salt).encode()).hexdigest()
        
        admin_user = {
            "username": "admin",
            "password_hash": password_hash,
            "salt": salt,
            "created_at": datetime.now()
        }
        
        admin_collection.insert_one(admin_user)
        st.warning("Default admin account created. Please change the password immediately.")

def verify_admin(username, password):
    """Verify admin credentials"""
    db = connect_to_mongodb()
    if db is None:
        return False
    
    admin_collection = db["admin_users"]
    admin_user = admin_collection.find_one({"username": username})
    
    if admin_user:
        salt = admin_user["salt"]
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash == admin_user["password_hash"]
    
    return False

def change_admin_password(username, current_password, new_password):
    """Change admin password"""
    if not verify_admin(username, current_password):
        return False, "Current password is incorrect"
    
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    admin_collection = db["admin_users"]
    
    # Generate new salt and hash
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((new_password + salt).encode()).hexdigest()
    
    result = admin_collection.update_one(
        {"username": username},
        {"$set": {
            "password_hash": password_hash,
            "salt": salt,
            "updated_at": datetime.now()
        }}
    )
    
    if result.modified_count > 0:
        return True, "Password updated successfully"
    else:
        return False, "Failed to update password"

# New functions for campaign management
def update_campaign_dates(voting_end_date, campaign_end_date):
    """Update campaign dates in the settings collection"""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    settings_collection = db["app_settings"]
    
    # Update or create settings document
    result = settings_collection.update_one(
        {"setting_type": "campaign_dates"},
        {"$set": {
            "voting_end_date": voting_end_date,
            "campaign_end_date": campaign_end_date,
            "updated_at": datetime.now()
        }},
        upsert=True
    )
    
    return result.acknowledged, "Campaign dates updated successfully"

def get_campaign_dates():
    """Get campaign dates from settings collection"""
    db = connect_to_mongodb()
    if db is None:
        return None, None
    
    settings_collection = db["app_settings"]
    settings = settings_collection.find_one({"setting_type": "campaign_dates"})
    
    if settings:
        return settings.get("voting_end_date"), settings.get("campaign_end_date")
    else:
        # Default dates if not set
        voting_end_date = datetime.now() + timedelta(days=7)
        campaign_end_date = voting_end_date + timedelta(days=7)
        return voting_end_date, campaign_end_date

def reset_campaign():
    """Reset the campaign - clear votes and registrations"""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    try:
        # Reset votes and registrations in cities collection
        cities_collection = db["cities"]
        cities_collection.update_many({}, {"$set": {"votes": 0, "registrations": 0}})
        
        # Clear voter records
        db["voter_records"].delete_many({})
        
        # Clear registrations
        db["registrations"].delete_many({})
        
        # Update campaign dates
        voting_end_date = datetime.now() + timedelta(days=7)
        campaign_end_date = voting_end_date + timedelta(days=7)
        update_campaign_dates(voting_end_date, campaign_end_date)
        
        return True, "Campaign reset successfully"
    except Exception as e:
        return False, f"Error resetting campaign: {str(e)}"

def add_new_city(city_name):
    """Add a new city to the database"""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    cities_collection = db["cities"]
    
    # Check if city already exists
    if cities_collection.find_one({"name": city_name}):
        return False, "City already exists"
    
    # Create new city entry
    city_data = {
        "name": city_name,
        "waste_index": random.randint(60, 95),
        "votes": 0,
        "registrations": 0
    }
    
    result = cities_collection.insert_one(city_data)
    return result.inserted_id is not None, "City added successfully"

def update_city_waste_index(city_name, waste_index):
    """Update waste index for a city"""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    cities_collection = db["cities"]
    result = cities_collection.update_one(
        {"name": city_name},
        {"$set": {"waste_index": waste_index}}
    )
    
    return result.modified_count > 0, "Waste index updated successfully"

def delete_city(city_name):
    """Delete a city from the database"""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    cities_collection = db["cities"]
    result = cities_collection.delete_one({"name": city_name})
    
    return result.deleted_count > 0, "City deleted successfully"

# Get registration stats
def get_registration_stats():
    """Get registration statistics"""
    db = connect_to_mongodb()
    if db is None:
        return None
    
    registrations_collection = db["registrations"]
    
    # Total registrations
    total_registrations = registrations_collection.count_documents({})
    
    # Registrations by city
    pipeline = [
        {"$group": {"_id": "$city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    city_stats = list(registrations_collection.aggregate(pipeline))
    
    # Time slot preferences
    pipeline = [
        {"$group": {"_id": "$time_slot", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    time_slot_stats = list(registrations_collection.aggregate(pipeline))
    
    return {
        "total": total_registrations,
        "by_city": city_stats,
        "by_time_slot": time_slot_stats
    }

# Functions for waste report management
def delete_waste_report(report_id):
    """Delete a waste report"""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    try:
        waste_reports_collection = db["waste_reports"]
        result = waste_reports_collection.delete_one({"_id": ObjectId(report_id)})
        
        return result.deleted_count > 0, "Report deleted successfully"
    except Exception as e:
        return False, f"Error deleting report: {str(e)}"

def tag_bbmp_waste_report(report_id, tag_status):
    """Tag or untag a waste report for BBMP attention"""
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    try:
        waste_reports_collection = db["waste_reports"]
        result = waste_reports_collection.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {"tag_bbmp": tag_status}}
        )
        
        return result.modified_count > 0, "Report updated successfully"
    except Exception as e:
        return False, f"Error updating report: {str(e)}"

# Modify your run_waste_awareness_app function to include the admin interface
def run_waste_awareness_app():
    # Initialize admin accounts
    initialize_admin_accounts()
    
    # Custom CSS (keep your existing CSS)
    st.markdown("""
    <style>
    .header {
        padding: 1.5rem;
        background: linear-gradient(135deg, #4CAF50, #2196F3);
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    /* ... rest of your CSS ... */
    
    /* Admin section styles */
    .admin-header {
        padding: 1rem;
        background: linear-gradient(135deg, #673AB7, #3F51B5);
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .admin-card {
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-top: 4px solid #673AB7;
        margin-bottom: 1rem;
    }
    .alert-success {
        padding: 0.75rem;
        margin-bottom: 1rem;
        border-radius: 0.25rem;
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .alert-error {
        padding: 0.75rem;
        margin-bottom: 1rem;
        border-radius: 0.25rem;
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get campaign dates from database
    voting_end_date, campaign_end_date = get_campaign_dates()
    if voting_end_date and campaign_end_date:
        st.session_state.voting_end_date = voting_end_date
        st.session_state.campaign_end_date = campaign_end_date
    
    # App header
    st.markdown("""
    <div class="header">
        <h1>City Cleanup Campaign</h1>
        <p>Vote for cities that need urgent cleanup, report waste sites, and join the community action</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for user identification (simulating login)
    if 'user_id' not in st.session_state:
        import uuid
        st.session_state.user_id = str(uuid.uuid4())
    
    # Initialize session state variables if they don't exist
    if 'campaign_phase' not in st.session_state:
        st.session_state.campaign_phase = 'voting'  # 'voting' or 'registration'

    # Fixed global deadlines instead of relative dates
    if 'voting_end_date' not in st.session_state:
        # Use a fixed date that's the same for all users and persists across refreshes
        # April 16, 2025 at 23:59:59
        st.session_state.voting_end_date = datetime(2025, 4, 26, 23, 59, 59)

    if 'campaign_end_date' not in st.session_state:
        # April 23, 2025 at 23:59:59
        st.session_state.campaign_end_date = datetime(2025, 5, 3, 23, 59, 59)

    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = datetime.now()
    
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = "Campaign"
        
    if 'feedback_message' not in st.session_state:
        st.session_state.feedback_message = None
        
    if 'feedback_type' not in st.session_state:
        st.session_state.feedback_type = None
    
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    # Initialize cities data in MongoDB if not exists
    initialize_cities_data()
    
    # Display feedback message if exists
    if st.session_state.feedback_message:
        feedback_type = st.session_state.feedback_type
        message = st.session_state.feedback_message
        
        if feedback_type == "success":
            st.markdown(f"""<div class="alert-success">{message}</div>""", unsafe_allow_html=True)
        elif feedback_type == "error":
            st.markdown(f"""<div class="alert-error">{message}</div>""", unsafe_allow_html=True)
        
        # Clear feedback after showing
        st.session_state.feedback_message = None
        st.session_state.feedback_type = None
    
    # Main app tabs
    tab_names = ["Campaign", "Community Chat", "Report Waste"]
    
    # Add Admin tab if authenticated or for login
    if st.session_state.admin_authenticated:
        tab_names.append("Admin Panel")
    else:
        tab_names.append("Admin Login")
    
    tabs = st.tabs(tab_names)
    
    
    # Tab 1: Original Campaign Functionality
    with tabs[0]:
        st.session_state.selected_tab = "Campaign"
        display_campaign_interface()
    
    # Tab 2: Community Chat - Show all waste reports
    with tabs[1]:
        st.session_state.selected_tab = "Community Chat"
        display_community_chat()
    
    # Tab 3: Report Waste Form
    with tabs[2]:
        st.session_state.selected_tab = "Report Waste"
        display_report_waste_form()
    
    # Tab 4: Admin Login or Admin Panel
    with tabs[3]:
        if st.session_state.admin_authenticated:
            display_admin_panel()
        else:
            display_admin_login()

# Add this new function for admin login
def display_admin_login():
    st.markdown("""
    <div class="admin-header">
        <h2>Admin Login</h2>
        <p>Enter your credentials to access the admin panel</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("admin_login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)
        
        if submitted:
            if username and password:
                if verify_admin(username, password):
                    st.session_state.admin_authenticated = True
                    st.session_state.admin_username = username
                    st.success("Login successful! Redirecting to admin panel...")
                    
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Please enter both username and password")

# Add this new function for admin panel
def display_admin_panel():
    st.markdown("""
    <div class="admin-header">
        <h2>Admin Control Panel</h2>
        <p>Manage campaign settings, cities, and waste reports</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Logout button
    if st.button("Logout", key="admin_logout"):
        st.session_state.admin_authenticated = False
        st.session_state.pop('admin_username', None)
        st.success("Logged out successfully!")
        st.rerun()
    
    # Admin navigation
    admin_tabs = st.tabs(["Campaign Settings", "City Management", "Registration Stats", "Waste Reports", "Account Settings"])
    
    # Tab 1: Campaign Settings
    with admin_tabs[0]:
        display_campaign_settings()
    
    # Tab 2: City Management
    with admin_tabs[1]:
        display_city_management()
    
    # Tab 3: Registration Stats
    with admin_tabs[2]:
        display_registration_stats()
    
    # Tab 4: Waste Reports Management
    with admin_tabs[3]:
        display_waste_reports_management()
    
    # Tab 5: Account Settings
    with admin_tabs[4]:
        display_account_settings()

# Add these new functions for each admin panel section
def display_campaign_settings():
    st.markdown("<h3>Campaign Settings</h3>", unsafe_allow_html=True)
    
    # Current campaign phase and dates
    current_time = datetime.now()
    campaign_phase = st.session_state.campaign_phase
    voting_end_date = st.session_state.voting_end_date
    campaign_end_date = st.session_state.campaign_end_date
    
    st.markdown(f"""
    <div class="admin-card">
        <h4>Current Campaign Status</h4>
        <p><strong>Phase:</strong> {campaign_phase.capitalize()}</p>
        <p><strong>Voting End Date:</strong> {voting_end_date.strftime('%d %b %Y, %I:%M %p')}</p>
        <p><strong>Campaign End Date:</strong> {campaign_end_date.strftime('%d %b %Y, %I:%M %p')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Update campaign dates form
    st.markdown("<h4>Update Campaign Dates</h4>", unsafe_allow_html=True)
    with st.form("update_campaign_dates_form"):
        default_date = max(voting_end_date.date(), current_time.date())  # Ensures default value >= min_value
        new_voting_end_date = st.date_input(
    "Voting End Date",
    value=default_date,
    min_value=current_time.date()
)
        new_voting_end_time = st.time_input(
            "Voting End Time",
            value=voting_end_date.time()
        )
        
        # Calculate new campaign end date (default to 7 days after voting ends)
        default_campaign_end_date = datetime.combine(new_voting_end_date, new_voting_end_time) + timedelta(days=7)
        
        new_campaign_end_date = st.date_input(
            "Campaign End Date",
            value=default_campaign_end_date.date(),
            min_value=new_voting_end_date
        )
        new_campaign_end_time = st.time_input(
            "Campaign End Time",
            value=default_campaign_end_date.time()
        )
        
        # Combine date and time
        combined_voting_end = datetime.combine(new_voting_end_date, new_voting_end_time)
        combined_campaign_end = datetime.combine(new_campaign_end_date, new_campaign_end_time)
        
        submitted = st.form_submit_button("Update Campaign Dates", use_container_width=True)
        
        if submitted:
            if combined_voting_end <= current_time:
                st.error("Voting end date must be in the future")
            elif combined_campaign_end <= combined_voting_end:
                st.error("Campaign end date must be after voting end date")
            else:
                success, message = update_campaign_dates(combined_voting_end, combined_campaign_end)
                if success:
                    st.session_state.voting_end_date = combined_voting_end
                    st.session_state.campaign_end_date = combined_campaign_end
                    st.success("Campaign dates updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to update campaign dates: {message}")
    
    # Reset campaign form
    st.markdown("<h4>Reset Campaign</h4>", unsafe_allow_html=True)
    st.warning("This will reset all votes and registrations. This action cannot be undone.")
    
    with st.form("reset_campaign_form"):
        confirm_reset = st.checkbox("I understand that this will clear all votes and registrations")
        
        submitted = st.form_submit_button("Reset Campaign", use_container_width=True)
        
        if submitted:
            if confirm_reset:
                success, message = reset_campaign()
                if success:
                    st.session_state.campaign_phase = 'voting'
                    st.success("Campaign reset successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to reset campaign: {message}")
            else:
                st.error("Please confirm that you understand the consequences of resetting the campaign")

def display_city_management():
    st.markdown("<h3>City Management</h3>", unsafe_allow_html=True)
    
    # Get cities data
    cities_data = get_cities_data()
    
    # Add new city form
    st.markdown("<h4>Add New City</h4>", unsafe_allow_html=True)
    with st.form("add_city_form"):
        new_city_name = st.text_input("City Name")
        initial_waste_index = st.slider("Initial Waste Index", min_value=1, max_value=100, value=70)
        
        submitted = st.form_submit_button("Add City", use_container_width=True)
        
        if submitted:
            if new_city_name:
                success, message = add_new_city(new_city_name)
                if success:
                    st.success(f"City '{new_city_name}' added successfully!")
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please enter a city name")
    
    # Manage existing cities
    st.markdown("<h4>Manage Existing Cities</h4>", unsafe_allow_html=True)
    
    if not cities_data:
        st.info("No cities found. Add cities using the form above.")
    else:
        # Create a table with cities data
        df = pd.DataFrame(cities_data)
        st.dataframe(df[["name", "waste_index", "votes", "registrations"]], use_container_width=True)
        
        # Form to update waste index
        with st.form("update_waste_index_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                city_to_update = st.selectbox(
                    "Select City to Update",
                    options=[city["name"] for city in cities_data]
                )
            
            with col2:
                selected_city = next((city for city in cities_data if city["name"] == city_to_update), None)
                current_waste_index = selected_city["waste_index"] if selected_city else 70
                
                new_waste_index = st.slider(
                    "New Waste Index",
                    min_value=1,
                    max_value=100,
                    value=current_waste_index
                )
            
            submitted = st.form_submit_button("Update Waste Index", use_container_width=True)
            
            if submitted:
                success, message = update_city_waste_index(city_to_update, new_waste_index)
                if success:
                    st.success(f"Waste index for '{city_to_update}' updated successfully!")
                    st.rerun()
                else:
                    st.error(message)
        
        # Form to delete city
        with st.form("delete_city_form"):
            city_to_delete = st.selectbox(
                "Select City to Delete",
                options=[city["name"] for city in cities_data],
                key="delete_city_select"
            )
            
            confirm_delete = st.checkbox("I confirm that I want to delete this city and all associated data")
            
            submitted = st.form_submit_button("Delete City", use_container_width=True)
            
            if submitted:
                if confirm_delete:
                    success, message = delete_city(city_to_delete)
                    if success:
                        st.success(f"City '{city_to_delete}' deleted successfully!")
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please confirm deletion")
def display_registration_stats():
    st.markdown("<h3>Registration Statistics</h3>", unsafe_allow_html=True)
   
    # Get registration statistics
    stats = get_registration_stats()
   
    if stats is None:
        st.error("Error connecting to database")
        return
   
    # Total registrations
    st.markdown(f"""
    <div class="admin-card">
        <h4>Total Registrations</h4>
        <p style="font-size: 2rem; font-weight: bold; text-align: center;">{stats['total']}</p>
    </div>
    """, unsafe_allow_html=True)
   
    # Registrations by city
    col1, col2 = st.columns(2)
   
    with col1:
        st.markdown("<h4>Registrations by City</h4>", unsafe_allow_html=True)
        if stats['by_city']:
            city_df = pd.DataFrame(stats['by_city']).rename(columns={"_id": "City", "count": "Registrations"})
            st.dataframe(city_df, use_container_width=True)
           
            # Create bar chart
            st.bar_chart(city_df.set_index("City"))
        else:
            st.info("No registration data by city available")
   
    with col2:
        st.markdown("<h4>Registrations by Time Slot</h4>", unsafe_allow_html=True)
        if stats['by_time_slot']:
            time_slot_df = pd.DataFrame(stats['by_time_slot']).rename(columns={"_id": "Time Slot", "count": "Registrations"})
            st.dataframe(time_slot_df, use_container_width=True)
           
            # Create pie chart using plotly
            import plotly.express as px
            fig = px.pie(time_slot_df, values="Registrations", names="Time Slot")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No registration data by time slot available")
   
    # Download registration data button
    db = connect_to_mongodb()
    if db is not None:
        registrations = list(db["registrations"].find({}, {"_id": 0}))
        if registrations:
            registrations_df = pd.DataFrame(registrations)
            
            # Convert datetime objects to strings for CSV export
            for col in registrations_df.columns:
                if registrations_df[col].dtype == 'datetime64[ns]':
                    registrations_df[col] = registrations_df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            csv = registrations_df.to_csv(index=False)
            
            st.download_button(
                label="Download Registration Data (CSV)",
                data=csv,
                file_name=f"registrations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No registration data available for download")
        
def display_waste_reports_management():
    st.markdown("<h3>Waste Reports Management</h3>", unsafe_allow_html=True)
    
    # Get waste reports
    reports = get_waste_reports()
    
    if not reports:
        st.info("No waste reports available")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_city = st.selectbox(
            "Filter by City",
            ["All Cities"] + list(set(report["city"] for report in reports)),
            key="waste_reports_city_filter"
        )
    
    with col2:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All Reports", "Tagged BBMP", "Resolved", "Pending"],
            key="waste_reports_status_filter"
        )
    
    with col3:
        filter_severity = st.selectbox(
            "Filter by Severity",
            ["All Levels", "High (4-5)", "Medium (3)", "Low (1-2)"],
            key="waste_reports_severity_filter"
        )
    
    # Apply filters
    filtered_reports = reports
    if filter_city != "All Cities":
        filtered_reports = [r for r in filtered_reports if r["city"] == filter_city]
    
    if filter_status == "Tagged BBMP":
        filtered_reports = [r for r in filtered_reports if r.get("tag_bbmp", False)]
    elif filter_status == "Resolved":
        filtered_reports = [r for r in filtered_reports if r.get("resolved", False)]
    elif filter_status == "Pending":
        filtered_reports = [r for r in filtered_reports if not r.get("resolved", False)]
    
    if filter_severity == "High (4-5)":
        filtered_reports = [r for r in filtered_reports if r.get("severity", 3) >= 4]
    elif filter_severity == "Medium (3)":
        filtered_reports = [r for r in filtered_reports if r.get("severity", 3) == 3]
    elif filter_severity == "Low (1-2)":
        filtered_reports = [r for r in filtered_reports if r.get("severity", 3) <= 2]
    
    # Display reports count
    st.markdown(f"### {len(filtered_reports)} Waste Reports")
    
    # Display each report with admin actions
    for report in filtered_reports:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Report title and meta info
                st.markdown(f"""
                <h4>{report['title']}</h4>
                <p>
                    <strong>Location:</strong> {report['city']} - {report['location']} | 
                    <strong>Severity:</strong> {report.get('severity', 3)}/5 | 
                    <strong>Upvotes:</strong> {report.get('upvotes', 0)} | 
                    <strong>Comments:</strong> {len(report.get('comments', []))}
                </p>
                <p>{report['description'][:100]}{'...' if len(report['description']) > 100 else ''}</p>
                <p><strong>Status:</strong> {
                    'Resolved' if report.get('resolved', False) else 
                    'Tagged for BBMP' if report.get('tag_bbmp', False) else 
                    'Pending'
                }</p>
                """, unsafe_allow_html=True)
                
                # Show image if available
                if 'image' in report and report['image']:
                    try:
                        image_data = base64.b64decode(report['image'])
                        image = Image.open(BytesIO(image_data))
                        st.image(image, caption="Waste Report Image", width=300)
                    except Exception as e:
                        st.error(f"Error displaying image: {e}")
            
            with col2:
                # Admin actions
                report_id = str(report['_id'])
                
                # Tag for BBMP button
                bbmp_tagged = report.get('tag_bbmp', False)
                if bbmp_tagged:
                    if st.button(f"Untag from BBMP", key=f"untag_{report_id}"):
                        success, message = tag_bbmp_waste_report(report_id, False)
                        if success:
                            st.session_state.feedback_message = "Report untagged from BBMP"
                            st.session_state.feedback_type = "success"
                            st.session_state.current_page = 'waste_reports' 
                            st.rerun()
                        else:
                            st.session_state.feedback_message = message
                            st.session_state.feedback_type = "error"
                            st.session_state.current_page = 'waste_reports' 
                            st.rerun()
                else:
                    if st.button(f"Tag for BBMP", key=f"tag_{report_id}"):
                        success, message = tag_bbmp_waste_report(report_id, True)
                        if success:
                            st.session_state.feedback_message = "Report tagged for BBMP"
                            st.session_state.feedback_type = "success"
                            st.session_state.current_page = 'waste_reports' 
                            st.rerun()
                        else:
                            st.session_state.feedback_message = message
                            st.session_state.feedback_type = "error"
                            st.session_state.current_page = 'waste_reports' 
                            st.rerun()
                
                # Mark as resolved button
                resolved = report.get('resolved', False)
                if resolved:
                    if st.button(f"Mark as Unresolved", key=f"unresolve_{report_id}"):
                        db = connect_to_mongodb()
                        if db is not None:
                            result = db["waste_reports"].update_one(
                                {"_id": ObjectId(report_id)},
                                {"$set": {"resolved": False}}
                            )
                            if result.modified_count > 0:
                                st.session_state.feedback_message = "Report marked as unresolved"
                                st.session_state.feedback_type = "success"
                                st.session_state.current_page = 'waste_reports' 
                                st.rerun()
                else:
                    if st.button(f"Mark as Resolved", key=f"resolve_{report_id}"):
                        db = connect_to_mongodb()
                        if db is not None:
                            result = db["waste_reports"].update_one(
                                {"_id": ObjectId(report_id)},
                                {"$set": {"resolved": True}}
                            )
                            if result.modified_count > 0:
                                st.session_state.feedback_message = "Report marked as resolved"
                                st.session_state.feedback_type = "success"
                                st.session_state.current_page = 'waste_reports' 
                                st.rerun()
                
                # Delete report button - FIXED DELETE FUNCTIONALITY
                delete_key = f"delete_requested_{report_id}"
                
                if not st.session_state.get(delete_key, False):
                    if st.button(f"Delete Report", key=f"delete_{report_id}"):
                        st.session_state[delete_key] = True
                        st.session_state.current_page = 'waste_reports' 
                        st.rerun()
                else:
                    st.warning("Are you sure you want to delete this report?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Confirm Delete", key=f"confirm_delete_{report_id}"):
                            success, message = delete_waste_report(report_id)
                            if success:
                                st.session_state.feedback_message = "Report deleted successfully"
                                st.session_state.feedback_type = "success"
                                st.session_state.current_page = 'waste_reports' 
                                if delete_key in st.session_state:
                                    del st.session_state[delete_key]
                                st.session_state.current_page = 'waste_reports' 
                                st.rerun()
                            else:
                                st.session_state.feedback_message = message
                                st.session_state.feedback_type = "error"
                                st.session_state.current_page = 'waste_reports' 
                                st.rerun()
                    with col2:
                        if st.button("Cancel", key=f"cancel_delete_{report_id}"):
                            if delete_key in st.session_state:
                                del st.session_state[delete_key]
                            st.session_state.current_page = 'waste_reports' 
                            st.rerun()
            
            st.markdown("<hr>", unsafe_allow_html=True)
    
    # Export reports to CSV
    if filtered_reports:
        reports_df = pd.DataFrame([
            {
                'Title': r['title'],
                'City': r['city'],
                'Location': r['location'],
                'Description': r['description'],
                'Severity': r.get('severity', 3),
                'Upvotes': r.get('upvotes', 0),
                'Comments': len(r.get('comments', [])),
                'Status': 'Resolved' if r.get('resolved', False) else 'Tagged for BBMP' if r.get('tag_bbmp', False) else 'Pending',
                'Reported On': r.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
            }
            for r in filtered_reports
        ])
        
        csv = reports_df.to_csv(index=False)
        
        st.download_button(
            label="Export Reports (CSV)",
            data=csv,
            file_name=f"waste_reports_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
def display_account_settings():
    st.markdown("<h3>Account Settings</h3>", unsafe_allow_html=True)
    
    # Change password form
    st.markdown("<h4>Change Admin Password</h4>", unsafe_allow_html=True)
    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submitted = st.form_submit_button("Change Password", use_container_width=True)
        
        if submitted:
            if not current_password or not new_password or not confirm_password:
                st.error("Please fill in all fields")
            elif new_password != confirm_password:
                st.error("New passwords do not match")
            elif len(new_password) < 8:
                st.error("New password must be at least 8 characters long")
            else:
                success, message = change_admin_password(
                    st.session_state.admin_username,
                    current_password,
                    new_password
                )
                
                if success:
                    st.success(message)
                else:
                    st.error(message)

# Function to fetch waste reports
def get_waste_reports():
    db = connect_to_mongodb()
    if db is None:
        return []
    
    try:
        waste_reports_collection = db["waste_reports"]
        reports = list(waste_reports_collection.find().sort("created_at", pymongo.DESCENDING))
        return reports
    except Exception as e:
        st.error(f"Error retrieving waste reports: {e}")
        return []

# Functions for the original campaign tabs
def initialize_cities_data():
    db = connect_to_mongodb()
    if db is None:
        return
    
    cities_collection = db["cities"]
    
    # Only initialize if the collection is empty
    if cities_collection.count_documents({}) == 0:
        # Sample initial data
        cities_data = [
            {"name": "Bangalore", "waste_index": 85, "votes": 0, "registrations": 0},
            {"name": "Mumbai", "waste_index": 78, "votes": 0, "registrations": 0},
            {"name": "Chennai", "waste_index": 72, "votes": 0, "registrations": 0},
            {"name": "Delhi", "waste_index": 90, "votes": 0, "registrations": 0},
            {"name": "Kolkata", "waste_index": 82, "votes": 0, "registrations": 0},
            {"name": "Hyderabad", "waste_index": 75, "votes": 0, "registrations": 0},
            {"name": "Pune", "waste_index": 70, "votes": 0, "registrations": 0},
            {"name": "Ahmedabad", "waste_index": 80, "votes": 0, "registrations": 0}
        ]
        
        cities_collection.insert_many(cities_data)

def get_cities_data():
    db = connect_to_mongodb()
    if db is None:
        return []
    
    cities_collection = db["cities"]
    cities = list(cities_collection.find())
    
    return cities

def record_vote(city_name):
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    # Get user ID from session state
    user_id = st.session_state.user_id
    
    # Check if user has already voted
    voter_records = db["voter_records"]
    existing_vote = voter_records.find_one({"user_id": user_id})
    
    if existing_vote:
        # If user changing their vote, decrement the old city's vote count
        if existing_vote["city"] != city_name:
            # Decrement the previous vote
            db["cities"].update_one(
                {"name": existing_vote["city"]},
                {"$inc": {"votes": -1}}
            )
            
            # Update the vote record
            voter_records.update_one(
                {"user_id": user_id},
                {"$set": {"city": city_name}}
            )
            
            # Increment the new city's vote count
            db["cities"].update_one(
                {"name": city_name},
                {"$inc": {"votes": 1}}
            )
            
            return True, "Vote changed successfully!"
        else:
            return False, "You have already voted for this city"
    else:
        # Record new vote
        voter_records.insert_one({
            "user_id": user_id,
            "city": city_name,
            "timestamp": datetime.now()
        })
        
        # Increment city's vote count
        db["cities"].update_one(
            {"name": city_name},
            {"$inc": {"votes": 1}}
        )
        
        return True, "Vote recorded successfully!"

def record_registration(form_data):
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    # Add user ID and timestamp
    form_data["user_id"] = st.session_state.user_id
    form_data["timestamp"] = datetime.now()
    
    # Insert into registrations collection
    registrations = db["registrations"]
    result = registrations.insert_one(form_data)
    
    if result.inserted_id:
        # Increment city's registration count
        db["cities"].update_one(
            {"name": form_data["city"]},
            {"$inc": {"registrations": 1}}
        )
        return True, "Registration successful!"
    else:
        return False, "Registration failed"

def record_waste_report(report_data):
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    # Add user ID and timestamp
    report_data["user_id"] = st.session_state.user_id
    report_data["created_at"] = datetime.now()
    report_data["upvotes"] = 0
    report_data["comments"] = []
    
    # Insert into waste_reports collection
    waste_reports = db["waste_reports"]
    result = waste_reports.insert_one(report_data)
    
    if result.inserted_id:
        return True, "Waste report submitted successfully!"
    else:
        return False, "Failed to submit waste report"

def upvote_report(report_id):
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    waste_reports = db["waste_reports"]
    result = waste_reports.update_one(
        {"_id": ObjectId(report_id)},
        {"$inc": {"upvotes": 1}}
    )
    
    if result.modified_count > 0:
        return True, "Upvoted successfully!"
    else:
        return False, "Failed to upvote"

def add_comment(report_id, comment_text):
    db = connect_to_mongodb()
    if db is None:
        return False, "Database connection error"
    
    comment = {
        "user_id": st.session_state.user_id,
        "text": comment_text,
        "timestamp": datetime.now()
    }
    
    waste_reports = db["waste_reports"]
    result = waste_reports.update_one(
        {"_id": ObjectId(report_id)},
        {"$push": {"comments": comment}}
    )
    
    if result.modified_count > 0:
        return True, "Comment added successfully!"
    else:
        return False, "Failed to add comment"

def display_campaign_interface():
    # Check campaign phase based on current date
    current_time = datetime.now()
    if current_time > st.session_state.campaign_end_date:
        st.session_state.campaign_phase = 'ended'
    elif current_time > st.session_state.voting_end_date:
        st.session_state.campaign_phase = 'registration'
    else:
        st.session_state.campaign_phase = 'voting'
    
    # Display appropriate interface based on campaign phase
    if st.session_state.campaign_phase == 'voting':
        display_voting_interface()
    elif st.session_state.campaign_phase == 'registration':
        display_registration_interface()
    else:  # campaign_phase == 'ended'
        display_campaign_ended()

def display_voting_interface():
    st.subheader("Vote for Cities Needing Cleanup")
    
    # Calculate time remaining for voting phase
    time_remaining = st.session_state.voting_end_date - datetime.now()
    days = time_remaining.days
    hours = time_remaining.seconds // 3600
    minutes = (time_remaining.seconds % 3600) // 60
    
    st.markdown(f"""
    <div style="padding: 10px; background-color: #f0f8ff; border-left: 5px solid #2196F3; margin-bottom: 20px;">
        <h3 style="margin:0; color: #1976D2;">Voting Phase</h3>
        <p>Time remaining: {days} days, {hours} hours, {minutes} minutes</p>
        <p>Vote for the city you believe needs the most urgent waste management attention.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get cities data from MongoDB
    cities_data = get_cities_data()
    
    # Sort cities by waste index (descending)
    sorted_cities = sorted(cities_data, key=lambda x: x['waste_index'], reverse=True)
    
    # Create columns for city cards
    col1, col2 = st.columns(2)
    
    for i, city in enumerate(sorted_cities):
        with col1 if i % 2 == 0 else col2:
            # Create a card for each city
            waste_level = "High" if city['waste_index'] >= 80 else "Medium" if city['waste_index'] >= 60 else "Low"
            waste_color = "#e53935" if waste_level == "High" else "#fb8c00" if waste_level == "Medium" else "#43a047"
            
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-top: 4px solid {waste_color};">
                <h3 style="margin-top:0;">{city['name']}</h3>
                <p><strong>Waste Index:</strong> <span style="color:{waste_color};">{city['waste_index']} ({waste_level})</span></p>
                <p><strong>Current Votes:</strong> {city['votes']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Vote button for this city
            if st.button(f"Vote for {city['name']}", key=f"vote_{city['name']}", use_container_width=True):
                success, message = record_vote(city['name'])
                if success:
                    st.session_state.feedback_message = message
                    st.session_state.feedback_type = "success"
                    st.rerun()
                else:
                    st.session_state.feedback_message = message
                    st.session_state.feedback_type = "error"
                    st.rerun()

def display_registration_interface():
    st.subheader("Register for Cleanup Activities")
    
    # Calculate time remaining for registration phase
    time_remaining = st.session_state.campaign_end_date - datetime.now()
    days = time_remaining.days
    hours = time_remaining.seconds // 3600
    minutes = (time_remaining.seconds % 3600) // 60
    
    st.markdown(f"""
    <div style="padding: 10px; background-color: #f0fff0; border-left: 5px solid #4CAF50; margin-bottom: 20px;">
        <h3 style="margin:0; color: #2E7D32;">Registration Phase</h3>
        <p>Time remaining: {days} days, {hours} hours, {minutes} minutes</p>
        <p>The voting phase has ended. Now you can register for cleanup activities in your city.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get cities data from MongoDB
    cities_data = get_cities_data()
    
    # Sort cities by votes (descending)
    sorted_cities = sorted(cities_data, key=lambda x: x['votes'], reverse=True)
    
    # Display winner announcement for the top voted city
    winner = sorted_cities[0] if sorted_cities else None
    if winner:
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; margin-bottom: 20px; background: linear-gradient(135deg, #4CAF50, #8BC34A); color: white;">
            <h2 style="margin-top:0; text-align: center;">🏆 {winner['name']} received the most votes! 🏆</h2>
            <p style="text-align: center;">With {winner['votes']} votes, {winner['name']} has been selected as the primary focus for our cleanup campaign.</p>
            <p style="text-align: center;">However, you can still register for cleanup activities in any city of your choice.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Registration form
    st.markdown("<h3>Registration Form</h3>", unsafe_allow_html=True)
    
    with st.form("cleanup_registration"):
        # Create columns for form layout
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            phone = st.text_input("Phone Number")
        
        with col2:
            city = st.selectbox("Select City", [city['name'] for city in sorted_cities])
            age_group = st.selectbox("Age Group", ["Under 18", "18-24", "25-34", "35-44", "45-54", "55+"])
            time_slot = st.selectbox("Preferred Time Slot", ["Morning (8 AM - 12 PM)", "Afternoon (12 PM - 4 PM)", "Evening (4 PM - 8 PM)"])
        
        experience = st.radio("Previous Cleanup Experience", ["Yes", "No"])
        
        interests = st.multiselect(
            "Areas of Interest",
            ["Waste Collection", "Waste Segregation", "Public Awareness", "Recycling Education", "Community Outreach"]
        )
        
        additional_info = st.text_area("Any additional information or special skills you'd like to share")
        
        agree_terms = st.checkbox("I agree to participate and follow all safety guidelines")
        
        submit_button = st.form_submit_button("Submit Registration", use_container_width=True)
        
        if submit_button:
            if not (name and email and phone and agree_terms):
                st.error("Please fill in all required fields and agree to the terms")
            else:
                # Prepare form data
                form_data = {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "city": city,
                    "age_group": age_group,
                    "time_slot": time_slot,
                    "experience": experience,
                    "interests": interests,
                    "additional_info": additional_info
                }
                
                # Record registration in MongoDB
                success, message = record_registration(form_data)
                if success:
                    st.session_state.feedback_message = message
                    st.session_state.feedback_type = "success"
                    st.rerun()
                else:
                    st.session_state.feedback_message = message
                    st.session_state.feedback_type = "error"
                    st.rerun()

def display_campaign_ended():
    st.subheader("Campaign Ended")
    
    st.markdown(f"""
    <div style="padding: 10px; background-color: #f5f5f5; border-left: 5px solid #9e9e9e; margin-bottom: 20px;">
        <h3 style="margin:0; color: #616161;">Campaign Completed</h3>
        <p>Thank you for your participation! The waste management campaign has concluded.</p>
        <p>We are now reviewing the results and planning for implementation.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get cities data from MongoDB
    cities_data = get_cities_data()
    
    # Sort cities by votes (descending)
    sorted_cities = sorted(cities_data, key=lambda x: x['votes'], reverse=True)
    
    # Display final results
    st.markdown("<h3>Final Results</h3>", unsafe_allow_html=True)
    
    # Create a DataFrame for display
    if sorted_cities:
        results_df = pd.DataFrame([
            {
                "City": city["name"],
                "Votes": city["votes"],
                "Registrations": city["registrations"],
                "Waste Index": city["waste_index"]
            }
            for city in sorted_cities
        ])
        
        st.dataframe(results_df, use_container_width=True)
        
        # Create bar chart for votes
        st.subheader("Votes by City")
        chart_data = pd.DataFrame({
            "City": [city["name"] for city in sorted_cities],
            "Votes": [city["votes"] for city in sorted_cities]
        })
        st.bar_chart(chart_data.set_index("City"))
        
        # Create bar chart for registrations
        st.subheader("Registrations by City")
        reg_data = pd.DataFrame({
            "City": [city["name"] for city in sorted_cities],
            "Registrations": [city["registrations"] for city in sorted_cities]
        })
        st.bar_chart(reg_data.set_index("City"))
        
        # Display winner announcement
        winner = sorted_cities[0]
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; margin-bottom: 20px; background: linear-gradient(135deg, #9C27B0, #673AB7); color: white;">
            <h2 style="margin-top:0; text-align: center;">🏆 Final Winner: {winner['name']} 🏆</h2>
            <p style="text-align: center;">With {winner['votes']} votes and {winner['registrations']} volunteer registrations, {winner['name']} was selected as the primary focus for our cleanup campaign.</p>
            <p style="text-align: center;">Implementation of waste management solutions has begun. Thank you to all participants!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display next steps
        st.markdown("""
        <h3>Next Steps</h3>
        <ul>
            <li>The cleanup activities and waste management solutions are being implemented in the winning city.</li>
            <li>All registered volunteers will be contacted through email for coordination.</li>
            <li>Follow-up surveys and reports will be shared to track progress.</li>
            <li>Stay tuned for the next campaign announcement!</li>
        </ul>
        """, unsafe_allow_html=True)
    else:
        st.info("No cities data available")

def display_community_chat():
    st.markdown("""
    <div style="padding: 10px; background-color: #fff8e1; border-left: 5px solid #ffc107; margin-bottom: 20px;">
        <h3 style="margin:0; color: #ff6f00;">Community Discussion</h3>
        <p>View waste reports from your community and join the discussion to address waste management issues.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get waste reports from MongoDB
    db = connect_to_mongodb()
    if db is None:
        st.error("Failed to connect to database")
        return
    
    waste_reports_collection = db["waste_reports"]
    reports = list(waste_reports_collection.find().sort("created_at", pymongo.DESCENDING))
    
    if not reports:
        st.info("No waste reports have been submitted yet. Be the first to report!")
    else:
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            filter_city = st.selectbox(
                "Filter by City",
                ["All Cities"] + list(set(report["city"] for report in reports))
            )
        
        with col2:
            sort_by = st.selectbox(
                "Sort By",
                ["Latest", "Most Upvotes", "Highest Severity"]
            )
        
        # Apply filters and sorting
        filtered_reports = reports
        if filter_city != "All Cities":
            filtered_reports = [r for r in filtered_reports if r["city"] == filter_city]
        
        if sort_by == "Latest":
            filtered_reports = sorted(filtered_reports, key=lambda x: x.get("created_at", datetime.now()), reverse=True)
        elif sort_by == "Most Upvotes":
            filtered_reports = sorted(filtered_reports, key=lambda x: x.get("upvotes", 0), reverse=True)
        elif sort_by == "Highest Severity":
            filtered_reports = sorted(filtered_reports, key=lambda x: x.get("severity", 3), reverse=True)
        
        # Display reports
        for report in filtered_reports:
            with st.container():
                # Report header with title and meta info
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <h3>{report['title']}</h3>
                    <p>
                        <strong>Location:</strong> {report['city']} - {report['location']} | 
                        <strong>Severity:</strong> {report.get('severity', 3)}/5 | 
                        <strong>Reported:</strong> {report.get('created_at', datetime.now()).strftime('%d %b %Y')}
                    </p>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Status badge
                    status = "Resolved" if report.get("resolved", False) else "BBMP Tagged" if report.get("tag_bbmp", False) else "Pending"
                    status_color = "#43a047" if status == "Resolved" else "#ff9800" if status == "BBMP Tagged" else "#757575"
                    
                    st.markdown(f"""
                    <div style="background-color: {status_color}; color: white; padding: 5px 10px; border-radius: 15px; text-align: center; margin-top: 10px;">
                        <strong>{status}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Report description
                st.markdown(report['description'])
                
                # Display image if available
                if 'image' in report and report['image']:
                    try:
                        image_data = base64.b64decode(report['image'])
                        image = Image.open(BytesIO(image_data))
                        st.image(image, width=400)
                    except Exception as e:
                        st.error(f"Error displaying image: {e}")
                
                # Upvote button and count
                col1, col2 = st.columns([1, 5])
                
                with col1:
                    report_id = str(report['_id'])
                    upvotes = report.get('upvotes', 0)
                    
                    if st.button(f"👍 {upvotes}", key=f"upvote_{report_id}"):
                        success, message = upvote_report(report_id)
                        if success:
                            st.session_state.feedback_message = message
                            st.session_state.feedback_type = "success"
                            st.rerun()
                        else:
                            st.session_state.feedback_message = message
                            st.session_state.feedback_type = "error"
                            st.rerun()
                
                # Comments section
                st.markdown("#### Comments")
                
                comments = report.get('comments', [])
                if not comments:
                    st.markdown("*No comments yet*")
                else:
                    for comment in comments:
                        st.markdown(f"""
                        <div style="border-left: 2px solid #e0e0e0; padding-left: 10px; margin-bottom: 10px;">
                            <p style="margin-bottom: 0; font-size: 0.9em; color: #757575;">
                                Anonymous User • {comment.get('timestamp', datetime.now()).strftime('%d %b %Y, %I:%M %p')}
                            </p>
                            <p style="margin-top: 5px;">{comment['text']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Add comment form
                with st.form(key=f"comment_form_{report_id}", clear_on_submit=True):
                    comment_text = st.text_area("Add a comment", key=f"comment_input_{report_id}", height=100)
                    submit_comment = st.form_submit_button("Post Comment")
                    
                    if submit_comment and comment_text:
                        success, message = add_comment(report_id, comment_text)
                        if success:
                            st.session_state.feedback_message = message
                            st.session_state.feedback_type = "success"
                            st.rerun()
                        else:
                            st.session_state.feedback_message = message
                            st.session_state.feedback_type = "error"
                            st.rerun()
                
                st.markdown("<hr>", unsafe_allow_html=True)

def image_to_base64(image):
    buffered = BytesIO()
    if image.mode == 'RGBA':  # Add this check
        image = image.convert('RGB')  # Add this conversion
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# NEW FUNCTION: Display report waste form
def display_report_waste_form():
    st.markdown("<h2 style='text-align: center; margin-bottom: 1.5rem;'>Report Waste Site</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <p style="text-align: center; margin-bottom: 2rem;">
        Found a waste site that needs attention? Report it here and tag BBMP for immediate action.
        Your report will be visible to the community and relevant authorities.
    </p>
    """, unsafe_allow_html=True)
    
    # Report waste form
    with st.form("report_waste_form"):
        # Basic report details
        st.markdown("### Report Details")
        title = st.text_input("Title of the Report")
        description = st.text_area("Describe the waste issue")
        
        col1, col2 = st.columns(2)
        with col1:
            cities = [city["name"] for city in get_cities_data()]
            city = st.selectbox("City", cities)
        with col2:
            location = st.text_input("Specific Location (Area, Street, Landmark)")
        
        # Photo upload
        st.markdown("### Upload Photo")
        uploaded_file = st.file_uploader("Upload a photo of the waste site", type=["jpg", "jpeg", "png"])
        
        # Preview uploaded image
        # Preview uploaded image
        if uploaded_file is not None:
    # Display preview of uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Preview of uploaded image", width=300)
    
    # Convert the image to base64 for storing in MongoDB
            buffered = BytesIO()
            if image.mode == 'RGBA':  # Add this check
                image = image.convert('RGB')  # Add this conversion
            image.save(buffered, format="JPEG")
            image_data = base64.b64encode(buffered.getvalue()).decode()
        
        # Tag BBMP option
        tag_bbmp = st.checkbox("Tag BBMP for immediate attention")
        
        # Additional information
        st.markdown("### Additional Information")
        waste_type = st.multiselect(
            "Type of Waste",
            ["Plastic", "Food/Organic", "Construction Debris", "Medical Waste", "Industrial Waste", "Mixed Waste", "Other"]
        )
        
        severity = st.slider("Severity Level", min_value=1, max_value=5, value=3, help="1 = Minor, 5 = Severe")
        
        st.markdown("""
        <p style="font-size: 0.9rem; color: #555;">
            By submitting this report, you agree to share this information with the community and relevant authorities.
        </p>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Submit Report", use_container_width=True)
        
        if submitted:
            if title and description and city and location:
                # Process the uploaded image
                image_data = None
                if uploaded_file is not None:
                    image = Image.open(uploaded_file)
                    # Resize image to reduce storage requirements
                    image = image.resize((800, int(800 * image.height / image.width)))
                    image_data = image_to_base64(image)
                
                # Create report data for MongoDB
                report_data = {
                    "username": "Anonymous",  # Would be replaced with logged-in user in real app
                    "title": title,
                    "description": description,
                    "city": city,
                    "location": location,
                    "waste_type": waste_type,
                    "severity": severity,
                    "tag_bbmp": tag_bbmp,
                    "resolved": False,
                    "upvotes": 0,
                    "comments": [],
                    "timestamp": datetime.now()
                }
                
                # Add image if available
                if image_data:
                    report_data["image"] = image_data
                
                # Add report to MongoDB
                if record_waste_report(report_data):
                    st.success("Thank you! Your waste site report has been submitted successfully.")
                    if tag_bbmp:
                        st.info("BBMP has been notified about this waste site.")
                    st.balloons()
                    
                    # Switch to community chat tab to see the report
                    st.session_state.selected_tab = "Community Chat"
                    st.rerun()
                else:
                    st.error("Failed to submit report. Please try again.")
            else:
                st.error("Please fill in all required fields.")

def get_waste_index_color(index):
    if index >= 80:
        return "#FF5252"  # Red for severe waste issues
    elif index >= 60:
        return "#FFC107"  # Amber for moderate waste issues
    else:
        return "#4CAF50"  # Green for lower waste issues

# Main function to run the app
if __name__ == "__main__":
    st.set_page_config(
        page_title="Waste Awareness App",
        page_icon="♻️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    
    run_waste_awareness_app()