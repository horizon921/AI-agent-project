# backend/api/llm_service.py
from typing import Dict, Any, Optional, List, Generator
import asyncio
import json
from openai import OpenAI
from backend.config.settings import get_settings

settings = get_settings()


class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url
        )

    def generate_response(self,
                          prompt: str,
                          model: str = "gpt-4o",
                          temperature: float = 0.7,
                          max_tokens: int = 1000,
                          # type: ignore
                          stream: bool = True) -> Dict[str, Any] or Generator:
        """生成LLM响应，支持流式输出"""
        try:
            messages = [{"role": "user", "content": prompt}]

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )

            if stream:
                return response  # 返回流式响应生成器
            else:
                # 非流式响应直接返回完整内容
                return {
                    "content": response.choices[0].message.content,
                    "model": model,
                    "finish_reason": response.choices[0].finish_reason
                }

        except Exception as e:
            # 异常处理
            return {"error": str(e)}

    def analyze_paper(self, paper_text: str, model: str = "gpt-4o") -> Dict[str, Any]:
        """分析学术论文"""
        prompt = f"""
        请分析以下学术论文，并提供以下信息：
        1. 论文摘要和主要贡献
        2. 研究方法评估
        3. 关键发现和结论
        4. 与相关工作的比较
        5. 潜在的研究局限性
        
        论文内容：
        {paper_text}
        
        请以结构化的方式回答，使用Markdown格式。
        """

        return self.generate_response(prompt, model, temperature=0.3, stream=False)

    def generate_educational_content(self, topic: str, level: str, model: str = "gpt-4o") -> Dict[str, Any]:
        """生成教育内容"""
        prompt = f"""
        请为{level}级别的学生生成关于"{topic}"的教育内容，包括：
        1. 概念简明解释
        2. 关键要点（3-5个）
        3. 实际应用示例
        4. 3个练习题（由简到难）及其详细解答
        5. 进一步学习建议
        
        请使用Markdown格式，确保内容准确、清晰且适合该级别学生理解。
        """

        return self.generate_response(prompt, model, temperature=0.5, stream=False)
