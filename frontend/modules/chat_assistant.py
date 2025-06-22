import streamlit as st
import time
import json
import requests
from PIL import Image
from datetime import datetime
from frontend.core.multimodal import encode_image_to_base64, process_audio_to_text, create_multimodal_message
from backend.utils.feedback_system import feedback_system
import sys
import os

project_root = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

API_BASE_URL = "http://127.0.0.1:8000/api"

def handle_chat_assistant(model_id: int, temperature: float, max_tokens: int):
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
      div[data-testid="stFileUploader"] > div:first-child > div:first-child > div:first-child { display: none !important; }
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

    # 显示聊天历史并为每个助手回复添加反馈表单
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

            if message["role"] == "assistant":
                message_content = message["content"] if isinstance(
                    message["content"], str) else str(message["content"])
                message_hash = str(hash(message_content[:100]))
                interaction_id = f"chat_msg_{i}_{message_hash}"
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
            uploaded_image = st.file_uploader("选择图片文件", type=['png', 'jpg', 'jpeg', 'gif', 'webp'], key=f"img_uploader_{st.session_state.get('upload_counter', 0)}", label_visibility="collapsed")
        with col2:
            uploaded_audio = st.file_uploader("选择音频文件", type=['wav', 'mp3', 'm4a', 'ogg'], key=f"audio_uploader_{st.session_state.get('upload_counter', 0)}", label_visibility="collapsed")

    if uploaded_image:
        st.session_state.pending_files['image'] = uploaded_image  # type: ignore
        st.success("✅ 图片已选择！请输入消息后发送")
    if uploaded_audio:
        st.session_state.pending_files['audio'] = uploaded_audio  # type: ignore
        st.success("✅ 音频已选择！请输入消息后发送")

    # 显示文件预览
    pending_image = st.session_state.pending_files.get('image')
    if pending_image is not None:
        st.markdown("📷 **待发送图片:**")
        try:
            st.image(Image.open(pending_image), width=200)
        except Exception as e:
            st.error(f"图片预览失败: {str(e)}")

    pending_audio = st.session_state.pending_files.get('audio')
    if pending_audio is not None:
        st.markdown("🎤 **待发送音频:**")
        try:
            st.audio(pending_audio)
        except Exception as e:
            st.error(f"音频预览失败: {str(e)}")

    prompt = st.chat_input("请输入您的问题...")

    if prompt:
        audio_text = None
        image = None

        # 处理语音
        pending_audio_file = st.session_state.pending_files.get('audio')
        if pending_audio_file is not None:
            with st.spinner("🎤 正在识别语音..."):
                try:
                    audio_bytes = pending_audio_file.read()
                    audio_text = process_audio_to_text(audio_bytes)
                    pending_audio_file.seek(0)
                except Exception as e:
                    audio_text = f"语音识别失败: {str(e)}"

        # 处理图片
        pending_image_file = st.session_state.pending_files.get('image')
        if pending_image_file is not None:
            try:
                image = Image.open(pending_image_file)
                pending_image_file.seek(0)
            except Exception as e:
                st.error(f"图片处理失败: {str(e)}")
                image = None

        user_content = create_multimodal_message(prompt, image, audio_text)
        st.session_state.messages.append({"role": "user", "content": user_content})

        with st.chat_message("user"):
            st.markdown(prompt)
            if audio_text and not audio_text.startswith("语音识别失败"):
                st.markdown(f"🎤 **语音输入**: {audio_text}")
            if image:
                st.image(image, width=300)

        st.session_state.pending_files = {'image': None, 'audio': None}
        st.session_state.upload_counter = st.session_state.get('upload_counter', 0) + 1

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            try:
                chat_request_payload = {
                    "model_id": model_id,
                    "messages": st.session_state.messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                }
                response = requests.post(
                    f"{API_BASE_URL}/chat",
                    json=chat_request_payload,
                    stream=True,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        if decoded_line.startswith("data: "):
                            json_content = decoded_line[len("data: "):].strip()
                            if json_content == "[DONE]":
                                break
                            if not json_content:
                                continue
                            try:
                                data = json.loads(json_content)
                                content = data.get("choices", [{}])[0].get("delta", {}).get("content")
                                if content:
                                    full_response += content
                                    message_placeholder.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                continue
                
                message_placeholder.markdown(full_response)

            except requests.exceptions.RequestException as e:
                error_message = f"API 调用失败: {e}"
                message_placeholder.error(error_message)
                full_response = error_message
            except Exception as e:
                error_message = f"处理响应时发生未知错误: {e}"
                message_placeholder.error(error_message)
                full_response = error_message

            st.session_state.messages.append({"role": "assistant", "content": full_response})

        if full_response and not full_response.startswith("API 调用失败"):
            latest_msg_index = len(st.session_state.messages) - 1
            message_hash = str(hash(full_response[:100]))
            new_interaction_id = f"chat_msg_{latest_msg_index}_{message_hash}"
            st.markdown("---")
            with st.container():
                feedback_system.show_feedback_form(new_interaction_id)
