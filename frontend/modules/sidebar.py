# frontend/sidebar.py - 修复版本
import streamlit as st
import os
import json
import time
from datetime import datetime
from backend.utils.validation import PAPER_ANALYSIS_SCHEMA, EDUCATION_CONTENT_SCHEMA, CHAT_MESSAGE_SCHEMA
from backend.utils.prompt_templates import prompt_manager
from backend.utils.feedback_system import feedback_system


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.header("模型设置")

        model_display = st.selectbox(
            "选择模型",
            ["DeepSeek-V3", "Qwen-72B", "DeepSeek-R1"]
        )

        model_mapping = {
            "DeepSeek-V3": "Pro/deepseek-ai/DeepSeek-V3",
            "Qwen-72B": "Qwen/Qwen2.5-72B-Instruct",
            "DeepSeek-R1": "Pro/deepseek-ai/DeepSeek-R1"
        }

        model = model_mapping.get(model_display, "deepseek-chat")

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="值越高，回答越多样化；值越低，回答越确定性"
        )

        max_tokens = st.slider(
            "最大生成长度",
            min_value=100,
            max_value=4000,
            value=1000,
            step=100,
            help="控制回答的最大长度"
        )

        st.divider()

        st.header("功能选择")
        app_mode = st.radio(
            "选择功能",
            ["聊天助手", "论文分析", "教育内容生成", "工具集成"]
        )

        st.divider()
        st.header("🔍 数据验证")

        if st.checkbox("显示Schema详情", help="显示当前使用的JSON Schema规范"):
            if app_mode == "论文分析":
                st.json(PAPER_ANALYSIS_SCHEMA)
            elif app_mode == "教育内容生成":
                st.json(EDUCATION_CONTENT_SCHEMA)
            elif app_mode == "聊天助手":
                st.json(CHAT_MESSAGE_SCHEMA)

        # 🔥 反馈统计部分
        st.divider()
        st.header("📊 反馈统计")

        # 添加操作按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 刷新", key="refresh_feedback", help="重新加载反馈数据"):
                feedback_system.force_refresh_data()
                st.success("✅ 数据已刷新")
                st.rerun()

        with col2:
            if st.button("📋 详情", key="show_detail", help="显示详细信息"):
                st.session_state.show_feedback_detail = not st.session_state.get(
                    'show_feedback_detail', False)

        # 显示反馈统计
        feedback_system.show_feedback_stats()

        # 详细信息部分
        if st.session_state.get('show_feedback_detail', False):
            render_feedback_details()

        # 测试反馈表单
        render_feedback_test_form()

    return model, temperature, max_tokens, app_mode


def render_feedback_details():
    """渲染反馈详细信息"""
    st.markdown("---")
    st.subheader("🔍 详细信息")

    # 显示调试信息
    feedback_data = st.session_state.get('feedback_data', [])
    interaction_feedback = st.session_state.get('interaction_feedback', {})

    st.write(f"**Session反馈:** {len(feedback_data)} 条")
    st.write(f"**已标记交互:** {len(interaction_feedback)} 个")

    # 检查文件状态
    data_file_path = feedback_system.data_file
    if os.path.exists(data_file_path):
        try:
            with open(data_file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            st.write(f"**文件反馈:** {len(file_data)} 条")
            st.write(f"**文件路径:** {data_file_path}")
        except Exception as e:
            st.error(f"❌ 文件读取失败: {e}")
    else:
        st.write("**文件状态:** 📄 不存在")
        st.write(f"**预期路径:** {data_file_path}")

    # 显示最近的反馈
    if feedback_data:
        st.write("**最近反馈:**")
        for i, feedback in enumerate(feedback_data[-2:]):
            rating = feedback.get('average_rating', feedback.get('rating', 0))
            fb_type = feedback.get('feedback_type', '未知')
            timestamp = feedback.get('timestamp', '')

            if timestamp:
                try:
                    dt = datetime.fromisoformat(
                        timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%m-%d %H:%M')
                except:
                    time_str = timestamp[:16]
            else:
                time_str = '未知时间'

            st.write(f"• ⭐{rating:.1f} - {fb_type} ({time_str})")

    # 管理操作部分
    st.markdown("**管理操作:**")
    col3, col4 = st.columns(2)

    with col3:
        if st.button("📊 导出CSV", key="export_csv", help="导出反馈数据"):
            csv_data = feedback_system.export_feedback_data()
            if csv_data:
                filename = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                st.download_button(
                    label="⬇️ 下载数据",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    key="download_csv"
                )
            else:
                st.warning("⚠️ 暂无数据可导出")

    with col4:
        if st.button("🗑️ 清除", key="clear_data", help="清除所有反馈数据"):
            if st.session_state.get('confirm_clear', False):
                # 执行清除
                st.session_state.feedback_data = []
                st.session_state.interaction_feedback = {}
                if os.path.exists(feedback_system.data_file):
                    os.remove(feedback_system.data_file)
                st.session_state.confirm_clear = False
                st.success("🗑️ 数据已清除")
                st.rerun()
            else:
                # 需要确认
                st.session_state.confirm_clear = True
                st.warning("⚠️ 再次点击确认清除")

    # 显示A/B测试组
    st.divider()
    if st.checkbox("显示A/B测试信息"):
        test_group = prompt_manager.ab_test_prompt_optimization()
        st.info(f"当前使用提示词模板: {test_group}")


def render_feedback_test_form():
    """渲染反馈测试表单"""
    with st.expander("🧪 反馈系统测试", expanded=False):
        st.write("### 📝 测试反馈表单")

        # 评分滑块
        col1, col2 = st.columns(2)
        with col1:
            accuracy = st.slider("准确性", 1, 5, 3, key="test_accuracy_rating")
            clarity = st.slider("清晰度", 1, 5, 3, key="test_clarity_rating")

        with col2:
            helpfulness = st.slider(
                "有用性", 1, 5, 3, key="test_helpfulness_rating")
            relevance = st.slider("相关性", 1, 5, 3, key="test_relevance_rating")

        # 评论框
        test_comment = st.text_area(
            "测试评论", key="test_user_comment", placeholder="输入测试评论...")

        # 提交按钮
        if st.button("提交测试反馈"):
            # 收集数据
            test_feedback_data = {
                'ratings': {
                    'accuracy': accuracy,
                    'helpfulness': helpfulness,
                    'clarity': clarity,
                    'relevance': relevance
                },
                'comment': test_comment.strip() if test_comment else ""
            }

            # 生成唯一ID
            interaction_id = f"test_feedback_{int(time.time() * 1000)}"

            # ✅ 修复：使用正确的方法名
            success = feedback_system.submit_feedback(
                interaction_id, test_feedback_data)

            if success:
                st.success("✅ 测试反馈提交成功！")
            else:
                st.error("❌ 测试反馈提交失败！")

        if st.button("📁 检查数据文件"):
            if os.path.exists(feedback_system.data_file):
                file_size = os.path.getsize(feedback_system.data_file)
                st.success(f"✅ 文件存在，大小: {file_size} bytes")

                with open(feedback_system.data_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        data = json.loads(content)
                        st.info(f"📊 包含 {len(data)} 条记录")
                    else:
                        st.warning("📭 文件为空")
            else:
                st.error(f"❌ 文件不存在: {feedback_system.data_file}")
