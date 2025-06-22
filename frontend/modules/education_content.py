import streamlit as st
import time
from datetime import datetime
from openai import OpenAI
from backend.utils.prompt_templates import prompt_manager
from backend.utils.validation import validator, EDUCATION_CONTENT_SCHEMA
from backend.utils.feedback_system import feedback_system
import sys
import os
project_root = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def display_education_content(parsed_data, topic, level, use_expanders=True):
    """显示教育内容的辅助函数"""
    st.markdown(f"# {topic} - {level}级别教育内容")

    st.markdown("## 📚 概念解释")
    st.markdown(parsed_data['concept_explanation'])

    st.markdown("## 🎯 关键要点")
    for i, point in enumerate(parsed_data['key_points'], 1):
        st.markdown(f"{i}. {point}")

    st.markdown("## 💡 实际应用示例")
    for i, example in enumerate(parsed_data['examples'], 1):
        st.markdown(f"**示例{i}**: {example}")

    st.markdown("## 📝 练习题")
    for i, exercise in enumerate(parsed_data['exercises'], 1):
        # 🔥 根据参数决定是否使用expander
        if use_expanders:
            with st.expander(f"练习{i} ({exercise['difficulty']})"):
                st.markdown(f"**问题**: {exercise['question']}")
                st.markdown(f"**答案**: {exercise['answer']}")
        else:
            # 🔥 不使用expander，直接显示
            st.markdown(f"### 练习{i} ({exercise['difficulty']})")
            st.markdown(f"**问题**: {exercise['question']}")

            # 使用详情标签来隐藏答案
            with st.container():
                if st.button(f"显示答案 {i}", key=f"show_answer_{i}_{topic}_{level}"):
                    st.markdown(f"**答案**: {exercise['answer']}")

    st.markdown("## 📖 进一步学习建议")
    for i, reading in enumerate(parsed_data['further_reading'], 1):
        st.markdown(f"{i}. {reading}")


def handle_education_content(model, max_tokens, api_key, base_url):
    """处理教育内容生成功能"""
    st.header("🎓 教育内容生成")
    st.session_state.current_app_mode = "教育内容生成"

    # 初始化反馈系统
    feedback_system.init_session_state()

    # 🔥 检查是否有上次生成的内容
    if 'last_generated_content' in st.session_state:
        content_data = st.session_state.last_generated_content

        with st.expander("📚 查看上次生成的内容", expanded=True):
            st.markdown(
                f"**主题**: {content_data['topic']} | **级别**: {content_data['level']}")

            # 🔥 显示内容时不使用expander
            display_education_content(
                content_data['content'],
                content_data['topic'],
                content_data['level'],
                use_expanders=False  # ✅ 关键修改
            )

            # 显示反馈表单
            interaction_id = content_data.get('interaction_id')
            if interaction_id:
                st.markdown("---")
                st.markdown("### 📝 内容评价")
                st.info(
                    f"📚 主题: {content_data['topic']} | 级别: {content_data['level']}")
                feedback_system.show_feedback_form(interaction_id)

        # 清除按钮
        if st.button("🗑️ 清除上次内容", key="clear_last_content"):
            del st.session_state.last_generated_content
            st.rerun()

        st.markdown("---")
        st.markdown("### 🆕 生成新内容")

    # 输入界面
    col1, col2 = st.columns(2)

    with col1:
        topic = st.text_input("请输入主题", placeholder="例如：光合作用、微积分、人工智能...")

    with col2:
        level = st.selectbox("选择教育级别", ["小学", "初中", "高中", "大学", "研究生"])

    generate_button = st.button("生成教育内容", type="primary")

    if generate_button and topic:
        # 输入验证
        input_data = {"topic": topic, "level": level}
        is_valid_input, input_error = validator.validate_input_data(
            input_data, "education_request")

        if not is_valid_input:
            st.error(f"❌ 输入验证失败: {input_error}")
            st.stop()

        with st.spinner(f"正在生成关于「{topic}」的{level}级别教育内容..."):
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)

                content_request = f"主题：{topic}，级别：{level}"
                structured_prompt = prompt_manager.create_structured_prompt(
                    content_request, "education_content")

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system",
                            "content": "你是一个专业的教育内容生成助手。请严格按照用户要求的JSON格式输出教育内容。"},
                        {"role": "user", "content": structured_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=max_tokens
                )

                content_result = response.choices[0].message.content

                # 验证结果
                parsed_data, is_valid, error_msg = validator.safe_parse_json_response(
                    content_result, EDUCATION_CONTENT_SCHEMA, "教育内容"
                )

                if is_valid and parsed_data:
                    st.success("✅ 教育内容生成完成，格式验证通过")

                    # 🔥 生成唯一ID并保存内容
                    interaction_id = f"education_{topic}_{level}_{int(time.time() * 1000)}"

                    # 保存到session_state
                    st.session_state.last_generated_content = {
                        'topic': topic,
                        'level': level,
                        'content': parsed_data,
                        'interaction_id': interaction_id,
                        'generated_at': datetime.now().isoformat()
                    }

                    # 🔥 显示内容时使用expander（新生成的内容可以使用）
                    display_education_content(
                        parsed_data, topic, level, use_expanders=True)

                    # 显示反馈表单
                    with st.expander("📝 为这次内容评分", expanded=False):
                        st.info(f"📚 主题: {topic} | 级别: {level}")
                        feedback_system.show_feedback_form(interaction_id)

                else:
                    st.warning(f"⚠️ {error_msg}")
                    st.markdown("### 📄 原始AI回复")
                    st.markdown(content_result)

                    if st.button("🔄 重新生成", key="retry_generation"):
                        st.rerun()

            except Exception as e:
                st.error(f"❌ API调用出错: {str(e)}")
