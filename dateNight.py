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

# MODIFIED FUNCTION SIGNATURE to include model_name
def generate_date_plan_with_gemini(api_key, selected_model_name, # ADDED selected_model_name
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
        *(Generated using {selected_model_name})*

        ### 🎉 The Plan:
        1.  **Activity/Step 1:** [Detailed description of the first activity or preparation step]
        2.  **Activity/Step 2:** [Detailed description of the second activity or step]
        3.  **(Optional) Food/Drinks:** [Suggestions for food and drinks that match the theme and budget]
        4.  **(Optional) Ambiance/Extras:** [Ideas for music, decorations, or other touches to enhance the experience]

        ### 💡 Tips & Considerations:
        *   [A tip related to the plan, or how to adapt it]
        *   [Another tip or consideration, especially if user restrictions were mentioned]

        Make the plan sound engaging and fun!
        **IMPORTANT: Keep the overall response concise and to the point. Focus on delivering all relevant information clearly within the provided structure. Avoid unnecessary verbosity to ensure the plan is easily readable and ideally fits on a single screen.**
        """
        response = model.generate_content(prompt)
        if hasattr(response, 'text'):
            return response.text
        elif isinstance(response, str):
            return response
        else:
            # Fallback for different response structures, ensure it's a string
            if hasattr(response, 'parts') and response.parts:
                 return "".join(part.text for part in response.parts if hasattr(part, 'text'))
            return str(response) # Last resort

    except Exception as e:
        return f"An error occurred while generating the plan with {selected_model_name}: {e}"

# --- Streamlit App UI ---
st.set_page_config(page_title="Date Night Planner", layout="wide", initial_sidebar_state="expanded")

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
        h3 {
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
        /* Sidebar selectbox label */
        div[data-testid="stSidebar"] div[data-testid="stSelectbox"] > label {
             font-size: 0.875rem !important;
             margin-bottom: 0.1rem !important;
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
    "gemini-1.5-flash-latest", # Good balance of speed and capability
    "gemini-1.5-pro-latest",   # Most capable, potentially slower/more expensive
    "gemini-1.0-pro",          # Older but stable Pro model
         # If you were doing image tasks (not for this app)
]
# Attempt to find a good default, otherwise use the first
default_model_index = 0
if "gemini-1.5-flash-latest" in available_models:
    default_model_index = available_models.index("gemini-1.5-flash-latest")

selected_model = st.sidebar.selectbox(
    "Choose Gemini Model",
    available_models,
    index=default_model_index,
    help="Select the AI model to generate ideas. Newer models might be more creative."
)
st.sidebar.markdown("---")

# --- Main Layout: Two Columns ---
left_column, right_column = st.columns([0.4, 0.6])

with left_column:
    st.markdown("**Preferences**")
    themes = ["Romantic ❤️", "Fun 🎉", "Chill 🧘", "Adventure 🚀", "Artsy 🎨", "Homebody 🏡", "Intellectual 🧠", "Foodie 🍲"]
    selected_theme = st.selectbox("Theme", themes, help="Mood of the date.")

    activity_types = ["At Home 🏠", "Out (Casual)🚶", "Out (Fancy)👗", "Outdoor 🌳", "Create 🖌️", "Learn 📚", "Volunteer 🤝"]
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
        "Restrictions/Ideas?",
        height=70,
        placeholder="e.g., Italian food, no cats, one person is vegan.",
        help="Any must-haves or must-nots."
    )

    if 'generated_plan_content' not in st.session_state:
        st.session_state.generated_plan_content = "Your date idea will appear here! ✨"

    if st.button("✨ Generate Plan ✨", type="primary", use_container_width=True):
        if not api_key_input:
            st.session_state.generated_plan_content = "⚠️ Please enter your Google API Key in the sidebar!"
        elif not selected_model:
            st.session_state.generated_plan_content = "⚠️ Please select a Gemini model in the sidebar!"
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
    st.subheader("💡 Your Date Night Idea")

    plan_display_content = st.session_state.generated_plan_content
    if not isinstance(plan_display_content, str):
        plan_display_content = str(plan_display_content) # Ensure it's a string

    # --- MODIFIED OUTPUT DIV ---
    st.markdown(
        f"""
        <div style="
            height: calc(100vh - 120px); /* Adjust 120px based on title, subheader, and some padding */
            overflow-y: auto; /* Keep auto scrolling in case content is still too long */
            padding: 10px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            background-color: #f9f9f9;
            font-size: 0.75em; /* Reduced font size (e.g., 75% of normal). Adjust as needed. */
            line-height: 1.4;  /* Slightly increased line height for readability with smaller font */
        ">
            {plan_display_content}
        </div>
        """,
        unsafe_allow_html=True
    )

st.sidebar.info("Adjust API key & model if needed. Some models are better at conciseness.")