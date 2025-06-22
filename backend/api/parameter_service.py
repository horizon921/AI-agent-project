# backend/api/parameter_service.py
from typing import Dict, List, Any
import asyncio
from .llm_service import LLMService


class ParameterComparisonService:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def compare_parameters(self,
                                 prompt: str,
                                 model_id: int,
                                 parameter_sets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """比较不同参数设置下的LLM输出"""
        results = {}
        tasks = []

        for i, params in enumerate(parameter_sets):
            task = asyncio.create_task(
                self.llm_service.generate_response(
                    prompt=prompt,
                    model_id=model_id,
                    **params,
                    stream=False  # 参数比较时不使用流式输出
                )
            )
            tasks.append((f"set_{i+1}", task))

        for name, task in tasks:
            results[name] = await task

        return results
