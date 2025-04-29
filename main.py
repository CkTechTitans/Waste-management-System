# Import streamlit first
import streamlit as st
import base64
from PIL import Image
import io

# Configure page (must be first Streamlit command)
st.set_page_config(
    page_title="Waste Management Solutions",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import other modules after page config
from ecosmart import run_ecosmart_app
from waste_exchange import run_waste_exchange_app
from waste_awareness import run_waste_awareness_app  # Import the new module

# Define color scheme
PRIMARY_COLOR = "#00796B"
SECONDARY_COLOR = "#4DB6AC"
ACCENT_COLOR = "#FF9800"
BG_COLOR = "#ECEFF1"
TEXT_COLOR = "#263238"
DARK_BG = "#263238"
LIGHT_TEXT = "#ECEFF1"

# Directly inject CSS using Streamlit components
def apply_custom_css():
    # CSS is directly applied to elements using st.markdown with unsafe_allow_html=True
    st.markdown("""
    <style>
    /* Base Styles */
    .main {
        background-color: #ECEFF1;
        color: #263238;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Custom Container */
    .custom-container {
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 6px 24px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    /* Header */
    .header {
        background: linear-gradient(135deg, #00796B 0%, #009688 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .header h1 {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .header p {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Cards */
    .card {
        background-color: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        height: 100%;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border-top: 5px solid #00796B;
        margin-bottom: 1rem;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    }
    
    .card-accent {
        border-top: 5px solid #FF9800;
    }
    
    /* App Icon */
    .app-icon {
        display: inline-block;
        font-size: 2.5rem;
        background-color: #E0F2F1;
        padding: 1rem;
        border-radius: 50%;
        margin-bottom: 1rem;
        color: #00796B;
    }
    
    .app-icon-accent {
        background-color: #FFF3E0;
        color: #FF9800;
    }
    
    /* Features List */
    .features {
        list-style-type: none;
        padding-left: 0;
    }
    
    .features li {
        padding: 0.75rem 1rem;
        background-color: #E0F2F1;
        margin-bottom: 0.5rem;
        border-radius: 8px;
        display: flex;
        align-items: center;
    }
    
    .features-accent li {
        background-color: #FFF3E0;
    }
    
    .feature-icon {
        margin-right: 10px;
        font-size: 1.25rem;
    }
    
    /* Action Button */
    .action-button {
        display: inline-block;
        background: linear-gradient(135deg, #00796B 0%, #009688 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 50px;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        cursor: pointer;
        transition: all 0.3s ease;
        border: none;
        margin-top: 1rem;
        width: 100%;
    }
    
    .action-button:hover {
        background: linear-gradient(135deg, #00695C 0%, #00796B 100%);
        box-shadow: 0 6px 16px rgba(0,0,0,0.18);
        transform: translateY(-2px);
    }
    
    .action-button-accent {
        background: linear-gradient(135deg, #FF9800 0%, #FB8C00 100%);
    }
    
    .action-button-accent:hover {
        background: linear-gradient(135deg, #FB8C00 0%, #F57C00 100%);
    }
    
    /* Stats Section */
    .stats {
        display: flex;
        justify-content: space-around;
        text-align: center;
        background-color: #00796B;
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
    }
    
    .stat-label {
        opacity: 0.9;
    }
    
    /* Testimonial */
    .testimonial {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #FF9800;
        margin-bottom: 2rem;
    }
    
    .quote {
        font-style: italic;
        margin-bottom: 0.5rem;
    }
    
    .author {
        font-weight: bold;
        color: #00796B;
    }
    
    /* Footer */
    .footer {
        background: #263238;
        color: white;
        padding: 2rem;
        text-align: center;
        border-radius: 15px;
        margin-top: 2rem;
    }
    
    /* Make buttons visible and styled */
    .stButton > button {
        background: linear-gradient(135deg, #00796B 0%, #009688 100%);
        color: white !important;
        font-weight: bold;
        padding: 0.75rem 1.5rem;
        border-radius: 50px;
        border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #00695C 0%, #00796B 100%);
        box-shadow: 0 6px 16px rgba(0,0,0,0.18);
        transform: translateY(-2px);
    }
    
    /* Sidebar Styling */
    .css-1d391kg, .css-163ttbj {
        background-color: #263238;
    }
    
    .sidebar .sidebar-content {
        background-color: #263238;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # Apply custom CSS
    apply_custom_css()
    
    # Initialize session state
    if 'app_choice' not in st.session_state:
        st.session_state.app_choice = None
    
    # Show app selection if no choice made
    if st.session_state.app_choice is None:
        show_app_selection()
        return
    
    # Add a way to go back to selection
    if st.sidebar.button("← Return to Home"):
        st.session_state.app_choice = None
        st.rerun()
    
    # Run the selected application
    if st.session_state.app_choice == "ecosmart":
        run_ecosmart_app()
    elif st.session_state.app_choice == "waste_exchange":
        run_waste_exchange_app()
    elif st.session_state.app_choice == "waste_awareness":  # New option
        run_waste_awareness_app()

def show_app_selection():
    # Header
    st.markdown("""
    <div class="header">
        <h1>Waste Management Solutions</h1>
        <p>Advanced digital tools for sustainable waste management</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats Section
    st.markdown("""
    <div class="stats">
        <div>
            <div class="stat-value">85%</div>
            <div class="stat-label">Waste Reduction</div>
        </div>
        <div>
            <div class="stat-value">3+</div>
            <div class="stat-label">Active Users</div>
        </div>
        <div>
            <div class="stat-value">1kg+</div>
            <div class="stat-label">Tons Recycled</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # App Selection Section
    st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>Choose Your Solution</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="large")  # Changed to 3 columns
    
    with col1:
        st.markdown("""
        <div class="card">
            <div class="app-icon">🤖</div>
            <h3>EcoSmart Waste Assistant</h3>
            <p style="margin-bottom: 1.5rem;">
                Our AI-powered assistant analyzes your waste data and provides 
                personalized recommendations to optimize your waste management processes.
            </p>
            <div>
            <ul class="features">
                <li><span class="feature-icon">🔍</span> Smart waste classification</li>
                <li><span class="feature-icon">🌱</span> Sustainability recommendations</li>
                <li><span class="feature-icon">♻️</span> 5R principle guidance</li>
            </ul></div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Launch EcoSmart Assistant", use_container_width=True):
            st.session_state.app_choice = "ecosmart"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="card card-accent">
            <div class="app-icon app-icon-accent">💱</div>
            <h3>Waste Exchange Platform</h3>
            <p style="margin-bottom: 1.5rem;">
                Connect with businesses to buy and sell waste materials, 
                turning waste into resources and supporting the circular economy.
            </p>
            <div>
            <ul class="features features-accent">
                <li><span class="feature-icon">🏪</span> Materials marketplace</li>
                <li><span class="feature-icon">📝</span> Easy listing creation</li>
                <li><span class="feature-icon">📊</span> Transaction management</li>
            </ul></div>
        </div>
        """, unsafe_allow_html=True)
        
        col2_button = st.button("Enter Waste Exchange", use_container_width=True)
        if col2_button:
            st.session_state.app_choice = "waste_exchange"
            st.rerun()
    
    # New third column for City Cleanup Campaign
    with col3:
        st.markdown("""
        <div class="card" style="border-top-color: #8BC34A;">
            <div class="app-icon" style="background-color: #F1F8E9; color: #8BC34A;">🌎</div>
            <h3>CleanCity Initiative</h3>
            <p style="margin-bottom: 1.5rem;">
                Vote for cities that need urgent cleanup action and participate in 
                community-driven waste management campaigns.
            </p>
            <div>
            <ul class="features" style="background-color: #F1F8E9;">
                <li><span class="feature-icon">🗳️</span> Vote for cleanup locations</li>
                <li><span class="feature-icon">👥</span> Report waste issues</li>
                <li><span class="feature-icon">🏆</span> Community chat</li>
            </ul></div>
        </div>
        """, unsafe_allow_html=True)
        
        col3_button = st.button("Join Cleanup Campaign", use_container_width=True)
        if col3_button:
            st.session_state.app_choice = "waste_awareness"
            st.rerun()
    
    # Testimonial
    st.markdown("""
    <div class="testimonial">
        <p class="quote">
            "This platform has transformed how we handle waste. We've reduced disposal costs 
            significantly and found new revenue streams through the exchange platform."
        </p>
        <p class="author">— Ck257, CK Recycle Industries</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class="footer">
        <h3>Making Sustainability Simple</h3>
        <p>Our solutions help businesses reduce waste, save resources, and protect our planet.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()