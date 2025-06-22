import streamlit as st
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Settings",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for Settings Page ---
def load_settings_css():
    st.markdown("""
    <style>
        /* Hide default Streamlit elements */
        #MainMenu, footer, .stDeployButton { display: none !important; }
        /* Remove padding from main block */
        .block-container {
            padding: 0 !important;
            margin: 0 !important;
        }
        /* Main settings container */
        .settings-container {
            display: flex;
            height: 100vh;
            width: 100vw;
            background-color: #1E1E1E; /* Dark background */
            color: #E0E0E0;
        }
        /* Column styles */
        .settings-nav {
            width: 200px;
            background-color: #252526;
            padding: 1rem;
            border-right: 1px solid #333;
        }
        .settings-list {
            width: 300px;
            background-color: #1E1E1E;
            padding: 1rem;
            border-right: 1px solid #333;
        }
        .settings-content {
            flex-grow: 1;
            padding: 2rem;
            overflow-y: auto;
        }
        /* Custom button styling */
        .settings-nav .stButton>button {
            width: 100%;
            text-align: left;
            background-color: transparent;
            border: none;
            color: #E0E0E0;
            padding: 0.5rem;
            margin-bottom: 0.5rem;
            border-radius: 5px;
        }
        .settings-nav .stButton>button:hover, .settings-nav .stButton>button:focus {
            background-color: #333;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

load_settings_css()

# --- Mock Data ---
# This would be loaded from the backend in a real application
PROVIDERS = {
    "hardhorse": {"type": "openai_compatible", "api_key": "sk-...", "base_url": "https://hard-horse-61.demo.dev", "models": ["claude-3", "claude-3-7-sonnet-20250219-thinking"]},
    "geminipool": {"type": "gemini", "api_key": "...", "base_url": "...", "models": []},
    "wenwen12345": {"type": "openai_compatible", "api_key": "...", "base_url": "...", "models": []},
}

# --- Main Settings Page Layout ---
st.markdown('<div class="settings-container">', unsafe_allow_html=True)

# --- Column 1: Main Navigation ---
st.markdown('<div class="settings-nav">', unsafe_allow_html=True)
main_categories = {
    "模型服务": "💬",
    "默认模型": "🤖",
    "网络搜索": "🌐",
    "MCP 服务器": "🔌",
    "常规设置": "⚙️",
    "显示设置": "🖥️",
}
selected_main_cat = st.radio("Main Navigation", list(main_categories.keys()), label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)


# --- Column 2: Item List ---
st.markdown('<div class="settings-list">', unsafe_allow_html=True)
if selected_main_cat == "模型服务":
    st.subheader("模型平台")
    st.text_input("搜索模型平台...", key="search_providers")
    
    # This list should be scrollable
    selected_provider_name = st.radio(
        "Providers",
        list(PROVIDERS.keys()),
        label_visibility="collapsed"
    )
else:
    st.write(f"Options for {selected_main_cat}")
st.markdown('</div>', unsafe_allow_html=True)


# --- Column 3: Content Details ---
st.markdown('<div class="settings-content">', unsafe_allow_html=True)
if selected_main_cat == "模型服务" and selected_provider_name:
    provider_details = PROVIDERS[selected_provider_name]
    st.header(selected_provider_name)
    
    st.text_input("API 密钥", value=provider_details["api_key"], type="password")
    st.text_input("API 地址", value=provider_details["base_url"])
    
    st.subheader("模型")
    for model in provider_details["models"]:
        c1, c2 = st.columns([10, 1])
        c1.text(model)
        c2.button("⚙️", key=f"config_{model}")

    c1, c2 = st.columns(2)
    c1.button("🔄 管理")
    c2.button("➕ 添加")

else:
    st.header(f"Settings for {selected_main_cat}")
    st.write("Configuration options will appear here.")

st.markdown('</div>', unsafe_allow_html=True)


st.markdown('</div>', unsafe_allow_html=True)