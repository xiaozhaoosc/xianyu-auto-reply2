"""
闲鱼 WebSocket 服务入口

功能：
1. 管理闲鱼 WebSocket 连接
2. 消息处理管道（解密 → 去重 → 分类 → 路由）
3. 自动回复引擎（关键词 → AI → 默认）
4. 自动发货引擎（卡券匹配 → 规则检查 → 发送）
5. 通过 gRPC 与 Java 平台层通信
"""
import os
from fastapi import FastAPI

app = FastAPI(title="闲鱼 WebSocket 服务", version="2.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "websocket"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("WEBSOCKET_PORT", "8090")))