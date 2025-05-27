# backend/api/tools_service.py
import requests
import json
import base64
from typing import Dict, Any, List
import numpy as np
import matplotlib.pyplot as plt
import io


class ToolsService:
    def __init__(self):
        self.search_api_key = "your_search_api_key"  # 实际项目中应从配置中读取

    def web_search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """执行网络搜索"""
        # 这里应该是实际的搜索API调用
        # 为了演示，返回模拟数据
        return [
            {"title": f"搜索结果 {i}", "url": f"https://example.com/{i}",
                "snippet": f"这是关于{query}的搜索结果片段 {i}"}
            for i in range(1, num_results + 1)
        ]

    def execute_code(self, code: str) -> Dict[str, Any]:
        """执行Python代码（简化版代码解释器）"""
        try:
            # 创建安全的执行环境
            local_vars = {}

            # 捕获输出
            stdout_buffer = io.StringIO()

            # 捕获图表
            fig_data = None

            # 执行代码
            exec(code, {"np": np, "plt": plt, "print": lambda *args: stdout_buffer.write(
                " ".join(map(str, args)) + "\n")}, local_vars)

            # 检查是否有图表
            if 'plt' in code:
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                fig_data = base64.b64encode(buf.read()).decode('utf-8')
                plt.close()

            return {
                "success": True,
                "output": stdout_buffer.getvalue(),
                "figure": fig_data,
                "variables": {k: str(v) for k, v in local_vars.items() if not k.startswith('_')}
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def calculate(self, expression: str) -> Dict[str, Any]:
        """执行数学计算"""
        try:
            # 安全的计算方式
            result = eval(expression, {"__builtins__": {}}, {"np": np})
            return {
                "success": True,
                "expression": expression,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "expression": expression,
                "error": str(e)
            }
