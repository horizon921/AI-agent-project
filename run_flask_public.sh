#!/bin/bash
# 启动 Flask 应用在后台运行
python -m flask run --host=0.0.0.0 --port=8080 &
FLASK_PID=$!

echo "Flask 应用已启动在 http://localhost:8080"
echo "使用 ngrok 暴露到公网..."

# 启动 ngrok
ngrok http 8080

# 当 ngrok 被关闭时，也关闭 Flask 应用
kill $FLASK_PID
echo "Flask 应用已关闭"

# 保持终端窗口打开
echo "按任意键关闭此窗口..."
read -n 1

