import streamlit as st
import time
from datetime import datetime
from openai import OpenAI
from backend.utils.prompt_templates import prompt_manager
from backend.utils.validation import validator, PAPER_ANALYSIS_SCHEMA
from backend.utils.feedback_system import feedback_system
import sys
import os
project_root = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def display_paper_analysis_results(parsed_data):
    """显示论文分析结果的辅助函数"""
    st.markdown("### 📊 论文分析结果")

    st.markdown("### 📝 摘要总结")
    st.markdown(parsed_data['summary'])

    st.markdown("### 🎯 主要贡献")
    for i, contrib in enumerate(parsed_data['main_contributions'], 1):
        st.markdown(f"{i}. {contrib}")

    st.markdown("### 🔬 研究方法")
    st.markdown(parsed_data['methodology'])

    st.markdown("### 🔍 关键发现")
    for i, finding in enumerate(parsed_data['key_findings'], 1):
        st.markdown(f"{i}. {finding}")

    st.markdown("### ⚠️ 研究局限")
    for i, limitation in enumerate(parsed_data['limitations'], 1):
        st.markdown(f"{i}. {limitation}")

    st.markdown("### 💡 研究意义")
    st.markdown(parsed_data['significance'])


def handle_paper_analysis(model, max_tokens, api_key, base_url):
    """处理论文分析功能"""
    st.header("📝 论文分析")
    st.session_state.current_app_mode = "论文分析"

    # 初始化反馈系统
    feedback_system.init_session_state()

    # 🔥 检查是否有上次分析的结果
    if 'last_paper_analysis' in st.session_state:
        analysis_data = st.session_state.last_paper_analysis

        with st.expander("📊 查看上次分析结果", expanded=True):
            st.markdown(f"**分析时间**: {analysis_data.get('analyzed_at', '未知')}")
            st.markdown(
                f"**论文字数**: {len(analysis_data.get('original_text', ''))} 字符")

            # 显示分析结果
            display_paper_analysis_results(analysis_data['analysis_result'])

            # 显示反馈表单
            interaction_id = analysis_data.get('interaction_id')
            if interaction_id:
                st.markdown("---")
                st.markdown("### 📝 分析评价")
                st.info("📊 为这次论文分析的质量评分")
                feedback_system.show_feedback_form(interaction_id)

        # 清除按钮
        if st.button("🗑️ 清除上次分析", key="clear_last_analysis"):
            del st.session_state.last_paper_analysis
            st.rerun()

        st.markdown("---")
        st.markdown("### 🆕 分析新论文")

    # 输入界面
    paper_text = st.text_area(
        "请输入论文文本或摘要",
        height=300,
        help="粘贴论文文本、摘要或PDF提取的内容"
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        analyze_button = st.button("分析论文", type="primary")

    if analyze_button and paper_text:
        # 输入验证
        input_data = {"text": paper_text}
        is_valid_input, input_error = validator.validate_input_data(
            input_data, "paper_text")

        if not is_valid_input:
            st.error(f"❌ 输入验证失败: {input_error}")
            st.stop()

        with st.spinner("正在分析论文..."):
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)

                # 使用模板管理器生成提示词
                structured_prompt = prompt_manager.create_structured_prompt(
                    paper_text, "paper_analysis")

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system",
                            "content": "你是一个专业的学术论文分析助手。请严格按照用户要求的JSON格式输出分析结果。"},
                        {"role": "user", "content": structured_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=max_tokens
                )

                analysis_result = response.choices[0].message.content

                # 验证结果
                parsed_data, is_valid, error_msg = validator.safe_parse_json_response(
                    analysis_result, PAPER_ANALYSIS_SCHEMA, "论文分析"
                )

                if is_valid and parsed_data:
                    st.success("✅ 论文分析完成，格式验证通过")

                    # 🔥 生成唯一ID并保存分析结果
                    interaction_id = f"paper_analysis_{int(time.time() * 1000)}"

                    # 保存到session_state
                    st.session_state.last_paper_analysis = {
                        'original_text': paper_text,
                        'analysis_result': parsed_data,
                        'interaction_id': interaction_id,
                        'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    # 显示分析结果
                    display_paper_analysis_results(parsed_data)

                    # 显示反馈表单
                    with st.expander("📝 为这次分析评分", expanded=False):
                        st.info("📊 为这次论文分析的质量评分")
                        feedback_system.show_feedback_form(interaction_id)

                else:
                    st.warning(f"⚠️ {error_msg}")
                    st.markdown("### 📄 原始AI回复")
                    st.markdown(analysis_result)

                    if st.button("🔄 重新分析", key="retry_analysis"):
                        st.rerun()

            except Exception as e:
                st.error(f"❌ API调用出错: {str(e)}")
