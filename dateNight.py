import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

# --- Configuration & Setup ---
load_dotenv()

# --- Helper Functions ---
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
            parsed_json = json.loads(raw_text_response.strip())
            return parsed_json
        except json.JSONDecodeError as e:
            error_detail = f"Failed to parse JSON. Error: {e}. Raw (first 500 chars): '{raw_text_response[:500]}...'"
            # Try to find where the JSON might be broken for debugging
            # This is a very basic attempt and might not always pinpoint the exact issue
            context_chars = 100
            error_pos = getattr(e, 'pos', None)
            if error_pos is not None:
                start = max(0, error_pos - context_chars)
                end = min(len(raw_text_response), error_pos + context_chars)
                error_context = raw_text_response[start:end]
                error_detail += f"\nContext around error position ({error_pos}): ...{error_context}..."
            return {"error": error_detail}

    except Exception as e:
        return {"error": f"An error occurred: {e}"}

# --- Streamlit App UI ---
st.set_page_config(page_title="Date Night Planner", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS for Styling ---
st.markdown("""
    <style>
        /* --- General App Body & Font --- */
        html, body, #root, .stApp {
            height: 100%;
            overflow: hidden; /* Prevents double scrollbars */
            background-color: #0E1117; /* Streamlit's default dark background */
            color: #FAFAFA; /* Default light text color */
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
        }
        .main .block-container {
            padding-top: 1.5rem; /* Increased top padding */
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* --- Titles & Headers --- */
        h1 { /* Main App Title */
            font-size: 2.2rem !important;
            color: #FF69B4; /* Hot Pink for a fun accent */
            text-align: center;
            margin-bottom: 1rem !important;
            font-weight: 700;
        }
        /* Subheader for the right column "Your Date Night Idea" */
        .right-column-subheader {
            font-size: 1.5rem !important; /* Larger */
            font-weight: 600;
            color: #A9D5FF; /* Light blue accent */
            margin-bottom: 0.75rem !important;
            text-align: center;
        }
        /* Titles for sections in the left column (Preferences, Practicalities) */
        .left-column-section-title {
            font-size: 1.1rem !important;
            font-weight: 600;
            color: #BDC3C7; /* Lighter gray */
            margin-top: 1rem !important;
            margin-bottom: 0.3rem !important;
            border-bottom: 1px solid #333A44;
            padding-bottom: 0.2rem;
        }

        /* --- Input Elements Styling (Left Column) --- */
        div[data-testid="stSelectbox"] > label,
        div[data-testid="stSlider"] > label,
        div[data-testid="stTextArea"] > label {
            margin-bottom: 0.2rem !important;
            font-size: 0.9rem; /* Slightly larger label */
            font-weight: 500;
            color: #A0A7B3;
        }
        /* Reducing vertical gap between input elements */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            gap: 0.3rem !important;
        }
        .stTextArea textarea {
            background-color: #1C2028 !important;
            color: #FAFAFA !important;
            border: 1px solid #333A44 !important;
            border-radius: 6px !important;
            min-height: 70px !important; /* Ensure min height for text area */
        }
        .stTextArea textarea:focus {
            border-color: #FF69B4 !important;
            box-shadow: 0 0 0 0.2rem rgba(255, 105, 180, 0.25) !important;
        }
        /* Slider track and thumb */
        div[data-testid="stSlider"] .stSlider {
             /* You can't style slider thumbs and tracks extensively with pure CSS here due to shadow DOM */
             /* But basic color of the label/value can be influenced */
        }

        /* --- Button Styling --- */
        div[data-testid="stButton"] > button {
            background-color: #FF69B4; /* Hot Pink */
            color: white;
            border: none;
            padding: 0.6rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1rem;
            transition: background-color 0.2s ease-in-out, transform 0.1s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            margin-top: 0.5rem; /* Add some space above the button */
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #FF85C8; /* Lighter pink on hover */
            transform: translateY(-1px);
        }
        div[data-testid="stButton"] > button:active {
            background-color: #E05A9A; /* Darker pink on active */
            transform: translateY(0px);
        }


        /* --- Sidebar Styling --- */
        [data-testid="stSidebar"] {
            background-color: #1C2028; /* Slightly different dark for sidebar */
            padding: 1rem;
        }
        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
            background-color: #262B34;
            color: #FAFAFA;
            border: 1px solid #333A44;
        }
        [data-testid="stSidebar"] h2 { /* "API & Model Config" */
            color: #A9D5FF;
            font-size: 1.2rem;
        }
         [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] .stAlert p { /* For st.info text */
            color: #BDC3C7;
        }


        /* --- Output Area Specific Styles (Right Column) --- */
        .date-plan-output-container {
            height: calc(100vh - 130px); /* Adjusted for potentially taller title/subheader */
            overflow-y: auto;
            padding: 20px;
            background-color: #1C2028; /* Dark background for output */
            border: 1px solid #333A44; /* Subtle border */
            border-radius: 8px;
            color: #D0D3D4; /* Default light text for output */
            font-size: 0.9em;
            line-height: 1.6;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3); /* More pronounced shadow */
        }
        .plan-title { /* Title of the Date Plan Itself */
            font-size: 1.6em; /* Relative to 0.9em base */
            font-weight: 700;
            color: #FFD700; /* Gold accent for plan title */
            margin-bottom: 0.6em;
            text-align: center;
            border-bottom: 2px solid #FFD700;
            padding-bottom: 0.3em;
        }
        .plan-meta-info {
            font-size: 0.95em; /* Relative to 0.9em base */
            color: #85929E; /* Softer gray for meta */
            margin-bottom: 1em;
            text-align: center;
            font-style: italic;
            line-height: 1.4;
        }
        .plan-meta-info b {
            color: #AAB7B8; /* Slightly brighter for bolded parts in meta */
            font-weight: 500;
        }
        .plan-section-title { /* "The Plan:", "Tips & Considerations:" */
            font-size: 1.25em; /* Relative to 0.9em base */
            font-weight: 600;
            color: #76D7C4; /* Teal accent for section titles */
            margin-top: 1.2em;
            margin-bottom: 0.5em;
            border-bottom: 1px solid #333A44;
            padding-bottom: 0.2em;
        }
        .plan-step-title { /* For "Step 1 Title:", "Food/Drinks:" */
            color: #A9D5FF; /* Light blue for step titles */
            font-weight: 600;
        }
        .plan-description {
            font-size: 1em; /* Relative to 0.9em base */
            color: #CACFD2; /* Main text color for descriptions */
            margin-bottom: 0.5em;
            padding-left: 10px; /* Indent description slightly */
        }
        .plan-list-item { /* For tips */
            font-size: 1em; /* Relative to 0.9em base */
            color: #CACFD2;
            margin-left: 1.5em; /* Indent list items */
            margin-bottom: 0.4em;
            list-style-type: "✨ "; /* Fun emoji bullet */
        }
        .plan-error-message {
            color: #FF6B6B; /* Red for errors */
            font-weight: 500;
            background-color: rgba(255, 107, 107, 0.1);
            padding: 10px;
            border-radius: 6px;
            border-left: 4px solid #FF6B6B;
        }
        .plan-initial-message {
            color: #A9D5FF;
            font-style: italic;
            text-align: center;
            padding-top: 20px;
        }

    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>💖 Date Night Planner AI 🥂</h1>", unsafe_allow_html=True)


# --- Sidebar for API Key & Model Selection ---
with st.sidebar:
    st.header("🔑 API & Model Config")
    default_api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key_input = st.text_input(
        "Google AI Key",
        type="password",
        value=default_api_key,
        help="Get your key from Google AI Studio."
    )
    if not api_key_input and default_api_key: api_key_input = default_api_key

    available_models = [
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest",
        "gemini-1.0-pro",
    ]
    default_model_index = 0
    if "gemini-1.5-flash-latest" in available_models:
        default_model_index = available_models.index("gemini-1.5-flash-latest")

    selected_model = st.selectbox(
        "Choose Gemini Model",
        available_models,
        index=default_model_index,
        help="Select the AI model. 'Flash' is faster, 'Pro' is more capable. Model choice affects conciseness & JSON adherence."
    )
    st.markdown("---")
    st.info("Adjust API key & model if needed. Ensure the selected model can follow JSON instructions well for best results.")


# --- Main Layout: Two Columns ---
left_column, right_column = st.columns([0.42, 0.58]) # Adjusted ratio

with left_column:
    st.markdown("<p class='left-column-section-title'>Your Preferences</p>", unsafe_allow_html=True)
    themes = ["Romantic ❤️", "Fun 🎉", "Chill 🧘", "Adventure 🚀", "Artsy 🎨", "Homebody 🏡", "Intellectual 🧠", "Foodie 🍲", "Mysterious 🕵️", "Nostalgic 🕰️"]
    selected_theme = st.selectbox("Theme", themes, help="What's the overall mood or vibe for the date?")

    activity_types = ["At Home 🏠", "Out (Casual)🚶", "Out (Fancy)👗", "Outdoor Adventure 🌳", "Creative/DIY 🎨", "Learning Together 📚", "Volunteer/Give Back 🤝", "Relax & Unwind 🛀"]
    selected_activity_type = st.selectbox("Activity Type", activity_types, help="What kind of general activity are you looking for?")

    st.markdown("<p class='left-column-section-title'>Practical Considerations</p>", unsafe_allow_html=True)
    col_budget, col_prep = st.columns(2)
    with col_budget:
        current_budget_val = st.slider("Budget Level", 1, 5, 2, format="%d/5", help="1 (very tight) to 5 (splurge / special occasion)")
    with col_prep:
        current_prep_time_val = st.slider("Preparation Time", 1, 5, 2, format="%d/5", help="1 (spontaneous) to 5 (elaborate planning)")

    selected_budget_description = map_budget_value_to_description(current_budget_val)
    selected_prep_time_description = map_prep_time_value_to_description(current_prep_time_val)

    st.markdown("<p class='left-column-section-title'>Any Specifics?</p>", unsafe_allow_html=True)
    user_custom_input = st.text_area(
        label="Suggestions or Restrictions",
        height=75, # Increased slightly as 68px is min
        placeholder="e.g., loves Italian food, allergic to cats, must be indoors, one person is vegan, surprise me!",
        help="Any must-haves, must-nots, or specific ideas you want to include?",
        key="user_custom_input_area_v2"
    )

    if 'generated_plan_content' not in st.session_state:
        st.session_state.generated_plan_content = {"message": "Let's plan something amazing! Fill in your preferences and click Generate."}


    if st.button("✨ Generate Date Plan ✨", type="primary", use_container_width=True):
        if not api_key_input:
            st.session_state.generated_plan_content = {"error": "⚠️ Oops! Please enter your Google API Key in the sidebar to get started."}
        elif not selected_model:
            st.session_state.generated_plan_content = {"error": "⚠️ Please select a Gemini model in the sidebar first."}
        else:
            with right_column:
                 with st.spinner("💖 Crafting your perfect date night..."):
                    plan_output = generate_date_plan_with_gemini(
                        api_key_input,
                        selected_model,
                        selected_theme,
                        selected_activity_type,
                        selected_budget_description,
                        selected_prep_time_description,
                        user_custom_input,
                        current_budget_val,
                        current_prep_time_val
                    )
            st.session_state.generated_plan_content = plan_output

with right_column:
    st.markdown("<h2 class='right-column-subheader'>💡 Your Personalized Date Night Idea 💡</h2>", unsafe_allow_html=True)

    plan_data = st.session_state.generated_plan_content
    
    st.markdown("<div class='date-plan-output-container'>", unsafe_allow_html=True)

    if isinstance(plan_data, dict):
        if "error" in plan_data:
            st.markdown(f"<div class='plan-error-message'>{plan_data['error']}</div>", unsafe_allow_html=True)
        elif "message" in plan_data:
            st.markdown(f"<p class='plan-initial-message'>{plan_data['message']}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p class='plan-title'>{plan_data.get('title', 'Awaiting Your Plan...')}</p>", unsafe_allow_html=True)
            
            meta_html = f"""
            <div class='plan-meta-info'>
                <b>Theme:</b> {plan_data.get('theme', 'N/A')} | 
                <b>Activity:</b> {plan_data.get('activity_type', 'N/A')} <br>
                <b>Budget:</b> {plan_data.get('budget_level', 'N/A')}/5 ({plan_data.get('budget_description', 'N/A')}) <br>
                <b>Prep Time:</b> {plan_data.get('prep_time_level', 'N/A')}/5 ({plan_data.get('prep_time_description', 'N/A')}) <br>
                <i>(Powered by {plan_data.get('model_used', 'Gemini AI')})</i>
            </div>
            """
            st.markdown(meta_html, unsafe_allow_html=True)

            plan_details = plan_data.get('plan_details', {})
            if any(plan_details.values()): # Check if there are any actual plan details
                st.markdown("<p class='plan-section-title'>🎉 The Plan Unveiled:</p>", unsafe_allow_html=True)

                if plan_details.get('step_1_title') and plan_details.get('step_1_description'):
                    st.markdown(f"<span class='plan-step-title'>{plan_details['step_1_title']}:</span> <span class='plan-description'>{plan_details['step_1_description']}</span>", unsafe_allow_html=True)
                
                if plan_details.get('step_2_title') and plan_details.get('step_2_description'):
                    st.markdown(f"<span class='plan-step-title'>{plan_details['step_2_title']}:</span> <span class='plan-description'>{plan_details['step_2_description']}</span>", unsafe_allow_html=True)

                if plan_details.get('food_drinks_suggestions'):
                    st.markdown(f"<span class='plan-step-title'>🍽️ Food & Drinks:</span> <span class='plan-description'>{plan_details['food_drinks_suggestions']}</span>", unsafe_allow_html=True)
                
                if plan_details.get('ambiance_extras_suggestions'):
                    st.markdown(f"<span class='plan-step-title'>✨ Ambiance & Extras:</span> <span class='plan-description'>{plan_details['ambiance_extras_suggestions']}</span>", unsafe_allow_html=True)

            tips = plan_data.get('tips_and_considerations', [])
            if tips and any(tip.strip() for tip in tips): # Ensure tips are not just empty strings
                st.markdown("<p class='plan-section-title'>💡 Pro Tips & Considerations:</p>", unsafe_allow_html=True)
                for tip in tips:
                    if tip.strip(): # Only display non-empty tips
                        st.markdown(f"<div class='plan-list-item'>{tip}</div>", unsafe_allow_html=True) # Using div for more control if needed
    else:
        st.markdown(f"<p class='plan-description'>{str(plan_data)}</p>", unsafe_allow_html=True) # Fallback
    
    st.markdown("</div>", unsafe_allow_html=True) # Close date-plan-output-container