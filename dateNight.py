import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

# --- Configuration & Setup ---
load_dotenv()

# --- Helper Functions ---
# (Keep your helper functions as they are)
def map_budget_value_to_description(value):
    if value == 1: return "Extremely tight, focus on free or DIY options, minimal to no spending."
    if value == 2: return "Very low budget, some minimal spending is acceptable."
    if value == 3: return "Moderate budget, allows for a casual outing or some purchases."
    if value == 4: return "Generous budget, can afford a nice dinner out or event tickets."
    return "Splurge / Special Occasion, high budget, willing to spend significantly."

def map_prep_time_value_to_description(value):
    if value == 1: return "Almost no preparation needed (under 30 mins), very spontaneous."
    if value == 2: return "Quick preparation (30 mins to 1 hour)."
    if value == 3: return "Moderate preparation (1-2 hours)."
    if value == 4: return "Involved preparation (2-4 hours), some planning."
    return "Elaborate preparation (4+ hours), significant planning."

def generate_date_plan_with_gemini(api_key, selected_model_name,
                                   theme, activity_type,
                                   budget_desc, prep_time_desc, user_input,
                                   current_budget_value, current_prep_time_value):
    if not api_key:
        return {"error": "Google API Key is missing. Please enter it in the sidebar."}
    if not selected_model_name:
        return {"error": "Please select a Gemini model in the sidebar."}
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=selected_model_name)
        # (Keep your prompt as is - it seems to be generating good concise JSON now)
        prompt = f"""
        You are a creative and helpful date night planning assistant.
        Your goal is to generate a fun and suitable date night plan based on the user's preferences.
        The user is utilizing the '{selected_model_name}' model.

        User Preferences:
        - Theme: {theme}
        - Activity Type: {activity_type}
        - Budget Consideration: "{budget_desc}" (Approx. level: {current_budget_value}/5)
        - Time to Prepare Consideration: "{prep_time_desc}" (Approx. level: {current_prep_time_value}/5)
        - User's specific suggestions or restrictions: "{user_input if user_input else 'None'}"

        **IMPORTANT INSTRUCTION:**
        Your response MUST be a single, valid JSON object. Do NOT include any text outside of this JSON object (e.g., no "Here is the JSON:" preamble).
        The JSON object should follow this structure:

        {{
          "title": "[Catchy Date Night Title - concise and engaging, max 5-7 words]",
          "theme": "{theme}",
          "activity_type": "{activity_type}",
          "budget_level": {current_budget_value},
          "budget_description": "{budget_desc}",
          "prep_time_level": {current_prep_time_value},
          "prep_time_description": "{prep_time_desc}",
          "model_used": "{selected_model_name}",
          "plan_details": {{
            "step_1_title": "[Concise title for Step 1, e.g., 'Cozy Corner Creation']",
            "step_1_description": "[Detailed but very concise description for Step 1, 1-2 sentences]",
            "step_2_title": "[Concise title for Step 2, e.g., 'Memory Lane & Dreams']",
            "step_2_description": "[Detailed but very concise description for Step 2, 1-2 sentences]",
            "food_drinks_suggestions": "[Optional: Very concise suggestions for food/drinks. If none, use an empty string or omit key. 1 sentence max.]",
            "ambiance_extras_suggestions": "[Optional: Very concise ideas for ambiance/extras. If none, use an empty string or omit key. 1 sentence max.]"
          }},
          "tips_and_considerations": [
            "[Very Concise Tip 1, max 1 sentence]",
            "[Very Concise Tip 2 (if applicable), max 1 sentence]"
          ]
        }}

        Ensure all string values within the JSON are extremely concise and to the point, providing essential information efficiently.
        Focus on delivering the plan clearly and engagingly within this JSON structure. Brevity is key.
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

# --- Custom CSS for Styling ---
st.markdown("""
    <style>
        /* --- General App Body & Font --- */
        html, body, #root, .stApp {
            height: 100%;
            overflow: hidden;
            background-color: #0E1117;
            color: #FAFAFA;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
        }
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* --- Titles & Headers --- */
        h1 { /* Main App Title */
            font-size: 2.2rem !important;
            color: #FF69B4;
            text-align: center;
            margin-bottom: 1rem !important; /* Space before columns start */
            font-weight: 700;
        }
        /* Wrapper for right column content to control top spacing */
        .right-column-content-wrapper {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        .right-column-subheader { /* "Your Personalized Date Night Idea" */
            font-size: 1.5rem !important;
            font-weight: 600;
            color: #A9D5FF;
            margin-top: 0 !important; /* Explicitly set to 0 */
            margin-bottom: 0.75rem !important; /* Space before plan/message */
            text-align: center;
        }
        .left-column-section-title {
            font-size: 1.1rem !important;
            font-weight: 600;
            color: #BDC3C7;
            margin-top: 1rem !important;
            margin-bottom: 0.3rem !important;
            border-bottom: 1px solid #333A44;
            padding-bottom: 0.2rem;
        }

        /* --- Input Elements Styling (Left Column) --- */
        /* (Keep existing input styles - they seem fine) */
        div[data-testid="stSelectbox"] > label,
        div[data-testid="stSlider"] > label,
        div[data-testid="stTextArea"] > label {
            margin-bottom: 0.2rem !important;
            font-size: 0.9rem;
            font-weight: 500;
            color: #A0A7B3;
        }
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            gap: 0.3rem !important;
        }
        .stTextArea textarea {
            background-color: #1C2028 !important;
            color: #FAFAFA !important;
            border: 1px solid #333A44 !important;
            border-radius: 6px !important;
            min-height: 70px !important;
        }
        .stTextArea textarea:focus {
            border-color: #FF69B4 !important;
            box-shadow: 0 0 0 0.2rem rgba(255, 105, 180, 0.25) !important;
        }
        div[data-testid="stButton"] > button {
            background-color: #FF69B4; color: white; border: none; padding: 0.6rem 1.5rem;
            border-radius: 8px; font-weight: 600; font-size: 1rem;
            transition: background-color 0.2s ease-in-out, transform 0.1s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2); margin-top: 0.5rem;
        }
        div[data-testid="stButton"] > button:hover { background-color: #FF85C8; transform: translateY(-1px); }
        div[data-testid="stButton"] > button:active { background-color: #E05A9A; transform: translateY(0px); }

        /* --- Sidebar Styling --- */
        /* (Keep existing sidebar styles) */
        [data-testid="stSidebar"] { background-color: #1C2028; padding: 1rem; }
        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
            background-color: #262B34; color: #FAFAFA; border: 1px solid #333A44;
        }
        [data-testid="stSidebar"] h2 { color: #A9D5FF; font-size: 1.2rem; }
        [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] .stAlert p { color: #BDC3C7; }


        /* --- Output Area Specific Styles (Right Column) --- */
        .date-plan-output-container { /* This is the BOX for plan/error */
            max-height: calc(100vh - 200px); /* Adjust 200px based on total height of elements above it + desired bottom margin */
            overflow-y: auto;
            padding: 20px;
            background-color: #1C2028;
            border: 1px solid #333A44;
            border-radius: 8px;
            color: #D0D3D4;
            font-size: 0.9em;
            line-height: 1.6;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            margin-top: 0.5rem; /* Small space after subheader if box is shown */
        }
        .plan-title {
            font-size: 1.6em; font-weight: 700; color: #FFD700; margin-bottom: 0.6em;
            text-align: center; border-bottom: 2px solid #FFD700; padding-bottom: 0.3em;
        }
        .plan-meta-info {
            font-size: 0.95em; color: #85929E; margin-bottom: 1em;
            text-align: center; font-style: italic; line-height: 1.4;
        }
        .plan-meta-info b { color: #AAB7B8; font-weight: 500; }
        .plan-section-title {
            font-size: 1.25em; font-weight: 600; color: #76D7C4; margin-top: 1.2em;
            margin-bottom: 0.5em; border-bottom: 1px solid #333A44; padding-bottom: 0.2em;
        }
        .plan-step-title { color: #A9D5FF; font-weight: 600; }
        .plan-description { font-size: 1em; color: #CACFD2; margin-bottom: 0.5em; padding-left: 10px; }
        .plan-list-item { font-size: 1em; color: #CACFD2; margin-left: 1.5em; margin-bottom: 0.4em; list-style-type: "✨ "; }
        
        .plan-error-message { /* Styled for when it's INSIDE the box */
            color: #FF6B6B; font-weight: 500; background-color: rgba(255, 107, 107, 0.1);
            padding: 10px; border-radius: 6px; border-left: 4px solid #FF6B6B;
        }
        .plan-initial-message { /* Styled for when it's OUTSIDE the box */
            color: #A9D5FF;
            font-style: italic;
            text-align: center;
            padding-top: 1rem; /* Space below the subheader */
            padding-bottom: 1rem;
            font-size: 0.95em;
        }

    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>💖 Date Night Planner AI 🥂</h1>", unsafe_allow_html=True)

# --- Sidebar ---
# (Keep sidebar code as is)
with st.sidebar:
    st.header("🔑 API & Model Config")
    default_api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key_input = st.text_input("Google AI Key", type="password", value=default_api_key, help="Get your key from Google AI Studio.")
    if not api_key_input and default_api_key: api_key_input = default_api_key
    available_models = ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-1.0-pro"]
    default_model_index = 0
    if "gemini-1.5-flash-latest" in available_models: default_model_index = available_models.index("gemini-1.5-flash-latest")
    selected_model = st.selectbox("Choose Gemini Model", available_models, index=default_model_index, help="Select model. Flash is faster, Pro is more capable.")
    st.markdown("---")
    st.info("Adjust API key & model. Ensure selected model follows JSON instructions well.")

# --- Main Layout: Two Columns ---
left_column, right_column = st.columns([0.42, 0.58])

with left_column:
    # (Keep left column content as is)
    st.markdown("<p class='left-column-section-title'>Your Preferences</p>", unsafe_allow_html=True)
    themes = ["Romantic ❤️", "Fun 🎉", "Chill 🧘", "Adventure 🚀", "Artsy 🎨", "Homebody 🏡", "Intellectual 🧠", "Foodie 🍲", "Mysterious 🕵️", "Nostalgic 🕰️"]
    selected_theme = st.selectbox("Theme", themes, help="What's the overall mood or vibe for the date?")
    activity_types = ["At Home 🏠", "Out (Casual)🚶", "Out (Fancy)👗", "Outdoor Adventure 🌳", "Creative/DIY 🎨", "Learning Together 📚", "Volunteer/Give Back 🤝", "Relax & Unwind 🛀"]
    selected_activity_type = st.selectbox("Activity Type", activity_types, help="What kind of general activity are you looking for?")
    st.markdown("<p class='left-column-section-title'>Practical Considerations</p>", unsafe_allow_html=True)
    col_budget, col_prep = st.columns(2)
    with col_budget: current_budget_val = st.slider("Budget Level", 1, 5, 2, format="%d/5", help="1 (very tight) to 5 (splurge / special occasion)")
    with col_prep: current_prep_time_val = st.slider("Preparation Time", 1, 5, 2, format="%d/5", help="1 (spontaneous) to 5 (elaborate planning)")
    selected_budget_description = map_budget_value_to_description(current_budget_val)
    selected_prep_time_description = map_prep_time_value_to_description(current_prep_time_val)
    st.markdown("<p class='left-column-section-title'>Any Specifics?</p>", unsafe_allow_html=True)
    user_custom_input = st.text_area(label="Suggestions or Restrictions", height=75, placeholder="e.g., loves Italian food, allergic to cats, must be indoors, surprise me!", help="Must-haves, must-nots, or specific ideas?", key="user_custom_input_area_v2")
    if 'generated_plan_content' not in st.session_state: st.session_state.generated_plan_content = {"message": "Let's plan something amazing! Fill in your preferences and click Generate."}
    if st.button("✨ Generate Date Plan ✨", type="primary", use_container_width=True):
        if not api_key_input: st.session_state.generated_plan_content = {"error": "⚠️ Oops! Please enter your Google API Key in the sidebar."}
        elif not selected_model: st.session_state.generated_plan_content = {"error": "⚠️ Please select a Gemini model in the sidebar."}
        else:
            with st.spinner("💖 Crafting your perfect date night..."): # Spinner now in left or global context
                plan_output = generate_date_plan_with_gemini(api_key_input, selected_model, selected_theme, selected_activity_type, selected_budget_description, selected_prep_time_description, user_custom_input, current_budget_val, current_prep_time_val)
            st.session_state.generated_plan_content = plan_output


with right_column:
    # Wrap the entire right column content to try and control top spacing
    st.markdown("<div class='right-column-content-wrapper'>", unsafe_allow_html=True)

    st.markdown("<h2 class='right-column-subheader'>💡 Your Personalized Date Night Idea 💡</h2>", unsafe_allow_html=True)

    plan_data = st.session_state.generated_plan_content
    
    # Determine if we are showing only the initial placeholder message
    is_initial_placeholder = isinstance(plan_data, dict) and "message" in plan_data and \
                             not plan_data.get("error") and not plan_data.get("title")

    if is_initial_placeholder:
        # Display initial message without the styled box
        st.markdown(f"<p class='plan-initial-message'>{plan_data['message']}</p>", unsafe_allow_html=True)
    else:
        # Display the styled box for errors or actual plans
        st.markdown("<div class='date-plan-output-container'>", unsafe_allow_html=True)
        if isinstance(plan_data, dict):
            if "error" in plan_data:
                st.markdown(f"<div class='plan-error-message'>{plan_data['error']}</div>", unsafe_allow_html=True)
            elif "title" in plan_data: # It's an actual plan
                st.markdown(f"<p class='plan-title'>{plan_data.get('title', 'N/A')}</p>", unsafe_allow_html=True)
                meta_html = f"""
                <div class='plan-meta-info'>
                    <b>Theme:</b> {plan_data.get('theme', 'N/A')} | <b>Activity:</b> {plan_data.get('activity_type', 'N/A')} <br>
                    <b>Budget:</b> {plan_data.get('budget_level', 'N/A')}/5 ({plan_data.get('budget_description', 'N/A')}) <br>
                    <b>Prep Time:</b> {plan_data.get('prep_time_level', 'N/A')}/5 ({plan_data.get('prep_time_description', 'N/A')}) <br>
                    <i>(Powered by {plan_data.get('model_used', 'Gemini AI')})</i>
                </div>"""
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
            # else: # Should not happen if logic is correct, but a fallback placeholder inside the box
            #    st.markdown(f"<p class='plan-description' style='text-align:center; padding:20px;'>Processing...</p>", unsafe_allow_html=True)

        else: # Fallback for non-dict, non-error, non-plan (e.g. old string message)
            st.markdown(f"<p class='plan-description'>{str(plan_data)}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True) # Close .date-plan-output-container

    st.markdown("</div>", unsafe_allow_html=True) # Close .right-column-content-wrapper