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
    "Authorization": f"Bearer {api_key}"
}

# 正确的API URL
api_url = "https://openapi.monica.im/v1/chat/completions"

# 请求数据
data = {
    "model": "gpt-4o",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Hello, how are you?"
                }
            ]
        }
    ]
}

# 发送请求
try:
    response = requests.post(api_url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

