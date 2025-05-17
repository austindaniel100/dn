import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import math # For rounding
import random

# --- Configuration & Setup ---
load_dotenv()

# --- Example Date Plans for Surprise Me ---
example_date_plans = [
    {
        "theme": "Romantic ❤️",
        "activity": "At Home 🏠",
        "budget": 30,
        "prep_time": "30 minutes",
        "duration": 2,
        "planning_style": "Planning For Her",
        "city": "Paris",
        "include_location": True,
        "custom_input": "Candlelit dinner, soft music, rose petals"
    },
    {
        "theme": "Adventure 🚀",
        "activity": "Outdoor Adventure 🌳",
        "budget": 100,
        "prep_time": "8 hours",
        "duration": 6,
        "planning_style": "Planning Together",
        "city": "Denver",
        "include_location": True,
        "custom_input": "Hiking, picnic with a view, sunset watching"
    },
    {
        "theme": "Fun 🎉",
        "activity": "Out (Casual)🚶",
        "budget": 60,
        "prep_time": "2 hours",
        "duration": 4,
        "planning_style": "Planning Together",
        "city": "Austin",
        "include_location": True,
        "custom_input": "Live music, food trucks, bar hopping"
    },
    {
        "theme": "Artsy 🎨",
        "activity": "Creative/DIY 🎨",
        "budget": 45,
        "prep_time": "1 day",
        "duration": 3,
        "planning_style": "Planning Together",
        "city": "New York",
        "include_location": True,
        "custom_input": "Pottery class, wine and paint, gallery walk"
    },
    {
        "theme": "Foodie 🍲",
        "activity": "Out (Fancy)👗",
        "budget": 150,
        "prep_time": "1 week",
        "duration": 4,
        "planning_style": "Planning For Her",
        "city": "San Francisco",
        "include_location": True,
        "custom_input": "Michelin star restaurant tour, wine pairing, dessert bar"
    },
    {
        "theme": "Chill 🧘",
        "activity": "Relax & Unwind 🛀",
        "budget": 80,
        "prep_time": "2 hours",
        "duration": 3,
        "planning_style": "Planning Together",
        "city": "Portland",
        "include_location": True,
        "custom_input": "Couple's spa, hot springs, meditation garden"
    }
]

# --- Helper Functions ---

def generate_detailed_itinerary(api_key, selected_model_name, original_plan):
    """Generate a detailed itinerary based on the original plan"""
    if not api_key:
        return {"error": "Google API Key is missing. Please enter it in the sidebar."}
    if not selected_model_name:
        return {"error": "Please select a Gemini model in the sidebar."}
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=selected_model_name)
        
        prompt = f"""
        You are a creative and helpful date night planning assistant. 
        You have already provided a date plan, and now the user wants a MORE DETAILED itinerary with ACTUAL places and activities.
        
        Original Plan Details:
        {json.dumps(original_plan, indent=2)}
        
        IMPORTANT: Now create a DETAILED ITINERARY with:
        1. Specific timings for each activity
        2. ACTUAL restaurant names, venues, or activity locations (search the internet for real places)
        3. Addresses when possible
        4. Reservation requirements or booking links if applicable
        5. Backup options for each activity
        6. Driving/transportation time between locations
        7. Specific menu recommendations if applicable
        8. Parking information if relevant
        
        If the user hasn't specified a location, suggest activities that could work in any major city, or ask them to specify their location.
        
        **IMPORTANT INSTRUCTION:**
        Your response MUST be a single, valid JSON object. Do NOT include any text outside of this JSON object.
        The JSON object should follow this structure:
        
        {{
          "title": "{original_plan.get('title', 'Date Night')} - Detailed Itinerary",
          "location_note": "[If no specific location was mentioned, note this and suggest general options]",
          "timeline": [
            {{
              "time": "6:00 PM",
              "activity": "Main Activity Name",
              "location": "Specific Venue Name",
              "address": "123 Main St, City, State",
              "details": "Detailed description of what to do here",
              "booking_required": true/false,
              "booking_link": "website.com/reservations (if applicable)",
              "cost_estimate": "$XX per person",
              "duration": "1.5 hours",
              "parking": "Street parking available / Valet available / Free lot",
              "tips": ["Tip 1", "Tip 2"]
            }}
          ],
          "backup_options": [
            {{
              "for_activity": "Main Activity Name",
              "alternative": "Alternative Venue Name",
              "reason": "Why this is a good backup",
              "details": "Brief description"
            }}
          ],
          "transportation_notes": "Estimated 15 min drive between venues, consider Uber if drinking",
          "total_estimated_cost": "$XXX for two people",
          "special_considerations": ["Consideration 1", "Consideration 2"],
          "weather_contingency": "If weather is bad, consider..."
        }}
        
        Make sure to search for REAL places and provide ACTUAL recommendations, not generic placeholders.
        """
        
        response = model.generate_content(prompt)
        raw_text_response = ""
        if hasattr(response, 'text'): 
            raw_text_response = response.text
        elif isinstance(response, str): 
            raw_text_response = response
        elif hasattr(response, 'parts') and response.parts: 
            raw_text_response = "".join(part.text for part in response.parts if hasattr(part, 'text'))
        else: 
            return {"error": f"Unexpected response format from API: {str(response)}"}
        
        if raw_text_response.strip().startswith("```json"):
            raw_text_response = raw_text_response.strip()[7:]
            if raw_text_response.strip().endswith("```"): 
                raw_text_response = raw_text_response.strip()[:-3]
        
        try:
            return json.loads(raw_text_response.strip())
        except json.JSONDecodeError as e:
            error_detail = f"Failed to parse JSON. Error: {e}. Raw (first 500 chars): '{raw_text_response[:500]}...'"
            return {"error": error_detail}
    except Exception as e: 
        return {"error": f"An error occurred: {e}"}

def generate_date_plan_with_gemini(api_key, selected_model_name,
                                   theme, activity_type,
                                   budget_dollars, prep_time_text, user_input,
                                   time_budget_hours,
                                   planning_style_prompt_line,
                                   location_prompt_line=None):
    if not api_key:
        return {"error": "Google API Key is missing. Please enter it in the sidebar."}
    if not selected_model_name:
        return {"error": "Please select a Gemini model in the sidebar."}
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=selected_model_name)

        time_budget_line = f"- Maximum Activity Duration: {time_budget_hours} hours." if time_budget_hours is not None else ""
        
        actual_planning_style_for_json = "Not specified"
        if planning_style_prompt_line:
            parts = planning_style_prompt_line.split(': ', 1)
            if len(parts) > 1:
                actual_planning_style_for_json = parts[1].strip()

        prompt = f"""
        You are a creative and helpful date night planning assistant.
        Your goal is to generate a fun and suitable date night plan based on the user's preferences.
        The user is utilizing the '{selected_model_name}' model.
        {planning_style_prompt_line}
        {location_prompt_line if location_prompt_line else ""}

        User Preferences:
        - Theme: {theme}
        - Activity Type: {activity_type}
        - Budget: ${budget_dollars} (The user has exactly ${budget_dollars} to spend on this date)
        - Preparation Time Available: {prep_time_text} (The user wants something that can be prepared within {prep_time_text})
        {time_budget_line}
        - User's specific suggestions or restrictions: "{user_input if user_input else 'None'}"


        **IMPORTANT INSTRUCTION:**
        Your response MUST be a single, valid JSON object. Do NOT include any text outside of this JSON object.
        The JSON object should follow this structure:

        {{
          "title": "[Catchy Date Night Title - concise, max 5-7 words]",
          "theme": "{theme}",
          "activity_type": "{activity_type}",
          "budget_dollars": {budget_dollars},
          "prep_time": "{prep_time_text}",
          "time_budget_hours": {time_budget_hours},
          "planning_style": "{actual_planning_style_for_json}",
          "model_used": "{selected_model_name}",
          "emoji_story": {{
            "story": "[A long string of emojis telling the emotional journey of the date - should be 20-40 emojis that capture the progression, emotions, activities, and moments]",
            "description": "[Brief explanation of what the emoji story represents]"
          }},
          "plan_details": {{
            "step_1_title": "[Concise title for Step 1]",
            "step_1_description": "[Concise description for Step 1, 1-2 sentences]",
            "step_2_title": "[Concise title for Step 2]",
            "step_2_description": "[Concise description for Step 2, 1-2 sentences]",
            "food_drinks_suggestions": "[Optional: Very concise food/drinks. 1 sentence max.]",
            "ambiance_extras_suggestions": "[Optional: Very concise ambiance/extras. 1 sentence max.]"
          }},
          "tips_and_considerations": [
            "[Very Concise Tip 1, max 1 sentence]",
            "[Very Concise Tip 2 (if applicable), max 1 sentence]"
          ]
        }}

        For emoji_story, create a sequence of 20-40 emojis that tells the emotional journey of this date night.
        The emojis should represent:
        - The initial mood and anticipation
        - Getting ready and excitement
        - Meeting or starting the date
        - The activities and experiences
        - Food and drinks (if applicable)  
        - Emotional highs and intimate moments
        - The progression through the evening
        - The ending and aftermath
        
        Make it like a mini emotional movie told only through emojis. Be creative and capture the essence of the date theme.
        
        Ensure all string values within the JSON are extremely concise and to the point. Brevity is key.
        If a time budget is provided, suggest activities that fit within that duration.
        """
        response = model.generate_content(prompt)
        raw_text_response = ""
        if hasattr(response, 'text'): raw_text_response = response.text
        elif isinstance(response, str): raw_text_response = response
        elif hasattr(response, 'parts') and response.parts: raw_text_response = "".join(part.text for part in response.parts if hasattr(part, 'text'))
        else: return {"error": f"Unexpected response format from API: {str(response)}"}

        if raw_text_response.strip().startswith("```json"):
            raw_text_response = raw_text_response.strip()[7:]
            if raw_text_response.strip().endswith("```"): raw_text_response = raw_text_response.strip()[:-3]
        try:
            return json.loads(raw_text_response.strip())
        except json.JSONDecodeError as e:
            error_detail = f"Failed to parse JSON. Error: {e}. Raw (first 500 chars): '{raw_text_response[:500]}...'"
            return {"error": error_detail}
    except Exception as e: return {"error": f"An error occurred: {e}"}

# --- Streamlit App UI ---
st.set_page_config(page_title="Date Night Planner", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS ---
st.markdown("""
    <style>
        html, body, #root, .stApp {
            height: 100%; overflow: hidden; background-color: #0E1117; color: #FAFAFA;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
        }
        .main .block-container {padding-top: 1.5rem; padding-bottom: 1rem; padding-left: 2rem; padding-right: 2rem;}
        h1 {font-size: 2.2rem !important; color: #FF69B4; text-align: center; margin-bottom: 1rem !important; font-weight: 700;}
        .right-column-content-wrapper {margin-top: 0 !important; padding-top: 0 !important;}
        .right-column-subheader {font-size: 1.5rem !important; font-weight: 600; color: #A9D5FF; margin-top: 0 !important; margin-bottom: 0.75rem !important; text-align: center;}
        .left-column-section-title {font-size: 1.1rem !important; font-weight: 600; color: #BDC3C7; margin-top: 0.8rem !important; margin-bottom: 0.2rem !important; border-bottom: 1px solid #333A44; padding-bottom: 0.1rem;}
        div[data-testid="stSelectbox"] > label,
        div[data-testid="stSlider"] > label,
        div[data-testid="stTextArea"] > label,
        div[data-testid="stRadio"] > label {
            margin-bottom: 0.2rem !important; font-size: 0.9rem; font-weight: 500; color: #A0A7B3;
        }
        div[data-testid="stRadio"] > div[role="radiogroup"] {display: flex; flex-direction: row; justify-content: center; gap: 5px;}
        div[data-testid="stRadio"] > div[role="radiogroup"] > label {
            background-color: #262B34; color: #A0A7B3; border: 1px solid #333A44;
            padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer;
            transition: background-color 0.2s, color 0.2s; font-size: 0.85rem;
        }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {background-color: #FF69B4; color: white; border-color: #FF69B4;}
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover:not(:has(input:checked)) {background-color: #333A44;}
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {gap: 0.3rem !important;}
        .stTextArea textarea {background-color: #1C2028 !important; color: #FAFAFA !important; border: 1px solid #333A44 !important; border-radius: 6px !important; min-height: 70px !important;}
        .stTextArea textarea:focus {border-color: #FF69B4 !important; box-shadow: 0 0 0 0.2rem rgba(255, 105, 180, 0.25) !important;}
        div[data-testid="stButton"] > button {background-color: #FF69B4; color: white; border: none; padding: 0.6rem 1.5rem; border-radius: 8px; font-weight: 600; font-size: 1rem; transition: background-color 0.2s ease-in-out, transform 0.1s ease; box-shadow: 0 2px 5px rgba(0,0,0,0.2); margin-top: 0.5rem;}
        div[data-testid="stButton"] > button:hover {background-color: #FF85C8; transform: translateY(-1px);}
        div[data-testid="stButton"] > button:active {background-color: #E05A9A; transform: translateY(0px);}
        [data-testid="stSidebar"] {background-color: #1C2028; padding: 1rem;}
        [data-testid="stSidebar"] .stTextInput input, [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {background-color: #262B34; color: #FAFAFA; border: 1px solid #333A44;}
        [data-testid="stSidebar"] h2 {color: #A9D5FF; font-size: 1.2rem;}
        [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] .stAlert p {color: #BDC3C7;}
        .date-plan-output-container {max-height: calc(100vh - 200px); overflow-y: auto; padding: 20px; background-color: rgba(28, 32, 40, 0.9); border: 1px solid #333A44; border-radius: 8px; color: #D0D3D4; font-size: 0.9em; line-height: 1.6; box-shadow: 0 4px 12px rgba(0,0,0,0.3); margin-top: 0.5rem; backdrop-filter: blur(10px);}
        .plan-title {font-size: 1.6em; font-weight: 700; color: #FFD700; margin-bottom: 0.6em; text-align: center; border-bottom: 2px solid #FFD700; padding-bottom: 0.3em;}
        .plan-meta-info {font-size: 0.95em; color: #85929E; margin-bottom: 1em; text-align: center; font-style: italic; line-height: 1.4;}
        .plan-meta-info b {color: #AAB7B8; font-weight: 500;}
        .plan-section-title {font-size: 1.25em; font-weight: 600; color: #76D7C4; margin-top: 1.2em; margin-bottom: 0.5em; border-bottom: 1px solid #333A44; padding-bottom: 0.2em;}
        .plan-step-title {color: #A9D5FF; font-weight: 600;}
        .plan-description {font-size: 1em; color: #CACFD2; margin-bottom: 0.5em; padding-left: 10px;}
        .plan-list-item {font-size: 1em; color: #CACFD2; margin-left: 1.5em; margin-bottom: 0.4em; list-style-type: "✨ ";}
        .plan-error-message {color: #FF6B6B; font-weight: 500; background-color: rgba(255, 107, 107, 0.1); padding: 10px; border-radius: 6px; border-left: 4px solid #FF6B6B;}
        .plan-initial-message {color: #A9D5FF; font-style: italic; text-align: center; padding-top: 1rem; padding-bottom: 1rem; font-size: 0.95em;}
        div[data-testid="stButton"] > button[type="button"]:not(:first-child) {
            background-color: #4A90E2; 
            color: white; 
            border: none; 
            padding: 0.5rem 1.2rem; 
            border-radius: 6px; 
            font-weight: 500; 
            font-size: 0.95rem; 
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        div[data-testid="stButton"] > button[type="button"]:not(:first-child):hover {
            background-color: #5BA3F5; 
            transform: translateY(-1px);
        }
        div[data-testid="stButton"] > button[type="button"]:not(:first-child):active {
            background-color: #3A7BC8; 
            transform: translateY(0px);
        }
        .plan-description a {color: #4A90E2; text-decoration: none;}
        .plan-description a:hover {color: #5BA3F5; text-decoration: underline;}
        
        /* Styling for checkbox labels */
        div[data-testid="stCheckbox"] > label {
            font-size: 0.8rem !important;
            color: #A0A7B3;
            margin-bottom: 0 !important;
            padding: 0 !important;
        }
        
        /* Style the location toggle similar to locks */
        div[data-testid="stCheckbox"][key="include_location"] > label {
            font-size: 1rem !important;
        }
        /* Styling for checkbox widget container */
        div[data-testid="stCheckbox"] {
            padding-top: 0 !important; /* MODIFIED: Was 0.8rem, caused downward shift */
            /* margin-bottom: -0.5rem !important; /* MODIFIED: Removed, may not be needed for locks */
        }

        /* Container for lock checkboxes (within col2) */
        .element-container:has(div[data-testid="stCheckbox"]) {
            display: flex;
            align-items: center; /* Vertically centers the checkbox */
            justify-content: flex-end; /* Aligns checkbox to the right of its column */
            height: 100%; /* Ensures the container takes full row height for alignment */
            min-width: 50px; /* Ensures some space for the lock icon */
        }

        /* Reduce spacing between controls */
        .stSelectbox, .stSlider, .stRadio {
            margin-bottom: 0.5rem !important;
        }
        /* Keep columns together on mobile */
        @media (max-width: 768px) {
            div[data-testid="stHorizontalBlock"] {
                gap: 0.5rem !important;
            }
            div[data-testid="stColumn"] {
                padding: 0 !important;
            }
        }
        /* Top button row styling */
        .element-container:has(div[data-testid="stButton"]:has(button[type="secondary"])) {
            margin-bottom: 1.5rem !important;
        }
        
        
        /* Randomize button styling */
        div[data-testid="stButton"]:has(button:contains("🎲")) > button {
            background-color: #9B59B6 !important;
            margin-bottom: 0 !important;
        }
        div[data-testid="stButton"]:has(button:contains("🎲")) > button:hover {
            background-color: #B47CC4 !important;
        }
        
        /* Surprise Me button styling */
        div[data-testid="stButton"]:has(button:contains("🎁")) > button {
            background-color: #2ECC71 !important;
            margin-bottom: 0 !important;
        }
        div[data-testid="stButton"]:has(button:contains("🎁")) > button:hover {
            background-color: #3DDC84 !important;
        }
        
        /* Separator styling */
        .plan-separator {
            margin: 2.5rem 0;
            border: none;
            height: 2px;
            background: linear-gradient(to right, transparent, #FFD700 20%, #FFD700 80%, transparent);
            opacity: 0.5;
        }
        
        /* Emoji story container */
        .emoji-story-container {
            font-size: 2em;
            line-height: 1.5;
            text-align: center;
            padding: 1.5rem;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            margin: 1.5rem 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            word-wrap: break-word;
            letter-spacing: 0.05em;
        }
        
        .emoji-story-description {
            text-align: center;
            font-style: italic;
            color: #A9D5FF;
            margin-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>💖 Date Night AI! 🥂</h1>", unsafe_allow_html=True)

# Button row at the top
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
with col_btn1:
    if st.button("🎲 Randomize Settings", type="secondary", use_container_width=True):
        # Randomize theme if not locked
        if not st.session_state.get('theme_lock', False):
            themes_list = ["Romantic ❤️", "Fun 🎉", "Chill 🧘", "Adventure 🚀", "Artsy 🎨", "Homebody 🏡", "Intellectual 🧠", "Foodie 🍲", "Mysterious 🕵️", "Nostalgic 🕰️"]
            st.session_state.theme_value = random.choice(themes_list)
        
        # Randomize activity type if not locked
        if not st.session_state.get('activity_lock', False):
            activity_types_list = ["At Home 🏠", "Out (Casual)🚶", "Out (Fancy)👗", "Outdoor Adventure 🌳", "Creative/DIY 🎨", "Learning Together 📚", "Volunteer/Give Back 🤝", "Relax & Unwind 🛀"]
            st.session_state.activity_value = random.choice(activity_types_list)
        
        # Randomize budget if not locked
        if not st.session_state.get('budget_lock', False):
            st.session_state.budget_value = random.randint(1, 200)
        
        # Randomize prep time if not locked
        if not st.session_state.get('prep_lock', False):
            prep_time_options_list = ["30 minutes", "2 hours", "8 hours", "1 day", "1 week", "1 month"]
            st.session_state.prep_value = random.choice(prep_time_options_list)
        
        # Randomize duration if not locked
        if not st.session_state.get('duration_lock', False):
            st.session_state.duration_value = random.randint(1, 8)
        
        # Randomize planning style if not locked
        if not st.session_state.get('planning_lock', False):
            planning_style_options_list = ["Planning Together", "Planning For Her"]
            st.session_state.planning_value = random.choice(planning_style_options_list)
        
        st.rerun()

with col_btn2:
    if st.button("🎁 Surprise Me!", type="secondary", use_container_width=True):
        # Randomly select an example plan
        surprise_plan = random.choice(example_date_plans)
        
        # Populate session state with the selected values
        st.session_state.theme_value = surprise_plan["theme"]
        st.session_state.activity_value = surprise_plan["activity"]
        st.session_state.budget_value = surprise_plan["budget"]
        st.session_state.prep_value = surprise_plan["prep_time"]
        st.session_state.duration_value = surprise_plan["duration"]
        st.session_state.planning_value = surprise_plan["planning_style"]
        st.session_state.city_input = surprise_plan["city"]
        st.session_state.include_location = surprise_plan["include_location"]
        st.session_state.user_custom_input_area_v2 = surprise_plan["custom_input"]
        
        # Unlock all fields so they can be populated
        st.session_state.theme_lock = False
        st.session_state.activity_lock = False
        st.session_state.budget_lock = False
        st.session_state.prep_lock = False
        st.session_state.duration_lock = False
        st.session_state.planning_lock = False
        
        # Set flag to auto-generate after rerun
        st.session_state.auto_generate = True
        
        st.rerun()

with st.sidebar:
    st.header("🔑 API & Model Config")
    default_api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key_input = st.text_input("Google AI Key", type="password", value=default_api_key, help="Get your key from Google AI Studio.")
    if not api_key_input and default_api_key: api_key_input = default_api_key
    available_models = ["gemini-2.5-pro-preview-05-06", "gemini-2.5-flash-preview-04-17", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-1.0-pro"]
    default_model_index = available_models.index("gemini-2.5-flash-preview-04-17") if "gemini-2.5-flash-preview-04-17" in available_models else 0
    selected_model = st.selectbox("Choose Gemini Model", available_models, index=default_model_index, help="Select model. Flash is faster, Pro is more capable.")
    st.markdown("---")
    st.info("Adjust API key & model. Ensure selected model follows JSON instructions well.")

left_column, right_column = st.columns([0.42, 0.58])

with left_column:
    st.markdown("<p class='left-column-section-title'>Your Preferences</p>", unsafe_allow_html=True)
    
    themes = ["Romantic ❤️", "Fun 🎉", "Chill 🧘", "Adventure 🚀", "Artsy 🎨", "Homebody 🏡", "Intellectual 🧠", "Foodie 🍲", "Mysterious 🕵️", "Nostalgic 🕰️"]
    activity_types = ["At Home 🏠", "Out (Casual)🚶", "Out (Fancy)👗", "Outdoor Adventure 🌳", "Creative/DIY 🎨", "Learning Together 📚", "Volunteer/Give Back 🤝", "Relax & Unwind 🛀"]
    prep_time_options = ["30 minutes", "2 hours", "8 hours", "1 day", "1 week", "1 month"]
    planning_style_options = ["Planning Together", "Planning For Her"]

    # Theme with lock
    col_theme_input, col_theme_lock = st.columns([0.85, 0.15], gap="small")
    with col_theme_input:
        if 'theme_value' not in st.session_state: st.session_state.theme_value = themes[0]
        selected_theme = st.selectbox("Theme", themes, index=themes.index(st.session_state.theme_value), help="Overall mood or vibe for the date?", key="theme_select")
        st.session_state.theme_value = selected_theme
    with col_theme_lock:
        theme_locked = st.checkbox("🔒", key="theme_lock", help="Lock this setting from randomization")

    # Activity Type with lock
    col_activity_input, col_activity_lock = st.columns([0.85, 0.15], gap="small")
    with col_activity_input:
        if 'activity_value' not in st.session_state: st.session_state.activity_value = activity_types[0]
        selected_activity_type = st.selectbox("Activity Type", activity_types, index=activity_types.index(st.session_state.activity_value), help="General kind of activity?", key="activity_select")
        st.session_state.activity_value = selected_activity_type
    with col_activity_lock:
        activity_locked = st.checkbox("🔒", key="activity_lock", help="Lock this setting from randomization")

    st.markdown("<p class='left-column-section-title'>Practical Considerations</p>", unsafe_allow_html=True)

    # Budget Level with lock
    col_budget_input, col_budget_lock = st.columns([0.85, 0.15], gap="small")
    with col_budget_input:
        if 'budget_value' not in st.session_state: st.session_state.budget_value = 50
        actual_budget_dollars_val = st.slider(
            "Budget (in dollars)", min_value=1, max_value=200, value=st.session_state.budget_value, step=1,
            format="$%d", help="Select your budget for the date ($1 to $200).", key="budget_slider"
        )
        st.session_state.budget_value = actual_budget_dollars_val
    with col_budget_lock:
        budget_locked = st.checkbox("🔒", key="budget_lock", help="Lock this setting from randomization")

    # Preparation Time with lock
    col_prep_input, col_prep_lock = st.columns([0.85, 0.15], gap="small")
    with col_prep_input:
        if 'prep_value' not in st.session_state: st.session_state.prep_value = "2 hours"
        selected_prep_time = st.select_slider(
            "Preparation Time", options=prep_time_options, value=st.session_state.prep_value,
            help="How much time do you have to prepare for this date?", key="prep_slider"
        )
        st.session_state.prep_value = selected_prep_time
    with col_prep_lock:
        prep_locked = st.checkbox("🔒", key="prep_lock", help="Lock this setting from randomization")

    # Max Activity Duration with lock
    col_duration_input, col_duration_lock = st.columns([0.85, 0.15], gap="small")
    with col_duration_input:
        if 'duration_value' not in st.session_state: st.session_state.duration_value = 3
        time_budget_hours_direct = st.slider(
            "Activity Duration (hours)", min_value=1, max_value=8, value=st.session_state.duration_value, step=1,
            format="%d hours", help="How long should the date activity last? (1-8 hours)", key="duration_slider"
        )
        st.session_state.duration_value = time_budget_hours_direct
    with col_duration_lock:
        duration_locked = st.checkbox("🔒", key="duration_lock", help="Lock this setting from randomization")

    st.markdown("<p class='left-column-section-title'>Planning Style & Location</p>", unsafe_allow_html=True)
    
    # Planning style with lock
    col_planning_input, col_planning_lock = st.columns([0.85, 0.15], gap="small")
    with col_planning_input:
        if 'planning_value' not in st.session_state: st.session_state.planning_value = planning_style_options[0]
        selected_planning_style = st.radio("How are you planning this date?", planning_style_options, 
                                         index=planning_style_options.index(st.session_state.planning_value), 
                                         horizontal=True, key="planning_style_toggle")
        st.session_state.planning_value = selected_planning_style
    with col_planning_lock:
        planning_locked = st.checkbox("🔒", key="planning_lock", help="Lock this setting from randomization")
    
    # Location input with toggle
    col_location_input, col_location_toggle = st.columns([0.85, 0.15], gap="small")
    with col_location_input:
        closest_city = st.text_input("Closest City", 
                                    placeholder="e.g., New York, Los Angeles, Austin", 
                                    help="Enter your closest city for specific local recommendations",
                                    key="city_input")
    with col_location_toggle:
        include_location = st.checkbox("📍", key="include_location", help="Include this location in the search")
    
    planning_style_prompt_line = ""
    if selected_planning_style == "Planning Together":
        planning_style_prompt_line = "The user is planning this date collaboratively with their significant other."
    elif selected_planning_style == "Planning For Her":
        planning_style_prompt_line = "The user is planning this date as a surprise or gift for their female significant other."
    
    # Add location information to prompt if enabled
    location_prompt_line = ""
    if include_location and closest_city.strip():
        location_prompt_line = f"The user is close to {closest_city} so find specific activities and dinners in that area."
    
    st.markdown("<p class='left-column-section-title'>Additional Information</p>", unsafe_allow_html=True)
    user_custom_input = st.text_area(label="Any Suggestions or Restrictions?", height=75, placeholder="e.g., loves Mexican food, allergic to cats, must be indoors, surprise me!", help="Must-haves, must-nots, or specific ideas?", key="user_custom_input_area_v2")
    
    if 'generated_plan_content' not in st.session_state: 
        st.session_state.generated_plan_content = {"message": "Let's plan something amazing! Fill in your preferences and click Generate."}
    
    if st.button("✨ Generate Date Plan ✨", type="primary", use_container_width=True):
        if not api_key_input: st.session_state.generated_plan_content = {"error": "⚠️ Oops! Please enter your Google API Key."}
        elif not selected_model: st.session_state.generated_plan_content = {"error": "⚠️ Please select a Gemini model."}
        else:
            with st.spinner("💖 Crafting your perfect date night..."):
                plan_output = generate_date_plan_with_gemini(
                    api_key_input, selected_model,
                    selected_theme, selected_activity_type,
                    actual_budget_dollars_val,
                    selected_prep_time,
                    user_custom_input,
                    time_budget_hours_direct,
                    planning_style_prompt_line,
                    location_prompt_line
                )
            st.session_state.generated_plan_content = plan_output
            st.session_state.detailed_itinerary = None  # Clear any existing itinerary
            st.session_state.should_generate_itinerary = isinstance(plan_output, dict) and "title" in plan_output

    # Check if auto-generation was triggered by Surprise Me button
    if st.session_state.get('auto_generate', False):
        st.session_state.auto_generate = False
        if api_key_input and selected_model:
            with st.spinner("💖 Crafting your surprise date night..."):
                plan_output = generate_date_plan_with_gemini(
                    api_key_input, selected_model,
                    selected_theme, selected_activity_type,
                    actual_budget_dollars_val,
                    selected_prep_time,
                    user_custom_input,
                    time_budget_hours_direct,
                    planning_style_prompt_line,
                    location_prompt_line
                )
            st.session_state.generated_plan_content = plan_output
            st.session_state.detailed_itinerary = None
            st.session_state.should_generate_itinerary = isinstance(plan_output, dict) and "title" in plan_output

with right_column:
    st.markdown("<div class='right-column-content-wrapper'>", unsafe_allow_html=True)
    st.markdown("<h2 class='right-column-subheader'>💡 Your Personalized Date Night Idea 💡</h2>", unsafe_allow_html=True)
    plan_data = st.session_state.generated_plan_content
    is_initial_placeholder = isinstance(plan_data, dict) and "message" in plan_data and not plan_data.get("error") and not plan_data.get("title")

    if is_initial_placeholder:
        st.markdown(f"<p class='plan-initial-message'>{plan_data['message']}</p>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='date-plan-output-container'>", unsafe_allow_html=True)
        if isinstance(plan_data, dict):
            if "error" in plan_data:
                st.markdown(f"<div class='plan-error-message'>{plan_data['error']}</div>", unsafe_allow_html=True)
            elif "title" in plan_data:
                st.markdown(f"<p class='plan-title'>{plan_data.get('title', 'N/A')}</p>", unsafe_allow_html=True)
                
                budget_display = f"<b>Budget:</b> ${plan_data.get('budget_dollars', 'N/A')}"
                meta_parts = [
                    f"<b>Theme:</b> {plan_data.get('theme', 'N/A')}",
                    f"<b>Activity:</b> {plan_data.get('activity_type', 'N/A')}",
                    budget_display,
                    f"<b>Prep Time:</b> {plan_data.get('prep_time', 'N/A')}",
                ]
                if plan_data.get('time_budget_hours'):
                    meta_parts.append(f"<b>Max Duration:</b> {plan_data.get('time_budget_hours', 'N/A')} hours")
                if plan_data.get('planning_style') != "Not specified" and plan_data.get('planning_style'):
                     meta_parts.append(f"<b>Planning Style:</b> {plan_data.get('planning_style')}")
                
                meta_html = "<div class='plan-meta-info'>"
                for i in range(0, len(meta_parts), 2):
                    line_parts = [part for part in meta_parts[i:i+2] if part]
                    line = " | ".join(line_parts)
                    if line: meta_html += line + "<br>"
                if meta_html.endswith("<br>"): meta_html = meta_html[:-4]
                meta_html += f"<br><i>(Powered by {plan_data.get('model_used', 'Gemini AI')})</i></div>"
                st.markdown(meta_html, unsafe_allow_html=True)

                plan_details = plan_data.get('plan_details', {})
                if any(plan_details.values()):
                    st.markdown("<p class='plan-section-title'>🎉 The Plan Unveiled:</p>", unsafe_allow_html=True)
                    if plan_details.get('step_1_title') and plan_details.get('step_1_description'): st.markdown(f"<span class='plan-step-title'>{plan_details['step_1_title']}:</span> <span class='plan-description'>{plan_details['step_1_description']}</span>", unsafe_allow_html=True)
                    if plan_details.get('step_2_title') and plan_details.get('step_2_description'): st.markdown(f"<span class='plan-step-title'>{plan_details['step_2_title']}:</span> <span class='plan-description'>{plan_details['step_2_description']}</span>", unsafe_allow_html=True)
                    if plan_details.get('food_drinks_suggestions'): st.markdown(f"<span class='plan-step-title'>🍽️ Food & Drinks:</span> <span class='plan-description'>{plan_details['food_drinks_suggestions']}</span>", unsafe_allow_html=True)
                    if plan_details.get('ambiance_extras_suggestions'): st.markdown(f"<span class='plan-step-title'>✨ Ambiance & Extras:</span> <span class='plan-description'>{plan_details['ambiance_extras_suggestions']}</span>", unsafe_allow_html=True)
                
                tips = plan_data.get('tips_and_considerations', [])
                if tips and any(tip.strip() for tip in tips):
                    st.markdown("<p class='plan-section-title'>💡 Pro Tips & Considerations:</p>", unsafe_allow_html=True)
                    for tip in tips:
                        if tip.strip(): st.markdown(f"<div class='plan-list-item'>{tip}</div>", unsafe_allow_html=True)
                
                # Display emoji story if available
                if plan_data.get('emoji_story'):
                    st.markdown("<p class='plan-section-title'>💫 Your Date Night Journey in Emojis:</p>", unsafe_allow_html=True)
                    
                    emoji_story = plan_data['emoji_story'].get('story', '')
                    if emoji_story:
                        st.markdown(f"<div class='emoji-story-container'>{emoji_story}</div>", unsafe_allow_html=True)
                    
                    emoji_description = plan_data['emoji_story'].get('description', '')
                    if emoji_description:
                        st.markdown(f"<div class='emoji-story-description'>{emoji_description}</div>", unsafe_allow_html=True)
                
                # Generate detailed itinerary if needed
                if st.session_state.get('should_generate_itinerary', False) and not st.session_state.get('detailed_itinerary'):
                    with st.spinner("🔍 Creating detailed itinerary..."):
                        detailed_itinerary_result = generate_detailed_itinerary(api_key_input, selected_model, plan_data)
                        st.session_state.detailed_itinerary = detailed_itinerary_result
                        st.session_state.should_generate_itinerary = False
                        st.rerun()
                
                # Add a visual separator before detailed itinerary
                if st.session_state.get('detailed_itinerary'):
                    st.markdown("<hr class='plan-separator'>", unsafe_allow_html=True)
                    st.markdown("<p class='plan-section-title' style='font-size: 1.4em; text-align: center; color: #FFD700; margin-bottom: 1.5rem;'>📍 Detailed Itinerary</p>", unsafe_allow_html=True)
                    
                    itinerary_data = st.session_state.detailed_itinerary
                    if "error" in itinerary_data:
                        st.markdown(f"<div class='plan-error-message'>{itinerary_data['error']}</div>", unsafe_allow_html=True)
                    else:
                        if itinerary_data.get('location_note'): st.markdown(f"<div class='plan-description'><b>Note:</b> {itinerary_data['location_note']}</div>", unsafe_allow_html=True)
                        st.markdown("<p class='plan-section-title'>⏰ Timeline:</p>", unsafe_allow_html=True)
                        for item in itinerary_data.get('timeline', []):
                            st.markdown(f"<div class='plan-step-title'>{item.get('time', 'TBD')} - {item.get('activity', 'Activity')}</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='plan-description'><b>📍 Location:</b> {item.get('location', 'TBD')}</div>", unsafe_allow_html=True)
                            if item.get('address'): st.markdown(f"<div class='plan-description'><b>🏠 Address:</b> {item.get('address')}</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='plan-description'>{item.get('details', '')}</div>", unsafe_allow_html=True)
                            if item.get('booking_required'):
                                booking_text = f"<b>📅 Booking Required</b>"
                                if item.get('booking_link'): booking_text += f" - <a href='{item['booking_link']}' target='_blank'>Make Reservation</a>"
                                st.markdown(f"<div class='plan-description'>{booking_text}</div>", unsafe_allow_html=True)
                            if item.get('cost_estimate'): st.markdown(f"<div class='plan-description'><b>💰 Cost:</b> {item['cost_estimate']}</div>", unsafe_allow_html=True)
                            if item.get('parking'): st.markdown(f"<div class='plan-description'><b>🚗 Parking:</b> {item['parking']}</div>", unsafe_allow_html=True)
                            if item.get('tips'):
                                for tip_item in item['tips']: st.markdown(f"<div class='plan-list-item'>{tip_item}</div>", unsafe_allow_html=True) # Renamed inner loop var
                            st.markdown("<br>", unsafe_allow_html=True)
                        
                        if itinerary_data.get('backup_options'):
                            st.markdown("<p class='plan-section-title'>🔄 Backup Options:</p>", unsafe_allow_html=True)
                            for backup in itinerary_data['backup_options']:
                                st.markdown(f"<div class='plan-step-title'>Alternative for {backup.get('for_activity', 'Activity')}: {backup.get('alternative', 'TBD')}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='plan-description'><b>Why:</b> {backup.get('reason', '')}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='plan-description'>{backup.get('details', '')}</div>", unsafe_allow_html=True)
                        
                        if itinerary_data.get('transportation_notes'): st.markdown(f"<div class='plan-description'><b>🚕 Transportation:</b> {itinerary_data['transportation_notes']}</div>", unsafe_allow_html=True)
                        if itinerary_data.get('total_estimated_cost'): st.markdown(f"<div class='plan-description'><b>💵 Total Estimated Cost:</b> {itinerary_data['total_estimated_cost']}</div>", unsafe_allow_html=True)
                        if itinerary_data.get('weather_contingency'): st.markdown(f"<div class='plan-description'><b>🌧️ Weather Contingency:</b> {itinerary_data['weather_contingency']}</div>", unsafe_allow_html=True)
                        if itinerary_data.get('special_considerations'):
                            st.markdown("<p class='plan-section-title'>⚠️ Special Considerations:</p>", unsafe_allow_html=True)
                            for consideration in itinerary_data['special_considerations']: st.markdown(f"<div class='plan-list-item'>{consideration}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p class='plan-description'>{str(plan_data)}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True) # End date-plan-output-container
    st.markdown("</div>", unsafe_allow_html=True) # End right-column-content-wrapper