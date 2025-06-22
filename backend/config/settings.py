# backend/config/settings.py
from functools import lru_cache
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()  # 加载.env文件


class Settings:
    """应用配置类"""
    
    def __init__(self):
        # API配置
        self.api_key: str = os.getenv(
            "API_KEY", "sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo")
        self.base_url: str = os.getenv(
            "BASE_URL", "https://api.siliconflow.cn/v1")
        
        # 模型配置
        self.available_models: List[str] = [
            "gpt-4o",
            "Qwen/Qwen2.5-72B-Instruct",
            "Pro/deepseek-ai/DeepSeek-R1"
        ]
        self.default_model: str = os.getenv("DEFAULT_MODEL", "gpt-4o")
        
        # 服务配置
        self.backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
        self.frontend_port: int = int(os.getenv("FRONTEND_PORT", "8501"))


@lru_cache()
def get_settings():
    return Settings()
