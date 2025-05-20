from flask import Flask, render_template, request, jsonify
import os
import requests
import json
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import logging
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 禁用不安全的HTTPS警告
urllib3.disable_warnings()

app = Flask(__name__)

# 从环境变量获取Monica API密钥
api_key = os.environ.get("MONICA_API_KEY")
if not api_key:
    logger.warning("未设置MONICA_API_KEY环境变量")

# 创建一个具有重试功能的会话
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)

# 配置代理（如果需要）
proxy_url = os.environ.get("HTTP_PROXY")
if proxy_url:
    session.proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    logger.info(f"已配置代理: {proxy_url}")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    # 检查API密钥是否存在
    if not api_key:
        return jsonify({"error": "未设置API密钥。请设置MONICA_API_KEY环境变量。", "status": "error"})

    # 获取请求参数
    user_message = request.form.get('message')
    temperature = float(request.form.get('temperature', 0.7))
    max_tokens = int(request.form.get('max_tokens', 1000))
    model = request.form.get('model', 'gpt-4o')

    # 定义请求格式 - 修正为Monica API要求的格式
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_message
                    }
                ]
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        logger.info(f"发送请求到Monica API: 模型={model}, 温度={temperature}")

        # 使用Monica的API端点
        start_time = time.time()
        response = session.post(
            "https://openapi.monica.im/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response_time = time.time() - start_time

        logger.info(
            f"API响应状态码: {response.status_code}, 响应时间: {response_time:.2f}秒")

        if response.status_code == 200:
            result = response.json()
            ai_message = result["choices"][0]["message"]["content"]
            return jsonify({
                "response": ai_message,
                "temperature": temperature,
                "model": model,
                "response_time": f"{response_time:.2f}秒",
                "status": "success"
            })
        elif response.status_code == 401:
            logger.error("API密钥无效或已过期")
            return jsonify({
                "error": "API密钥无效或已过期",
                "status": "error"
            })
        elif response.status_code == 429:
            logger.warning("API请求过于频繁，已达到速率限制")
            return jsonify({
                "error": "请求过于频繁，请稍后再试",
                "status": "error"
            })
        else:
            logger.error(f"API错误: {response.status_code}, 详情: {response.text}")
            return jsonify({
                "error": f"API错误: {response.status_code}",
                "details": response.text,
                "status": "error"
            })

    except requests.exceptions.Timeout:
        logger.error("API请求超时")
        return jsonify({"error": "请求超时，请稍后再试", "status": "error"})
    except requests.exceptions.ConnectionError:
        logger.error("无法连接到API服务器")
        return jsonify({"error": "无法连接到API服务器", "status": "error"})
    except Exception as e:
        logger.exception("处理请求时发生未知错误")
        return jsonify({"error": str(e), "status": "error"})


@app.route('/api/status', methods=['GET'])
def api_status():
    """检查API连接状态"""
    if not api_key:
        return jsonify({"status": "error", "message": "未设置API密钥"})

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        response = session.get(
            "https://openapi.monica.im/v1/models",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            return jsonify({"status": "success", "message": "API连接正常"})
        else:
            logger.warning(f"API状态检查失败: {response.status_code}")
            return jsonify({"status": "error", "message": f"API错误: {response.status_code}"})

    except Exception as e:
        logger.error(f"API状态检查异常: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})


@app.route('/models', methods=['GET'])
def get_models():
    """获取可用的模型列表"""
    if not api_key:
        return jsonify({"status": "error", "message": "未设置API密钥"})

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        response = session.get(
            "https://openapi.monica.im/v1/models",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            models = response.json()
            return jsonify({"status": "success", "models": models})
        else:
            return jsonify({
                "status": "error",
                "message": f"获取模型列表失败: {response.status_code}"
            })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
