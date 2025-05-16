import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

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
        return "Google API Key is missing. Please enter it in the sidebar."
    if not selected_model_name:
        return "Please select a Gemini model in the sidebar."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=selected_model_name)

        # REFINED PROMPT FOR CONCISENESS
        prompt = f"""
        You are a creative and helpful date night planning assistant.
        Your goal is to generate a VERY CONCISE yet complete date night plan based on the user's preferences.
        Aim for a plan that is easy to read quickly and fits in a small space.
        Prioritize brevity while ensuring all essential information is present.
        Use bullet points or short numbered lists where appropriate.
        The user is utilizing the '{selected_model_name}' model.

        User Preferences:
        - Theme: {theme}
        - Activity Type: {activity_type}
        - Budget Consideration: "{budget_desc}" (Approx. level: {current_budget_value}/5)
        - Time to Prepare Consideration: "{prep_time_desc}" (Approx. level: {current_prep_time_value}/5)
        - User's specific suggestions or restrictions: "{user_input if user_input else 'None'}"

        Please generate the date night plan. Output in the following Markdown format.
        BE AS CONCISE AS POSSIBLE.

        ## [Catchy & Short Date Title]

        **Theme:** {theme}
        **Activity Type:** {activity_type}
        **Budget:** ~{current_budget_value}/5 | **Prep:** ~{current_prep_time_value}/5
        *(Using {selected_model_name})*

        ### 🎉 The Plan:
        1.  **Main Activity:** [Brief description, 1-2 short sentences]
        2.  **(Optional) Next Step/Food:** [Brief suggestion, 1 short sentence]

        ### 💡 Quick Tips:
        *   [One very brief tip or consideration]

        Keep all descriptions extremely brief. If an optional section isn't highly relevant, omit it.
        Focus on the core idea.
        """
        response = model.generate_content(prompt)
        if hasattr(response, 'text'):
            return response.text
        elif isinstance(response, str):
            return response
        else:
            return str(response)

    except Exception as e:
        # If the error is about quota, provide a more specific message
        if "quota" in str(e).lower():
            return (f"Rate limit or quota exceeded for {selected_model_name}. "
                    "Please wait a bit, try a different model, or check your Google AI/Cloud billing. "
                    f"Details: {str(e)[:200]}...") # Show only part of a long error
        return f"An error occurred with {selected_model_name}: {str(e)[:300]}..."


# --- Streamlit App UI ---
st.set_page_config(page_title="Date Night Planner", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        .main .block-container {
            padding-top: 1rem; padding-bottom: 1rem;
        }
        [data-testid="stVerticalBlock"] {
            gap: 0.25rem !important;
        }
        div[data-testid="stSelectbox"] > label,
        div[data-testid="stSlider"] > label,
        div[data-testid="stTextArea"] > label {
            margin-bottom: 0.1rem !important; font-size: 0.875rem;
        }
        h1 { /* Main Title */
            font-size: 1.6rem !important; margin-bottom: 0.5rem !important;
        }
        h3 { /* st.subheader for right column title */
            font-size: 1.1rem !important; margin-top: 0rem !important; margin-bottom: 0.25rem !important;
        }
        html, body, #root, .stApp {
            height: 100%; overflow: hidden; /* Critical for no page scroll */
        }

        /* Style for the output plan box */
        .plan-output-box {
            height: calc(100vh - 110px); /* Adjust 110px as needed */
            overflow-y: auto; /* Scroll INSIDE the box if content overflows */
            padding: 10px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            background-color: #f9f9f9;
            font-size: 0.8rem; /* Smaller font size for the plan text (approx 20% smaller than 1rem default) */
                               /* You can try 0.7rem for ~30% smaller, but it might be hard to read */
        }
        .plan-output-box p, .plan-output-box li, .plan-output-box h2, .plan-output-box h3 {
            font-size: inherit !important; /* Ensure child elements inherit this smaller font */
            line-height: 1.3; /* Adjust line height for smaller font */
            margin-bottom: 0.3rem; /* Reduce space between paragraphs/list items */
        }
        .plan-output-box h2 { /* Markdown ## */
            font-size: 1.1em !important; /* Relative to parent's 0.8rem */
            margin-top: 0.5rem; margin-bottom: 0.25rem;
        }
        .plan-output-box h3 { /* Markdown ### */
            font-size: 1.0em !important;  /* Relative to parent's 0.8rem */
            margin-top: 0.4rem; margin-bottom: 0.2rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("💖 Date Night Planner AI 🥂")

st.sidebar.header("🔑 API & Model Config")
default_api_key = os.getenv("GOOGLE_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "Google AI Key", type="password", value=default_api_key, help="Get your key from Google AI Studio."
)
if not api_key_input and default_api_key: api_key_input = default_api_key

available_models = [
    "gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-1.0-pro",
]
selected_model = st.sidebar.selectbox(
    "Choose Gemini Model", available_models, index=0,
    help="Select AI model. Newer models may be more creative but have different free tier limits."
)
st.sidebar.markdown("---")

left_column, right_column = st.columns([0.4, 0.6])

with left_column:
    st.markdown("**Preferences**")
    themes = ["Romantic ❤️", "Fun 🎉", "Chill 🧘", "Adventure 🚀", "Artsy 🎨", "Homebody 🏡"]
    selected_theme = st.selectbox("Theme", themes, help="Mood of the date.")

    activity_types = ["At Home 🏠", "Out (Casual)🚶", "Out (Fancy)👗", "Outdoor 🌳", "Create 🖌️"]
    selected_activity_type = st.selectbox("Activity Type", activity_types, help="General type of activity.")

    st.markdown("**Practicalities**")
    col_budget, col_prep = st.columns(2)
    with col_budget:
        current_budget_val = st.slider("Budget", 1, 5, 2, format="%d/5", help="1 (tight) - 5 (splurge)")
    with col_prep:
        current_prep_time_val = st.slider("Prep Time", 1, 5, 2, format="%d/5", help="1 (quick) - 5 (elaborate)")

    selected_budget_description = map_budget_value_to_description(current_budget_val)
    selected_prep_time_description = map_prep_time_value_to_description(current_prep_time_val)

    st.markdown("**Your Specifics**")
    user_custom_input = st.text_area(
        "Restrictions/Ideas?", height=70, placeholder="e.g., Italian food, no cats.", help="Any must-haves or must-nots."
    )

    if 'generated_plan_content' not in st.session_state:
        st.session_state.generated_plan_content = "Your date idea will appear here! ✨"

    if st.button("✨ Generate Plan ✨", type="primary", use_container_width=True):
        if not api_key_input:
            st.session_state.generated_plan_content = "⚠️ Please enter your Google API Key in the sidebar!"
        elif not selected_model:
            st.session_state.generated_plan_content = "⚠️ Please select a Gemini model in the sidebar!"
        else:
            with right_column:
                 with st.spinner("💖 Planning..."):
                    plan_output = generate_date_plan_with_gemini(
                        api_key_input, selected_model, selected_theme, selected_activity_type,
                        selected_budget_description, selected_prep_time_description, user_custom_input,
                        current_budget_val, current_prep_time_val
                    )
            st.session_state.generated_plan_content = plan_output

with right_column:
    st.subheader("💡 Your Date Night Idea")

    plan_display_content = st.session_state.generated_plan_content
    if not isinstance(plan_display_content, str):
        plan_display_content = str(plan_display_content)

    # Using a div with a class for styling the output box
    st.markdown(f"""<div class="plan-output-box">{plan_display_content}</div>""", unsafe_allow_html=True)

st.sidebar.info("Adjust API key & model if needed.")