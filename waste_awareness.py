import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
import base64
import plotly.express as px
import uuid
import json

# Import the styles module
from styles import main_css, admin_css, public_reports_css

# Import database operations
from database2 import (
    connect_to_mongodb,
    initialize_admin_accounts,
    verify_admin,
    change_admin_password,
    update_campaign_dates,
    get_campaign_dates,
    reset_campaign,
    add_new_city,
    update_city_waste_index,
    delete_city,
    get_registration_stats,
    delete_waste_report,
    tag_bbmp_waste_report,
    get_waste_reports,
    get_cities_data,
    record_vote,
    record_registration,
    record_waste_report,
    upvote_report,
    add_comment,
    initialize_cities_data,
    resolve_waste_report,
)

# Initialize session state variables if they don't exist
if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False
if 'admin_username' not in st.session_state:
    st.session_state.admin_username = ""
if 'feedback_message' not in st.session_state:
    st.session_state.feedback_message = None
if 'feedback_type' not in st.session_state:
    st.session_state.feedback_type = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'voted_city' not in st.session_state:
    st.session_state.voted_city = None
if 'registered' not in st.session_state:
    st.session_state.registered = False


def display_admin_login():
    """Handle admin login form"""
    with st.form("admin_login"):
        st.subheader("Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if verify_admin(username, password):
                st.session_state.admin_authenticated = True
                st.session_state.admin_username = username
                st.session_state.feedback_message = "Login successful!"
                st.session_state.feedback_type = "success"
                st.rerun()
            else:
                st.error("Invalid username or password")


def display_admin_dashboard():
    """Display admin dashboard with campaign dates and reset option"""
    st.subheader("Admin Dashboard")
    
    try:
        voting_end, campaign_end = get_campaign_dates()
        st.markdown(f"""
        <div class="admin-card">
            <h4>Campaign Dates</h4>
            <p>Voting Ends: {voting_end.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Campaign Ends: {campaign_end.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Form to update campaign dates
        with st.form("update_dates_form"):
            st.subheader("Update Campaign Dates")
            col1, col2 = st.columns(2)
            with col1:
                new_voting_end = st.date_input("New Voting End Date", voting_end)
            with col2:
                new_campaign_end = st.date_input("New Campaign End Date", campaign_end)
            
            update_dates_submitted = st.form_submit_button("Update Dates")
            if update_dates_submitted:
                try:
                    # Convert date-only to datetime with time (00:00:00)
                    new_voting_end_dt = datetime.combine(new_voting_end, datetime.min.time())
                    new_campaign_end_dt = datetime.combine(new_campaign_end, datetime.min.time())
                    
                    if new_voting_end_dt >= datetime.now() and new_campaign_end_dt > new_voting_end_dt:
                        update_campaign_dates(new_voting_end_dt, new_campaign_end_dt)
                        st.success("Campaign dates updated successfully.")
                        st.rerun()
                    else:
                        st.error("Invalid dates. Voting end must be in the future, and campaign end must be after voting end.")
                except Exception as e:
                    st.error(f"Error updating campaign dates: {e}")
    except Exception as e:
        st.error(f"Error retrieving campaign dates: {e}")
        st.markdown("""
        <div class="admin-card">
            <h4>Campaign Dates</h4>
            <p>Error retrieving dates. Please check database connection.</p>
        </div>
        """, unsafe_allow_html=True)

    if st.button("Reset Campaign (Votes & Registrations)"):
        try:
            reset_campaign()
            st.success("Campaign data reset successfully.")
            st.rerun()
        except Exception as e:
            st.error(f"Error resetting campaign: {e}")


def display_manage_cities():
    """Display interface for adding, updating, and deleting cities"""
    st.subheader("Manage Cities")

    with st.form("add_city_form"):
        st.subheader("Add New City")
        new_city_name = st.text_input("City Name")
        add_submitted = st.form_submit_button("Add City")
        if add_submitted and new_city_name:
            try:
                success, message = add_new_city(new_city_name)
                if success:
                    st.success(message)
                else:
                    st.error(message)
                st.rerun()
            except Exception as e:
                st.error(f"Error adding city: {e}")

    st.markdown("<hr>", unsafe_allow_html=True)

    try:
        cities_data = get_cities_data()
        if cities_data and len(cities_data) > 0:
            st.subheader("Current Cities")
            cities_df = pd.DataFrame(cities_data)
            cities_df = cities_df[["name", "waste_index", "votes", "registrations"]]
            st.dataframe(cities_df)

            st.subheader("Update City Waste Index")
            with st.form("update_waste_index_form"):
                city_to_update = st.selectbox("Select City to Update", [city["name"] for city in cities_data])
                new_waste_index = st.number_input("New Waste Index (0-100)", min_value=0, max_value=100, step=1)
                update_submitted = st.form_submit_button("Update Index")
                if update_submitted:
                    success, message = update_city_waste_index(city_to_update, new_waste_index)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                    st.rerun()

            st.subheader("Delete City")
            with st.form("delete_city_form"):
                city_to_delete = st.selectbox("Select City to Delete", [city["name"] for city in cities_data])
                delete_submitted = st.form_submit_button("Delete City")
                if delete_submitted:
                    success, message = delete_city(city_to_delete)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                    st.rerun()
        else:
            st.info("No cities available.")
    except Exception as e:
        st.error(f"Error retrieving city data: {e}")


def display_registration_stats():
    """Display registration statistics with visualizations"""
    st.subheader("Registration Statistics")
    
    try:
        stats = get_registration_stats()
        if stats and stats.get('total', 0) > 0:
            st.markdown(f"<h4>Total Registrations: {stats['total']}</h4>", unsafe_allow_html=True)

            if stats.get('by_city', []):
                df_by_city = pd.DataFrame(stats['by_city']).rename(columns={"_id": "City", "count": "Registrations"})
                st.subheader("Registrations by City")
                st.dataframe(df_by_city)
                fig_city = px.bar(df_by_city, x="City", y="Registrations", title="Registrations per City")
                st.plotly_chart(fig_city)

            if stats.get('by_time_slot', []):
                df_by_time_slot = pd.DataFrame(stats['by_time_slot']).rename(columns={"_id": "Time Slot", "count": "Registrations"})
                st.subheader("Registrations by Time Slot")
                st.dataframe(df_by_time_slot)
                fig_time_slot = px.pie(df_by_time_slot, names="Time Slot", values="Registrations", title="Registrations per Time Slot")
                st.plotly_chart(fig_time_slot)

            # Download Raw Data
            try:
                registrations_data = connect_to_mongodb()["registrations"].find()
                registrations_df = pd.DataFrame(list(registrations_data))
                if not registrations_df.empty:
                    registrations_df = registrations_df.drop(columns=['_id', 'user_id', 'timestamp'], errors='ignore')
                    csv = registrations_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Raw Registrations Data (CSV)",
                        data=csv,
                        file_name="registrations.csv",
                        mime="text/csv",
                    )
            except Exception as e:
                st.error(f"Error preparing download data: {e}")
        else:
            st.info("No registration data available yet.")
    except Exception as e:
        st.error(f"Error retrieving registration statistics: {e}")


def display_waste_reports_management():
    """Display interface for managing waste reports"""
    st.subheader("Waste Reports Management")
    
    try:
        reports = get_waste_reports()
        if not reports or len(reports) == 0:
            st.info("No waste reports submitted yet.")
            return

        # Filter controls
        cities = ["All Cities"] + list(set(report["city"] for report in reports))
        statuses = ["All", "Pending", "Tagged BBMP", "Resolved"]
        severities = ["All", 1, 2, 3, 4, 5]

        col1, col2, col3 = st.columns(3)
        with col1:
            filter_city = st.selectbox("Filter by City", cities)
        with col2:
            filter_status = st.selectbox("Filter by Status", statuses)
        with col3:
            filter_severity = st.selectbox("Filter by Severity", severities)

        # Apply filters
        filtered_reports = reports
        if filter_city != "All Cities":
            filtered_reports = [r for r in filtered_reports if r["city"] == filter_city]
        if filter_status != "All":
            if filter_status == "Pending":
                filtered_reports = [r for r in filtered_reports if not r.get("tag_bbmp", False) and not r.get("resolved", False)]
            elif filter_status == "Tagged BBMP":
                filtered_reports = [r for r in filtered_reports if r.get("tag_bbmp", False)]
            elif filter_status == "Resolved":
                filtered_reports = [r for r in filtered_reports if r.get("resolved", False)]
        if filter_severity != "All":
            filtered_reports = [r for r in filtered_reports if r.get("severity", 3) == filter_severity]

        st.markdown(f"**{len(filtered_reports)}** reports found.")

        # Display reports
        for report in filtered_reports:
            with st.container():
                st.markdown(f"<h4>{report['title']}</h4>", unsafe_allow_html=True)
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"Location: {report['city']} - {report['location']}")
                    st.markdown(f"Severity: {report.get('severity', 3)}/5 | Upvotes: {report.get('upvotes', 0)} | Comments: {len(report.get('comments', []))}")
                    st.markdown(f"Reported on: {report.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}")
                    short_description = report['description'][:100] + "..." if len(report['description']) > 100 else report['description']
                    st.markdown(short_description)
                    
                    # Display image if available
                    if 'image' in report and report['image']:
                        try:
                            image_data = base64.b64decode(report['image'])
                            image = Image.open(BytesIO(image_data))
                            st.image(image, width=200)
                        except Exception as e:
                            st.error(f"Error displaying image: {e}")
                
                with col2:
                    report_id = str(report['_id'])
                    st.markdown("<div class='report-actions'>", unsafe_allow_html=True)
                    
                    # BBMP Tag button
                    if st.button(f"{'Untag' if report.get('tag_bbmp', False) else 'Tag'} BBMP", key=f"bbmp_{report_id}"):
                        success, message = tag_bbmp_waste_report(report_id, not report.get('tag_bbmp', False))
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    # Resolve button
                    if st.button(f"{'Unresolve' if report.get('resolved', False) else 'Resolve'}", key=f"resolve_{report_id}"):
                        success, message = resolve_waste_report(report_id, not report.get('resolved', False))
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    # Delete button
                    if st.button("Delete", key=f"delete_{report_id}"):
                        success, message = delete_waste_report(report_id)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Comments section
                if report.get('comments', []):
                    with st.expander(f"View {len(report.get('comments', []))} Comments"):
                        for i, comment in enumerate(report.get('comments', [])):
                            st.markdown(f"**Comment {i+1}** - {comment.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}")
                            st.markdown(f"_{comment.get('text', '')}_")
                            st.markdown("---")
                
                st.markdown("<hr>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error in waste reports management: {e}")


def handle_password_change():
    """Handle admin password change form"""
    st.subheader("Change Admin Password")
    
    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submitted = st.form_submit_button("Change Password")
        if submitted:
            if new_password != confirm_password:
                st.error("New password and confirmation do not match.")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long.")
            else:
                success, message = change_admin_password(st.session_state.admin_username, current_password, new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)


def admin_section():
    """Admin section with authentication and management tools"""
    st.markdown(admin_css, unsafe_allow_html=True)
    st.markdown("<h2 class='admin-header'>Admin Panel</h2>", unsafe_allow_html=True)
    
    if not st.session_state.admin_authenticated:
        display_admin_login()
    else:
        # Display logout button
        if st.button("Logout"):
            st.session_state.admin_authenticated = False
            st.session_state.admin_username = ""
            st.rerun()
            
        # Display feedback message if there is one
        if st.session_state.feedback_message:
            feedback_type = st.session_state.feedback_type if st.session_state.feedback_type else "info"
            st.markdown(f"<p class='admin-message {feedback_type}'>{st.session_state.feedback_message}</p>", unsafe_allow_html=True)
            st.session_state.feedback_message = None
            st.session_state.feedback_type = None
        
        # Admin tabs
        admin_tabs = st.tabs([
            "📊 Dashboard", 
            "🏙️ Manage Cities", 
            "📈 Registration Stats",
            "🗑️ Waste Reports",
            "🔐 Settings"
        ])
        
        with admin_tabs[0]:
            display_admin_dashboard()
            
        with admin_tabs[1]:
            display_manage_cities()
            
        with admin_tabs[2]:
            display_registration_stats()
            
        with admin_tabs[3]:
            display_waste_reports_management()
            
        with admin_tabs[4]:
            handle_password_change()


def render_waste_map():
    """Render a waste severity map using plotly"""
    try:
        cities_data = get_cities_data()
        if not cities_data:
            st.info("No cities data available to display on the map.")
            return
            
        # Updated coordinates to include Bangalore areas and use Bengaluru as alternative name
        city_coordinates = {
            # Major cities
             "Koramangala": [12.9352, 77.6245],
            "HSR Layout": [12.9086, 77.6476],
            "Indiranagar": [12.9784, 77.6408],
             "Bengaluru": [12.9716, 77.5946],
            # Bangalore areas
            "Whitefield": [12.9698, 77.7500],
            "Electronic City": [12.8446, 77.6613],
            "Marathahalli": [12.9592, 77.7010],
            "Hebbal": [13.0358, 77.5946],
            "JP Nagar": [12.9077, 77.5751],
            "Banashankari": [12.9250, 77.5470],
            "Jayanagar": [12.9300, 77.5833],
            "rrnagar": [12.9261, 77.5235],
        }
        
        # Prepare data for map
        map_data = []
        missing_cities = []
        
        for city in cities_data:
            city_name = city["name"]
            if city_name in city_coordinates:
                map_data.append({
                    "city": city_name,
                    "waste_index": city["waste_index"],
                    "lat": city_coordinates[city_name][0],
                    "lon": city_coordinates[city_name][1],
                    "votes": city["votes"],
                    "registrations": city["registrations"]
                })
            else:
                missing_cities.append(city_name)
            
        if not map_data:
            st.info("No geographical data available for the cities.")
            return
            
        # Show which cities were missing coordinates, if any
        if missing_cities:
            st.warning(f"Missing coordinates for: {', '.join(missing_cities)}")
            
        df_map = pd.DataFrame(map_data)
        
        # Create map
        fig = px.scatter_mapbox(
            df_map,
            lat="lat",
            lon="lon",
            color="waste_index",
            size="votes",  # Consider a minimum size for visibility when votes are 0
            hover_name="city",
            hover_data=["waste_index", "votes", "registrations"],
            color_continuous_scale=px.colors.sequential.Plasma,
            size_max=15,
            zoom=10,  # Increased zoom level to better see Bangalore areas
            center={"lat": 12.9716, "lon": 77.5946},  # Center on Bangalore
            title="Waste Severity Map"
        )
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
            coloraxis_colorbar=dict(
                title="Waste Index",
                tickvals=[0, 25, 50, 75, 100],
                ticktext=["Very Low", "Low", "Medium", "High", "Very High"]
            )
        )
        
        # Ensure minimum marker size for visibility when votes are 0
        for trace in fig.data:
            trace.marker.size = [max(5, s) for s in trace.marker.size]
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering waste map: {e}")
        st.exception(e)  # Show full traceback for debugging

import streamlit as st
import base64
from io import BytesIO
from datetime import datetime
def display_waste_reports_public():
    """Display waste reports for public view with improved UI"""
    
    try:
        # Add some custom CSS for better styling
        st.markdown("""
        <style>
            .report-card {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                border-left: 5px solid #4CAF50;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .report-title {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 8px;
            }
            .report-location {
                color: #34495e;
                font-size: 16px;
                margin-bottom: 10px;
            }
            .report-metadata {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin-bottom: 15px;
                font-size: 14px;
                color: #555;
            }
            .report-description {
                background-color: white;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 15px;
                border-left: 3px solid #ddd;
            }
            .tag {
                display: inline-block;
                padding: 3px 10px;
                border-radius: 15px;
                font-size: 12px;
                font-weight: bold;
                margin-right: 8px;
            }
            .bbmp-tag {
                background-color: #3498db;
                color: white;
            }
            .resolved-tag {
                background-color: #2ecc71;
                color: white;
            }
            .pending-tag {
                background-color: #f39c12;
                color: white;
            }
            .severity-indicator {
                display: inline-flex;
                align-items: center;
            }
            .severity-dot {
                height: 10px;
                width: 10px;
                border-radius: 50%;
                display: inline-block;
                margin-right: 3px;
            }
            .upvote-btn {
                background-color: #f1f1f1;
                border: none;
                border-radius: 20px;
                padding: 5px 15px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            .upvote-btn:hover {
                background-color: #e1e1e1;
            }
            .comment-box {
                background-color: #f1f1f1;
                padding: 10px 15px;
                border-radius: 8px;
                margin-bottom: 10px;
            }
            .filter-container {
                background-color: white;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .section-header {
                margin-top: 30px;
                margin-bottom: 20px;
                color: #2c3e50;
                border-bottom: 2px solid #4CAF50;
                padding-bottom: 10px;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Get all reports
        reports = get_waste_reports()
        if not reports:
            st.info("No waste reports have been submitted yet.")
            return

        # Extract cities for filter
        cities = ["All Cities"] + sorted(list(set(report["city"] for report in reports)))

        # Filters in a nicer container
        st.markdown("### 🔍 Filter Reports")
        with st.container():
            st.markdown('<div class="filter-container">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                filter_city = st.selectbox("City", cities, key="public_city_filter")
            
            with col2:
                filter_status = st.selectbox("Status", ["All", "Pending", "Tagged for BBMP", "Resolved"], key="public_status_filter")
            
            with col3:
                sort_by = st.selectbox("Sort By", ["Newest First", "Oldest First", "Most Upvotes", "Severity (High to Low)"])
            
            st.markdown('</div>', unsafe_allow_html=True)

        # Apply filters
        filtered_reports = reports
        if filter_city != "All Cities":
            filtered_reports = [r for r in filtered_reports if r["city"] == filter_city]

        if filter_status != "All":
            if filter_status == "Pending":
                filtered_reports = [r for r in filtered_reports if not r.get("tag_bbmp", False) and not r.get("resolved", False)]
            elif filter_status == "Tagged for BBMP":
                filtered_reports = [r for r in filtered_reports if r.get("tag_bbmp", False)]
            elif filter_status == "Resolved":
                filtered_reports = [r for r in filtered_reports if r.get("resolved", False)]

        # Apply sorting
        if sort_by == "Newest First":
            filtered_reports = sorted(filtered_reports, key=lambda x: x.get('created_at', datetime.now()), reverse=True)
        elif sort_by == "Oldest First":
            filtered_reports = sorted(filtered_reports, key=lambda x: x.get('created_at', datetime.now()))
        elif sort_by == "Most Upvotes":
            filtered_reports = sorted(filtered_reports, key=lambda x: x.get('upvotes', 0), reverse=True)
        elif sort_by == "Severity (High to Low)":
            filtered_reports = sorted(filtered_reports, key=lambda x: x.get('severity', 0), reverse=True)

        # Show report count with better formatting
        st.markdown(f"<h3 class='section-header'>📋 Showing {len(filtered_reports)} waste reports</h3>", unsafe_allow_html=True)

        # Display reports with improved UI
        for report in filtered_reports:
            report_id = str(report['_id'])
            
            with st.container():
                st.markdown(f'<div class="report-card">', unsafe_allow_html=True)
                
                # Report header
                st.markdown(f'<div class="report-title">{report["title"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="report-location">📍 {report["city"]} - {report["location"]}</div>', unsafe_allow_html=True)
                
                # Status tags
                tags_html = '<div style="margin-bottom: 10px;">'
                if report.get('tag_bbmp', False) and not report.get('resolved', False):
                    tags_html += '<span class="tag bbmp-tag">BBMP Tagged</span>'
                elif report.get('resolved', False):
                    tags_html += '<span class="tag resolved-tag">Resolved</span>'
                else:
                    tags_html += '<span class="tag pending-tag">Pending</span>'
                tags_html += '</div>'
                st.markdown(tags_html, unsafe_allow_html=True)
                
                # Report metadata
                severity = report.get('severity', 3)
                severity_color = {
                    1: "#c9e3c3",
                    2: "#a5d28d",
                    3: "#ffeb99", 
                    4: "#ffa07a",
                    5: "#ff6961"
                }.get(severity, "#ffeb99")
                
                st.markdown(f"""
                <div class="report-metadata">
                    <span class="severity-indicator">
                        Severity: 
                        <span class="severity-dot" style="background-color: {severity_color};"></span>
                        {severity}/5
                    </span>
                    <span>👍 {report.get('upvotes', 0)} Upvotes</span>
                    <span>💬 {len(report.get('comments', []))} Comments</span>
                    <span>📅 Reported: {report.get('created_at', datetime.now()).strftime('%Y-%m-%d')}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Description
                st.markdown(f"""
                <div class="report-description">
                    {report['description']}
                </div>
                """, unsafe_allow_html=True)
                
                # Display image if available
                if 'image' in report and report['image']:
                    try:
                        image_data = base64.b64decode(report['image'])
                        image = Image.open(BytesIO(image_data))
                        st.image(image, width=300)
                    except Exception as e:
                        st.error(f"Error displaying image: {e}")
                
                # Upvote and Comment Actions
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    upvote_btn = st.button(f"👍 Upvote ({report.get('upvotes', 0)})", key=f"upvote_{report_id}")
                    if upvote_btn:
                        success, message = upvote_report(report_id, st.session_state.user_id)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                with col2:
                    with st.expander("💬 Add a comment"):
                        with st.form(key=f"comment_form_{report_id}"):
                            comment_text = st.text_area("Your comment", key=f"comment_text_{report_id}")
                            submit_comment = st.form_submit_button("Post Comment")
                            if submit_comment and comment_text:
                                success, message = add_comment(report_id, comment_text, st.session_state.user_id)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                
                # Display comments
                if report.get('comments', []):
                    with st.expander(f"View {len(report.get('comments', []))} Comments"):
                        for comment in report.get('comments', []):
                            st.markdown(f"""
                            <div class="comment-box">
                                <strong>Anonymous</strong> · {comment.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M')}
                                <p>{comment.get('text', '')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"An error occurred: {e}")

def display_report_form():
    """Display the waste report submission form with improved UI"""
    st.markdown("<h3>Report Waste Issue</h3>", unsafe_allow_html=True)
    
    # Introduction text
    st.markdown("""
    <div style="background-color: #e8f5e9; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <p style="margin-bottom: 0;">Help improve your city by reporting waste issues. Your reports help authorities identify problem areas.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("waste_report_form"):
        title = st.text_input("Title of the Issue", placeholder="E.g., 'Garbage piling up near MG Road'")
        
        cities_data = get_cities_data()
        city_names = [city["name"] for city in cities_data]
        city = st.selectbox("City", city_names)
        
        location = st.text_input("Specific Location", placeholder="Address, landmark, or area")
        description = st.text_area("Describe the waste issue", placeholder="Provide details about the waste issue, when you noticed it, and any other relevant information.")
        
        # Improved severity selection with visual indicators
        st.markdown("""
        <p style="margin-bottom: 5px;">Severity of the Issue</p>
        <div style="margin-bottom: 10px; font-size: 13px; color: #666;">
            1 = Minor (cosmetic issue), 5 = Severe (health hazard)
        </div>
        """, unsafe_allow_html=True)
        
        severity = st.slider("", 1, 5, 3, label_visibility="collapsed")
        
        # Show severity description based on selection
        severity_descriptions = {
            1: "Minor issue, mostly cosmetic",
            2: "Small amount of waste, not urgent",
            3: "Moderate issue, needs attention",
            4: "Significant waste problem, urgent attention needed",
            5: "Severe issue, potential health hazard"
        }
        
        severity_colors = {
            1: "#C5E1A5",
            2: "#AED581",
            3: "#FFF59D",
            4: "#FFB74D",
            5: "#EF9A9A"
        }
        
        st.markdown(f"""
        <div style="background-color: {severity_colors[severity]}; padding: 8px 15px; border-radius: 8px; margin-bottom: 15px;">
            <p style="margin: 0; font-weight: 500;">Level {severity}: {severity_descriptions[severity]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Upload image with preview
        st.markdown("### Add a photo (recommended)")
        st.markdown("""
        <div style="font-size: 13px; color: #666; margin-bottom: 10px;">
            Adding a photo helps others understand the issue better
        </div>
        """, unsafe_allow_html=True)
        
        image_file = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        
        if image_file is not None:
            try:
                image = Image.open(image_file)
                st.image(image, caption="Image preview", use_column_width=True)
            except Exception as e:
                st.error(f"Error displaying preview: {e}")
        
        # Submit button with improved styling
        submit_col1, submit_col2 = st.columns([3, 1])
        with submit_col1:
            submitted = st.form_submit_button("Post Report", use_container_width=True)
        with submit_col2:
            st.markdown("") # Spacer
        
        if submitted:
            if not title or not location or not description:
                st.error("Please fill in all required fields")
            else:
                # Process image if uploaded
                image_data = None
                if image_file is not None:
                    try:
                        image = Image.open(image_file)
                        
                        # Convert RGBA to RGB if needed
                        if image.mode == 'RGBA':
                            background = Image.new('RGB', image.size, (255, 255, 255))
                            background.paste(image, mask=image.split()[3])
                            image = background
                        
                        # Resize image to save space
                        image.thumbnail((800, 800))
                        buffered = BytesIO()
                        image.save(buffered, format="JPEG")
                        image_data = base64.b64encode(buffered.getvalue()).decode()
                    except Exception as e:
                        st.error(f"Error processing image: {e}")
                
                # Create report data
                report_data = {
                    "title": title,
                    "city": city,
                    "location": location,
                    "description": description,
                    "severity": severity,
                    "image": image_data
                }
                
                success = record_waste_report(report_data, st.session_state.user_id)
                if success:
                    st.success("Your waste report has been posted successfully!")
                    # Show confetti for positive reinforcement
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Failed to submit report. Please try again.")
                    
def display_registration_form():
    """Display the volunteer registration form"""
    st.subheader("Register as a Volunteer")
    
    with st.form("registration_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your Name")
        with col2:
            email = st.text_input("Email Address")
        
        cities_data = get_cities_data()
        city_names = ["Select City"] + [city["name"] for city in cities_data]
        city = st.selectbox("City", city_names)
        
        time_slots = ["Any Time", "Morning (8 AM - 12 PM)", "Afternoon (12 PM - 4 PM)", "Evening (4 PM - 8 PM)"]
        time_slot = st.selectbox("Preferred Time", time_slots)
        
        st.markdown("""
        By registering, you agree to volunteer in waste management activities organized in your city.
        """)
        
        submitted = st.form_submit_button("Register")
        if submitted:
            if not name or not email or city == "Select City":
                st.error("Please fill in all required fields.")
            elif "@" not in email or "." not in email:
                st.error("Please enter a valid email address.")
            else:
                success, message = record_registration(name, email, city, time_slot)
                if success:
                    st.session_state.registered = True
                    st.success(message)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(message)

def display_cities():
    """Display cities with waste index and voting options"""
    try:
        cities_data = get_cities_data()
        if not cities_data:
            st.warning("No cities data available.")
            return
            
        st.markdown("### Help Choose a City for Our Next Waste Management Campaign")
        st.markdown("Vote for a city you think needs urgent waste management intervention.")
        
        # Get current voting leader
        sorted_cities = sorted(cities_data, key=lambda x: x.get("votes", 0), reverse=True)
        if sorted_cities and sorted_cities[0].get("votes", 0) > 0:
            leader = sorted_cities[0]
            st.markdown(f"**Current leader: {leader['name']} with {leader['votes']} votes**")
        
        # Create three columns for city cards
        cols = st.columns(3)
        
        # Display city cards in columns
        for i, city in enumerate(cities_data):
            col_index = i % 3
            with cols[col_index]:
                # Check if user has voted for this city
                is_voted = st.session_state.voted_city == city["name"]
                
                # Display city card
                st.markdown(f"""
                <div class="city-card">
                    <div class="city-name">{city["name"]}</div>
                    <div class="waste-index">Waste Index: <strong>{city["waste_index"]}/100</strong></div>
                    <div class="city-stats">
                        <div class="stat-item">
                            <div class="stat-value">{city.get("votes", 0)}</div>
                            <div class="stat-label">Votes</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{city.get("registrations", 0)}</div>
                            <div class="stat-label">Volunteers</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Vote button
                button_text = "Voted" if is_voted else "Vote"
                button_class = "vote-button voted" if is_voted else "vote-button"
                
                # Check if voting period ended
                voting_end, _ = get_campaign_dates()
                voting_ended = datetime.now() > voting_end
                
                if voting_ended:
                    st.info("Voting period has ended")
                else:
                    if st.button(button_text, key=f"vote_{city['name']}", 
                               disabled=is_voted):
                        success, message = record_vote(city["name"])
                        if success:
                            st.session_state.voted_city = city["name"]
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
    except Exception as e:
        st.error(f"Error displaying cities: {e}")

def display_info_section():
    """Display waste management information and tips"""
    st.subheader("Waste Management Education")
    
    tab1, tab2, tab3 = st.tabs(["📋 Tips", "🔄 Recycling Guide", "💡 Facts"])
    
    with tab1:
        st.markdown("""
        ### Everyday Waste Reduction Tips
        
        1. **Reduce Single-Use Items**
           - Carry a reusable water bottle
           - Use cloth bags for shopping
           - Avoid disposable cutlery and straws
        
        2. **Food Waste Reduction**
           - Plan meals and shop with a list
           - Store food properly to extend shelf life
           - Use leftovers creatively
           - Consider composting food scraps
        
        3. **Mindful Purchasing**
           - Buy items with less packaging
           - Choose products with recyclable or compostable packaging
           - Consider product durability and repairability
        
        4. **At Work or School**
           - Print double-sided and only when necessary
           - Use digital documents when possible
           - Bring lunch in reusable containers
        """)
    
    with tab2:
        st.markdown("""
        ### Recycling Guide
        
        #### Common Recyclables
        
        | Material | Recyclable? | Preparation Tips |
        |----------|-------------|------------------|
        | Paper & Cardboard | ✅ Yes | Keep dry and clean, remove tape |
        | Glass Bottles & Jars | ✅ Yes | Rinse, remove caps & lids |
        | Metal Cans | ✅ Yes | Rinse clean, labels can stay |
        | Plastic Bottles (PET/HDPE) | ✅ Yes | Empty, rinse, crush to save space |
        | Plastic Bags | ❌ Often No | Return to store collection points |
        | Styrofoam | ❌ Usually No | Check local guidelines |
        | E-Waste | ⚠️ Special | Take to designated collection points |
        | Batteries | ⚠️ Special | Take to designated collection points |
        
        #### Common Recycling Mistakes
        
        1. **Contaminated Items** - Food-soiled containers can contaminate entire batches
        2. **Plastic Bags** - These jam sorting machinery at recycling centers
        3. **Small Items** - Items smaller than a credit card typically can't be sorted
        4. **Mixed Materials** - Items made of multiple materials are difficult to recycle
        """)
    
    with tab3:
        st.markdown("""
        ### Interesting Waste Facts
        
        - **Global Waste Production** is expected to increase by 70% by 2050 if we don't change our habits.
        
        - **Plastic Production** has increased exponentially from 2.3 million tons in 1950 to 448 million tons by 2015. 
        
        - **Food Waste** accounts for approximately 8% of global greenhouse gas emissions.
        
        - **Electronic Waste** is the fastest-growing waste stream in the world, with only 20% being recycled.
        
        - **India** generates approximately 62 million tonnes of waste each year, with about 43 million tonnes being collected and less than 12 million tonnes being processed.
        
        - **Bangalore** alone generates around 5,000 tonnes of waste daily.
        
        - **Recycling** one ton of paper saves about 17 trees, 7,000 gallons of water, and 3 cubic yards of landfill space.
        """)

def run_waste_awareness_app():
    """Main function to run the Streamlit application"""
    # Initialize the database
    try:
        initialize_admin_accounts()
        initialize_cities_data()
    except Exception as e:
        st.error(f"Error initializing database: {e}")
    
    # Page config
   
    
    # Inject custom CSS
    st.markdown(main_css, unsafe_allow_html=True)
    
    # Display header
    st.markdown("""
    <div class="header">
        <h1>♻️ CleanCities: Waste Management Campaign</h1>
        <p>Join our community-driven initiative to reduce waste and make our cities cleaner.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Admin login in sidebar only if not authenticated
    if not st.session_state.admin_authenticated:
        with st.sidebar:
            st.subheader("Admin Access")
            if st.button("Admin Login"):
                st.session_state.show_admin = True
    
    # Show admin login or dashboard if requested
    if st.session_state.get("show_admin", False) and not st.session_state.admin_authenticated:
        display_admin_login()
    
    # Main content - different based on admin authentication
    if st.session_state.admin_authenticated:
        admin_section()
    else:
        # User view
        # Create tabs for different sections
        home_tab, vote_tab, report_tab, register_tab, resources_tab = st.tabs([
            "🏠 Home", 
            "🗳️ Vote", 
            "🚨 Report", 
            "✋ Register", 
            "📚 Resources"
        ])
        
        with home_tab:
            # Show campaign timer
            voting_end, campaign_end = get_campaign_dates()
            days_to_voting_end = (voting_end - datetime.now()).days
            days_to_campaign_end = (campaign_end - datetime.now()).days
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                ### Campaign Timeline
                - **Voting ends in:** {max(0, days_to_voting_end)} days ({voting_end.strftime('%b %d, %Y')})
                - **Campaign ends in:** {max(0, days_to_campaign_end)} days ({campaign_end.strftime('%b %d, %Y')})
                """)
            
            with col2:
                # Show campaign stats
                cities_data = get_cities_data()
                total_votes = sum(city.get("votes", 0) for city in cities_data)
                total_registrations = sum(city.get("registrations", 0) for city in cities_data)
                
                st.markdown(f"""
                ### Campaign Statistics
                - **Total Votes Cast:** {total_votes}
                - **Volunteers Registered:** {total_registrations}
                """)
            
            # Display waste severity map
            st.subheader("Waste Severity Map")
            render_waste_map()
            
            # Display waste reports
            st.subheader("Recent Waste Reports")
            display_waste_reports_public()
        
        with vote_tab:
            display_cities()
        
        with report_tab:
            display_report_form()
        
        with register_tab:
            if st.session_state.registered:
                st.success("Thank you for registering! Your participation is valued.")
                if st.button("Register Another Person"):
                    st.session_state.registered = False
                    st.rerun()
            else:
                display_registration_form()
        
        with resources_tab:
            display_info_section()
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
        <p>© 2025 CleanCities Initiative. Powered by Streamlit.</p>
    </div>
    """, unsafe_allow_html=True)
if __name__ == "__main__":
    st.set_page_config(
        page_title="Waste Awareness App",
        page_icon="♻️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    run_waste_awareness_app()
