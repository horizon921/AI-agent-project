# frontend/app.py - 最终修复版本
from backend.utils.feedback_system import feedback_system
from backend.utils.validation import validator, PAPER_ANALYSIS_SCHEMA, EDUCATION_CONTENT_SCHEMA, CHAT_MESSAGE_SCHEMA
from backend.utils.prompt_templates import prompt_manager
from modules.tool_integration import handle_tool_integration
from modules.education_content import handle_education_content
from modules.paper_analysis import handle_paper_analysis
from modules.chat_assistant import handle_chat_assistant
from modules.sidebar import render_sidebar
import streamlit as st
import os
import sys
from datetime import datetime

# ✅ 添加项目根目录到Python路径 - 必须放在最前面
current_dir = os.path.dirname(os.path.abspath(__file__))  # frontend目录
project_root = os.path.dirname(current_dir)  # AI-LLM-Project目录
sys.path.insert(0, project_root)

# ✅ 导入模块 - 现在可以正确导入了


# 页面配置
st.set_page_config(
    page_title="Chat-AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """主应用函数"""
    # 初始化 session state
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(datetime.now().timestamp())

    feedback_system.init_session_state()

    st.title("📚 Chat-AI")

    # 渲染侧边栏
    model, temperature, max_tokens, app_mode = render_sidebar()

    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 根据选择的功能调用相应的处理函数
    if app_mode == "聊天助手":
        handle_chat_assistant(model, temperature, max_tokens,
                              "sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo", "https://api.siliconflow.cn/v1")
    elif app_mode == "论文分析":
        handle_paper_analysis(
            model, max_tokens, "sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo", "https://api.siliconflow.cn/v1")
    elif app_mode == "教育内容生成":
        handle_education_content(
            model, max_tokens, "sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo", "https://api.siliconflow.cn/v1")
    elif app_mode == "工具集成":
        handle_tool_integration()

    st.markdown("---")
    st.markdown("© 2025 Chat-AI | 基于多种LLM模型构建 | 模块化架构设计")


if __name__ == "__main__":
    main()
