import requests
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥
api_key = os.getenv("MONICA_API_KEY")

print("Testing Monica API...")

# 设置请求头 - OpenAI兼容格式
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# API URL - OpenAI兼容格式
api_url = "https://api.monica.im/v1/chat/completions"

# 请求数据 - OpenAI兼容格式
data = {
    "model": "claude-3-5-sonnet-20240620",
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 100
}

# 发送请求
try:
    response = requests.post(api_url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
import requests
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥
api_key = os.getenv("MONICA_API_KEY")

# 设置请求头
headers = {
    "Content-Type": "application/json",
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01"
}

# API URL
api_url = "https://api.monica.im/v1/messages"

# 请求数据
data = {
    "model": "claude-3-5-sonnet-20240620",
    "max_tokens": 100,
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ]
}

# 发送请求
try:
    response = requests.post(api_url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# 尝试备选URL
api_url_alt = "https://api.anthropic.com/v1/messages"
print("\nTrying alternative URL...")

headers_alt = {
    "Content-Type": "application/json",
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01"
}

try:
    response = requests.post(api_url_alt, headers=headers_alt, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Rimport requests
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取API密钥
api_key = os.getenv("MONICA_API_KEY")

print("Testing Monica API...")

# 设置请求头 - OpenAI兼容格式
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# API URL - OpenAI兼容格式
api_url = "https://api.monica.im/v1/chat/completions"

# 请求数据 - OpenAI兼容格式
data = {
    "model": "claude-3-5-sonnet-20240620",
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 100
}

# 发送请求
try:
    response = requests.post(api_url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

