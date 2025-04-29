import streamlit as st
import time
import requests
from PIL import Image
import google.generativeai as genai
import json
from collections import Counter

# Function to upload image to ImgBB
def upload_image_to_imgbb(image):
    api_url = "https://api.imgbb.com/1/upload"
    api_key = st.secrets["imgbb_api"]
    
    # Debug the API key (mask it partially for security)
    masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "Invalid key"
    st.write(f"Using ImgBB API key: {masked_key}")
    
    files = {"image": image.getvalue()}
    payload = {"key": api_key}
    
    try:
        response = requests.post(api_url, files=files, data=payload)
        st.write(f"ImgBB Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'url' in data['data']:
                return data['data']['url']
            else:
                st.error("Unexpected ImgBB response format")
                return None
        else:
            st.error(f"Error uploading image: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Exception during image upload: {e}")
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
        "x-rapidapi-key": st.secrets["Rapid_api"],
        "x-rapidapi-host": "ai-object-detection-image-analysis-object-analysis.p.rapidapi.com",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(api_url, data={}, headers=headers, params=querystring)
        st.write(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            st.write("Response keys:", list(response_data.keys()))
            return response_data
        else:
            st.error(f"API Error: {response.status_code}")
            st.write("Response text:", response.text)
            return None
    except Exception as e:
        st.error(f"Exception during API call: {e}")
        return None

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
    
    api_key = st.secrets["Gemini_api"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    object_list = ', '.join(unique_objects)
    
    prompt = f"""
    Here image is identified and all parts inside image is identified so analyse the {object_list} and assume its a single image and most of cases its a waste products,then
Generate highly creative, artistic and practical transformation ideas for these item: {object_list}  

First, focus on ARTISTIC REPURPOSING ideas - these should be your most creative and detailed suggestions. For each item, provide 5 specific, step-by-step artistic transformations that turn waste into beautiful or functional art objects.

For example, for broken glass:
1. "Create sea glass jewelry by tumbling broken glass pieces with sand and water, then wire-wrapping the smoothed pieces into pendants and earrings"
2. "Make a stunning mosaic table by arranging colored glass fragments in a pattern on a wooden surface, then securing with grout and finishing with resin"
3. "Create stained glass wind chimes by wrapping the edges of glass pieces with copper foil tape and soldering them together with wire connectors"

Then provide suggestions for each of the 5Rs:
...
For REFUSE suggestions:
- Focus on direct substitutes people can make themselves (e.g., "Make your own reusable food wraps from beeswax and cotton instead of buying plastic wrap")
- Describe DIY alternatives to purchasing new items
- Suggest specific ways to adapt existing items instead of buying this one

For REDUCE suggestions:
- Provide specific maintenance techniques to extend the item's life dramatically
- Describe exact methods to repair or restore the item when it starts failing
- Explain how to maximize the item's utility through specific modifications

For REUSE suggestions:
- Describe exact methods to clean, sanitize or restore the item for continued use
- Suggest specific secondary uses in its current form
- Provide concrete examples of how to share or redistribute the item

For REPURPOSE suggestions:
- Give step-by-step transformation ideas (e.g., "Cut the bottom off glass bottles to create self-watering planters")
- Describe artistic or functional projects that transform the item completely
- Include surprising combinations with other common items to create something new

For RECYCLE suggestions:
- Explain exactly how to prepare the item for optimal recycling
- Mention specific places or programs that accept this particular item
- Suggest creative ways to separate components for proper recycling

VERY IMPORTANT: Each suggestion must be:
1. Specific and actionable - describe exactly what to do with the item
2. Practical and doable by an average person
3. Creative and unexpected - go beyond obvious ideas
4. Focused on physical transformation where appropriate
5. Written as clear instructions a person could follow

Return a valid JSON object with this structure:
{{
    "{object_list}": {{
        "refuse": [
            "Specific actionable suggestion 1",
            "Specific actionable suggestion 2",
            "Specific actionable suggestion 3",
            "Specific actionable suggestion 4",
            "Specific actionable suggestion 5"
        ],
        "reduce": [
            "Specific actionable suggestion 1",
            "Specific actionable suggestion 2",
            "Specific actionable suggestion 3",
            "Specific actionable suggestion 4",
            "Specific actionable suggestion 5"
        ],
        "reuse": [
            "Specific actionable suggestion 1",
            "Specific actionable suggestion 2",
            "Specific actionable suggestion 3",
            "Specific actionable suggestion 4",
            "Specific actionable suggestion 5"
        ],
        "repurpose": [
            "Specific actionable suggestion 1",
            "Specific actionable suggestion 2",
            "Specific actionable suggestion 3",
            "Specific actionable suggestion 4",
            "Specific actionable suggestion 5"
        ],
        "recycle": [
            "Specific actionable suggestion 1",
            "Specific actionable suggestion 2",
            "Specific actionable suggestion 3",
            "Specific actionable suggestion 4",
            "Specific actionable suggestion 5"
        ]
    }}
}}

Focus heavily on creative REPURPOSE ideas that transform the item into something completely different and useful.
"""

    try:
        result = model.generate_content(prompt)
        response_text = result._result.candidates[0].content.parts[0].text
        
        # Validate JSON
        json.loads(response_text)
        return response_text
    except Exception as e:
        # Return object-specific creative transformation suggestions
        transformation_ideas = {
            "glass": {
                "refuse": [
                    "Make your own glass storage containers by cutting the tops off bottles with a glass cutter tool",
                    "Create a reusable water bottle by cutting a glass bottle and attaching a cork stopper",
                    "Make your own glass straws by cutting glass tubing and sanding the ends smooth",
                    "Create custom glass soap dispensers from olive oil bottles instead of buying plastic ones",
                    "Cut the bottoms off wine bottles to create plant protectors for your garden"
                ],
                "reduce": [
                    "Repair cracked glassware with food-safe epoxy resin to extend its life",
                    "Restore cloudy glass by soaking in vinegar and baking soda solution for 30 minutes",
                    "Cover glass containers with silicone sleeves to prevent breakage during transport",
                    "Use glass jar lid screws on mason jars to create spill-proof drink containers",
                    "Apply rubber gaskets to glass containers to create airtight seals that preserve contents longer"
                ],
                "reuse": [
                    "Clean glass jars with baking soda paste to remove labels and adhesive for food storage",
                    "Store homemade sauces and jams in sterilized glass jars with proper canning techniques",
                    "Convert wine bottles into olive oil dispensers with pouring spouts",
                    "Use glass baby food jars as spice containers with labels on the lids",
                    "Create tiered serving trays by gluing glass plates of decreasing sizes with candlesticks between"
                ],
                "repurpose": [
                    "Transform broken glass pieces into stunning mosaic garden stepping stones with cement",
                    "Cut the bottoms off wine bottles to create elegant candle holders for your patio",
                    "Melt broken glass in a microwave kiln to create unique pendants and earrings",
                    "Convert glass bottles into self-watering planters by inserting a cotton wick",
                    "Make sea glass-style decorations by tumbling broken glass with sand and water"
                ],
                "recycle": [
                    "Crush colored glass pieces into gravel-sized fragments for decorative garden mulch",
                    "Separate glass by color (clear, green, brown) before taking to recycling centers",
                    "Remove metal caps, corks and plastic labels before recycling glass bottles",
                    "Locate specialty glass recyclers for window glass, mirrors, and heat-resistant glass",
                    "Check if your local artists' collective accepts donated glass for mosaic projects"
                ]
            },
            # Other transformation ideas for different materials (as in your original code)
            # ...
        }
        
        # Removed the duplicate "repurpose" key that was in your original code
        
        # More fallback logic (as in your original code)
        # ...
        
        # Generic fallback response when all else fails
        generic_transformations = {
            "refuse": [
                f"Create your own {object_list} alternative using sustainable materials like bamboo or reclaimed wood",
                f"Build a multipurpose tool that replaces the need for a dedicated {object_list}",
                f"Design a {object_list} substitute from materials you already have at home",
                f"Make a biodegradable version of {object_list} using natural materials",
                f"Create a community sharing system for occasionally used {object_list} instead of buying"
            ],
            "reduce": [
                f"Apply a protective coating of beeswax and mineral oil to extend {object_list} life",
                f"Create a custom storage solution to prevent damage to your {object_list}",
                f"Repair {object_list} by reinforcing weak points with natural twine or metal wire",
                f"Restore worn {object_list} surfaces using sandpaper and natural oils",
                f"Create a maintenance kit specifically designed for your {object_list}"
            ],
            "reuse": [
                f"Convert your {object_list} into a vertical storage system for small items",
                f"Transform {object_list} into a custom-designed garden tool or plant support",
                f"Use your {object_list} as a unique mold for concrete or clay projects",
                f"Adapt your {object_list} into a specialized cooking tool for your kitchen",
                f"Modify your {object_list} to create a one-of-a-kind musical instrument"
            ],
            "repurpose": [
                f"Transform your {object_list} into wall art by mounting it on reclaimed wood",
                f"Convert your {object_list} into a unique lamp with simple electrical components",
                f"Create a bird feeder or bath using your {object_list} as the main structure",
                f"Build a kids' toy or game using your {object_list} as the central element",
                f"Make a statement piece of furniture by incorporating your {object_list} in the design"
            ],
            "recycle": [
                f"Disassemble your {object_list} into component materials for separate recycling",
                f"Donate your {object_list} to art schools for sculpture or mixed media projects",
                f"Create mulch or compost from any biodegradable parts of your {object_list}",
                f"Research specialty recycling facilities that accept your specific {object_list} type",
                f"Contact manufacturers about take-back programs for your {object_list}"
            ]
        }
        
        # Return a valid JSON for a generic case
        return json.dumps({object_list: generic_transformations}, indent=2)


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

def run_ecosmart_app():
    st.title("🌍 EcoSmart Waste Assistant")
    st.markdown("*Transform waste into opportunity*")

    uploaded_file = st.file_uploader(
        "Upload an image of your items", 
        type=["jpg", "jpeg", "png"], 
        help="Select an image to analyze potential waste management strategies"
    )

    if uploaded_file is not None:
        process_image(uploaded_file)
    
    display_footer()

def process_image(uploaded_file):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

    with col2:
        with st.spinner("🔍 Analyzing image..."):
            try:
                # Upload the image to ImgBB
                image_url = upload_image_to_imgbb(uploaded_file)
                if not image_url:
                    st.error("Failed to upload the image. Please try again.")
                    return

                # Call the object detection API
                response_data = call_object_detection_api(image_url)
                
                # Check if we got a valid response
                if not response_data:
                    st.error("Failed to analyze the image. Please try a different image.")
                    return
                
                # Debug response structure
                st.write("Response keys:", list(response_data.keys()))
                
                # Extract objects from response with additional validation
                if 'result' in response_data and isinstance(response_data['result'], list):
                    extracted_objects = [item.get('name', 'Unknown Object') for item in response_data['result']]
                    if not extracted_objects:
                        st.warning("No objects detected in the image. Using default object 'Item'.")
                        extracted_objects = ['Item']
                else:
                    # Handle missing or invalid 'result' field
                    st.warning("API response format unexpected. Using default object 'Item'.")
                    extracted_objects = ['Item']
                    
                # Continue with processing
                cleaned_objects = [clean_object_name(obj) for obj in extracted_objects]
                object_counts = Counter(cleaned_objects)
                
                st.markdown("### 🏷️ Detected Objects")
                for obj, count in object_counts.items():
                    st.write(f"{obj} (×{count})")
                
                # Generate suggestions based on detected objects
                suggestions_text = generate_5r_suggestions(extracted_objects)
                
                # Display the suggestions
                display_suggestions(suggestions_text, object_counts)
            
            except Exception as e:
                st.error(f"😓 Oops! Something went wrong: {e}")
                st.error("Please try a different image or check your internet connection.")
                # Add debugging information
                import traceback
                st.write("Error details:")
                st.write(traceback.format_exc())

def display_suggestions(suggestions_text, object_counts):
    st.markdown("### ♻️ 5R Sustainability Suggestions")
    
    try:
        suggestions_dict = json.loads(suggestions_text)
        
        for obj_name, categories in suggestions_dict.items():
            # Handle case where the cleaned object name might not be in object_counts
            count = object_counts.get(clean_object_name(obj_name), 1)
            st.markdown(f"""
                <div class="object-header">
                    📦 {obj_name} {f'(×{count})' if count > 1 else ''}
                </div>
            """, unsafe_allow_html=True)
            
            # Creative Transformations Highlight
            st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
                    border-radius: 10px;
                    padding: 15px;
                    margin-bottom: 20px;
                    color: white;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                ">
                    <h3 style="margin-top: 0; display: flex; align-items: center;">
                        <span style="margin-right: 10px;">✨</span> Creative Transformation Ideas
                    </h3>
            """, unsafe_allow_html=True)
            
            # Extract top creative ideas from repurpose category
            creative_ideas = categories.get('repurpose', [])[:3]  # Take top 3 creative ideas
            
            for idea in creative_ideas:
                st.markdown(f"""
                    <div style="
                        background-color: rgba(255,255,255,0.1);
                        border-radius: 8px;
                        padding: 12px;
                        margin-bottom: 10px;
                    ">
                        <div style="display: flex; align-items: center;">
                            <span style="font-size: 24px; margin-right: 12px;">🎨</span>
                            <span>{idea}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
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
                # Make sure category exists in the data
                if category in categories:
                    suggestions = categories[category]
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
                else:
                    # Handle missing category
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
                            <p>No suggestions available for this category.</p>
                        </div>
                    """, unsafe_allow_html=True)
            
            # Close horizontal container
            st.markdown("</div>", unsafe_allow_html=True)
    
    except json.JSONDecodeError as e:
        st.error(f"Error processing suggestions: {e}")
        st.write("Raw suggestions text (for debugging):")
        st.code(suggestions_text[:500] + "..." if len(suggestions_text) > 500 else suggestions_text)

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

if __name__ == "__main__":
    run_ecosmart_app()
