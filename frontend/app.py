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
import numpy as np
import math
from scipy import stats, optimize, integrate
import speech_recognition as sr
import tempfile
import os
import re
from typing import Dict, Any, Optional
from datetime import datetime
# 设置页面配置
st.set_page_config(
    page_title="Chat-AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_default_format = """
<style>
#MainMenu {visibility: hidden; }
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none;}
</style>
"""
st.markdown(hide_default_format, unsafe_allow_html=True)

# API端点
API_BASE_URL = "http://localhost:8000/api"

# 设置标题
st.title("📚 Chat-AI")


def create_structured_prompt(content: str, task_type: str) -> str:
    """创建结构化提示词"""
    if task_type == "paper_analysis":
        return f"""
请按照以下JSON格式分析论文：
{{
    "summary": "论文摘要总结",
    "main_contributions": ["贡献1", "贡献2", "贡献3"],
    "methodology": "研究方法描述",
    "key_findings": ["发现1", "发现2", "发现3"],
    "limitations": ["局限1", "局限2"],
    "significance": "研究意义"
}}

重要：必须严格按照上述JSON格式输出，不要添加任何其他文字。

论文内容：{content}
"""

    elif task_type == "education_content":
        return f"""
请按照以下JSON格式生成教育内容：
{{
    "concept_explanation": "概念解释",
    "key_points": ["要点1", "要点2", "要点3"],
    "examples": ["示例1", "示例2", "示例3"],
    "exercises": [
        {{"question": "问题", "answer": "答案", "difficulty": "基础/中级/高级"}}
    ],
    "further_reading": ["推荐1", "推荐2"]
}}

重要：必须严格按照上述JSON格式输出，不要添加任何其他文字。

生成内容：{content}
"""

    return content


def parse_json_response(response: str):
    """尝试解析JSON响应"""
    try:
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None
    except:
        return None


# 多模态处理函数


def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def process_audio_to_text(audio_bytes):
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


# 侧边栏配置
with st.sidebar:
    st.header("模型设置")

    # 使用用户友好的显示名称
    model_display = st.selectbox(
        "选择模型",
        ["DeepSeek-V3", "Qwen-72B", "DeepSeek-R1"]
    )

    # 模型名称映射 - 将显示名称映射到API使用的实际名称
    model_mapping = {
        "DeepSeek-V3": "Pro/deepseek-ai/DeepSeek-V3",
        "Qwen-72B": "Qwen/Qwen2.5-72B-Instruct",
        "DeepSeek-R1": "Pro/deepseek-ai/DeepSeek-R1"
    }

    # 获取API使用的实际模型名称
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

    # 功能选择
    st.header("功能选择")
    app_mode = st.radio(
        "选择功能",
        ["聊天助手", "论文分析", "教育内容生成", "工具集成"]
    )

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

if "code_output" not in st.session_state:
    st.session_state.code_output = None

# 功能实现
if app_mode == "聊天助手":
    st.header("💬 聊天助手")

    # 添加自定义CSS
    st.markdown("""
    <style>
      /* 隐藏 Streamlit 默认上传控件 */
      div[data-testid="stFileUploader"] > lable { display: none !important; }

      /* 隐藏我们将插入的原生 input[type=file] */
      #file-input, #audio-input {
        display: none;
      }
      /* 隐藏英文提示文字 */
      div[data-testid="stFileUploader"] > div:first-child > div:first-child > div:first-child {
            display: none !important;
        }

        /* 自定义中文提示 */
        div[data-testid="stFileUploader"]:before {
            content: "拖拽文件到这里或点击浏览";
            display: block;
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
      /* 上传图标按钮 */
      .upload-btn {
        flex: none;
        width: 32px;
        height: 32px;
        margin-left: 8px;
        margin-right: 8px;
        border-radius: 50%;
        background: #fff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        transition: transform .2s, box-shadow .2s;
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
    if 'uploaded_image' not in st.session_state:
        st.session_state.uploaded_image = None
    if 'uploaded_audio' not in st.session_state:
        st.session_state.uploaded_audio = None
    if 'pending_files' not in st.session_state:
        st.session_state.pending_files = {'image': None, 'audio': None}

    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], str):
                st.markdown(message["content"])
            else:
                for content_item in message["content"]:
                    if content_item["type"] == "text":
                        st.markdown(content_item["text"])
                    elif content_item["type"] == "image_url":
                        st.image(content_item["image_url"]["url"], width=300)

    # 创建隐藏的文件上传器，使用唯一的key
    with st.container():
        uploaded_image = st.file_uploader(
            "选择图片文件",
            type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
            key=f"img_uploader_{st.session_state.get('upload_counter', 0)}",
            label_visibility="collapsed"
        )

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

    # 显示待发送的文件预览
    if st.session_state.pending_files['image']:
        with st.container():
            st.markdown('<div class="file-preview">', unsafe_allow_html=True)
            st.markdown("📷 **待发送图片:**")
            try:
                image = Image.open(st.session_state.pending_files['image'])
                st.image(image, width=200)
            except Exception as e:
                st.error(f"图片预览失败: {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.pending_files['audio']:
        with st.container():
            st.markdown('<div class="file-preview">', unsafe_allow_html=True)
            st.markdown("🎤 **待发送音频:**")
            try:
                st.audio(st.session_state.pending_files['audio'])
            except Exception as e:
                st.error(f"音频预览失败: {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)

    # 聊天输入框
    prompt = st.chat_input("请输入您的问题...")

    # 添加JavaScript来创建按钮并绑定点击事件
    st.markdown("""
    <script>
    (function() {
      // 每次渲染后尝试往输入框里插入按钮
      function insertButtons() {
        const container = document.querySelector('div[data-testid="stChatInput"]');
        if (!container || container.querySelector('.upload-btn')) return;

        // 在输入框最左侧插入两对 <label> + 隐藏 <input>
        container.insertAdjacentHTML('afterbegin', `
          <label for="file-input"  class="upload-btn" title="上传图片">📷</label>
          <label for="audio-input" class="upload-btn" title="上传音频">🎤</label>
          <input type="file" id="file-input"  accept="image/*">
          <input type="file" id="audio-input" accept="audio/*">
        `);
      }

      // 触发选择：图片/音频
      window.addEventListener('click', e => {
        if (e.target.matches('.upload-btn[title="上传图片"]'))
          document.getElementById('file-input').click();
        if (e.target.matches('.upload-btn[title="上传音频"]'))
          document.getElementById('audio-input').click();
      });

      // 初次插入 & 监听异步渲染
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

        # 处理待发送的语音
        if st.session_state.pending_files['audio']:
            with st.spinner("🎤 正在识别语音..."):
                try:
                    audio_bytes = st.session_state.pending_files['audio'].read(
                    )
                    audio_text = process_audio_to_text(audio_bytes)
                    st.session_state.pending_files['audio'].seek(0)
                except Exception as e:
                    audio_text = f"语音识别失败: {str(e)}"

        # 处理待发送的图片
        if st.session_state.pending_files['image']:
            try:
                image = Image.open(st.session_state.pending_files['image'])
                st.session_state.pending_files['image'].seek(0)
            except Exception as e:
                st.error(f"图片处理失败: {str(e)}")
                image = None

        # 创建多模态消息
        user_content = create_multimodal_message(prompt, image, audio_text)

        # 选择模型
        if image:
            current_model = "Qwen/Qwen2.5-VL-72B-Instruct"
        else:
            current_model = model

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

        # 清除待发送的文件并更新计数器
        st.session_state.pending_files = {'image': None, 'audio': None}
        st.session_state.upload_counter = st.session_state.get(
            'upload_counter', 0) + 1

        # 生成AI回复
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            try:
                client = OpenAI(
                    api_key="sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo",
                    base_url="https://api.siliconflow.cn/v1"
                )

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

            st.session_state.messages.append(
                {"role": "assistant", "content": full_response})

        st.rerun()


elif app_mode == "论文分析":
    st.header("📝 论文分析")

    paper_text = st.text_area(
        "请输入论文文本或摘要",
        height=300,
        help="粘贴论文文本、摘要或PDF提取的内容"
    )

    col1, col2 = st.columns([1, 3])

    with col1:
        analyze_button = st.button("分析论文", type="primary")

    if analyze_button and paper_text:
        with st.spinner("正在分析论文..."):
            try:
                client = OpenAI(
                    api_key="sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo",
                    base_url="https://api.siliconflow.cn/v1"
                )

                # 使用结构化提示
                structured_prompt = create_structured_prompt(
                    paper_text, "paper_analysis")

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system",
                            "content": "你是一个专业的学术论文分析助手。请严格按照用户要求的JSON格式输出分析结果。"},
                        {"role": "user", "content": structured_prompt}
                    ],
                    temperature=0.1,  # 降低随机性确保格式稳定
                    max_tokens=max_tokens
                )

                analysis_result = response.choices[0].message.content

                # 尝试解析JSON并美化显示
                parsed_data = parse_json_response(analysis_result)

                if parsed_data:
                    # 结构化显示
                    st.markdown("### 📊 论文分析结果")

                    st.markdown("### 📝 摘要总结")
                    st.markdown(parsed_data.get('summary', '未提供摘要'))

                    st.markdown("### 🎯 主要贡献")
                    for i, contrib in enumerate(parsed_data.get('main_contributions', []), 1):
                        st.markdown(f"{i}. {contrib}")

                    st.markdown("### 🔬 研究方法")
                    st.markdown(parsed_data.get('methodology', '未描述'))

                    st.markdown("### 🔍 关键发现")
                    for i, finding in enumerate(parsed_data.get('key_findings', []), 1):
                        st.markdown(f"{i}. {finding}")

                    st.markdown("### ⚠️ 研究局限")
                    for i, limitation in enumerate(parsed_data.get('limitations', []), 1):
                        st.markdown(f"{i}. {limitation}")

                    st.markdown("### 💡 研究意义")
                    st.markdown(parsed_data.get('significance', '未评估'))

                else:
                    # 如果JSON解析失败，直接显示原始回复
                    st.markdown(analysis_result)

            except Exception as e:
                st.error(f"API调用出错: {str(e)}")

elif app_mode == "教育内容生成":
    st.header("🎓 教育内容生成")

    col1, col2 = st.columns(2)

    with col1:
        topic = st.text_input("请输入主题", placeholder="例如：光合作用、微积分、人工智能...")

    with col2:
        level = st.selectbox(
            "选择教育级别",
            ["小学", "初中", "高中", "大学", "研究生"]
        )

    generate_button = st.button("生成教育内容", type="primary")

    if generate_button and topic:
        with st.spinner(f"正在生成关于「{topic}」的{level}级别教育内容..."):
            try:
                client = OpenAI(
                    api_key="sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo",
                    base_url="https://api.siliconflow.cn/v1"
                )

                # 使用结构化提示
                content_request = f"主题：{topic}，级别：{level}"
                structured_prompt = create_structured_prompt(
                    content_request, "education_content")

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system",
                            "content": "你是一个专业的教育内容生成助手。请严格按照用户要求的JSON格式输出教育内容。"},
                        {"role": "user", "content": structured_prompt}
                    ],
                    temperature=0.1,  # 降低随机性确保格式稳定
                    max_tokens=max_tokens
                )

                content_result = response.choices[0].message.content

                # 尝试解析JSON并美化显示
                parsed_data = parse_json_response(content_result)

                if parsed_data:
                    # 结构化显示
                    st.markdown(f"# {topic} - {level}级别教育内容")

                    st.markdown("## 📚 概念解释")
                    st.markdown(parsed_data.get(
                        'concept_explanation', '未提供解释'))

                    st.markdown("## 🎯 关键要点")
                    for i, point in enumerate(parsed_data.get('key_points', []), 1):
                        st.markdown(f"{i}. {point}")

                    st.markdown("## 💡 实际应用示例")
                    for i, example in enumerate(parsed_data.get('examples', []), 1):
                        st.markdown(f"**示例{i}**: {example}")

                    st.markdown("## 📝 练习题")
                    exercises = parsed_data.get('exercises', [])
                    for i, exercise in enumerate(exercises, 1):
                        with st.expander(f"练习{i} ({exercise.get('difficulty', '未知')})"):
                            st.markdown(
                                f"**问题**: {exercise.get('question', '未提供')}")
                            st.markdown(
                                f"**答案**: {exercise.get('answer', '未提供')}")

                    st.markdown("## 📖 进一步学习建议")
                    for i, reading in enumerate(parsed_data.get('further_reading', []), 1):
                        st.markdown(f"{i}. {reading}")

                else:
                    # 如果JSON解析失败，直接显示原始回复
                    st.markdown(content_result)

            except Exception as e:
                st.error(f"API调用出错: {str(e)}")

elif app_mode == "工具集成":
    st.header("🛠️ 工具集成")

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
                    # 创建输出捕获对象
                    from io import StringIO
                    import sys
                    import contextlib

                    # 捕获标准输出
                    stdout_capture = StringIO()

                    # 创建一个图表容器用于显示matplotlib图表
                    fig_container = st.empty()

                    # 重定向标准输出并执行代码
                    with contextlib.redirect_stdout(stdout_capture):
                        # 创建本地变量环境
                        local_vars = {}

                        # 如果代码中包含matplotlib，添加特殊处理
                        if "plt" in code:
                            # 添加自动显示图表的代码
                            exec_code = code + "\n\n# 捕获图表\nif 'plt' in locals() or 'plt' in globals():\n    fig = plt.gcf()\n    plt.close()"
                        else:
                            exec_code = code

                        # 执行代码
                        exec(exec_code, globals(), local_vars)

                        # 如果生成了图表，显示它
                        if "plt" in code and "fig" in local_vars:
                            fig_container.pyplot(local_vars["fig"])

                    # 获取标准输出
                    output = stdout_capture.getvalue()

                    st.success("代码执行成功！")
                    if output:
                        st.code(f"输出：\n{output}", language="text")
                    else:
                        st.code("输出：\n(无标准输出)", language="text")

                except Exception as e:
                    st.error(f"代码执行失败：{str(e)}")
                    import traceback
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

                    # 显示搜索结果
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
                    # 导入常用的数学库

                    # 安全地评估表达式
                    result = eval(expression)

                    # 格式化结果
                    if isinstance(result, (int, float, complex, np.number)):
                        formatted_result = f"{result}"
                        if isinstance(result, float) or isinstance(result, np.floating):
                            # 对于浮点数，限制小数位数
                            formatted_result = f"{result:.8g}"
                    elif isinstance(result, np.ndarray):
                        if result.size <= 10:  # 如果是小数组，完整显示
                            formatted_result = f"{result}"
                        else:  # 如果是大数组，显示形状和部分内容
                            formatted_result = f"数组形状: {result.shape}\n前几个元素: {result.flatten()[:5]}..."
                    else:
                        formatted_result = str(result)

                    st.success(f"计算结果：{formatted_result}")

                    # 尝试使用LaTeX显示表达式和结果
                    try:
                        st.latex(f"{expression} = {formatted_result}")
                    except:
                        st.text(f"{expression} = {formatted_result}")

                    # 如果结果是数组且大小适中，显示图表
                    if isinstance(result, np.ndarray) and 1 < result.size <= 1000:
                        try:
                            import matplotlib.pyplot as plt
                            fig, ax = plt.subplots()

                            if result.ndim == 1:  # 一维数组
                                ax.plot(result)
                                ax.set_title("计算结果可视化")
                                ax.set_xlabel("索引")
                                ax.set_ylabel("值")
                            # 二维数组
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

# 页脚
st.markdown("---")
st.markdown("© 2025 Chat-AI | 基于多种LLM模型构建")
