# backend/utils/helpers.py
import json
import re
import time
from typing import Dict, Any, List, Callable, Optional
import logging

logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(
    func: Callable,
    initial_delay: float = 1,
    exponential_base: float = 2,
    max_retries: int = 5,
    errors: tuple = (Exception,),
):
    """指数退避重试装饰器"""
    def wrapper(*args, **kwargs):
        num_retries = 0
        delay = initial_delay

        while True:
            try:
                return func(*args, **kwargs)
            except errors as e:
                num_retries += 1
                if num_retries > max_retries:
                    logger.error(f"Maximum retries ({max_retries}) exceeded.")
                    raise

                logger.warning(
                    f"Retry {num_retries}/{max_retries} after error: {str(e)}")
                time.sleep(delay)
                delay *= exponential_base

    return wrapper


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """从文本中提取JSON"""
    json_pattern = r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}'
    match = re.search(json_pattern, text)

    if match:
        json_str = match.group(1) if match.group(1) else match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {json_str}")
            return None
    return None


def truncate_text(text: str, max_length: int = 100) -> str:
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def calculate_tokens(text: str) -> int:
    """粗略估计文本的token数量"""
    # 这是一个非常粗略的估计，实际token数量取决于具体的分词器
    return len(text.split())
