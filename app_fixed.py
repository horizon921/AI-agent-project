from flask import Flask, render_template, request, jsonify
import os
import requests
import json

app = Flask(__name__)

# 从环境变量获取Monica API密钥
api_key = os.environ.get("MONICA_API_KEY")
if not api_key:
    print("警告: 未设置MONICA_API_KEY环境变量")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    # 检查API密钥是否存在
    if not api_key:
        return jsonify({"error": "未设置API密钥。请设置MONICA_API_KEY环境变量。"})
        
    user_message = request.form.get('message')
    temperature = float(request.form.get('temperature', 0.7))  # 默认温度为0.7
    
    # 定义请求格式 - 使用Monica API调用GPT-4o
    payload = {
        "model": "gpt-4o",  # 指定使用GPT-4o模型
        "messages": [{"role": "user", "content": user_message}],
        "temperature": temperature,
        "max_tokens": 1000
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"  # 修正为正确的Authorization格式
    }
    
    try:
        # 使用Monica的API端点
        response = requests.post(
            "https://api.monica.ai/v1/chat/completions",  # Monica的API端点
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_message = result["choices"][0]["message"]["content"]
            return jsonify({"response": ai_message, "temperature": temperature})
        else:
            return jsonify({"error": f"API错误: {response.status_code}", "details": response.text})
    
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
