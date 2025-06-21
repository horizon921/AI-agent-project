from backend.utils.prompt_templates import prompt_manager
from backend.utils.validation import validator, PAPER_ANALYSIS_SCHEMA, EDUCATION_CONTENT_SCHEMA, CHAT_MESSAGE_SCHEMA
from backend.utils.feedback_system import *
from duckduckgo_search import DDGS
import streamlit as st
import requests
import json
import time
import base64
from PIL import Image
import io
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from openai import OpenAI
import math
from scipy import stats, optimize, integrate
import speech_recognition as sr
import tempfile
import os
import re
from typing import Dict, Any, Optional
from datetime import datetime
import contextlib
from io import StringIO
import sys
import traceback
from backend.utils.feedback_system import feedback_system

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


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

API_BASE_URL = "http://localhost:8000/api"
API_KEY = "sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo"
BASE_URL = "https://api.siliconflow.cn/v1"

# 多模态处理函数


def encode_image_to_base64(image):
    """将图片编码为base64"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def process_audio_to_text(audio_bytes):
    """处理音频转文本"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name

        recognizer = sr.Recognizer()

        try:
            with sr.AudioFile(tmp_file_path) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio, language='zh-CN')
        except:
            try:
                with sr.AudioFile(tmp_file_path) as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio, language='zh-CN')
            except Exception as e:
                raise e

        os.unlink(tmp_file_path)
        return text
    except Exception as e:
        return f"语音识别失败: {str(e)}"


def create_multimodal_message(text, image=None, audio_text=None):
    """创建多模态消息"""
    content = []

    if text:
        content.append({"type": "text", "text": text})

    if audio_text and not audio_text.startswith("语音识别失败"):
        content.append({"type": "text", "text": f"[语音输入]: {audio_text}"})

    if image:
        image_base64 = encode_image_to_base64(image)
        content.append({
            "type": "image_url",
            "image_url": {"url": image_base64}
        })

    return content if len(content) > 0 else [{"type": "text", "text": ""}]

# ==================== 功能模块 ====================


def handle_chat_assistant(model, temperature, max_tokens):
    """处理聊天助手功能"""
    st.header("💬 聊天助手")
    st.session_state.current_app_mode = "聊天助手"

    # 初始化反馈系统
    feedback_system.init_session_state()

    # 添加自定义CSS
    st.markdown("""
    <style>
      div[data-testid="stFileUploader"] > label { display: none !important; }
      #file-input, #audio-input { display: none; }

      div[data-testid="stFileUploader"] > div:first-child > div:first-child > div:first-child {
            display: none !important;
        }

        div[data-testid="stFileUploader"]:before {
            content: "拖拽文件到这里或点击浏览";
            display: block;
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }

      .upload-btn {
        flex: none; width: 32px; height: 32px;
        margin-left: 8px; margin-right: 8px;
        border-radius: 50%; background: #fff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        cursor: pointer; display: flex;
        align-items: center; justify-content: center;
        font-size: 18px; transition: transform .2s, box-shadow .2s;
      }
      .upload-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
      }
    </style>
    """, unsafe_allow_html=True)

    # 初始化会话状态
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'pending_files' not in st.session_state:
        st.session_state.pending_files = {'image': None, 'audio': None}

    # 🔥 修改这整个部分：显示聊天历史并为每个助手回复添加反馈表单
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if isinstance(message["content"], str):
                st.markdown(message["content"])
            else:
                for content_item in message["content"]:
                    if content_item["type"] == "text":
                        st.markdown(content_item["text"])
                    elif content_item["type"] == "image_url":
                        st.image(content_item["image_url"]["url"], width=300)

            # 🔥 为每个助手回复添加反馈表单
            if message["role"] == "assistant":
                # 使用消息索引和内容哈希创建唯一ID
                message_content = message["content"] if isinstance(
                    message["content"], str) else str(message["content"])
                message_hash = str(hash(message_content[:100]))
                interaction_id = f"chat_msg_{i}_{message_hash}"

                # 检查是否已经提交过反馈
                feedback_key = f"feedback_{interaction_id}"
                is_submitted = st.session_state.get(
                    feedback_key, {}).get('submitted', False)

                if not is_submitted:
                    with st.expander("📝 为这次回答评分", expanded=False):
                        feedback_system.show_feedback_form(interaction_id)
                else:
                    st.success("✅ 已提交反馈")

    # 文件上传器
    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            uploaded_image = st.file_uploader(
                "选择图片文件",
                type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
                key=f"img_uploader_{st.session_state.get('upload_counter', 0)}",
                label_visibility="collapsed"
            )

        with col2:
            uploaded_audio = st.file_uploader(
                "选择音频文件",
                type=['wav', 'mp3', 'm4a', 'ogg'],
                key=f"audio_uploader_{st.session_state.get('upload_counter', 0)}",
                label_visibility="collapsed"
            )

    # 处理文件上传
    if uploaded_image:
        st.session_state.pending_files['image'] = uploaded_image
        st.success("✅ 图片已选择！请输入消息后发送")

    if uploaded_audio:
        st.session_state.pending_files['audio'] = uploaded_audio
        st.success("✅ 音频已选择！请输入消息后发送")

    # 显示文件预览
    if st.session_state.pending_files['image']:
        st.markdown("📷 **待发送图片:**")
        try:
            image = Image.open(st.session_state.pending_files['image'])
            st.image(image, width=200)
        except Exception as e:
            st.error(f"图片预览失败: {str(e)}")

    if st.session_state.pending_files['audio']:
        st.markdown("🎤 **待发送音频:**")
        try:
            st.audio(st.session_state.pending_files['audio'])
        except Exception as e:
            st.error(f"音频预览失败: {str(e)}")

    # 聊天输入框
    prompt = st.chat_input("请输入您的问题...")

    # JavaScript按钮（保持原有功能）
    st.markdown("""
    <script>
    (function() {
      function insertButtons() {
        const container = document.querySelector('div[data-testid="stChatInput"]');
        if (!container || container.querySelector('.upload-btn')) return;

        container.insertAdjacentHTML('afterbegin', `
          <label for="file-input"  class="upload-btn" title="上传图片">📷</label>
          <label for="audio-input" class="upload-btn" title="上传音频">🎤</label>
          <input type="file" id="file-input"  accept="image/*">
          <input type="file" id="audio-input" accept="audio/*">
        `);
      }

      window.addEventListener('click', e => {
        if (e.target.matches('.upload-btn[title="上传图片"]'))
          document.getElementById('file-input').click();
        if (e.target.matches('.upload-btn[title="上传音频"]'))
          document.getElementById('audio-input').click();
      });

      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', insertButtons);
      } else {
        insertButtons();
      }
      new MutationObserver(insertButtons).observe(document.body, {
        childList: true, subtree: true
      });
    })();
    </script>
    """, unsafe_allow_html=True)

    # 处理用户输入
    if prompt:
        audio_text = None
        image = None

        # 处理语音
        if st.session_state.pending_files['audio']:
            with st.spinner("🎤 正在识别语音..."):
                try:
                    audio_bytes = st.session_state.pending_files['audio'].read(
                    )
                    audio_text = process_audio_to_text(audio_bytes)
                    st.session_state.pending_files['audio'].seek(0)
                except Exception as e:
                    audio_text = f"语音识别失败: {str(e)}"

        # 处理图片
        if st.session_state.pending_files['image']:
            try:
                image = Image.open(st.session_state.pending_files['image'])
                st.session_state.pending_files['image'].seek(0)
            except Exception as e:
                st.error(f"图片处理失败: {str(e)}")
                image = None

        # 创建消息
        user_content = create_multimodal_message(prompt, image, audio_text)
        current_model = "Qwen/Qwen2.5-VL-72B-Instruct" if image else model

        # 添加用户消息
        st.session_state.messages.append(
            {"role": "user", "content": user_content})

        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)
            if audio_text and not audio_text.startswith("语音识别失败"):
                st.markdown(f"🎤 **语音输入**: {audio_text}")
            if image:
                st.image(image, width=300)

        # 清除文件
        st.session_state.pending_files = {'image': None, 'audio': None}
        st.session_state.upload_counter = st.session_state.get(
            'upload_counter', 0) + 1

        # 生成AI回复
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            try:
                client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

                messages = [
                    {"role": "system", "content": "你是一个专业的学术论文分析与教育辅导助手，擅长帮助用户解答学术问题、分析论文和提供教育指导。当用户提供图片时，请详细描述图片内容并回答相关问题。"}
                ]

                recent_messages = st.session_state.messages[-10:] if len(
                    st.session_state.messages) > 10 else st.session_state.messages

                for msg in recent_messages:
                    messages.append(
                        {"role": msg["role"], "content": msg["content"]})

                response = client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )

                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        message_placeholder.markdown(full_response + "▌")
                        time.sleep(0.01)

                message_placeholder.markdown(full_response)

            except Exception as e:
                error_message = f"API调用出错: {str(e)}"
                message_placeholder.error(error_message)
                full_response = error_message

            # 添加助手消息到历史
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response})

        # 🔥 修改新回复后的反馈表单（约第230-250行）
        if full_response and not full_response.startswith("API调用出错"):
            # 为最新的回复创建反馈表单
            latest_msg_index = len(st.session_state.messages) - 1
            message_hash = str(hash(full_response[:100]))
            new_interaction_id = f"chat_msg_{latest_msg_index}_{message_hash}"

            st.markdown("---")

            # 🔥 使用容器来确保稳定显示
            with st.container():
                feedback_system.show_feedback_form(new_interaction_id)


def handle_paper_analysis(model, max_tokens):
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
                client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

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


def handle_education_content(model, max_tokens):
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
                client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

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


def handle_tool_integration():
    """处理工具集成功能"""
    st.header("🛠️ 工具集成")
    st.session_state.current_app_mode = "工具集成"

    tool_tabs = st.tabs(["代码执行", "网络搜索", "数学计算"])

    with tool_tabs[0]:
        st.subheader("Python代码执行")

        code = st.text_area(
            "输入Python代码",
            height=200,
            placeholder="# 示例：绘制简单图表\nimport matplotlib.pyplot as plt\nimport numpy as np\n\nx = np.linspace(0, 10, 100)\ny = np.sin(x)\nplt.plot(x, y)\nplt.title('正弦函数')"
        )

        execute_button = st.button("执行代码", key="execute_code")

        if execute_button and code:
            with st.spinner("正在执行代码..."):
                try:
                    stdout_capture = StringIO()
                    fig_container = st.empty()

                    with contextlib.redirect_stdout(stdout_capture):
                        local_vars = {}

                        if "plt" in code:
                            exec_code = code + "\n\n# 捕获图表\nif 'plt' in locals() or 'plt' in globals():\n    fig = plt.gcf()\n    plt.close()"
                        else:
                            exec_code = code

                        exec(exec_code, globals(), local_vars)

                        if "plt" in code and "fig" in local_vars:
                            fig_container.pyplot(local_vars["fig"])

                    output = stdout_capture.getvalue()

                    st.success("代码执行成功！")
                    if output:
                        st.code(f"输出：\n{output}", language="text")
                    else:
                        st.code("输出：\n(无标准输出)", language="text")

                except Exception as e:
                    st.error(f"代码执行失败：{str(e)}")
                    st.code(f"错误详情：\n{traceback.format_exc()}",
                            language="python")

    with tool_tabs[1]:
        st.subheader("DuckDuckGo网络搜索")

        search_query = st.text_input("输入搜索关键词")
        search_button = st.button("搜索", key="search")

        if search_button and search_query:
            with st.spinner(f"正在搜索「{search_query}」..."):
                try:
                    with DDGS() as ddgs:
                        results = list(ddgs.text(search_query, max_results=5))

                    if results:
                        for i, result in enumerate(results):
                            st.markdown(f"### 搜索结果 {i+1}")
                            st.markdown(f"**{result['title']}**")
                            st.markdown(f"{result['body']}")
                            st.markdown(
                                f"[{result['href']}]({result['href']})")
                    else:
                        st.info("未找到相关结果")

                except Exception as e:
                    st.error(f"搜索出错: {str(e)}")

    with tool_tabs[2]:
        st.subheader("数学计算")

        expression = st.text_input(
            "输入数学表达式",
            placeholder="例如：(5 + 3) * 2 或 np.sin(np.pi/2)"
        )

        calculate_button = st.button("计算", key="calculate")

        if calculate_button and expression:
            with st.spinner(f"正在计算「{expression}」..."):
                try:
                    result = eval(expression)

                    if isinstance(result, (int, float, complex, np.number)):
                        formatted_result = f"{result}"
                        if isinstance(result, float) or isinstance(result, np.floating):
                            formatted_result = f"{result:.8g}"
                    elif isinstance(result, np.ndarray):
                        if result.size <= 10:
                            formatted_result = f"{result}"
                        else:
                            formatted_result = f"数组形状: {result.shape}\n前几个元素: {result.flatten()[:5]}..."
                    else:
                        formatted_result = str(result)

                    st.success(f"计算结果：{formatted_result}")

                    try:
                        st.latex(f"{expression} = {formatted_result}")
                    except:
                        st.text(f"{expression} = {formatted_result}")

                    if isinstance(result, np.ndarray) and 1 < result.size <= 1000:
                        try:
                            fig, ax = plt.subplots()

                            if result.ndim == 1:
                                ax.plot(result)
                                ax.set_title("计算结果可视化")
                                ax.set_xlabel("索引")
                                ax.set_ylabel("值")
                            elif result.ndim == 2 and min(result.shape) <= 50:
                                ax.imshow(result, cmap='viridis')
                                ax.set_title("二维数组可视化")

                            st.pyplot(fig)
                        except Exception as viz_error:
                            st.info(f"无法可视化结果: {str(viz_error)}")

                except Exception as e:
                    st.error(f"计算错误: {str(e)}")
                    st.info("提示：您可以使用Python语法，包括numpy (np)、math库的函数")
                    st.code("""
    示例:
    - 基本运算: (5 + 3) * 2
    - 三角函数: np.sin(np.pi/2)
    - 对数: math.log(100, 10)
    - 数组: np.array([1, 2, 3]) * 5
    - 统计: np.mean([1, 2, 3, 4, 5])
                    """)

# ==================== 主应用 ====================


def main():
    """主应用函数"""
    DEBUG_MODE = True
    # 初始化 session state
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(datetime.now().timestamp())
    feedback_system.init_session_state()

    # 设置标题
    st.title("📚 Chat-AI")

    # 侧边栏配置
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

        # 🔥 完全替换这整个部分：反馈统计部分
        st.divider()
        st.header("📊 反馈统计")

        # 添加操作按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 刷新", key="refresh_feedback", help="重新加载反馈数据"):
                # 强制重新加载数据
                feedback_system.force_refresh_data()
                st.success("✅ 数据已刷新")
                st.rerun()

        with col2:
            if st.button("📋 详情", key="show_detail", help="显示详细信息"):
                st.session_state.show_feedback_detail = not st.session_state.get(
                    'show_feedback_detail', False)

        # 显示反馈统计
        feedback_system.show_feedback_stats()

    # 🔥 完全替换这个部分
    if st.session_state.get('show_feedback_detail', False):
        st.markdown("---")
        st.subheader("🔍 详细信息")

        # 显示调试信息
        feedback_data = st.session_state.get('feedback_data', [])
        interaction_feedback = st.session_state.get('interaction_feedback', {})

        st.write(f"**Session反馈:** {len(feedback_data)} 条")
        st.write(f"**已标记交互:** {len(interaction_feedback)} 个")

        # 🔥 检查文件状态 - 确保使用正确的变量名
        data_file_path = feedback_system.data_file  # ✅ 使用 data_file
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
            for i, feedback in enumerate(feedback_data[-2:]):  # 只显示最近2条
                rating = feedback.get(
                    'average_rating', feedback.get('rating', 0))
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

        # 🔥 管理操作部分
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
                    if os.path.exists(feedback_system.data_file):  # ✅ 使用 data_file
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
    with st.sidebar.expander("🧪 反馈系统测试", expanded=False):
        # 🔥 添加实际的反馈表单
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
            import time
            interaction_id = f"test_feedback_{int(time.time() * 1000)}"

            # 提交反馈
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

    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "code_output" not in st.session_state:
        st.session_state.code_output = None

    # 根据选择的功能调用相应的处理函数
    if app_mode == "聊天助手":
        handle_chat_assistant(model, temperature, max_tokens)
    elif app_mode == "论文分析":
        handle_paper_analysis(model, max_tokens)
    elif app_mode == "教育内容生成":
        handle_education_content(model, max_tokens)
    elif app_mode == "工具集成":
        handle_tool_integration()

    # 页脚信息
    st.markdown("---")

    # 显示反馈分析
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
