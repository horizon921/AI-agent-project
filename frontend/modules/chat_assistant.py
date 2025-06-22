import streamlit as st
import time
from PIL import Image
from openai import OpenAI
from datetime import datetime
from frontend.core.multimodal import encode_image_to_base64, process_audio_to_text, create_multimodal_message
from backend.utils.feedback_system import feedback_system
import sys
import os
project_root = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def handle_chat_assistant(model, temperature, max_tokens, api_key, base_url):
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

    # 🔥 显示聊天历史并为每个助手回复添加反馈表单
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
                client = OpenAI(api_key=api_key, base_url=base_url)

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

        # 🔥 为最新回复添加反馈表单
        if full_response and not full_response.startswith("API调用出错"):
            # 为最新的回复创建反馈表单
            latest_msg_index = len(st.session_state.messages) - 1
            message_hash = str(hash(full_response[:100]))
            new_interaction_id = f"chat_msg_{latest_msg_index}_{message_hash}"

            st.markdown("---")

            # 🔥 使用容器来确保稳定显示
            with st.container():
                feedback_system.show_feedback_form(new_interaction_id)
