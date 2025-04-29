import time
import streamlit as st
import requests
from PIL import Image
import google.generativeai as genai
import json
from collections import Counter



# Function to upload image to ImgBB
def upload_image_to_imgbb(image):
    api_url = "https://api.imgbb.com/1/upload"
    api_key = "5925c1f71b047e5f719d217d4ae353ac"
    
    files = {"image": image.getvalue()}
    payload = {"key": api_key}
    
    response = requests.post(api_url, files=files, data=payload)
    
    if response.status_code == 200:
        return response.json()['data']['url']
    else:
        st.write(f"Error uploading image: {response.status_code}")
        return None

# Function to call object detection API
def call_object_detection_api(image_url):
    api_url = "https://ai-object-detection-image-analysis-object-analysis.p.rapidapi.com/check"
    querystring = {
        "language": "en",
        "imageUrl": image_url,
        "noqueue": "1"
    }
    headers = {
        "x-rapidapi-key": "8bb9930ecbmshde8a48ada585d84p1abda5jsn8b465635a679",
        "x-rapidapi-host": "ai-object-detection-image-analysis-object-analysis.p.rapidapi.com",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(api_url, data={}, headers=headers, params=querystring)
    return response.json()

# Function to clean object names
def clean_object_name(name):
    """Clean and standardize object names."""
    # Remove directional prefixes and numbers
    common_prefixes = ['left', 'right', 'front', 'back', 'top', 'bottom']
    words = name.lower().split()
    
    # Remove directional words and numbers
    cleaned_words = [
        word for word in words 
        if not any(c.isdigit() for c in word)
        and word not in common_prefixes
    ]
    
    return ' '.join(cleaned_words).strip().title()

# Function to format suggestions with icons
def format_suggestion(suggestion):
    action_emojis = {
        "buy": "🛍️", "choose": "✅", "avoid": "⛔", "donate": "🎁",
        "recycle": "♻️", "reuse": "🔄", "create": "🎨", 
        "transform": "✨", "repair": "🔧", "clean": "🧹",
        "check": "✔️", "use": "👍", "make": "🛠️", "turn": "🔄"
    }
    
    for action, emoji in action_emojis.items():
        if action.lower() in suggestion.lower():
            return f"{emoji} {suggestion}"
    return f"• {suggestion}"

# Function to generate 5R suggestions
def generate_5r_suggestions(objects):
    cleaned_objects = [clean_object_name(obj) for obj in objects]
    unique_objects = list(set(cleaned_objects))
    
    api_key = 'AIzaSyAnTnUdsQkXQklacaB5UKWc5jTORUKBWhE'
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    object_list = ', '.join(unique_objects)
    
    prompt = f"""
Generate detailed 5R (Refuse, Reduce, Reuse, Repurpose, Recycle) suggestions for: {object_list}

For each category, provide 5 specific suggestions that are:
1. Practical and immediately actionable
2. Focused on environmental impact
3. Cost-effective for the average person
4. Creative but realistic
5. Specific to the material and type of item

Return a valid JSON object with this structure:

{{
    "{object_list}": {{
        "refuse": [
            "Specific suggestion about avoiding new purchases",
            "Alternative option to buying new",
            "Way to prevent accumulating more",
            "Sustainable choice instead of buying",
            "Method to avoid unnecessary consumption"
        ],
        "reduce": [
            "Way to minimize usage or purchase",
            "Method to extend lifespan",
            "Approach to reduce consumption",
            "Maintenance tip to reduce replacement",
            "Strategy to minimize waste"
        ],
        "reuse": [
            "Direct reuse suggestion",
            "Alternative use case",
            "Sharing or donation approach",
            "Repair or restoration method",
            "Creative reuse idea"
        ],
        "repurpose": [
            "Creative transformation idea",
            "New use case",
            "Artistic repurposing suggestion",
            "Practical conversion method",
            "Innovative reuse approach"
        ],
        "recycle": [
            "Proper recycling method",
            "Material separation technique",
            "Local recycling option",
            "Recycling program suggestion",
            "Responsible disposal approach"
        ]
    }}
}}

Ensure suggestions are detailed, specific to {object_list}, and focus on real-world application.
"""

    try:
        result = model.generate_content(prompt)
        response_text = result._result.candidates[0].content.parts[0].text
        
        # Validate JSON
        json.loads(response_text)
        return response_text
    except Exception as e:
        # Return fallback response with more specific suggestions
        return json.dumps({
            object_list: {
                "refuse": [
                    "Invest in high-quality, durable alternatives",
                    "Choose products with sustainable materials",
                    "Avoid impulse purchases and trendy items",
                    "Say no to items with excessive packaging",
                    "Select items with longer warranties"
                ],
                "reduce": [
                    "Buy only when absolutely necessary",
                    "Choose versatile designs that work for multiple occasions",
                    "Practice proper maintenance to extend lifespan",
                    "Consider renting for occasional use",
                    "Share resources within community"
                ],
                "reuse": [
                    "Donate to local charities or shelters",
                    "Organize swap meets with friends",
                    "Repair and restore when possible",
                    "Pass down to family members",
                    "Use for alternative purposes"
                ],
                "repurpose": [
                    "Transform into decorative items",
                    "Convert into storage solutions",
                    "Create artistic projects",
                    "Use parts for other purposes",
                    "Make into protective equipment"
                ],
                "recycle": [
                    "Research local recycling programs",
                    "Separate different materials properly",
                    "Support manufacturer take-back programs",
                    "Find specialized recycling facilities",
                    "Learn about material-specific recycling"
                ]
            }
        }, indent=2)

# Streamlit app setup
st.set_page_config(
    page_title="EcoSmart Waste Assistant", 
    page_icon="♻️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS
st.markdown("""
    <style>
        /* Global Typography */
        body {
            font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
            color: #2c3e50;
        }

        /* Page Header */
        .stApp > header {
            background-color: rgba(46, 204, 113, 0.1);
        }

        /* Title Styling */
        h1 {
            color: #2ecc71;
            font-weight: 700;
            text-align: center;
            margin-bottom: 1.5rem;
        }

        /* Image Upload Card */
        .stFileUploader {
            background-color: #f9f9f9;
            border-radius: 12px;
            padding: 1rem;
            border: 2px dashed #2ecc71;
            transition: all 0.3s ease;
        }

        .stFileUploader:hover {
            background-color: #f0f8f3;
            border-color: #27ae60;
        }

        /* Suggestion Styling */
        .suggestion-box {
            background-color: #ecf0f1;
            border-left: 5px solid #3498db;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }

        .suggestion-box:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }

        .category-header {
            font-size: 1.2rem;
            color: #2980b9;
            font-weight: 600;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
        }

        .category-header span {
            margin-right: 0.5rem;
            font-size: 1.5rem;
        }

        .suggestion-item {
            background-color: white;
            border-radius: 6px;
            padding: 0.5rem;
            margin-bottom: 0.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            transition: background-color 0.3s ease;
        }

        .suggestion-item:hover {
            background-color: #f1f8ff;
        }

        .object-header {
            background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
            color: white;
            padding: 0.75rem 1.25rem;
            border-radius: 10px;
            margin: 1.5rem 0 1rem 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .footer {
            background-color: #f4f4f4;
            padding: 1.5rem;
            border-radius: 12px;
            margin-top: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("🌍 EcoSmart Waste Management Assistant")
    st.markdown("*Transform waste into opportunity*")

    uploaded_file = st.file_uploader(
        "Upload an image of your items", 
        type=["jpg", "jpeg", "png"], 
        help="Select an image to analyze potential waste management strategies"
    )

    if uploaded_file is not None:
        process_image(uploaded_file)

def process_image(uploaded_file):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

    with col2:
        with st.spinner("🔍 Analyzing image..."):
            try:
                image_url = upload_image_to_imgbb(uploaded_file)
                response_data = call_object_detection_api(image_url)
                
                extracted_objects = [item.get('name', 'Unknown Object') for item in response_data['result']]
                cleaned_objects = [clean_object_name(obj) for obj in extracted_objects]
                object_counts = Counter(cleaned_objects)
                
                st.markdown("### 🏷️ Detected Objects")
                for obj, count in object_counts.items():
                    st.write(f"{obj} (×{count})")
                
                suggestions_text = generate_5r_suggestions(extracted_objects)
                
                display_suggestions(suggestions_text, object_counts)
            
            except Exception as e:
                st.error(f"😓 Oops! Something went wrong: {e}")
                st.error("Please try a different image or check your internet connection.")

def display_suggestions(suggestions_text, object_counts):
    st.markdown("### ♻️ 5R Sustainability Suggestions")
    
    try:
        suggestions_dict = json.loads(suggestions_text)
        
        for obj_name, categories in suggestions_dict.items():
            count = object_counts[clean_object_name(obj_name)]
            st.markdown(f"""
                <div class="object-header">
                    📦 {obj_name} {f'(×{count})' if count > 1 else ''}
                </div>
            """, unsafe_allow_html=True)
            
            # Create horizontal container for 5R categories
            st.markdown("""
                <div style="display: flex; gap: 15px; overflow-x: auto; padding: 10px 0;">
            """, unsafe_allow_html=True)
            
            category_details = [
                ('refuse', '🚫', '#e74c3c', '#fdedee'),
                ('reduce', '📉', '#f39c12', '#fff4e6'),
                ('reuse', '🔄', '#3498db', '#e8f4f8'),
                ('repurpose', '🎨', '#9b59b6', '#f4ecf7'),
                ('recycle', '♻️', '#2ecc71', '#eafaf1')
            ]
            
            for category, icon, border_color, bg_color in category_details:
                suggestions = suggestions_dict[obj_name][category]
                st.markdown(f"""
                    <div style="
                        flex: 0 0 250px; 
                        border: 2px solid {border_color};
                        border-radius: 10px;
                        padding: 15px;
                        background-color: {bg_color};
                        min-height: 350px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    ">
                        <h4 style="color: #2c3e50; display: flex; align-items: center;">
                            {icon} {category.title()}
                        </h4>
                        <ul style="list-style-type: none; padding: 0;">
                            {''.join(f'<li style="margin-bottom: 10px; display: flex; align-items: center;">{format_suggestion(suggestion)}</li>' for suggestion in suggestions)}
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
            
            # Close horizontal container
            st.markdown("</div>", unsafe_allow_html=True)
    
    except json.JSONDecodeError:
        st.error("Error processing suggestions.")
# Footer Section
def display_footer():
    st.markdown("""
        <div class="footer">
            <h3>📘 About 5R Principles</h3>
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <strong>🚫 Refuse:</strong> Avoid unnecessary items<br>
                    <strong>📉 Reduce:</strong> Minimize consumption
                </div>
                <div>
                    <strong>🔄 Reuse:</strong> Multiple item uses<br>
                    <strong>🎨 Repurpose:</strong> New item purposes
                </div>
                <div>
                    <strong>♻️ Recycle:</strong> Transform materials
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# App Execution
if __name__ == "__main__":
    main()
    display_footer()