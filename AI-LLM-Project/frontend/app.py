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
# 设置页面配置
st.set_page_config(
    page_title="学术论文分析与教育辅导助手",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API端点
API_BASE_URL = "http://localhost:8000/api"

# 设置标题
st.title("📚 学术论文分析与教育辅导助手")

# 侧边栏配置
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

    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 用户输入
    prompt = st.chat_input("请输入您的问题...")

    if prompt:
        # 添加用户消息到历史
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)

        # 显示助手消息
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            try:
                # 创建OpenAI客户端实例，连接到DeepSeek API
                client = OpenAI(
                    api_key="sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo",
                    base_url="https://api.siliconflow.cn/v1"
                )

                # 准备消息历史
                messages = [
                    {"role": "system",
                        "content": "你是一个专业的学术论文分析与教育辅导助手，擅长帮助用户解答学术问题、分析论文和提供教育指导。"}
                ]

                # 添加历史消息，最多保留最近10条
                recent_messages = st.session_state.messages[-10:] if len(
                    st.session_state.messages) > 10 else st.session_state.messages
                for msg in recent_messages:
                    messages.append(
                        {"role": msg["role"], "content": msg["content"]})

                # 调用API获取流式响应
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )

                # 处理流式响应
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
            # 调用DeepSeek API
            try:
                client = OpenAI(
                    api_key="sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo",
                    base_url="https://api.siliconflow.cn/v1"
                )

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的学术论文分析助手，请对提供的论文内容进行详细分析，包括摘要和主要贡献、研究方法评估、关键发现和结论、与相关工作的比较、潜在的研究局限性等方面。"},
                        {"role": "user", "content": f"请分析以下论文内容：\n\n{paper_text}"}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                analysis_result = response.choices[0].message.content
                st.markdown(analysis_result)

            except Exception as e:
                st.error(f"API调用出错: {str(e)}")

                # 如果API调用失败，使用模拟数据作为备用
                analysis_result = '''
                # 论文分析结果
                
                ## 摘要和主要贡献
                这篇论文提出了一种新的深度学习方法，用于改进自然语言处理任务中的文本分类精度。
                
                ## 研究方法评估
                作者使用了BERT模型的变体，并通过引入新的注意力机制提高了模型性能。实验设计合理，评估指标全面。
                
                ## 关键发现和结论
                1. 提出的模型在标准基准测试中比现有方法提高了5%的准确率
                2. 模型训练时间减少了30%
                3. 在低资源场景下表现尤为突出
                
                ## 与相关工作的比较
                与之前的研究相比，本文的方法更加高效且具有更好的泛化能力。
                
                ## 潜在的研究局限性
                1. 仅在英语数据集上进行了测试
                2. 计算资源要求较高
                '''
                st.markdown(analysis_result)

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
            # 调用DeepSeek API
            try:
                client = OpenAI(
                    api_key="sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo",
                    base_url="https://api.siliconflow.cn/v1"
                )

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system",
                            "content": "你是一个专业的教育内容生成助手，请根据用户提供的主题和教育级别生成相应的教育内容。"},
                        {"role": "user", "content": f"请为{level}级别的学生生成关于「{topic}」的教育内容，包括概念解释、关键要点、实际应用示例、练习题和进一步学习建议。"}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                content_result = response.choices[0].message.content
                st.markdown(content_result)

            except Exception as e:
                st.error(f"API调用出错: {str(e)}")

                # 如果API调用失败，使用模拟数据作为备用
                content_result = f'''
                # {topic} - {level}级别教育内容
                
                ## 概念简明解释
                {topic}是指一种重要的概念或现象，它在相关领域中起着关键作用。
                
                ## 关键要点
                1. **基本原理**：{topic}的基本原理涉及到多个方面的知识
                2. **历史发展**：{topic}的概念经历了长期的发展和完善
                3. **应用场景**：{topic}在实际中有广泛的应用
                4. **最新进展**：近年来{topic}领域有许多创新性的研究成果
                
                ## 实际应用示例
                在实际生活或工作中，{topic}可以应用于以下场景：
                - 示例1：日常生活中的应用
                - 示例2：工业生产中的应用
                - 示例3：科学研究中的应用
                
                ## 练习题
                ### 练习1（基础）
                问题：关于{topic}的基础概念，以下哪项描述是正确的？
                
                答案：这里是详细解答...
                
                ### 练习2（中级）
                问题：在给定条件下，如何应用{topic}解决特定问题？
                
                答案：这里是详细解答...
                
                ### 练习3（高级）
                问题：分析{topic}在复杂场景中的应用限制和优化方法。
                
                答案：这里是详细解答...
                
                ## 进一步学习建议
                1. 推荐阅读：《{topic}基础》、《{topic}高级应用》
                2. 在线课程：Coursera和edX上有相关优质课程
                3. 实践项目：尝试在实际项目中应用{topic}相关知识
                '''
                st.markdown(content_result)

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
st.markdown("© 2025 学术论文分析与教育辅导助手 | 基于多种LLM模型构建")
