import streamlit as st
from datetime import datetime
from auth import auth_page
from database import (
    init_database,
    create_seller_listing,
    create_buyer_request,
    get_seller_listings,
    get_buyer_requests,
    update_listing_status,
    delete_listing
)
import base64
from io import BytesIO
from PIL import Image
import webbrowser
import re
import urllib.parse

# Set page configuration for better appearance

# Custom CSS for better UI
def load_css():
    st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .listing-card {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 0.5rem;
            margin-bottom: 1.5rem;
            background-color: #4caf50;;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            color: rgb(255, 255, 255);;
            font-size: 1.8rem;
            font-weight: bold;
            text-align: center;
            letter-spacing: 1px;
            text-transform: uppercase;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
            
        }
        .card-header {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
            color: #2c3e50;
        }
        .contact-btn {
            display: inline-block;
            padding: 0.5rem 1rem;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-right: 0.5rem;
            font-weight: bold;
        }
        .whatsapp-btn {
            background-color: #25D366;
        }
        .sms-btn {
            background-color: #007bff;
        }
        .delete-btn {
            background-color: #dc3545;
        }
        .badge {
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .waste-type {
            background-color: #17a2b8;
            color: white;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f8f9fa;
            border-radius: 4px 4px 0 0;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #e6f3ff;
            border-bottom: 2px solid #4CAF50;
        }
        .listing-separator {
            height: 5px;
            background: linear-gradient(90deg, #4CAF50, #17a2b8);
            border-radius: 2px;
            margin: 20px 0;
        }
    </style>
    """, unsafe_allow_html=True)

def upload_and_save_image():
    uploaded_file = st.file_uploader("Upload Waste Image", type=['png', 'jpg', 'jpeg'])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        
        if image.mode == 'RGBA':
            image = image.convert('RGB')
            
        st.image(image, caption='Image Preview', use_container_width=True)
        
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    return None

def format_phone_number(phone_number):
    # Clean the phone number of non-numeric characters
    clean_number = re.sub(r'\D', '', phone_number)
    
    # If the number starts with 0, replace it with country code (assuming India +91)
    if clean_number.startswith('0'):
        clean_number = '91' + clean_number[1:]
    # If the number doesn't have country code, add it (assuming India +91)
    elif len(clean_number) == 10:
        clean_number = '91' + clean_number
        
    return clean_number

# Functions for generating contact links
def get_whatsapp_link(phone_number, message):
    # Clean the phone number (ensure it has country code)
    clean_number = ''.join(filter(str.isdigit, str(phone_number)))
    
    # Make sure message is properly encoded
    import urllib.parse
    encoded_message = urllib.parse.quote(message)  # Using quote instead of quote_plus
    
    # Use the api.whatsapp.com/send endpoint
    return f"https://wa.me/{clean_number}?text={encoded_message}"


def create_selling_listing():
    st.header("🌱 Create Waste Selling Listing")
    
    with st.form("seller_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            waste_type = st.selectbox("Waste Type", [
                "Metal Scraps", "Wood Waste", "Packaging Materials", 
                "Construction Waste", "Electronics", "Furniture",
                "Organic Waste", "Others"
            ])
            
            quantity = st.number_input("Quantity (kg)", min_value=0.1, step=0.1)
            price = st.number_input("Price (₹)", min_value=0.0, step=0.1)
            
        with col2:
            location = st.text_input("Location")
            contact_number = st.text_input("Contact Number")
            best_contact_time = st.selectbox("Best Time to Contact", [
                "Any Time", "Morning (8AM-12PM)", "Afternoon (12PM-4PM)", 
                "Evening (4PM-8PM)", "Night (After 8PM)"
            ])
        
        description = st.text_area("Description", placeholder="Describe your waste in detail (condition, dimensions, etc.)")
        
        st.write("Upload Waste Image")
        image_data = upload_and_save_image()
        
        submitted = st.form_submit_button("Create Listing", type="primary", use_container_width=True)
        
        if submitted:
            if not contact_number:
                st.error("Please provide a contact number")
                return
                
            listing_data = {
                "user": st.session_state.username,
                "waste_type": waste_type,
                "quantity": quantity,
                "price": price,
                "location": location,
                "description": description,
                "contact_number": contact_number,
                "best_contact_time": best_contact_time,
                "image": image_data,
                "created_at": datetime.now(),
                "status": "Active"
            }
            
            success, message = create_seller_listing(listing_data)
            if success:
                st.success("Seller listing created successfully!")
                st.balloons()
            else:
                st.error(f"Error creating listing: {message}")

def create_buying_request():
    st.header("🔍 Create Waste Buying Request")
    
    with st.form("buyer_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            waste_type = st.selectbox("Required Waste Type", [
                "Metal Scraps", "Wood Waste", "Packaging Materials", 
                "Construction Waste", "Electronics", "Furniture",
                "Organic Waste", "Others"
            ])
            
            quantity_required = st.number_input("Required Quantity (kg)", min_value=0.1, step=0.1)
            budget = st.number_input("Budget (₹, optional)", min_value=0.0, step=0.1)
        
        with col2:
            location = st.text_input("Location")
            contact_number = st.text_input("Contact Number")
            best_contact_time = st.selectbox("Best Time to Contact", [
                "Any Time", "Morning (8AM-12PM)", "Afternoon (12PM-4PM)", 
                "Evening (4PM-8PM)", "Night (After 8PM)"
            ])
        
        requirements = st.text_area("Specific Requirements", placeholder="Describe any specific requirements or quality standards needed")
        
        submitted = st.form_submit_button("Create Request", type="primary", use_container_width=True)
        
        if submitted:
            if not contact_number:
                st.error("Please provide a contact number")
                return
                
            request_data = {
                "user": st.session_state.username,
                "waste_type": waste_type,
                "quantity_required": quantity_required,
                "budget": budget,
                "location": location,
                "requirements": requirements,
                "contact_number": contact_number,
                "best_contact_time": best_contact_time,
                "created_at": datetime.now(),
                "status": "Active"
            }
            
            success, message = create_buyer_request(request_data)
            if success:
                st.success("Buying request created successfully!")
                st.balloons()
            else:
                st.error(f"Error creating request: {message}")

def display_seller_listing(item, show_delete=False):
    with st.container():
        
        st.markdown('<div class="listing-card">Waste Exchange System</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f'<div class="card-header">🗑️ <span class="badge waste-type">{item["waste_type"]}</span> Waste Listing</div>', unsafe_allow_html=True)
            
            st.markdown(f"""
            | Detail | Information |
            |--------|-------------|
            | **Quantity** | {item['quantity']} kg |
            | **Price** | ₹{item.get('price', 'Not specified')} |
            | **Location** | {item['location']} |
            | **Best Contact Time** | {item.get('best_contact_time', 'Any Time')} |
            | **Posted By** | {item['user']} |
            | **Posted On** | {item['created_at'].strftime('%Y-%m-%d %H:%M')} |
            """)
            
            st.markdown(f"**Description:** {item['description']}")
            
            # Contact buttons with properly formatted template messages
            template_msg = f"Hello! I'm interested in your {item['waste_type']} waste listing on the Waste Exchange Platform. Is it still available? The listing mentions {item['quantity']} kg at ₹{item.get('price', 'unspecified price')}. "
            
            whatsapp_link = get_whatsapp_link(item['contact_number'], template_msg)
            
            st.markdown(f"""
            <p>Contact: {item['contact_number']}</p>
            <a href="{whatsapp_link}" target="_blank" class="contact-btn whatsapp-btn">Contact via WhatsApp</a>
       
            """, unsafe_allow_html=True)
            
            if show_delete:
                if st.button(f"Delete Listing", key=f"del_sell_{item['_id']}"):
                    success, message = delete_listing(item['_id'], 'seller_listings')
                    if success:
                        st.success("Listing deleted successfully!")
                        st.rerun()
                    else:
                        st.error(f"Error deleting listing: {message}")
        
        with col2:
            if item.get('image'):
                try:
                    img_data = base64.b64decode(item['image'])
                    img = Image.open(BytesIO(img_data))
                    st.image(img, caption='Waste Image', use_container_width=True)
                except Exception as e:
                    st.error("Error loading image")
            else:
                st.image("https://via.placeholder.com/300x200?text=No+Image", caption="No Image Available", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Colored separator between listings
    st.markdown('<div class="listing-separator"></div>', unsafe_allow_html=True)
    
def display_buyer_request(item, show_delete=False):
    with st.container():
        st.markdown('<div class="listing-card">Waste Exchange System</div>', unsafe_allow_html=True)
        
        st.markdown(f'<div class="card-header">🌍 <span class="badge waste-type">{item["waste_type"]}</span> Waste Buying Request</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            | Detail | Information |
            |--------|-------------|
            | **Quantity Required** | {item['quantity_required']} kg |
            | **Budget** | {f"₹{item.get('budget')}" if item.get('budget') else 'Not specified'} |
            | **Location** | {item['location']} |
            | **Best Contact Time** | {item.get('best_contact_time', 'Any Time')} |
            | **Posted By** | {item['user']} |
            | **Posted On** | {item['created_at'].strftime('%Y-%m-%d %H:%M')} |
            """)
            
            st.markdown(f"**Specific Requirements:** {item.get('requirements', 'No specific requirements')}")
            
            # Contact buttons with properly formatted template messages
            template_msg = f"Hello! I have the {item['waste_type']} waste you're looking for on the Waste Exchange Platform. You requested {item['quantity_required']} kg. Would you like to discuss further?"
            
            whatsapp_link = get_whatsapp_link(item['contact_number'], template_msg)
            
            
            st.markdown(f"""
            <p>Contact: {item['contact_number']}</p>
            <a href="{whatsapp_link}" target="_blank" class="contact-btn whatsapp-btn">Contact via WhatsApp</a>
            
            """, unsafe_allow_html=True)
        
        with col2:
            if show_delete:
                if st.button(f"Delete Request", key=f"del_buy_{item['_id']}"):
                    success, message = delete_listing(item['_id'], 'buyer_requests')
                    if success:
                        st.success("Request deleted successfully!")
                        st.rerun()
                    else:
                        st.error(f"Error deleting request: {message}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Colored separator between listings
    st.markdown('<div class="listing-separator"></div>', unsafe_allow_html=True)
        
def view_seller_listings():
    st.header("♻️ Available Waste Listings")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        waste_type_filter = st.selectbox(
            "Filter by Waste Type",
            ["All", "Metal Scraps", "Wood Waste", "Packaging Materials", 
             "Construction Waste", "Electronics", "Furniture",
             "Organic Waste", "Others"]
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort By",
            ["Newest First", "Oldest First", "Price: Low to High", "Price: High to Low"]
        )
    
    query = {"status": "Active"}
    if waste_type_filter != "All":
        query["waste_type"] = waste_type_filter
    
    listings = get_seller_listings(query)
    
    if not listings:
        st.info("No selling listings available")
        return
    
    # Sort listings
    if sort_by == "Newest First":
        listings = sorted(listings, key=lambda x: x['created_at'], reverse=True)
    elif sort_by == "Oldest First":
        listings = sorted(listings, key=lambda x: x['created_at'])
    elif sort_by == "Price: Low to High":
        listings = sorted(listings, key=lambda x: x.get('price', 0))
    elif sort_by == "Price: High to Low":
        listings = sorted(listings, key=lambda x: x.get('price', 0), reverse=True)
    
    for item in listings:
        display_seller_listing(item)

def view_buyer_requests():
    st.header("🔍 Active Buying Requests")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        waste_type_filter = st.selectbox(
            "Filter by Waste Type",
            ["All", "Metal Scraps", "Wood Waste", "Packaging Materials", 
             "Construction Waste", "Electronics", "Furniture",
             "Organic Waste", "Others"],
            key="buyer_filter"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort By",
            ["Newest First", "Oldest First"],
            key="buyer_sort"
        )
    
    query = {"status": "Active"}
    if waste_type_filter != "All":
        query["waste_type"] = waste_type_filter
    
    requests = get_buyer_requests(query)
    
    if not requests:
        st.info("No buying requests available")
        return
    
    # Sort requests
    if sort_by == "Newest First":
        requests = sorted(requests, key=lambda x: x['created_at'], reverse=True)
    elif sort_by == "Oldest First":
        requests = sorted(requests, key=lambda x: x['created_at'])
    
    for item in requests:
        display_buyer_request(item)
        
def my_listings():
    st.header("My Listings")
    
    tab1, tab2 = st.tabs(["💰 My Selling Listings", "🛒 My Buying Requests"])
    
    with tab1:
        sell_listings = get_seller_listings({
            "user": st.session_state.username,
            "status": "Active"
        })
        
        if not sell_listings:
            st.info("You haven't created any selling listings yet")
        else:
            for item in sell_listings:
                display_seller_listing(item, show_delete=True)
    
    with tab2:
        buy_requests = get_buyer_requests({
            "user": st.session_state.username,
            "status": "Active"
        })
        
        if not buy_requests:
            st.info("You haven't created any buying requests yet")
        else:
            for item in buy_requests:
                display_buyer_request(item, show_delete=True)

def dashboard():
    st.header("♻️ Waste Exchange Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    # Get stats
    seller_listings = get_seller_listings({"status": "Active"})
    buyer_requests = get_buyer_requests({"status": "Active"})
    
    with col1:
        st.metric("Active Waste Listings", len(seller_listings))
    
    with col2:
        st.metric("Active Buying Requests", len(buyer_requests))
    
    with col3:
        my_listings_count = len(get_seller_listings({"user": st.session_state.username, "status": "Active"}))
        my_requests_count = len(get_buyer_requests({"user": st.session_state.username, "status": "Active"}))
        st.metric("My Active Posts", my_listings_count + my_requests_count)
    
    # Most common waste types
    waste_types = {}
    for item in seller_listings:
        waste_type = item.get('waste_type')
        if waste_type in waste_types:
            waste_types[waste_type] += 1
        else:
            waste_types[waste_type] = 1
    
    # Display waste types distribution if any exist
    if waste_types:
        st.subheader("Popular Waste Categories")
        
        # Sort waste types by count
        sorted_waste_types = sorted(waste_types.items(), key=lambda x: x[1], reverse=True)
        
        # Create a horizontal bar chart
        chart_data = {
            "Category": [item[0] for item in sorted_waste_types],
            "Count": [item[1] for item in sorted_waste_types]
        }
        
        st.bar_chart(chart_data, x="Category", y="Count")
    
    # Recent listings
    st.subheader("Recent Listings")
    recent_listings = sorted(seller_listings, key=lambda x: x['created_at'], reverse=True)[:3]
    
    if recent_listings:
        for item in recent_listings:
            display_seller_listing(item)
    else:
        st.info("No recent listings available")
        
def recycling_centers():
    st.header("Recycling Centers")
    
    # Add custom CSS
    st.markdown("""
    <style>
        /* Main Styles */
        .main-header {
            color: #2E7D32;
            font-family: 'Helvetica Neue', sans-serif;
            border-bottom: 2px solid #81C784;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        /* Card Styles */
        .recycling-card {
            background-color: #F1F8E9;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #4CAF50;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .card-title {
            color: #33691E;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 1.2em;
        }
        
        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #E8F5E9;
            padding: 10px 20px;
            border-radius: 5px 5px 0 0;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #81C784 !important;
            color: white !important;
            font-weight: bold;
        }
        
        /* Button Styles */
        .stButton button {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 5px 15px;
            transition: all 0.3s;
        }
        
        .stButton button:hover {
            background-color: #2E7D32;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        /* Search Section */
        .search-container {
            background-color: #E8F5E9;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        /* Resources Section */
        .resource-link {
            color: #2E7D32;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }
        
        .resource-link:hover {
            color: #1B5E20;
            text-decoration: underline;
        }
        
        /* Divider */
        hr {
            border-top: 1px dashed #81C784;
            margin: 30px 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">🔄  Recycling Centers</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    Below is a list of recycling centers that can help process various types of waste materials.
    Contact them directly to learn more about their services and requirements.
    """)
    
    # Create tabs for different regions
    tab1, tab2, tab3, tab4 = st.tabs(["North Region", "South Region", "East Region", "West Region"])
    
    with tab1:
        st.subheader("North Region Recycling Centers")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="recycling-card">
                <div class="card-title">Prakruthi Recycling</div>
                <strong>Location:</strong> No.103, Ground Floor, 5th Cross, 5th Block, Ssi Area, Rajajinagar, Bangalore, Karnataka 560010<br>
                <strong>Contact:</strong> 080 2350 9001<br>
                <strong>Services:</strong> Paper, plastic, metal, and e-waste recycling<br>
                <strong>Hours:</strong> Mon-Fri: 8AM-6PM, Sat: 9AM-2PM
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📍 Get Directions to Prakruthi Recycling", key="gc_directions"):
                location_url = "https://www.bing.com/maps?mepi=107%7ELocal%7EMiddleOfPage%7EMap_Image&ty=17&q=bengaluru+recycling+centers&segment=Local&mb=13.013863%7E77.509003%7E12.948852%7E77.563904&ppois=12.984375_77.5537338256836_Prakruthi+Recycling_YN4070x10896634689570749147%7E12.960190773010254_77.52484130859375_Prakruthi+Recycling+Private+Limited_YN4070x10792203897317850538%7E13.013862609863281_77.50900268554688_E2e+Recycling+Business+Private+Limited_YN4070x430487672664804377%7E12.95868968963623_77.56390380859375_Exigo+Recycling+Private+Limited_YN4070x16374233223629992508%7E12.948851585388184_77.52577209472656_Eco+Birdd+Recycling+Company_YN4070x16102799366993288182%7E&usebfpr=true&v=2&sV=1&FORM=MPSRPL&cp=12.984375%7E77.553747&lvl=14.5"
                st.markdown(f'<a href="{location_url}" target="_blank" class="resource-link">🗺️ Open in Google Maps</a>', unsafe_allow_html=True)

        
        with col2:
            st.markdown("""
            <div class="recycling-card">
                <div class="card-title">Northern Waste Management</div>
                <strong>Location:</strong> 456 Recycling Road, North District<br>
                <strong>Contact:</strong> +1-555-765-4321<br>
                <strong>Services:</strong> Industrial waste, construction materials, and hazardous waste<br>
                <strong>Hours:</strong> Mon-Sat: 7AM-7PM
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📍 Get Directions to Northern Waste", key="nw_directions"):
                st.markdown('<a href="https://maps.google.com" target="_blank" class="resource-link">🗺️ Open in Maps</a>', unsafe_allow_html=True)
    
    with tab2:
        st.subheader("South Region Recycling Centers")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="recycling-card">
                <div class="card-title">EcoSouth Recyclers</div>
                <strong>Location:</strong> 789 Green Street, South District<br>
                <strong>Contact:</strong> +1-555-987-6543<br>
                <strong>Services:</strong> Paper, cardboard, glass, and organic waste<br>
                <strong>Hours:</strong> Mon-Fri: 9AM-5PM, Sat: 10AM-3PM
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📍 Get Directions to EcoSouth", key="es_directions"):
                st.markdown('<a href="https://maps.google.com" target="_blank" class="resource-link">🗺️ Open in Maps</a>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="recycling-card">
                <div class="card-title">Southern Materials Recovery</div>
                <strong>Location:</strong> 321 Sustainability Lane, South District<br>
                <strong>Contact:</strong> +1-555-246-8020<br>
                <strong>Services:</strong> Plastic, metal, electronics, and textile recycling<br>
                <strong>Hours:</strong> Mon-Sat: 8AM-8PM, Sun: 10AM-4PM
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📍 Get Directions to Southern Materials", key="sm_directions"):
                st.markdown('<a href="https://maps.google.com" target="_blank" class="resource-link">🗺️ Open in Maps</a>', unsafe_allow_html=True)
    
    with tab3:
        st.subheader("East Region Recycling Centers")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="recycling-card">
                <div class="card-title">Eastern Eco Processors</div>
                <strong>Location:</strong> 159 Reclaim Drive, East District<br>
                <strong>Contact:</strong> +1-555-369-8520<br>
                <strong>Services:</strong> All types of plastic, metal, and battery recycling<br>
                <strong>Hours:</strong> 24/7 Drop-off, Office: Mon-Fri: 8AM-5PM
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📍 Get Directions to Eastern Eco", key="ee_directions"):
                st.markdown('<a href="https://maps.google.com" target="_blank" class="resource-link">🗺️ Open in Maps</a>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="recycling-card">
                <div class="card-title">East Valley Recycling Co-op</div>
                <strong>Location:</strong> 753 Community Circle, East District<br>
                <strong>Contact:</strong> +1-555-147-2583<br>
                <strong>Services:</strong> Community-based recycling for households and small businesses<br>
                <strong>Hours:</strong> Tue-Sat: 9AM-4PM
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📍 Get Directions to East Valley", key="ev_directions"):
                st.markdown('<a href="https://maps.google.com" target="_blank" class="resource-link">🗺️ Open in Maps</a>', unsafe_allow_html=True)
    
    with tab4:
        st.subheader("West Region Recycling Centers")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="recycling-card">
                <div class="card-title">West Coast Waste Solutions</div>
                <strong>Location:</strong> 951 Ocean View Road, West District<br>
                <strong>Contact:</strong> +1-555-753-9510<br>
                <strong>Services:</strong> Specialized in ocean waste and plastics recycling<br>
                <strong>Hours:</strong> Mon-Fri: 7AM-7PM, Sat-Sun: 9AM-5PM
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📍 Get Directions to West Coast", key="wc_directions"):
                st.markdown('<a href="https://maps.google.com" target="_blank" class="resource-link">🗺️ Open in Maps</a>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="recycling-card">
                <div class="card-title">WestSide Electronics Recycling</div>
                <strong>Location:</strong> 357 Tech Terrace, West District<br>
                <strong>Contact:</strong> +1-555-852-9631<br>
                <strong>Services:</strong> E-waste, computers, phones, and other electronics<br>
                <strong>Hours:</strong> Mon-Sat: 10AM-6PM
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📍 Get Directions to WestSide", key="ws_directions"):
                st.markdown('<a href="https://maps.google.com" target="_blank" class="resource-link">🗺️ Open in Maps</a>', unsafe_allow_html=True)
    
    # Additional centers section
    st.markdown('<hr>', unsafe_allow_html=True)
    st.subheader("Additional Specialized Recycling Centers")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="recycling-card">
            <div class="card-title">Central Hazardous Waste Facility</div>
            <strong>Location:</strong> 555 Safety Boulevard, Central District<br>
            <strong>Contact:</strong> +1-555-911-0099<br>
            <strong>Services:</strong> Proper disposal of hazardous materials, chemicals, and medical waste<br>
            <strong>Hours:</strong> Mon-Fri: 8AM-4PM (Appointment required)
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📍 Get Directions to Central Hazardous", key="ch_directions"):
            st.markdown('<a href="https://maps.google.com" target="_blank" class="resource-link">🗺️ Open in Maps</a>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="recycling-card">
            <div class="card-title">Circular Economy Hub</div>
            <strong>Location:</strong> 888 Innovation Park, Industrial Zone<br>
            <strong>Contact:</strong> +1-555-404-2030<br>
            <strong>Services:</strong> Research and development for waste-to-resource technologies<br>
            <strong>Hours:</strong> By appointment only
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📍 Get Directions to Circular Economy Hub", key="ce_directions"):
            st.markdown('<a href="https://maps.google.com" target="_blank" class="resource-link">🗺️ Open in Maps</a>', unsafe_allow_html=True)
    
    # Add search and filter functionality
    
    
    # Additional resources
    st.markdown('<hr>', unsafe_allow_html=True)
    st.subheader("Resources")
    
    st.markdown("""
    <ul>
        <li><a href="https://example.com" class="resource-link">📄 Download our Recycling Guide PDF</a></li>
        <li><a href="https://example.com" class="resource-link">📚 Learn about Waste Sorting Best Practices</a></li>
        <li><a href="https://example.com" class="resource-link">📅 Check your local Collection Schedule</a></li>
    </ul>
    """, unsafe_allow_html=True)

def about_page():
    st.header("About Waste Exchange Platform")
    
    st.markdown("""
    ### 🌍 Our Mission
    
    The Waste Exchange Platform aims to create a circular economy by connecting waste generators with waste recyclers and users. 
    Our goal is to reduce waste going to landfills by facilitating its reuse and recycling.
    
    ### How It Works
    
    1. **For Waste Sellers**: List your waste materials that could be valuable to others.
    2. **For Waste Buyers**: Post requests for specific waste materials you need.
    3. **Connect and Exchange**: Use our platform to find matches and contact potential partners.
    
    ### Benefits
    
    - **Environmental Impact**: Reduce landfill waste and conserve natural resources
    - **Economic Value**: Save money on disposal costs and find affordable raw materials
    - **Community Building**: Connect with like-minded individuals and businesses
    
    ### Contact Us
    
    For support or feedback, please contact us at ck257
    """)

def run_waste_exchange_app():
    # Load custom CSS
    load_css()
    
    # Handle authentication
    if not auth_page():
        return
    
    # Sidebar with improved navigation
    with st.sidebar:
        st.image("D:/downloads/project/img3.png", width=300)
        st.title("♻️ Waste Exchange")
        
        st.markdown(f"Welcome, **{st.session_state.username}**!")
        
        st.markdown("---")
        
        menu = st.selectbox(
            "Navigation",
            ["Dashboard", "Seller Listings", "Buyer Requests", 
             "Create Selling Listing", "Create Buying Request", 
             "My Listings","Recycling Centers", "About"],
            index=0
        )
        
        st.markdown("---")
        
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # Main content area
    if menu == "Dashboard":
        dashboard()
    elif menu == "Create Selling Listing":
        create_selling_listing()
    elif menu == "Create Buying Request":
        create_buying_request()
    elif menu == "Seller Listings":
        view_seller_listings()
    elif menu == "Buyer Requests":
        view_buyer_requests()
    elif menu == "My Listings":
        my_listings()
    elif menu == "Recycling Centers":
        recycling_centers()
    elif menu == "About":
        about_page()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "© 2025 Waste Exchange Platform | Built with ❤️ for a cleaner planet",
        help="Version 2.0.0"
    )

if __name__ == "__main__":
    run_waste_exchange_app()