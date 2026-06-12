# 闲鱼智能运营平台 v2.0 — Python 运行时引擎

> 本目录保留现有 Python 核心能力，作为不可变的运行时组件存在。

## 目录结构

```
python-runtime/
├── websocket_service/    # 闲鱼 WebSocket 连接 + 消息处理 + AI 回复 + 自动发货
│   ├── main.py
│   ├── app/
│   │   ├── services/
│   │   │   ├── xianyu_async.py       # 闲鱼连接
│   │   │   ├── auto_reply_service.py # 自动回复
│   │   │   ├── auto_delivery_handler.py # 自动发货
│   │   │   ├── ai_reply_engine.py    # AI 引擎
│   │   │   └── captcha_handler.py    # 验证码处理
│   │   └── grpc/
│   │       └── grpc_client.py        # gRPC 客户端（替代直连 DB）
│   └── proto/                        # Proto 编译输出
│
└── playwright_service/   # Playwright 浏览器自动化
    └── browser_worker.py             # 登录、Cookie 刷新、商品发布
```

## 集成要点

- **读取规则**：通过 gRPC 从 Java 平台层获取关键词规则、AI 设置、发货规则
- **写入日志**：通过 gRPC 向 Java 平台层写入回复日志、发货日志、AI 聊天记录
- **高频读取**：走 Redis 缓存（规则、配置），降低 gRPC 调用频率
- **Playwright**：保留不变，继续使用现有 Playwright 脚本