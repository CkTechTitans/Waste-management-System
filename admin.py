import streamlit as st
import pandas as pd
import numpy as np
from geopy.distance import geodesic
import folium
from streamlit_folium import folium_static
import random

# Set page config
st.set_page_config(
    page_title="RecycleMate",
    page_icon="♻️",
    layout="wide"
)

# Sample data for recycling centers
def load_recycling_centers():
    # In a real app, this would come from a database
    centers = pd.DataFrame({
        'name': [
            'Green Earth Recycling', 
            'EcoCity Recyclers', 
            'Community Recycling Hub', 
            'Planet Protectors', 
            'Urban Recycling Co.'
        ],
        'latitude': [40.7128, 40.7300, 40.7400, 40.7000, 40.7200],
        'longitude': [-74.0060, -74.0100, -73.9800, -74.0200, -73.9900],
        'accepts': [
            'Paper, Plastic, Glass, Electronics',
            'Plastic, Metal, Clothing',
            'Paper, Cardboard, Glass',
            'Electronics, Batteries, Metal',
            'All recyclables'
        ],
        'pays': [
            'Yes (Electronics only)',
            'Yes (Metal only)',
            'No',
            'Yes (Batteries and Electronics)',
            'Yes (All items)'
        ],
        'hours': [
            '9AM-5PM Mon-Fri',
            '8AM-8PM All days',
            '10AM-6PM Mon-Sat',
            '9AM-7PM Mon-Fri, 10AM-4PM Sat',
            '24/7 Drop-off'
        ]
    })
    return centers

# Sample data for user inventory
def load_user_inventory():
    # In a real app, this would be stored in a database
    if 'user_inventory' not in st.session_state:
        st.session_state.user_inventory = pd.DataFrame({
            'item': ['Cardboard boxes', 'Plastic bottles', 'Old laptop'],
            'category': ['Paper', 'Plastic', 'Electronics'],
            'quantity': [5, 20, 1],
            'listed_on': ['2025-03-10', '2025-03-12', '2025-03-13']
        })
    return st.session_state.user_inventory

# Main function
def main():
    st.title("♻️ RecycleMate")
    st.subheader("Connect with recycling centers near you")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigate", 
        ["Home", "My Recyclables", "Find Centers", "Transactions"]
    )
    
    # User location (would be obtained from device in a real app)
    if 'user_location' not in st.session_state:
        st.session_state.user_location = (40.7128, -74.0060)  # Default: NYC
    
    # Load data
    centers = load_recycling_centers()
    inventory = load_user_inventory()
    
    # Pages
    if page == "Home":
        show_home_page(centers)
    elif page == "My Recyclables":
        show_inventory_page(inventory)
    elif page == "Find Centers":
        show_centers_page(centers)
    elif page == "Transactions":
        show_transactions_page()

def show_home_page(centers):
    st.markdown("""
    ## Welcome to RecycleMate! 
    
    Connect with recycling centers in your area to responsibly dispose of recyclable items 
    or even earn money for your recyclables.
    
    ### How it works:
    1. List the recyclable items you have
    2. Find centers near you that accept those items
    3. Arrange for drop-off or request pickup
    4. Track your environmental impact
    """)
    
    st.info("🌟 Quick Stats: You've recycled 26 items this month, saving approximately 15 kg of CO2!")
    
    # Display map with nearby centers
    st.subheader("Recycling Centers Near You")
    display_centers_map(centers)
    
    # Display recent transactions
    st.subheader("Recent Activity")
    recent = pd.DataFrame({
        'date': ['2025-03-10', '2025-03-05', '2025-02-28'],
        'center': ['Green Earth Recycling', 'EcoCity Recyclers', 'Planet Protectors'],
        'items': ['Paper (2kg)', 'Metal cans (0.5kg)', 'Old phone'],
        'earned': ['$0', '$1.25', '$5.00']
    })
    st.table(recent)

def show_inventory_page(inventory):
    st.subheader("My Recyclable Items")
    
    # Display current inventory
    st.write("Current inventory:")
    st.dataframe(inventory)
    
    # Add new item form
    st.subheader("Add New Item")
    col1, col2 = st.columns(2)
    with col1:
        new_item = st.text_input("Item Description")
        new_category = st.selectbox("Category", ["Paper", "Plastic", "Glass", "Metal", "Electronics", "Clothing", "Other"])
    with col2:
        new_quantity = st.number_input("Quantity", min_value=1, value=1)
        new_date = st.date_input("Date")
    
    if st.button("Add Item"):
        new_row = pd.DataFrame({
            'item': [new_item],
            'category': [new_category],
            'quantity': [new_quantity],
            'listed_on': [new_date.strftime("%Y-%m-%d")]
        })
        st.session_state.user_inventory = pd.concat([inventory, new_row], ignore_index=True)
        st.success(f"Added {new_quantity} {new_item} to your inventory!")
        st.experimental_rerun()
    
    # Environmental impact
    st.subheader("Your Environmental Impact")
    impact = calculate_impact(inventory)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("CO2 Saved", f"{impact['co2']} kg")
    with col2:
        st.metric("Water Saved", f"{impact['water']} liters")
    with col3:
        st.metric("Trees Saved", f"{impact['trees']}")

def show_centers_page(centers):
    st.subheader("Find Recycling Centers")
    
    # Filter options
    st.write("Filter by item type:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filter_paper = st.checkbox("Paper/Cardboard")
    with col2:
        filter_plastic = st.checkbox("Plastic")
    with col3:
        filter_electronics = st.checkbox("Electronics")
    with col4:
        filter_pays = st.checkbox("Pays for items")
    
    # Apply filters
    filtered_centers = centers.copy()
    if filter_paper:
        filtered_centers = filtered_centers[filtered_centers['accepts'].str.contains('Paper|Cardboard')]
    if filter_plastic:
        filtered_centers = filtered_centers[filtered_centers['accepts'].str.contains('Plastic')]
    if filter_electronics:
        filtered_centers = filtered_centers[filtered_centers['accepts'].str.contains('Electronics')]
    if filter_pays:
        filtered_centers = filtered_centers[filtered_centers['pays'].str.contains('Yes')]
    
    # Display centers
    st.write(f"Found {len(filtered_centers)} centers matching your criteria:")
    
    # Display map
    display_centers_map(filtered_centers)
    
    # Display center details
    for _, center in filtered_centers.iterrows():
        with st.expander(f"{center['name']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Accepts:** {center['accepts']}")
                st.write(f"**Pays for items:** {center['pays']}")
            with col2:
                st.write(f"**Hours:** {center['hours']}")
                distance = calculate_distance(st.session_state.user_location, (center['latitude'], center['longitude']))
                st.write(f"**Distance:** {distance:.1f} km")
            
            # Actions
            if st.button(f"Request pickup from {center['name']}"):
                st.success(f"Pickup request sent to {center['name']}! They will contact you shortly.")
            
            st.write("---")

def show_transactions_page():
    st.subheader("My Recycling Transactions")
    
    # Sample transactions
    transactions = pd.DataFrame({
        'date': ['2025-03-10', '2025-03-05', '2025-02-28', '2025-02-15', '2025-02-05'],
        'center': ['Green Earth Recycling', 'EcoCity Recyclers', 'Planet Protectors', 'Urban Recycling Co.', 'EcoCity Recyclers'],
        'items': ['Paper (2kg)', 'Metal cans (0.5kg)', 'Old phone', 'Cardboard (3kg)', 'Plastic (1kg)'],
        'earned': ['$0', '$1.25', '$5.00', '$0', '$0'],
        'status': ['Completed', 'Completed', 'Completed', 'Completed', 'Completed']
    })
    
    st.dataframe(transactions)
    
    # Transaction stats
    st.subheader("Transaction Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transactions", "5")
    with col2:
        st.metric("Items Recycled", "26")
    with col3:
        st.metric("Money Earned", "$6.25")
    
    # Download transactions
    st.download_button(
        label="Download Transaction History",
        data=transactions.to_csv(index=False),
        file_name="recycling_transactions.csv",
        mime="text/csv"
    )

# Helper functions
def display_centers_map(centers):
    # Create a map centered on user's location
    m = folium.Map(location=st.session_state.user_location, zoom_start=13)
    
    # Add user marker
    folium.Marker(
        st.session_state.user_location,
        popup="Your Location",
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)
    
    # Add center markers
    for _, center in centers.iterrows():
        folium.Marker(
            [center['latitude'], center['longitude']],
            popup=f"{center['name']}<br>Accepts: {center['accepts']}<br>Pays: {center['pays']}",
            icon=folium.Icon(color="green", icon="leaf")
        ).add_to(m)
    
    # Display the map
    folium_static(m)

def calculate_distance(loc1, loc2):
    # Calculate distance in kilometers
    return geodesic(loc1, loc2).kilometers

def calculate_impact(inventory):
    # Simplified impact calculation
    paper_items = inventory[inventory['category'] == 'Paper']['quantity'].sum()
    plastic_items = inventory[inventory['category'] == 'Plastic']['quantity'].sum()
    electronic_items = inventory[inventory['category'] == 'Electronics']['quantity'].sum()
    
    # Very simplified calculations
    co2 = paper_items * 0.5 + plastic_items * 0.3 + electronic_items * 2.5
    water = paper_items * 10 + plastic_items * 5 + electronic_items * 20
    trees = paper_items * 0.1
    
    return {
        'co2': round(co2, 1),
        'water': round(water, 1),
        'trees': round(trees, 2)
    }

if __name__ == "__main__":
    main()