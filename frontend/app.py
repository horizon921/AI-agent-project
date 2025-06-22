# ==================== 导入模块 ====================
from frontend.modules.sidebar import render_sidebar
from frontend.modules.tool_integration import handle_tool_integration
from frontend.modules.education_content import handle_education_content
from frontend.modules.paper_analysis import handle_paper_analysis
from frontend.modules.chat_assistant import handle_chat_assistant
from backend.utils.prompt_templates import prompt_manager
from backend.utils.validation import validator, PAPER_ANALYSIS_SCHEMA, EDUCATION_CONTENT_SCHEMA, CHAT_MESSAGE_SCHEMA
from backend.utils.feedback_system import feedback_system
import streamlit as st
import os
import sys
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入功能模块

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="Chat-AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 隐藏默认UI元素
hide_default_format = """
<style>
#MainMenu {visibility: hidden; }
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none;}
</style>
"""
st.markdown(hide_default_format, unsafe_allow_html=True)

# ==================== 配置常量 ====================
API_BASE_URL = "http://localhost:8000/api"
API_KEY = "sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo"
BASE_URL = "https://api.siliconflow.cn/v1"

# ==================== 主应用函数 ====================


def main():
    """主应用函数"""
    # 初始化 session state
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(datetime.now().timestamp())

    # 🔥 保持原有的反馈系统初始化
    feedback_system.init_session_state()

    # 设置标题
    st.title("📚 Chat-AI")

    # 🔥 渲染侧边栏 - 保持原有逻辑
    model, temperature, max_tokens, app_mode = render_sidebar()

    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "code_output" not in st.session_state:
        st.session_state.code_output = None

    # 🔥 根据选择的功能调用相应的处理函数 - 传递API配置
    if app_mode == "聊天助手":
        handle_chat_assistant(model, temperature,
                              max_tokens, API_KEY, BASE_URL)
    elif app_mode == "论文分析":
        handle_paper_analysis(model, max_tokens, API_KEY, BASE_URL)
    elif app_mode == "教育内容生成":
        handle_education_content(model, max_tokens, API_KEY, BASE_URL)
    elif app_mode == "工具集成":
        handle_tool_integration()

    # 页脚信息
    st.markdown("---")

    # 🔥 显示反馈分析 - 保持原有逻辑
    if st.session_state.get("feedback_data"):
        analysis = feedback_system.analyze_feedback_trends()
        if analysis and analysis.get("improvement_areas"):
            with st.expander("💡 系统优化建议", expanded=False):
                st.markdown("### 📈 反馈分析")
                st.metric("总反馈数", analysis["total_feedback"])
                st.metric("平均评分", f"{analysis['avg_rating']:.1f}/5.0")
                st.metric("低评分数量", analysis["low_rating_count"])

                if analysis["improvement_areas"]:
                    st.markdown("### 🎯 改进建议")
                    for suggestion in analysis["improvement_areas"]:
                        st.markdown(f"- {suggestion}")

                # 导出反馈数据
                if st.button("📥 导出反馈数据"):
                    csv_data = feedback_system.export_feedback_data()
                    if csv_data:
                        st.download_button(
                            label="下载CSV文件",
                            data=csv_data,
                            file_name=f"feedback_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                        st.success("✅ 反馈数据已准备好下载！")

    st.markdown("© 2025 Chat-AI | 基于多种LLM模型构建 | 模块化架构设计")


if __name__ == "__main__":
    main()
