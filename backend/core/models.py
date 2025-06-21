# backend/core/models.py
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class ModelProvider(str, Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    OTHER = "other"


class ModelConfig(BaseModel):
    """模型配置"""
    name: str
    provider: ModelProvider
    max_tokens: int = 4096
    default_temperature: float = 0.7


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str
    content: str


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[ChatMessage]
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = True


class ChatResponse(BaseModel):
    """聊天响应"""
    content: str
    model: str
    finish_reason: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    details: Optional[Dict[str, Any]] = None


class PaperAnalysisRequest(BaseModel):
    """论文分析请求"""
    paper_text: str
    model: str = "gpt-4o"


class EducationalContentRequest(BaseModel):
    """教育内容请求"""
    topic: str
    level: str
    model: str = "gpt-4o"
