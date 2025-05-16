import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json # Import the json library

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
          "title": "[Catchy Date Night Title - concise and engaging]",
          "theme": "{theme}",
          "activity_type": "{activity_type}",
          "budget_level": {current_budget_value},
          "budget_description": "{budget_desc}",
          "prep_time_level": {current_prep_time_value},
          "prep_time_description": "{prep_time_desc}",
          "model_used": "{selected_model_name}",
          "plan_details": {{
            "step_1_title": "[Concise title for Step 1, e.g., 'Cozy Corner Creation']",
            "step_1_description": "[Detailed but concise description for Step 1]",
            "step_2_title": "[Concise title for Step 2, e.g., 'Memory Lane & Dreams']",
            "step_2_description": "[Detailed but concise description for Step 2]",
            "food_drinks_suggestions": "[Optional: Concise suggestions for food/drinks. If none, use an empty string or omit key.]",
            "ambiance_extras_suggestions": "[Optional: Concise ideas for ambiance/extras. If none, use an empty string or omit key.]"
          }},
          "tips_and_considerations": [
            "[Concise Tip 1]",
            "[Concise Tip 2 (if applicable)]"
          ]
        }}

        Ensure all string values within the JSON are concise and to the point, while still providing all relevant information.
        Focus on delivering the plan clearly and engagingly within this JSON structure.
        """
        response = model.generate_content(prompt)
        raw_text_response = ""
        if hasattr(response, 'text'):
            raw_text_response = response.text
        elif isinstance(response, str):
             raw_text_response = response # Should not happen with current genai
        elif hasattr(response, 'parts') and response.parts:
            raw_text_response = "".join(part.text for part in response.parts if hasattr(part, 'text'))
        else:
            return {"error": f"Unexpected response format from API: {str(response)}"}

        # Clean the response: Gemini might sometimes wrap JSON in ```json ... ```
        if raw_text_response.strip().startswith("```json"):
            raw_text_response = raw_text_response.strip()[7:] # Remove ```json
            if raw_text_response.strip().endswith("```"):
                raw_text_response = raw_text_response.strip()[:-3] # Remove trailing ```

        try:
            parsed_json = json.loads(raw_text_response.strip())
            return parsed_json
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse JSON response from AI. Error: {e}. Raw response: '{raw_text_response[:500]}'..."} # Show beginning of raw response

    except Exception as e:
        return {"error": f"An error occurred while generating the plan with {selected_model_name}: {e}"}

# --- Streamlit App UI ---
st.set_page_config(page_title="Date Night Planner", layout="wide", initial_sidebar_state="expanded")

# Global CSS for smaller base font in the output area
st.markdown("""
    <style>
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        /* Reduce gap for input elements */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            gap: 0.1rem !important;
        }
        div[data-testid="stSelectbox"] > label,
        div[data-testid="stSlider"] > label,
        div[data-testid="stTextArea"] > label {
            margin-bottom: 0.05rem !important; /* even smaller margin */
            font-size: 0.875rem;
        }
        h1 { /* Main Title */
            font-size: 1.8rem !important;
            margin-bottom: 0.5rem !important;
        }
        /* Titles for sections in the left column */
        .left-column-section-title {
            font-size: 1.0rem !important;
            font-weight: bold;
            margin-top: 0.5rem !important;
            margin-bottom: 0.1rem !important;
        }
        html, body, #root, .stApp {
            height: 100%;
            overflow: hidden;
        }
        .stApp {
             height: 100vh;
        }
        div[data-testid="stSidebar"] div[data-testid="stSelectbox"] > label {
             font-size: 0.875rem !important;
             margin-bottom: 0.1rem !important;
        }

        /* --- Output Area Specific Styles --- */
        .date-plan-output-container {
            height: calc(100vh - 100px); /* Adjust 100px based on title, subheader etc. */
            overflow-y: auto;
            padding: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background-color: #f9f9f9;
            font-size: 0.8em; /* Base smaller font for the output area */
            line-height: 1.5;
        }
        .plan-title {
            font-size: 1.4em; /* Relative to 0.8em base -> approx 1.12em of normal */
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 0.5em;
        }
        .plan-section-title {
            font-size: 1.1em; /* Relative to 0.8em base */
            font-weight: bold;
            color: #34495e;
            margin-top: 0.8em;
            margin-bottom: 0.3em;
        }
        .plan-meta-info {
            font-size: 0.9em; /* Relative to 0.8em base */
            color: #7f8c8d;
            margin-bottom: 0.6em;
            font-style: italic;
        }
        .plan-description {
            font-size: 1em; /* Relative to 0.8em base */
            color: #333;
            margin-bottom: 0.4em;
        }
        .plan-list-item {
            font-size: 1em; /* Relative to 0.8em base */
            margin-left: 1.2em; /* Indent list items */
            margin-bottom: 0.3em;
        }
    </style>
""", unsafe_allow_html=True)

st.title("💖 Date Night Planner AI 🥂")

# --- Sidebar for API Key & Model Selection ---
st.sidebar.header("🔑 API & Model Config")
default_api_key = os.getenv("GOOGLE_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "Google AI Key",
    type="password",
    value=default_api_key,
    help="Get your key from Google AI Studio."
)
if not api_key_input and default_api_key: api_key_input = default_api_key

available_models = [
    "gemini-2.5-flash-preview-04-17",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro-latest",
    "gemini-1.0-pro",
]
default_model_index = 0
if "gemini-1.5-flash-latest" in available_models:
    default_model_index = available_models.index("gemini-1.5-flash-latest")

selected_model = st.sidebar.selectbox(
    "Choose Gemini Model",
    available_models,
    index=default_model_index,
    help="Select the AI model to generate ideas. 'Flash' is faster, 'Pro' is more capable."
)
st.sidebar.markdown("---")

# --- Main Layout: Two Columns ---
left_column, right_column = st.columns([0.4, 0.6]) # Adjusted ratio slightly

with left_column:
    st.markdown("<p class='left-column-section-title'>Preferences</p>", unsafe_allow_html=True)
    themes = ["Romantic ❤️", "Fun 🎉", "Chill 🧘", "Adventure 🚀", "Artsy 🎨", "Homebody 🏡", "Intellectual 🧠", "Foodie 🍲"]
    selected_theme = st.selectbox("Theme", themes, help="Mood of the date.")

    activity_types = ["At Home 🏠", "Out (Casual)🚶", "Out (Fancy)👗", "Outdoor 🌳", "Create 🖌️", "Learn 📚", "Volunteer 🤝"]
    selected_activity_type = st.selectbox("Activity Type", activity_types, help="General type of activity.")

    st.markdown("<p class='left-column-section-title'>Practicalities</p>", unsafe_allow_html=True)
    col_budget, col_prep = st.columns(2)
    with col_budget:
        current_budget_val = st.slider("Budget", 1, 5, 2, format="%d/5", help="1 (tight) - 5 (splurge)")
    with col_prep:
        current_prep_time_val = st.slider("Prep Time", 1, 5, 2, format="%d/5", help="1 (quick) - 5 (elaborate)")

    selected_budget_description = map_budget_value_to_description(current_budget_val)
    selected_prep_time_description = map_prep_time_value_to_description(current_prep_time_val)

    st.markdown("<p class='left-column-section-title'>Your Specifics</p>", unsafe_allow_html=True)

    # --- START TROUBLESHOOTING HERE ---
    try:
            user_custom_input = st.text_area(
        label="Restrictions/Ideas?",
        height=70, # Or 68, or any value >= 68. Let's use 70 for a bit of buffer.
        placeholder="e.g., Italian food, no cats, one person is vegan.",
        help="Any must-haves or must-nots.",
        key="user_custom_input_area_v1" # Keep the key
    )
    except Exception as e:
        st.error(f"Error creating text_area: {e}") # Try to catch and display the error directly
        user_custom_input = "" # Provide a fallback value
    # --- END TROUBLESHOOTING HERE ---


    if 'generated_plan_content' not in st.session_state:
        st.session_state.generated_plan_content = {"message": "Your date idea will appear here! ✨"}

    # ... rest of your left_column code


    if st.button("✨ Generate Plan ✨", type="primary", use_container_width=True):
        if not api_key_input:
            st.session_state.generated_plan_content = {"error": "⚠️ Please enter your Google API Key in the sidebar!"}
        elif not selected_model:
            st.session_state.generated_plan_content = {"error": "⚠️ Please select a Gemini model in the sidebar!"}
        else:
            with right_column: # Show spinner in the right column
                 with st.spinner("💖 Planning your perfect date..."):
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
    st.markdown("<h3 style='font-size: 1.2rem; margin-bottom: 0.3rem;'>💡 Your Date Night Idea</h3>", unsafe_allow_html=True)

    plan_data = st.session_state.generated_plan_content
    
    # Start the container div for the output
    st.markdown("<div class='date-plan-output-container'>", unsafe_allow_html=True)

    if isinstance(plan_data, dict):
        if "error" in plan_data:
            st.error(plan_data["error"])
        elif "message" in plan_data: # For initial message
            st.markdown(f"<p class='plan-description'>{plan_data['message']}</p>", unsafe_allow_html=True)
        else:
            # Displaying the structured JSON data
            st.markdown(f"<p class='plan-title'>{plan_data.get('title', 'N/A')}</p>", unsafe_allow_html=True)
            
            meta_html = f"""
            <p class='plan-meta-info'>
                <b>Theme:</b> {plan_data.get('theme', 'N/A')} | 
                <b>Activity:</b> {plan_data.get('activity_type', 'N/A')} <br>
                <b>Budget:</b> {plan_data.get('budget_level', 'N/A')}/5 ({plan_data.get('budget_description', 'N/A')}) <br>
                <b>Prep Time:</b> {plan_data.get('prep_time_level', 'N/A')}/5 ({plan_data.get('prep_time_description', 'N/A')}) <br>
                <i>(Generated using {plan_data.get('model_used', 'N/A')})</i>
            </p>
            """
            st.markdown(meta_html, unsafe_allow_html=True)

            plan_details = plan_data.get('plan_details', {})
            st.markdown("<p class='plan-section-title'>🎉 The Plan:</p>", unsafe_allow_html=True)

            if plan_details.get('step_1_title') and plan_details.get('step_1_description'):
                st.markdown(f"<b>{plan_details['step_1_title']}:</b> <span class='plan-description'>{plan_details['step_1_description']}</span>", unsafe_allow_html=True)
            
            if plan_details.get('step_2_title') and plan_details.get('step_2_description'):
                st.markdown(f"<b>{plan_details['step_2_title']}:</b> <span class='plan-description'>{plan_details['step_2_description']}</span>", unsafe_allow_html=True)

            if plan_details.get('food_drinks_suggestions'):
                st.markdown(f"<b>Food/Drinks:</b> <span class='plan-description'>{plan_details['food_drinks_suggestions']}</span>", unsafe_allow_html=True)
            
            if plan_details.get('ambiance_extras_suggestions'):
                st.markdown(f"<b>Ambiance/Extras:</b> <span class='plan-description'>{plan_details['ambiance_extras_suggestions']}</span>", unsafe_allow_html=True)

            tips = plan_data.get('tips_and_considerations', [])
            if tips:
                st.markdown("<p class='plan-section-title'>💡 Tips & Considerations:</p>", unsafe_allow_html=True)
                for tip in tips:
                    st.markdown(f"<li class='plan-list-item'>{tip}</li>", unsafe_allow_html=True)
    else:
        # Fallback for any unexpected string content (e.g., old error messages)
        st.markdown(f"<p class='plan-description'>{str(plan_data)}</p>", unsafe_allow_html=True)
    
    # Close the container div
    st.markdown("</div>", unsafe_allow_html=True)


st.sidebar.info("Using JSON for structured output. Model choice can affect conciseness & JSON adherence.")