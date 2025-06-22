import streamlit as st
import os
import sys

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# --- Component Imports ---
from components.chat_history import show_chat_history
from components.chat_interface import show_chat_interface
from components.model_parameters import show_model_parameters

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Agent",
    page_icon="🤖",
    layout="wide"
)

# --- Initialize Session State for Sidebars ---
if "left_sidebar_collapsed" not in st.session_state:
    st.session_state.left_sidebar_collapsed = False
if "right_sidebar_collapsed" not in st.session_state:
    st.session_state.right_sidebar_collapsed = False

# --- Dynamic CSS Generation ---
def apply_dynamic_layout():
    left_width = 0 if st.session_state.left_sidebar_collapsed else 280
    right_width = 0 if st.session_state.right_sidebar_collapsed else 320

    dynamic_style = f"""
    <style>
        /* Hide default Streamlit elements */
        #MainMenu, footer, .stDeployButton {{
            display: none !important;
        }}
        /* Force the main block container to be a flexbox */
        .block-container {{
            padding: 0 !important;
            margin: 0 !important;
            display: flex;
            flex-direction: row;
            height: 100vh;
            width: 100vw;
            overflow: hidden;
        }}
        /* Target the direct children of the block-container, which are our columns */
        div[data-testid="stVerticalBlock"] {{
            height: 100vh;
            overflow: hidden;
        }}
        /* Left Sidebar Column */
        div[data-testid="stVerticalBlock"]:nth-of-type(1) {{
            width: {left_width}px;
            min-width: {left_width}px;
            background-color: #f7f7f7;
            transition: width 0.2s ease-in-out, min-width 0.2s ease-in-out;
            padding: 1rem;
            overflow-y: auto;
        }}
        /* Main Content Column */
        div[data-testid="stVerticalBlock"]:nth-of-type(2) {{
            flex-grow: 1;
            padding: 1rem 2rem;
            overflow-y: auto;
        }}
        /* Right Sidebar Column */
        div[data-testid="stVerticalBlock"]:nth-of-type(3) {{
            width: {right_width}px;
            min-width: {right_width}px;
            background-color: #f7f7f7;
            border-left: 1px solid #e0e0e0;
            transition: width 0.2s ease-in-out, min-width 0.2s ease-in-out;
            padding: 1rem;
            overflow-y: auto;
        }}
    </style>
    """
    st.markdown(dynamic_style, unsafe_allow_html=True)

# --- Render the App ---
apply_dynamic_layout()

# Define the three main columns of the layout using st.container
left_sidebar = st.container()
main_content = st.container()
right_sidebar = st.container()

# --- Populate Left Sidebar ---
with left_sidebar:
    if not st.session_state.left_sidebar_collapsed:
        show_chat_history()

# --- Populate Main Content ---
with main_content:
    # Header with controls
    cols = st.columns([1, 1, 10, 1])
    with cols[0]:
        if st.button("H", help="Toggle History"):
            st.session_state.left_sidebar_collapsed = not st.session_state.left_sidebar_collapsed
            st.rerun()
    with cols[1]:
        if st.button("P", help="Toggle Parameters"):
            st.session_state.right_sidebar_collapsed = not st.session_state.right_sidebar_collapsed
            st.rerun()
    with cols[3]:
        if st.button("⚙️", help="Settings"):
            st.switch_page("pages/⚙️_Settings.py")
    
    st.title("AI Agent")
    show_chat_interface()

# --- Populate Right Sidebar ---
with right_sidebar:
    if not st.session_state.right_sidebar_collapsed:
        show_model_parameters()

# --- Cleanup one-off script ---
# The database initialization script has served its purpose.
if os.path.exists("initialize_database.py"):
    os.remove("initialize_database.py")
