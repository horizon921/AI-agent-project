"""
应用配置管理模块
"""
import streamlit as st

# API配置
API_BASE_URL = "http://localhost:8000/api"
API_KEY = "sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo"
BASE_URL = "https://api.siliconflow.cn/v1"

# 模型映射
MODEL_MAPPING = {
    "DeepSeek-V3": "Pro/deepseek-ai/DeepSeek-V3",
    "Qwen-72B": "Qwen/Qwen2.5-72B-Instruct",
    "DeepSeek-R1": "Pro/deepseek-ai/DeepSeek-R1"
}


def setup_page_config():
    """设置页面配置"""
    st.set_page_config(
        page_title="Chat-AI",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def hide_default_ui():
    """隐藏默认UI元素"""
    hide_default_format = """
    <style>
    #MainMenu {visibility: hidden; }
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* 🔥 修复深色模式下侧边栏折叠按钮问题 */
    button[data-testid="collapsedControl"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    button[data-testid="collapsedControl"]:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }
    
    .css-1lcbmhc .css-1d391kg {
        visibility: visible !important;
        opacity: 1 !important;
    }
    </style>
    """
    st.markdown(hide_default_format, unsafe_allow_html=True)
