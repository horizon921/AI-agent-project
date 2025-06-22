import streamlit as st
import contextlib
from io import StringIO
import traceback
import matplotlib.pyplot as plt
import numpy as np
import math
from duckduckgo_search import DDGS


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
