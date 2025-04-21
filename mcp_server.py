from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()

# 假设所有会话和消息都存内存
sessions = {}


class MCPMessage(BaseModel):
    from_app: str
    to_service: str
    content: str


@app.post("/mcp/send")
async def send_message(msg: MCPMessage):
    # 这里可以做权限校验、日志等
    print(f"收到来自 {msg.from_app} 的消息，将转发给 {msg.to_service}")
    # 模拟转发到外部服务
    response = await fake_send_to_service(msg.to_service, msg.content)
    return {"status": "ok", "service_response": response}


async def fake_send_to_service(service, content):
    # 这里你可以接入 Slack/X/Github/Drive 等服务的 API
    print(f"发送到 {service}: {content}")
    return f"已发送到 {service}"

# 下层服务回调 MCP Server


@app.post("/mcp/callback/{service}")
async def service_callback(service: str, req: Request):
    data = await req.json()
    print(f"{service} 回调 MCP，内容为: {data}")
    # 可以将消息分发给对应的上层 APP
    # 这里简单打印
    return {"status": "received"}

# 运行: uvicorn mcp_server:app --reload
