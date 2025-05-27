# backend/main.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional

from backend.api.llm_service import LLMService
from backend.api.parameter_service import ParameterComparisonService
from backend.api.tools_service import ToolsService
from backend.api.validation import SchemaValidator
from backend.config.settings import get_settings
from backend.config.logging_config import setup_logging
from backend.core.models import (
    ChatRequest, ChatResponse, ErrorResponse,
    PaperAnalysisRequest, EducationalContentRequest
)

# 设置日志
logger = setup_logging()

# 获取设置
settings = get_settings()

# 创建FastAPI应用
app = FastAPI(
    title="学术论文分析与教育辅导助手",
    description="基于多种LLM模型的论文分析和教育辅导工具",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 依赖注入


def get_llm_service():
    return LLMService()


def get_parameter_service(llm_service: LLMService = Depends(get_llm_service)):
    return ParameterComparisonService(llm_service)


def get_tools_service():
    return ToolsService()

# 路由


@app.get("/")
async def root():
    """API根路径"""
    return {"message": "欢迎使用学术论文分析与教育辅导助手API"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """聊天API端点"""
    try:
        # 提取最后一条用户消息作为提示
        user_messages = [
            msg for msg in request.messages if msg.role.lower() == "user"]
        if not user_messages:
            raise HTTPException(
                status_code=400, detail="No user message found")

        prompt = user_messages[-1].content

        if request.stream:
            # 流式响应需要特殊处理
            return StreamingResponse(
                content=llm_service.generate_response(
                    prompt,
                    request.model,
                    request.temperature,
                    request.max_tokens,
                    request.stream
                ),
                media_type="text/event-stream"
            )
        else:
            return llm_service.generate_response(
                prompt,
                request.model,
                request.temperature,
                request.max_tokens,
                request.stream
            )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze_paper")
async def analyze_paper(
    request: PaperAnalysisRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """论文分析API端点"""
    try:
        return llm_service.analyze_paper(request.paper_text, request.model)
    except Exception as e:
        logger.error(f"Error in analyze_paper endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/educational_content")
async def generate_educational_content(
    request: EducationalContentRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """教育内容生成API端点"""
    try:
        return llm_service.generate_educational_content(
            request.topic,
            request.level,
            request.model
        )
    except Exception as e:
        logger.error(f"Error in educational_content endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/execute_code")
async def execute_code(
    code: str,
    tools_service: ToolsService = Depends(get_tools_service)
):
    """代码执行API端点"""
    try:
        return tools_service.execute_code(code)
    except Exception as e:
        logger.error(f"Error in execute_code endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def search(
    query: str,
    num_results: int = 5,
    tools_service: ToolsService = Depends(get_tools_service)
):
    """网络搜索API端点"""
    try:
        return tools_service.web_search(query, num_results)
    except Exception as e:
        logger.error(f"Error in search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/calculate")
async def calculate(
    expression: str,
    tools_service: ToolsService = Depends(get_tools_service)
):
    """数学计算API端点"""
    try:
        return tools_service.calculate(expression)
    except Exception as e:
        logger.error(f"Error in calculate endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare_parameters")
async def compare_parameters(
    prompt: str,
    model: str,
    parameter_sets: List[Dict[str, Any]],
    parameter_service: ParameterComparisonService = Depends(
        get_parameter_service)
):
    """参数比较API端点"""
    try:
        return await parameter_service.compare_parameters(prompt, model, parameter_sets)
    except Exception as e:
        logger.error(f"Error in compare_parameters endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
