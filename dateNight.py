import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# --- Configuration & Setup ---
load_dotenv()

# --- Helper Functions (keep these as they are) ---
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

# MODIFIED FUNCTION SIGNATURE
def generate_date_plan_with_gemini(api_key, theme, activity_type,
                                   budget_desc, prep_time_desc, user_input,
                                   current_budget_value, current_prep_time_value): # ADDED PARAMS
    if not api_key:
        return "Google API Key is missing. Please enter it in the sidebar."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

        # REMOVED global statement
        # The prompt now uses the passed-in current_budget_value and current_prep_time_value
        prompt = f"""
        You are a creative and helpful date night planning assistant.
        Your goal is to generate a fun and suitable date night plan based on the user's preferences.

        User Preferences:
        - Theme: {theme}
        - Activity Type: {activity_type}
        - Budget Consideration: "{budget_desc}" (Approx. level: {current_budget_value}/5)
        - Time to Prepare Consideration: "{prep_time_desc}" (Approx. level: {current_prep_time_value}/5)
        - User's specific suggestions or restrictions: "{user_input if user_input else 'None'}"

        Please generate a date night plan.
        The plan should be creative, fitting the theme and activity type.
        Consider the budget and preparation time descriptions provided.
        If the user provided specific suggestions or restrictions, make sure to incorporate or respect them.

        Output the plan in the following Markdown format:

        ## [Catchy Date Night Title]
        **Theme:** {theme}
        **Activity Type:** {activity_type}
        **Budget Guide:** Approx. {current_budget_value}/5 ({budget_desc})
        **Prep Time Guide:** Approx. {current_prep_time_value}/5 ({prep_time_desc})

        ### 🎉 The Plan:
        1.  **Activity/Step 1:** [Detailed description of the first activity or preparation step]
        2.  **Activity/Step 2:** [Detailed description of the second activity or step]
        3.  **(Optional) Food/Drinks:** [Suggestions for food and drinks that match the theme and budget]
        4.  **(Optional) Ambiance/Extras:** [Ideas for music, decorations, or other touches to enhance the experience]

        ### 💡 Tips & Considerations:
        *   [A tip related to the plan, or how to adapt it]
        *   [Another tip or consideration, especially if user restrictions were mentioned]

        Make the plan sound engaging and fun!
        Keep the overall response concise enough to be easily readable.
        """
        response = model.generate_content(prompt)
        if hasattr(response, 'text'):
            return response.text
        elif isinstance(response, str):
            return response
        else:
            return str(response)

    except Exception as e:
        return f"An error occurred while generating the plan: {e}"

# --- Streamlit App UI ---
st.set_page_config(page_title="Date Night Planner", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        [data-testid="stVerticalBlock"] {
            gap: 0.25rem !important;
        }
        div[data-testid="stSelectbox"] > label,
        div[data-testid="stSlider"] > label,
        div[data-testid="stTextArea"] > label {
            margin-bottom: 0.1rem !important;
            font-size: 0.875rem;
        }
        h1 {
            font-size: 1.6rem !important;
            margin-bottom: 0.5rem !important;
        }
        h3 { /* st.subheader in right column */
            font-size: 1.1rem !important;
            margin-top: 0rem !important;
            margin-bottom: 0.25rem !important;
        }
        html, body, #root {
            height: 100%;
            overflow: hidden;
        }
        .stApp {
             height: 100vh;
             overflow: hidden;
        }
    </style>
""", unsafe_allow_html=True)

st.title("💖 Date Night Planner AI 🥂")

st.sidebar.header("🔑 API Config")
default_api_key = os.getenv("GOOGLE_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "Google AI Key",
    type="password",
    value=default_api_key,
    help="Get your key from Google AI Studio."
)
if not api_key_input and default_api_key: api_key_input = default_api_key

left_column, right_column = st.columns([0.4, 0.6])

with left_column:
    # REMOVED global budget_value, prep_time_value

    st.markdown("**Preferences**")
    themes = ["Romantic ❤️", "Fun 🎉", "Chill 🧘", "Adventure 🚀", "Artsy 🎨", "Homebody 🏡"]
    selected_theme = st.selectbox("Theme", themes, help="Mood of the date.")

    activity_types = ["At Home 🏠", "Out (Casual)🚶", "Out (Fancy)👗", "Outdoor 🌳", "Create 🖌️"]
    selected_activity_type = st.selectbox("Activity Type", activity_types, help="General type of activity.")

    st.markdown("**Practicalities**")
    col_budget, col_prep = st.columns(2)
    with col_budget:
        budget_value_slider = st.slider("Budget", 1, 5, 2, format="%d/5", help="1 (tight) - 5 (splurge)", key="budget_slider_key") # Renamed to avoid conflict
    with col_prep:
        prep_time_value_slider = st.slider("Prep Time", 1, 5, 2, format="%d/5", help="1 (quick) - 5 (elaborate)", key="prep_time_slider_key") # Renamed

    # These are the values we'll pass to the function and use for descriptions
    current_budget_val = budget_value_slider
    current_prep_time_val = prep_time_value_slider

    selected_budget_description = map_budget_value_to_description(current_budget_val)
    selected_prep_time_description = map_prep_time_value_to_description(current_prep_time_val)

    st.markdown("**Your Specifics**")
    user_custom_input = st.text_area(
        "Restrictions/Ideas?",
        height=70,
        placeholder="e.g., Italian food, no cats.",
        help="Any must-haves or must-nots."
    )

    if 'generated_plan_content' not in st.session_state:
        st.session_state.generated_plan_content = "Your date idea will appear here! ✨"

    if st.button("✨ Generate Plan ✨", type="primary", use_container_width=True):
        if not api_key_input:
            st.session_state.generated_plan_content = "⚠️ Please enter your Google API Key in the sidebar!"
        else:
            with right_column:
                 with st.spinner("💖 Planning..."):
                    plan_output = generate_date_plan_with_gemini( # MODIFIED FUNCTION CALL
                        api_key_input,
                        selected_theme,
                        selected_activity_type,
                        selected_budget_description,
                        selected_prep_time_description,
                        user_custom_input,
                        current_budget_val,      # PASSING THE VALUE
                        current_prep_time_val    # PASSING THE VALUE
                    )
            st.session_state.generated_plan_content = plan_output

with right_column:
    st.subheader("💡 Your Date Night Idea")

    plan_display_content = st.session_state.generated_plan_content
    if not isinstance(plan_display_content, str):
        plan_display_content = str(plan_display_content)

    st.markdown(
        f"""
        <div style="
            height: calc(100vh - 110px); /* Adjust 110px based on title, subheader height */
            overflow-y: auto;
            padding: 10px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            background-color: #f9f9f9;
        ">
            {plan_display_content}
        </div>
        """,
        unsafe_allow_html=True
    )