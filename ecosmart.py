import streamlit as st
import time
import requests
from PIL import Image
import google.generativeai as genai
import json
from collections import Counter

# Copy all functions from your original EcoSmart code here
def upload_image_to_imgbb(image):
    api_url = "https://api.imgbb.com/1/upload"
    api_key = st.secrets["imgbb_api"]
    
    files = {"image": image.getvalue()}
    payload = {"key": api_key}
    
    response = requests.post(api_url, files=files, data=payload)
    
    if response.status_code == 200:
        return response.json()['data']['url']
    else:
        st.write(f"Error uploading image: {response.status_code}")
        return None

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
    api_key = st.secrets["imgbb_api"]
    
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
        "x-rapidapi-key": st.secrets["Rapid_api"],
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
    
    api_key = 'AIzaSyAnTnUdsQklacaB5UKWc5jTORUKBWhE'
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
                ],
                "repurpose": [
        "Transform broken glass pieces into stunning mosaic garden stepping stones with cement",
        "Cut the bottoms off wine bottles to create elegant candle holders for your patio",
        "Melt broken glass in a microwave kiln to create unique pendants and earrings",
        "Create a decorative wind chime by wrapping copper wire around glass fragments",
        "Design an illuminated art piece by embedding glass pieces in resin with LED lights"
    ],
            },
            "plastic": {
                "refuse": [
                    "Make your own beeswax wraps using cotton scraps and beeswax instead of plastic wrap",
                    "Create reusable mesh produce bags from old curtain sheers to replace plastic produce bags",
                    "Sew cloth bowl covers from cotton fabric and elastic instead of using plastic wrap",
                    "Make your own plastic-free scrubbers from dried loofah gourds cut into slices",
                    "Create your own bamboo utensil set with a carrying case made from fabric scraps"
                ],
                "reduce": [
                    "Repair cracked plastic containers with a heated needle to melt edges together",
                    "Restore yellowed plastic by soaking in hydrogen peroxide and placing in sunlight",
                    "Extend plastic container life by hand-washing instead of dishwashing to prevent warping",
                    "Reinforce plastic bag handles with decorative duct tape to make them reusable",
                    "Apply food-grade mineral oil to plastic cutting boards to prevent cracking"
                ],
                "reuse": [
                    "Clean plastic containers with baking soda paste to remove tomato sauce stains",
                    "Use plastic bottle spray tops on glass bottles for homemade cleaning solutions",
                    "Convert plastic milk jugs into watering cans by poking small holes in the cap",
                    "Turn plastic containers into drawer organizers with custom dividers",
                    "Use plastic takeout containers for seed starting with drainage holes added"
                ],
                "repurpose": [
                    "Cut plastic bottles into spiral strips to make colorful plant markers",
                    "Transform plastic 6-pack rings into small organizational grids for desk drawers",
                    "Melt plastic bottle caps in the oven (with ventilation) to create mosaic art pieces",
                    "Convert plastic containers into hanging planters with macramé hangers",
                    "Turn plastic bottles into bird feeders by cutting side openings and adding perches"
                ],
                "recycle": [
                    "Clean food residue from plastic containers with cold water to save energy",
                    "Remove paper labels from plastic bottles to improve recyclability",
                    "Separate plastic by resin code (numbers 1-7) before recycling",
                    "Take plastic bags and film to grocery store collection points, not curbside",
                    "Find TerraCycle programs for hard-to-recycle plastics like toothpaste tubes"
                ]
            },
            "paper": {
                "refuse": [
                    "Create reusable cloth gift bags from fabric scraps instead of wrapping paper",
                    "Make your own notebook from single-sided printed paper bound with string",
                    "Design your own greeting cards from cardstock scraps and pressed flowers",
                    "Create digital shopping lists on your phone instead of paper lists",
                    "Set up a digital receipt system with vendors to avoid paper copies"
                ],
                "reduce": [
                    "Print on both sides of paper to cut paper consumption in half",
                    "Use smaller margins and fonts to fit more content on each page",
                    "Repair torn books with Japanese washi tape for a decorative fix",
                    "Extend the life of paper towels by cutting each sheet in half",
                    "Reuse envelopes by placing a new label over the old address"
                ],
                "reuse": [
                    "Turn used envelopes into scratch paper pads with binder clips",
                    "Use newspaper to clean windows streak-free (with vinegar spray)",
                    "Shred paper to use as packaging material instead of bubble wrap",
                    "Use coffee filters to strain yogurt for a thicker Greek-style result",
                    "Line vegetable drawers with newspaper to absorb excess moisture"
                ],
                "repurpose": [
                    "Create paper mache bowls using old newspaper strips and flour paste",
                    "Roll magazine pages into tight tubes to create colorful coasters",
                    "Make fire starters by rolling newspaper and dipping in melted wax",
                    "Create decorative wall art by weaving strips of colorful magazine pages",
                    "Transform cereal boxes into desk organizers with decorative paper covering"
                ],
                "recycle": [
                    "Remove plastic windows from envelopes before recycling the paper portion",
                    "Soak paper egg cartons to make seed starting pots that decompose when planted",
                    "Compost shredded paper to add carbon to your compost pile",
                    "Remove staples and paper clips before recycling documents",
                    "Check if your local recycling accepts shredded paper (often needs to be bagged)"
                ]
            },
            "metal": {
                "refuse": [
                    "Make your own reusable metal straw from copper or stainless steel tubing",
                    "Create DIY cake pans by shaping heavy-duty aluminum foil over bowls",
                    "Use a metal tea infuser instead of buying tea bags with metal staples",
                    "Make your own gardening tools from old flatware (spoon plant markers)",
                    "Create reusable metal clothespins from wire coat hangers"
                ],
                "reduce": [
                    "Remove rust from metal tools by soaking in white vinegar overnight",
                    "Apply food-grade mineral oil to cast iron and carbon steel to prevent rust",
                    "Repair small holes in metal pots with food-safe epoxy",
                    "Sharpen dull metal knives with a whetstone to extend their life",
                    "Clean tarnished metal with baking soda and aluminum foil electrochemical process"
                ],
                "reuse": [
                    "Convert coffee cans into desk organizers with decorative coverings",
                    "Use tin cans as herb planters with drainage holes punched in the bottom",
                    "Turn metal bottle caps into refrigerator magnets with adhesive magnet strips",
                    "Reuse metal jar lids as coasters by lining with cork or felt",
                    "Create cookie cutters from aluminum cans by shaping with pliers"
                ],
                "repurpose": [
                    "Transform old silverware into unique jewelry, wind chimes, or garden markers",
                    "Create industrial-style shelving brackets from metal pipes and fittings",
                    "Make a modern wall clock from bicycle gears and an inexpensive clock mechanism",
                    "Convert a metal colander into a hanging planter with chains or macramé",
                    "Turn metal cookie tins into drum-style side tables with added legs"
                ],
                "recycle": [
                    "Separate different metals (aluminum, steel, copper) before recycling",
                    "Clean food residue from metal cans before recycling to avoid contamination",
                    "Keep metal lids with their containers, but loosely placed inside",
                    "Find scrap metal yards that pay by weight for larger metal items",
                    "Check if your recycling program accepts aerosol cans (empty and depressurized)"
                ]
            },
            "fabric": {
                "refuse": [
                    "Make your own cleaning rags from old t-shirts instead of buying disposable wipes",
                    "Create cloth napkins from fabric scraps with simple hemmed edges",
                    "Sew reusable produce bags from old sheets or curtains with drawstring tops",
                    "Make your own wool dryer balls from old wool sweaters to replace dryer sheets",
                    "Create fabric gift wrap from decorative scarves that become part of the gift"
                ],
                "reduce": [
                    "Repair small holes in clothing using the Japanese Sashiko embroidery technique",
                    "Extend jeans life by reinforcing the inner thighs with iron-on patches",
                    "Turn worn shirt collars inside out for a fresh look and extended wear",
                    "Dye faded clothing with natural dyes like avocado pits (pink) or tea (brown)",
                    "Apply beeswax to canvas items to make them water-resistant and longer-lasting"
                ],
                "reuse": [
                    "Convert stained t-shirts into workout or gardening clothes",
                    "Turn old bedsheets into drop cloths for painting projects",
                    "Use outgrown children's clothes as doll or stuffed animal clothing",
                    "Repurpose old towels as pet bedding or bath mats",
                    "Turn fabric scraps into reusable makeup remover pads with simple stitching"
                ],
                "repurpose": [
                    "Create a t-shirt quilt from shirts with sentimental value",
                    "Make floor poufs by stuffing large fabric bags with plastic bags or fabric scraps",
                    "Turn jeans into a sturdy market bag by sewing the legs closed and adding handles",
                    "Create pet toys by braiding strips of old t-shirts and tying knots",
                    "Make a memory bear from a loved one's clothing as a keepsake"
                ],
                "recycle": [
                    "Cut worn-out cotton clothing into strips for rag rug making",
                    "Shred clean natural-fiber fabrics to use as stuffing for pillows",
                    "Donate worn textiles to animal shelters for bedding material",
                    "Find textile recycling programs that convert fabric to insulation",
                    "Compost 100% natural fiber fabrics after removing synthetic threads and buttons"
                ]
            },
            "electronics": {
                "refuse": [
                    "Build a simple solar charger from old solar garden lights instead of buying new",
                    "Create a smartphone projector from a magnifying glass and a shoebox",
                    "Make your own stylus from aluminum foil and a cotton swab",
                    "Build a laptop cooling pad from mesh wire and old computer fans",
                    "Create a DIY bluetooth speaker from upcycled materials and salvaged components"
                ],
                "reduce": [
                    "Clean laptop cooling vents with compressed air to prevent overheating damage",
                    "Replace failing smartphone batteries instead of upgrading the entire phone",
                    "Apply heat sink compound to processors in overheating computers to extend life",
                    "Use a voltage regulator to protect electronics from power surges",
                    "Update firmware on older devices to optimize performance and security"
                ],
                "reuse": [
                    "Convert an old smartphone into a dedicated security camera with security apps",
                    "Turn an outdated tablet into a digital recipe book in your kitchen",
                    "Repurpose old laptops as media centers connected to your TV",
                    "Use old digital cameras as webcams with adapter software",
                    "Turn old smartphones into smart home controllers or music players"
                ],
                "repurpose": [
                    "Create a desk lamp from computer parts with LED lights",
                    "Make wall art from colorful circuit boards mounted in frames",
                    "Transform computer towers into side tables with added shelving",
                    "Convert old keyboards into unique jewelry by using the keys",
                    "Turn CD/DVD drives into automatic pet feeders with simple electronics"
                ],
                "recycle": [
                    "Remove batteries from electronics for separate specialized recycling",
                    "Erase personal data from storage devices before recycling",
                    "Disassemble electronics to separate plastic, metal, and circuit boards",
                    "Look for manufacturer take-back programs for responsible recycling",
                    "Donate working electronics to schools or nonprofit refurbishing programs"
                ]
            },
            "wood": {
                "refuse": [
                    "Make your own cutting board from scrap hardwood pieces joined together",
                    "Create wood plant markers from tree branches sliced at an angle",
                    "Build your own compost bin from wooden pallets instead of buying plastic ones",
                    "Make wooden toys from scrap lumber with non-toxic finishes",
                    "Craft your own wooden utensils from fallen branches using simple carving tools"
                ],
                "reduce": [
                    "Apply linseed oil to wooden cutting boards monthly to prevent cracking",
                    "Restore scratched wood furniture with a mixture of vinegar and olive oil",
                    "Repair wobbly chairs by reinforcing joints with wood glue and clamps",
                    "Sand and refinish wooden floors instead of replacing them",
                    "Protect outdoor wood with natural beeswax and mineral oil sealer"
                ],
                "reuse": [
                    "Convert wooden pallets into vertical gardens with attached planters",
                    "Use wine crates as wall-mounted shelving with brackets",
                    "Turn wooden crates into rustic storage ottomans with added cushions",
                    "Repurpose wooden ladders as blanket or towel racks",
                    "Use tree stumps as natural outdoor seating or side tables"
                ],
                "repurpose": [
                    "Transform an old wooden door into a headboard with decorative molding",
                    "Create a garden trellis from wooden bed frames or cribs",
                    "Make floating shelves from old wooden drawers with hidden brackets",
                    "Turn wooden fence pickets into rustic wall art or signs",
                    "Convert wooden shutters into folding privacy screens or room dividers"
                ],
                "recycle": [
                    "Chip clean wood scraps for garden mulch or compost material",
                    "Find woodworking clubs that accept scrap wood for student projects",
                    "Turn sawdust into fire starters by mixing with melted wax in egg cartons",
                    "Donate usable lumber to habitat for humanity or similar building programs",
                    "Use wood ashes from untreated wood as garden fertilizer for alkaline-loving plants"
                ]
            }
        }
        
        # Specific transformation ideas for unique objects
        specialized_items = {
            "threaded rod": {
                "refuse": [
                    "Use bamboo dowels with carved threads for light-duty applications",
                    "Create your own fastening systems from twisted wire for craft projects",
                    "Use natural jute rope with knots instead of threaded systems for garden projects",
                    "Replace metal threaded systems with wooden dowel and hole joinery for furniture",
                    "Use interlocking notched wood joints instead of threaded fasteners for cabinets"
                ],
                "reduce": [
                    "Apply food-grade mineral oil to prevent rust and extend the life of threaded rods",
                    "Create protective caps from plastic tubing to cover thread ends during storage",
                    "Re-tap damaged threads using a threading die to restore functionality",
                    "Clean threads with a wire brush and vinegar solution to remove rust and debris",
                    "Store in PVC tubes with endcaps to protect threads from damage"
                ],
                "reuse": [
                    "Use threaded rods as sturdy support stakes for large garden plants",
                    "Create adjustable shelving brackets using threaded rods with nuts as stops",
                    "Make custom curtain rods by adding decorative finials to threaded rods",
                    "Use as supports for DIY hydroponics systems with plastic pipe",
                    "Create hanging pot racks with threaded rods and S-hooks"
                ],
                "repurpose": [
                    "Create industrial-style table legs by combining threaded rods with pipe fittings",
                    "Make modern coat racks by mounting threaded rods at angles in a wooden base",
                    "Design a minimalist wine rack using threaded rods through drilled wooden blocks",
                    "Build a custom spice rack with glass jars suspended between threaded rod frames",
                    "Craft a unique vertical garden by threading pots with center holes onto rods"
                ],
                "recycle": [
                    "Clean thoroughly and donate to school shop classes for student projects",
                    "Offer on neighborhood sharing apps for others' DIY projects",
                    "Take to scrap metal recyclers who accept steel or other metal types",
                    "Bring to hardware store recycling programs that accept metal building materials",
                    "Contact local artists who work with metal for possible creative reuse"
                ]
            },
            "bottle": {
                "refuse": [
                    "Make your own reusable water bottle by retrofitting a mason jar with a pump lid",
                    "Create a self-filtering water system using activated charcoal in a ceramic vessel",
                    "Grow aloe plants in your kitchen for natural gel instead of buying bottled aloe",
                    "Make your own fermented drinks in ceramic crocks instead of buying bottled versions",
                    "Install a wall-mounted soap dispenser instead of using bottle dispensers"
                ],
                "reduce": [
                    "Add a small marble to pump bottles to raise the bottom and access all product",
                    "Cut lotion bottles in half when nearly empty to access 25% more product",
                    "Dilute concentrated products correctly to make bottles last twice as long",
                    "Apply silicone sleeves to glass bottles to prevent breakage and extend life",
                    "Create a bottle inverter from a binder clip to extract every last drop"
                ],
                "reuse": [
                    "Clean wine bottles to use as water carafes with decorative stoppers",
                    "Reuse spray bottles for homemade cleaning solutions with essential oils",
                    "Use glass bottles as rolling pins for pastry with cold water inside",
                    "Sterilize glass bottles for homemade vanilla extract or infused oils",
                    "Convert pump bottles into plant watering devices for targeted irrigation"
                ],
                "repurpose": [
                    "Transform wine bottles into tabletop torches with wick kits and citronella oil",
                    "Cut the bottoms off glass bottles to create self-watering plant covers",
                    "Make a glass bottle wind chime by scoring and separating colorful bottles",
                    "Convert plastic bottles into bird feeders with wooden spoons as perches",
                    "Create decorative light fixtures using bottle cutting techniques and LED strips"
                ],
                "recycle": [
                    "Remove caps and lids (recycle separately) from bottles before processing",
                    "Rinse bottles with minimal water to remove residue without wasting resources",
                    "Participate in deposit return programs for bottle credits at stores",
                    "Look for glass bottle recycling that creates sand for construction projects",
                    "Check if local artists need bottles for glass blowing or mosaic projects"
                ]
            }
        }
        
        # Generic creative transformations for objects not in our dictionaries
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
        
        fallback_responses = {}
        
        # Check each object against our dictionary of specific suggestions
        for obj in unique_objects:
            obj_lower = obj.lower()
            matched_key = None
            
            # First check specialized items
            if obj_lower in specialized_items:
                matched_key = obj_lower
                fallback_responses[obj] = specialized_items[matched_key]
                continue
                
            # Then check broader categories
            for key in transformation_ideas.keys():
                if key in obj_lower:
                    matched_key = key
                    fallback_responses[obj] = transformation_ideas[matched_key]
                    break
            
            # Use generic but customized transformations if no match found
            if not matched_key:
                # Create object-specific version of the generic responses
                obj_specific = {
                    category: [suggestion.replace(object_list, obj) for suggestion in suggestions]
                    for category, suggestions in generic_transformations.items()
                }
                fallback_responses[obj] = obj_specific
        
        # Format all objects into a single response
        if len(unique_objects) == 1:
            # If there's only one object, use its suggestions directly
            obj = unique_objects[0]
            return json.dumps({obj: fallback_responses[obj]}, indent=2)
        else:
            # For multiple objects, create individual entries
            combined_suggestions = {}
            
            # Create separate entry for each object
            for obj in unique_objects:
                combined_suggestions[obj] = fallback_responses[obj]
            
            return json.dumps(combined_suggestions, indent=2)
# Streamlit app setup



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
            
            # ADD THIS SECTION - Creative Transformations Highlight
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
            
            # Extract 3-5 top creative ideas from repurpose category
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

if __name__ == "__main__":
    run_ecosmart_app()