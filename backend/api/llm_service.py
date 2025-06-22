# backend/api/llm_service.py
from typing import Dict, Any, Optional, List, Generator, Union
import asyncio
import json
from openai import OpenAI
from sqlalchemy.orm import Session

from backend.core.models import AIModel
from backend.api.model_management_service import ModelManagementService


class LLMService:
    def __init__(self, db: Session):
        self.db = db
        self.model_service = ModelManagementService()

    def generate_response(self,
                          messages: List[Dict[str, Any]],
                          model_id: int,
                          temperature: float = 0.7,
                          max_tokens: int = 1000,
                          stream: bool = True) -> Union[Generator, Dict]:
        """生成LLM响应，支持流式和非流式输出"""
        try:
            model_info = self.model_service.get_model(self.db, model_id)
            if not model_info or not model_info.provider:
                raise ValueError(f"Model with id {model_id} or its provider not found.")

            client = OpenAI(
                api_key=model_info.provider.api_key,
                base_url=model_info.provider.base_url
            )

            response = client.chat.completions.create(
                model=str(model_info.name),
                messages=messages, # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )

            if stream:
                return response
            else:
                return {
                    "content": response.choices[0].message.content,
                    "model": str(model_info.name),
                    "finish_reason": response.choices[0].finish_reason
                }
        except Exception as e:
            return {"error": str(e)}

    def analyze_paper(self, paper_text: str, model_id: int) -> Dict[str, Any]:
        """分析学术论文"""
        messages = [
            {"role": "system", "content": "你是一个专业的学术论文分析助手。请严格按照用户要求的JSON格式输出分析结果。"},
            {"role": "user", "content": f"请分析以下学术论文，并提供以下信息：\n1. 论文摘要和主要贡献\n2. 研究方法评估\n3. 关键发现和结论\n4. 与相关工作的比较\n5. 潜在的研究局限性\n\n论文内容：\n{paper_text}\n\n请以结构化的方式回答，使用Markdown格式。"}
        ]
        result = self.generate_response(messages, model_id, temperature=0.3, stream=False)
        if isinstance(result, dict):
            return result
        # This part should ideally not be reached if stream=False works as expected
        return {"error": "Failed to get a valid response"}

    def generate_educational_content(self, topic: str, level: str, model_id: int) -> Dict[str, Any]:
        """生成教育内容"""
        messages = [
            {"role": "system", "content": "你是一个专业的教育内容生成助手。请严格按照用户要求的JSON格式输出教育内容。"},
            {"role": "user", "content": f"请为{level}级别的学生生成关于\"{topic}\"的教育内容，包括：\n1. 概念简明解释\n2. 关键要点（3-5个）\n3. 实际应用示例\n4. 3个练习题（由简到难）及其详细解答\n5. 进一步学习建议\n\n请使用Markdown格式，确保内容准确、清晰且适合该级别学生理解。"}
        ]
        result = self.generate_response(messages, model_id, temperature=0.5, stream=False)
        if isinstance(result, dict):
            return result
        return {"error": "Failed to get a valid response"}
