"""
提示词模板模块
管理各种AI任务的提示词模板
"""

from typing import Dict
import streamlit as st
from datetime import datetime


class PromptTemplateManager:
    """提示词模板管理器"""

    def __init__(self):
        self.templates = {
            "paper_analysis": {
                "A": self._paper_analysis_template_a,
                "B": self._paper_analysis_template_b
            },
            "education_content": {
                "A": self._education_content_template_a,
                "B": self._education_content_template_b
            }
        }

    def ab_test_prompt_optimization(self) -> str:
        """A/B测试不同的提示词优化"""
        if "ab_test_group" not in st.session_state:
            st.session_state.ab_test_group = "A" if hash(
                str(datetime.now())) % 2 == 0 else "B"
        return st.session_state.ab_test_group

    def create_structured_prompt(self, content: str, task_type: str) -> str:
        """创建结构化提示词（支持A/B测试）"""
        test_group = self.ab_test_prompt_optimization()

        if task_type in self.templates:
            return self.templates[task_type][test_group](content)
        else:
            return content

    def _paper_analysis_template_a(self, content: str) -> str:
        """论文分析模板A（原版）"""
        return f"""请按照以下JSON格式分析论文：

{{
    "summary": "论文摘要总结",
    "main_contributions": ["贡献1", "贡献2", "贡献3"],
    "methodology": "研究方法描述",
    "key_findings": ["发现1", "发现2", "发现3"],
    "limitations": ["局限1", "局限2"],
    "significance": "研究意义"
}}

请严格按照上述JSON格式输出，不要添加任何其他文字。

论文内容：
{content}"""

    def _paper_analysis_template_b(self, content: str) -> str:
        """论文分析模板B（优化版）"""
        return f"""作为专业的学术研究助手，请深入分析以下论文并按照JSON格式输出：

分析要求：
1. 提供简洁而全面的摘要总结
2. 识别3-5个主要学术贡献
3. 详细描述研究方法和技术路线
4. 总结关键发现和创新点
5. 客观评估研究局限性
6. 阐述学术和实践意义

输出格式（严格遵循JSON结构）：
{{
    "summary": "详细的论文摘要总结",
    "main_contributions": ["具体贡献1", "具体贡献2", "具体贡献3"],
    "methodology": "详细的研究方法和技术描述",
    "key_findings": ["关键发现1", "关键发现2", "关键发现3"],
    "limitations": ["局限性1", "局限性2"],
    "significance": "学术价值和实践意义分析"
}}

论文内容：
{content}

请确保输出为有效的JSON格式，内容准确专业。"""

    def _education_content_template_a(self, content: str) -> str:
        """教育内容模板A（原版）"""
        return f"""请为以下主题生成教育内容，按JSON格式输出：

{content}

格式要求：
{{
    "concept_explanation": "概念解释",
    "key_points": ["要点1", "要点2"],
    "examples": ["例子1", "例子2"],
    "exercises": [
        {{"question": "问题", "answer": "答案", "difficulty": "基础"}}
    ],
    "further_reading": ["建议1", "建议2"]
}}

重要提醒：difficulty字段必须使用以下值之一：["基础", "中级", "高级"]"""

    def _education_content_template_b(self, content: str) -> str:
        """教育内容模板B（优化版）"""
        return f"""作为专业的教育内容专家，请为以下主题创建结构化的学习材料：

{content}

请确保内容：
- 概念解释清晰易懂，适合目标学习者
- 关键要点突出重点，逻辑清晰
- 实例生动具体，贴近生活
- 练习题难度适中，覆盖核心知识点
- 进一步学习建议实用可行

JSON输出格式：
{{
    "concept_explanation": "深入浅出的概念解释",
    "key_points": ["核心要点1", "核心要点2", "核心要点3"],
    "examples": ["生动实例1", "生动实例2", "生动实例3"],
    "exercises": [
        {{
            "question": "练习题目", 
            "answer": "详细答案", 
            "difficulty": "基础"
        }}
    ],
    "further_reading": ["学习建议1", "学习建议2", "学习建议3"]
}}

🔥 重要约束：
- difficulty字段只能使用：["基础", "中级", "高级"] 之一
- 不要使用：中等、简单、困难、容易、难等其他词汇
- 确保JSON格式完全正确，无语法错误

请确保内容质量高，严格遵循格式要求。"""


# 全局模板管理器实例
prompt_manager = PromptTemplateManager()
