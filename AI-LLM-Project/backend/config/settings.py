# backend/config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()  # 加载.env文件


class Settings(BaseSettings):
    api_key: str = os.getenv(
        "API_KEY", "sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo")
    base_url: str = os.getenv("BASE_URL", "https://api.siliconflow.cn/v1")
    available_models: list = [
        "gpt-4o",
        "Qwen/Qwen2.5-72B-Instruct",
        "Pro/deepseek-ai/DeepSeek-R1"
    ]
    default_model: str = "gpt-4o"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
