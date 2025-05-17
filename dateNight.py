import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import math # For rounding

# --- Configuration & Setup ---
load_dotenv()

# --- Helper Functions ---
def map_budget_value_to_description(value_float):
    value = round(value_float)
    if value == 1: return "Extremely tight, focus on free or DIY options, minimal to no spending."
    if value == 2: return "Very low budget, some minimal spending is acceptable."
    if value == 3: return "Moderate budget, allows for a casual outing or some purchases."
    if value == 4: return "Generous budget, can afford a nice dinner out or event tickets."
    return "Splurge / Special Occasion, high budget, willing to spend significantly."

def map_prep_time_value_to_description(value_float):
    value = round(value_float)
    if value == 1: return "Almost no preparation needed (under 30 mins), very spontaneous."
    if value == 2: return "Quick preparation (30 mins to 1 hour)."
    if value == 3: return "Moderate preparation (1-2 hours)."
    if value == 4: return "Involved preparation (2-4 hours), some planning."
    return "Elaborate preparation (4+ hours), significant planning."

def generate_date_plan_with_gemini(api_key, selected_model_name,
                                   theme, activity_type,
                                   budget_desc, prep_time_desc, user_input,
                                   current_budget_level, current_prep_time_level,
                                   time_budget_hours, planning_style_prompt_line):
    if not api_key:
        return {"error": "Google API Key is missing. Please enter it in the sidebar."}
    if not selected_model_name:
        return {"error": "Please select a Gemini model in the sidebar."}
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=selected_model_name)

        time_budget_line = f"- Maximum Activity Duration: Approximately {time_budget_hours:.2f} hours." if time_budget_hours is not None else ""
        
        actual_planning_style_for_json = "Not specified"
        if planning_style_prompt_line:
            parts = planning_style_prompt_line.split(': ', 1)
            if len(parts) > 1:
                actual_planning_style_for_json = parts[1].strip()
            # If no ": " is found, or if it's at the very end, this will keep "Not specified"
            # or you could use parts[0] if you want the whole string in that case.
            # For now, this logic is fine for extracting text after ": ".

        prompt = f"""
        You are a creative and helpful date night planning assistant.
        Your goal is to generate a fun and suitable date night plan based on the user's preferences.
        The user is utilizing the '{selected_model_name}' model.
        {planning_style_prompt_line}

        User Preferences:
        - Theme: {theme}
        - Activity Type: {activity_type}
        - Budget Consideration: "{budget_desc}" (Approx. level: {current_budget_level:.2f}/5)
        - Time to Prepare Consideration: "{prep_time_desc}" (Approx. level: {current_prep_time_level:.2f}/5)
        {time_budget_line}
        - User's specific suggestions or restrictions: "{user_input if user_input else 'None'}"


        **IMPORTANT INSTRUCTION:**
        Your response MUST be a single, valid JSON object. Do NOT include any text outside of this JSON object.
        The JSON object should follow this structure:

        {{
          "title": "[Catchy Date Night Title - concise, max 5-7 words]",
          "theme": "{theme}",
          "activity_type": "{activity_type}",
          "budget_level": {current_budget_level:.2f},
          "budget_description": "{budget_desc}",
          "prep_time_level": {current_prep_time_level:.2f},
          "prep_time_description": "{prep_time_desc}",
          "time_budget_hours": "{time_budget_hours:.2f} hours" if time_budget_hours is not None else "Not specified",
          "planning_style": "{actual_planning_style_for_json}",
          "model_used": "{selected_model_name}",
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
        .left-column-section-title {font-size: 1.1rem !important; font-weight: 600; color: #BDC3C7; margin-top: 1rem !important; margin-bottom: 0.3rem !important; border-bottom: 1px solid #333A44; padding-bottom: 0.2rem;}
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
        .date-plan-output-container {max-height: calc(100vh - 200px); overflow-y: auto; padding: 20px; background-color: #1C2028; border: 1px solid #333A44; border-radius: 8px; color: #D0D3D4; font-size: 0.9em; line-height: 1.6; box-shadow: 0 4px 12px rgba(0,0,0,0.3); margin-top: 0.5rem;}
        .plan-title {font-size: 1.6em; font-weight: 700; color: #FFD700; margin-bottom: 0.6em; text-align: center; border-bottom: 2px solid #FFD700; padding-bottom: 0.3em;}
        .plan-meta-info {font-size: 0.95em; color: #85929E; margin-bottom: 1em; text-align: center; font-style: italic; line-height: 1.4;}
        .plan-meta-info b {color: #AAB7B8; font-weight: 500;}
        .plan-section-title {font-size: 1.25em; font-weight: 600; color: #76D7C4; margin-top: 1.2em; margin-bottom: 0.5em; border-bottom: 1px solid #333A44; padding-bottom: 0.2em;}
        .plan-step-title {color: #A9D5FF; font-weight: 600;}
        .plan-description {font-size: 1em; color: #CACFD2; margin-bottom: 0.5em; padding-left: 10px;}
        .plan-list-item {font-size: 1em; color: #CACFD2; margin-left: 1.5em; margin-bottom: 0.4em; list-style-type: "✨ ";}
        .plan-error-message {color: #FF6B6B; font-weight: 500; background-color: rgba(255, 107, 107, 0.1); padding: 10px; border-radius: 6px; border-left: 4px solid #FF6B6B;}
        .plan-initial-message {color: #A9D5FF; font-style: italic; text-align: center; padding-top: 1rem; padding-bottom: 1rem; font-size: 0.95em;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>💖 Date Night Planner AI 🥂</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("🔑 API & Model Config")
    default_api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key_input = st.text_input("Google AI Key", type="password", value=default_api_key, help="Get your key from Google AI Studio.")
    if not api_key_input and default_api_key: api_key_input = default_api_key
    available_models = ["gemini-2.5-flash-preview-04-17", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-1.0-pro"]
    default_model_index = available_models.index("gemini-1.5-flash-latest") if "gemini-1.5-flash-latest" in available_models else 0
    selected_model = st.selectbox("Choose Gemini Model", available_models, index=default_model_index, help="Select model. Flash is faster, Pro is more capable.")
    st.markdown("---")
    st.info("Adjust API key & model. Ensure selected model follows JSON instructions well.")

left_column, right_column = st.columns([0.42, 0.58])

with left_column:
    st.markdown("<p class='left-column-section-title'>Your Preferences</p>", unsafe_allow_html=True)
    themes = ["Romantic ❤️", "Fun 🎉", "Chill 🧘", "Adventure 🚀", "Artsy 🎨", "Homebody 🏡", "Intellectual 🧠", "Foodie 🍲", "Mysterious 🕵️", "Nostalgic 🕰️"]
    selected_theme = st.selectbox("Theme", themes, help="Overall mood or vibe for the date?")
    activity_types = ["At Home 🏠", "Out (Casual)🚶", "Out (Fancy)👗", "Outdoor Adventure 🌳", "Creative/DIY 🎨", "Learning Together 📚", "Volunteer/Give Back 🤝", "Relax & Unwind 🛀"]
    selected_activity_type = st.selectbox("Activity Type", activity_types, help="General kind of activity?")

    st.markdown("<p class='left-column-section-title'>Practical Considerations</p>", unsafe_allow_html=True)
    raw_budget_val = st.slider("Budget Level", min_value=50, max_value=250, value=100, step=1, help="1 (very tight) to 5 (splurge), precision 0.02")
    current_budget_level_scaled = raw_budget_val / 50.0
    st.caption(f"Selected: {current_budget_level_scaled:.2f}/5")

    raw_prep_time_val = st.slider("Preparation Time", min_value=50, max_value=250, value=100, step=1, help="1 (spontaneous) to 5 (elaborate), precision 0.02")
    current_prep_time_level_scaled = raw_prep_time_val / 50.0
    st.caption(f"Selected: {current_prep_time_level_scaled:.2f}/5")

    raw_time_budget_val = st.slider("Max Activity Duration (Hours)", min_value=25, max_value=400, value=150, step=1, help="Set the maximum duration, precision 0.02 hours.")
    time_budget_hours_val = raw_time_budget_val / 50.0
    st.caption(f"Selected: {time_budget_hours_val:.2f} hours")

    selected_budget_description = map_budget_value_to_description(current_budget_level_scaled)
    selected_prep_time_description = map_prep_time_value_to_description(current_prep_time_level_scaled)

    st.markdown("<p class='left-column-section-title'>Planning Style & Specifics</p>", unsafe_allow_html=True)
    planning_style_options = ["Planning Together", "Planning For Her"]
    selected_planning_style = st.radio("How are you planning this date?", planning_style_options, index=0, horizontal=True, key="planning_style_toggle")
    
    planning_style_prompt_line = ""
    if selected_planning_style == "Planning Together":
        planning_style_prompt_line = "The user is planning this date collaboratively with their significant other."
    elif selected_planning_style == "Planning For Her":
        planning_style_prompt_line = "The user is planning this date as a surprise or gift for their female significant other."

    user_custom_input = st.text_area(label="Any Suggestions or Restrictions?", height=75, placeholder="e.g., loves Italian food, allergic to cats, must be indoors, surprise me!", help="Must-haves, must-nots, or specific ideas?", key="user_custom_input_area_v2")
    
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
                    selected_budget_description, selected_prep_time_description,
                    user_custom_input,
                    current_budget_level_scaled, 
                    current_prep_time_level_scaled, 
                    time_budget_hours_val,
                    planning_style_prompt_line
                )
            st.session_state.generated_plan_content = plan_output

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
                meta_parts = [
                    f"<b>Theme:</b> {plan_data.get('theme', 'N/A')}",
                    f"<b>Activity:</b> {plan_data.get('activity_type', 'N/A')}",
                    f"<b>Budget:</b> {plan_data.get('budget_level', 'N/A')}/5 ({plan_data.get('budget_description', 'N/A')})",
                    f"<b>Prep Time:</b> {plan_data.get('prep_time_level', 'N/A')}/5 ({plan_data.get('prep_time_description', 'N/A')})",
                ]
                if plan_data.get('time_budget_hours') != "Not specified":
                    meta_parts.append(f"<b>Max Duration:</b> {plan_data.get('time_budget_hours', 'N/A')}")
                if plan_data.get('planning_style') != "Not specified" and plan_data.get('planning_style'): # Ensure it's not empty either
                     meta_parts.append(f"<b>Planning Style:</b> {plan_data.get('planning_style')}") # No 'N/A' needed if it's not "Not specified"
                
                meta_html = "<div class='plan-meta-info'>"
                for i in range(0, len(meta_parts), 2):
                    line_parts = [part for part in meta_parts[i:i+2] if part] # Filter out potential None if a .get() fails without default
                    line = " | ".join(line_parts)
                    if line: # Only add <br> if line is not empty
                        meta_html += line + "<br>"
                # Remove last <br> if it exists
                if meta_html.endswith("<br>"):
                    meta_html = meta_html[:-4]

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
        else:
            st.markdown(f"<p class='plan-description'>{str(plan_data)}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)