# backend/core/models.py
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from .database import Base


class ProviderType(str, PyEnum):
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    provider_type = Column(SQLEnum(ProviderType), nullable=False)
    base_url = Column(String, nullable=False, unique=True)
    api_key = Column(String)  # Can be nullable for local models like Ollama

    models = relationship("AIModel", back_populates="provider", cascade="all, delete-orphan")


class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"))

    # Pricing
    input_price = Column(Float, default=0.0)
    output_price = Column(Float, default=0.0)

    # Capabilities
    supports_streaming = Column(Boolean, default=True)
    supports_inference = Column(Boolean, default=True)
    supports_multimodality = Column(Boolean, default=False)
    supports_tools = Column(Boolean, default=False)
    context_length = Column(Integer, default=4096)

    provider = relationship("Provider", back_populates="models")


# Pydantic Schemas for API

class AIModelBase(BaseModel):
    name: str
    input_price: float = 0.0
    output_price: float = 0.0
    supports_streaming: bool = True
    supports_inference: bool = True
    supports_multimodality: bool = False
    supports_tools: bool = False
    context_length: int = 4096

class AIModelCreate(AIModelBase):
    pass

class AIModelRead(AIModelBase):
    id: int
    provider_id: int

    class Config:
        from_attributes = True

class ProviderBase(BaseModel):
    name: str
    provider_type: ProviderType
    base_url: str
    api_key: Optional[str] = None

class ProviderCreate(ProviderBase):
    pass

class ProviderRead(BaseModel):
    id: int
    name: str
    provider_type: ProviderType
    base_url: str
    models: List[AIModelRead] = []

    class Config:
        from_attributes = True


# --- Existing Models ---

class ChatMessage(BaseModel):
    """聊天消息"""
    role: str
    content: Any # Can be string or list for multimodal


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[ChatMessage]
    model_id: int
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
    model_id: int


class EducationalContentRequest(BaseModel):
    """教育内容请求"""
    topic: str
    level: str
    model_id: int
