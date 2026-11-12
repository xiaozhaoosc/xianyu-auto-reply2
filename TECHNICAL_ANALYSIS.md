# 闲鱼自动回复系统 — 技术分析报告

> 分析日期: 2026-06-11  
> 项目: xianyu-auto-reply (AGPL-3.0)

---

## 1. 项目结构

```
xianyu-auto-reply/
├── backend-web/          # FastAPI API 服务 (:8089)
│   ├── app/
│   │   ├── api/routes/   # 55+ 路由文件
│   │   ├── core/         # config, security, http_client
│   │   └── services/     # 40+ 业务服务
│   ├── _bootstrap.py     # 实际启动逻辑
│   ├── main.py           # 最小入口桩
│   ├── Dockerfile
│   └── pyproject.toml
├── websocket/            # 闲鱼 WebSocket 消息服务 (:8090)
│   ├── app/
│   │   ├── api/routes/   # 内部API + Cookie刷新 + 密码登录
│   │   ├── services/
│   │   │   ├── xianyu/   # 核心: auto_reply, ai_reply, delivery, connection, notification
│   │   │   ├── captcha/  # 滑块验证码处理
│   │   │   └── shipping/ # 发货服务
│   │   └── websocket/    # 前端 WebSocket 管理器
│   ├── _bootstrap.py
│   ├── main.py
│   ├── Dockerfile
│   └── pyproject.toml
├── scheduler/            # 定时任务服务 (:8091)
│   ├── app/
│   │   ├── api/routes/   # 内部API
│   │   └── services/
│   │       └── scheduler/ # 15个定时任务
│   ├── _bootstrap.py
│   ├── main.py
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/             # React SPA (:9000)
│   ├── src/
│   │   ├── pages/        # 40+ 页面组件
│   │   ├── components/   # layout + common
│   │   ├── config/       # navigation.ts
│   │   ├── store/        # Zustand stores
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
├── common/               # 共享代码库
│   ├── models/           # 57 个 SQLAlchemy 模型
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # 共享业务逻辑
│   ├── utils/            # 工具函数
│   ├── db/               # 数据库连接/初始化/Redis
│   └── core/             # 基础配置
├── launcher/             # Windows 桌面启动器 (Nuitka EXE)
├── promotion/            # 返佣子系统 (独立, 不在主 compose)
│   ├── backend/          # (:8092)
│   └── frontend/         # (:9001)
├── docker-compose.yml    # 主系统 4 服务编排
├── docker-compose-cn.yml # 国内镜像版
├── xianyu_schema.sql     # 完整数据库 Schema (54 表)
├── global_config.yml     # 全局配置 (API endpoints, headers, websocket URL)
├── deploy.sh / update.sh / build.sh
├── nginx/nginx.conf
└── README.md
```

**关键配置文件:**
- `.env` — 环境变量 (MySQL/Redis/端口/JWT)
- `global_config.yml` — 闲鱼 API 端点、WebSocket URL、默认 Headers
- `docker-compose.yml` — 4 服务 + 外部 MySQL/Redis
- 各服务 `pyproject.toml` — Python 依赖管理

---

## 2. 系统架构

### 2.1 服务间交互

```
┌──────────┐     HTTP      ┌──────────────┐     WebSocket      ┌──────────────┐
│ Frontend ├──────────────►│ Backend-Web  │◄───────────────────│  Scheduler   │
│  (:9000) │  REST API     │   (:8089)    │   定时任务触发      │   (:8091)    │
└──────────┘               └──────┬───────┘                    └──────┬───────┘
                                  │ HTTP                              │ HTTP
                                  ▼                                   ▼
                           ┌──────────────┐                    ┌──────────────┐
                           │  WebSocket   │◄───────────────────│  Scheduler   │
                           │   (:8090)    │   任务委托          │   (:8091)    │
                           └──────┬───────┘                    └──────────────┘
                                  │ WebSocket
                                  ▼
                           ┌──────────────┐
                           │ Goofish/     │
                           │ DingTalk WS  │
                           │ (wss://)     │
                           └──────────────┘
```

**Docker 依赖链:** `mysql/redis → backend-web → websocket → scheduler; frontend → backend-web`

**服务职责:**
| 服务 | 端口 | 职责 |
|------|------|------|
| `frontend` | 9000 | React SPA, 用户界面 |
| `backend-web` | 8089 | API 网关, 业务接口, JWT 认证 |
| `websocket` | 8090 | 闲鱼 WebSocket 连接, 消息收发, 自动回复, 自动发货, AI 引擎 |
| `scheduler` | 8091 | 定时任务: 补发货, 补评价, Cookie 刷新, 擦亮, 订单拉取, DB 备份 |

### 2.2 技术栈

| 层 | 技术 |
|---|------|
| 后端框架 | **FastAPI** (Python 3.11+) |
| ORM | **SQLAlchemy 2.0** (async) |
| 数据库 | **MySQL 8.0** (InnoDB, utf8mb4) |
| 缓存 | **Redis 7** (缓存, 分布式锁, 会话) |
| 前端 | **React 18 + TypeScript + Vite** |
| UI | **TailwindCSS + Lucide React + Framer Motion** |
| 状态管理 | **Zustand** |
| 浏览器自动化 | **Playwright** (登录, Cookie 刷新, 发布) |
| 定时任务 | **APScheduler** |
| 日志 | **Loguru** |
| 部署 | **Docker Compose + Nginx** |

### 2.3 数据库 Schema

**54 张表**, 全部使用 `xy_` 前缀, 无外键约束 (关系由代码维护). 关键表:

| 分组 | 表 |
|------|-----|
| 用户/认证 | `xy_users`, `xy_user_settings`, `xy_system_settings`, `xy_token_cache` |
| 账号管理 | `xy_accounts`, `xy_account_login_logs`, `xy_cookie_refresh_schedules` |
| 消息/回复 | `xy_keyword_rules`, `xy_default_replies`, `xy_default_reply_records`, `xy_message_filters`, `xy_auto_reply_message_logs`, `xy_ai_chat_messages` |
| 发货/订单 | `xy_orders`, `xy_cards`, `xy_card_item_relations`, `xy_delivery_block_rules`, `xy_confirm_receipt_messages` |
| 通知 | `xy_notification_channels`, `xy_message_notifications` |
| 分销 | `xy_dock_records`, `xy_dock_code_bindings`, `xy_agent_orders`, `xy_settlement_records`, `xy_fund_flows` |
| 商品 | `xy_catalog_items`, `xy_product_materials`, `xy_publish_addresses`, `xy_publish_logs` |
| 采集 | `xy_goofish_crawl_jobs`, `xy_goofish_crawl_items` |
| 定时任务 | `xy_scheduled_tasks`, `xy_scheduled_redelivery_log`, `xy_scheduled_rate_log`, `xy_scheduled_polish_log`, 等 |
| 黑名单 | `xy_personal_blacklist`, `xy_platform_blacklist` |
| 返佣 (fy_) | `fy_accounts`, `fy_materials`, `fy_product_rules`, `fy_publish_rules`, `fy_delete_rules` |

---

## 3. Backend-Web (API 服务)

### 3.1 路由模块 (55+ 路由文件)

| 路由文件 | 功能 |
|----------|------|
| `auth.py` | 登录/注册/登出/JWT 令牌验证 |
| `ai.py` | AI 设置管理, 模型列表, 连接测试 |
| `auto_reply_logs.py` | 自动回复日志查询 |
| `blacklist.py` | 个人/平台黑名单 CRUD |
| `cards.py` | 卡券管理 |
| `chat_new.py` / `chat_new_ws.py` | 在线聊天 (REST + WebSocket) |
| `cookies.py` / `cookie_refresh.py` | Cookie 管理与续期 |
| `default_replies.py` | 默认回复配置 |
| `distribution.py` | 分销管理 (货源/对接/代理订单) |
| `goofish_crawler.py` / `goofish_tasks.py` | Goofish 商品采集 |
| `items.py` | 商品目录管理 |
| `keywords.py` | 关键词规则 CRUD |
| `message_filters.py` | 消息过滤规则 |
| `notifications.py` | 通知渠道管理 |
| `orders.py` | 订单管理 |
| `product_publish.py` | 商品发布 (单品/批量) |
| `qr_login.py` / `qrcode.py` | 扫码登录 |
| `search.py` | 商品搜索 |
| `system_settings.py` | 系统设置 |
| `users.py` | 用户管理 (管理员) |

### 3.2 认证系统

- **JWT 认证**: HS256, 访问令牌 1440 分钟, 刷新令牌 10080 分钟
- **JWT 密钥**: 数据库托管, 首次启动自动生成强随机密钥持久化到 `xy_system_settings`
- **密码**: bcrypt 哈希存储
- **登录方式**: 用户名+密码, 邮箱+密码, 支持极验滑动验证码
- **角色**: ADMIN / OPERATOR / MEMBER
- **登录保护**: 失败次数计数, 账号锁定机制
- **统一响应**: 所有 API 返回 HTTP 200, 业务状态由 `success` + `code` 字段区分

### 3.3 服务层 (40+ 服务)

核心服务: `account_service`, `ai_reply_service`, `card_service`, `keyword_service`, `order_service`, `notification_service`, `product_publish_service`, `websocket_client` (调用 websocket 服务), `settlement_service`, `goofish_crawler`

---

## 4. WebSocket 服务 (核心引擎)

这是系统最核心的服务, 负责与闲鱼平台的实时通信.

### 4.1 核心类 `XianyuAsync` (2703 行)

单例模式管理每个闲鱼账号的 WebSocket 连接生命周期:

```
XianyuAsync
├── ConnectionManager  — 连接状态/心跳/重连
├── TokenManager       — IM Token 获取/刷新
├── MessageHandler     — 消息解析/去重/防抖/分发
├── AutoReplyService   — 自动回复引擎 (1882 行)
├── AIReplyEngine      — AI 回复引擎 (996 行)
├── AutoDeliveryHandler — 自动发货 (3176 行)
├── NotificationManager — 通知管理
└── ResourceManager    — 暂停/恢复控制
```

### 4.2 消息处理流程 (MessageHandler, 644 行)

```
闲鱼 WebSocket 消息
    │
    ▼
消息解密 (common.utils.xianyu_utils.decrypt)
    │
    ▼
消息分类判断
    ├── 卡片更新消息 (付款状态变更) → 触发自动发货
    ├── 卡片消息 (小刀等) → 卡片回调
    ├── 聊天消息 → 聊天回调 → AutoReplyService
    ├── 订单消息 → 订单回调
    └── 系统消息 → 系统回调
```

**消息去重**: 基于 message_id 的字典缓存, 可配置过期时间 (默认 3600 秒)  
**消息防抖**: 3 秒延迟, 同一聊天的多条消息合并处理

### 4.3 自动回复引擎 (AutoReplyService, 1882 行)

处理优先级 (从高到低):

1. **系统消息过滤** — 跳过不需要回复的系统消息 (约 20 种预定义)
2. **消息过滤规则** — `xy_message_filters` 表配置的过滤关键词
3. **暂停状态检查** — 账号暂停期间不回复
4. **消息去重** — 相同消息等待时间内不重复回复
5. **关键词匹配** — `xy_keyword_rules` 表, 支持:
   - 商品 ID 优先匹配 (商品专属回复 > 通用回复)
   - 文本/图片类型回复
   - 优先级排序
6. **AI 回复** — 如果启用 AI, 调用 AIReplyEngine
7. **默认回复** — `xy_default_replies` 表, 支持:
   - 只回复一次 (记录已回复用户)
   - API 回调获取回复内容
   - 商品专属默认回复

**变量替换**: 回复内容支持 `{send_user_name}`, `{item_title}` 等变量

### 4.4 AI 回复引擎 (AIReplyEngine, 996 行)

**支持的 AI 服务商:**
- OpenAI 兼容 API (包括 DashScope/通义千问)
- Anthropic Claude
- Google Gemini
- DashScope 应用模式

**意图识别**: 基于本地关键词检测, 分为:
- `price` — 议价意图 (包含"便宜","优惠","少点"等)
- `tech` — 技术问题
- `default` — 默认

**对话上下文**: 存储在 `xy_ai_chat_messages` 表, 按 chat_id + cookie_id 管理

**议价策略**: 系统提示词内置递减优惠策略:
- 第 1 次: 小幅优惠
- 第 2 次: 中等优惠
- 第 3 次: 最大优惠 (底线)
- 支持配置最大议价轮数、最大优惠百分比/金额

**并发控制**: 每个聊天会话独立的 asyncio.Lock, 防止并发回复冲突

### 4.5 自动发货 (AutoDeliveryHandler, 3176 行)

**发货触发条件:**
- 买家付款后卡片更新消息
- 订单消息中的"待发货"状态

**发货内容类型 (卡券):**
- `text` — 固定文本内容
- `data` — 批量数据 (逐条发送)
- `image` — 图片 URL
- `api` — 调用外部 API 获取发货内容
- `yifan_api` — 亦凡 API 委托

**发货流程:**
```
订单付款 → 禁止发货规则检查 → 卡券匹配 → 获取发货内容
    → 延迟等待 → 发送消息 → 确认发货 → 记录日志
```

### 4.6 禁止发货规则引擎 (Delivery Rules)

基于策略模式的规则引擎, 支持优先级排序, 首条命中即停:

| 规则 | 说明 |
|------|------|
| `buyer_credit_rule` | 买家信用等级检查 |
| `buyer_has_order_rule` | 买家已有订单检查 |
| `buyer_unconfirmed_rule` | 买家未确认收货检查 |
| `personal_blacklist_rule` | 个人黑名单检查 |

规则配置存储在 `xy_delivery_block_rules` 表, 支持:
- 启用/禁用
- 优先级排序
- 命中后自动关闭订单
- 排除特定商品

### 4.7 连接管理 (ConnectionManager, 398 行)

**状态机:**
```
DISCONNECTED → CONNECTING → CONNECTED → RECONNECTING → CONNECTED
                            ↓
                       FAILED / CLOSED
```

**重连策略:**
- 认证失败: 最多 5 次后停止
- 网络失败: 最多 20 次后停止 (更宽松)
- 短连接频繁断开检测: 5 分钟内 5 次 < 30 秒的连接触发告警

**心跳:** 15 秒间隔, 30 秒超时

### 4.8 通知管理 (NotificationManager)

支持 7 种通知渠道:
- 钉钉机器人
- 飞书机器人
- Bark 推送
- 邮件
- Webhook
- 微信推送
- Telegram

**防重复**: 同一账号 5 分钟冷却期

---

## 5. Scheduler 服务 (定时任务)

### 5.1 任务列表 (15 个定时任务)

| 任务代码 | 功能 | 默认间隔 |
|----------|------|----------|
| `redelivery` | 定时补发货 | 5 分钟 |
| `rate` | 定时补评价 | 20 分钟 |
| `polish` | 商品自动擦亮 | 可配置 |
| `day_switch` | 日切换任务 | 每日 |
| `cleanup_browser_data` | 清理浏览器数据 | 可配置 |
| `fetch_orders` | 拉取订单 | 可配置 |
| `fetch_pending_orders` | 拉取待处理订单 | 可配置 |
| `fetch_items` | 拉取商品列表 | 可配置 |
| `login_renew` | 登录续期 | 可配置 |
| `cookies_refresh` | Cookie 浏览器刷新 | 可配置 |
| `api_cookie_renew` | Cookie 接口续期 | 可配置 |
| `close_notice` | 关闭通知 | 可配置 |
| `red_flower` | 求小红花 | 可配置 |
| `db_backup` | 数据库备份 | 可配置 |

**任务配置**: 存储在 `xy_scheduled_tasks` 表, 支持动态启停和间隔调整

**任务日志**: 每个任务类型有独立的日志表 (`xy_scheduled_*_log`), 记录批次 ID、账号、状态、错误信息

---

## 6. Frontend

### 6.1 技术栈

- **React 18 + TypeScript** — 组件化 SPA
- **Vite** — 构建工具
- **TailwindCSS** — 原子化 CSS
- **Zustand** — 轻量状态管理
- **React Router** — 路由
- **Framer Motion** — 动画
- **Lucide React** — 图标

### 6.2 页面结构 (40+ 页面)

**主菜单:**
| 页面 | 路径 |
|------|------|
| 仪表盘 | `/dashboard` |
| 数据分析 | `/data-analysis/overview` |
| 账号管理 | `/accounts` |
| 在线聊天 | `/online-chat-new` |
| 商品管理 | `/items` |
| 商品搜索/采集 | `/item-search` |
| 定时采集 | `/goofish-scheduled-crawler` |
| 卡券管理 | `/cards` |
| 订单管理 | `/orders` |
| 分销管理 | `/distribution/*` (6 子页面) |
| 商品发布 | `/product-publish/*` (5 子页面) |
| 自动回复 | `/keywords` |
| 消息日志 | `/message-logs` |
| 风控日志 | `/risk-logs` |
| 消息过滤 | `/message-filters` |
| 通知渠道 | `/notification-channels` |
| 消息通知 | `/message-notifications` |
| 黑名单 | `/blacklist` |
| 个人设置 | `/personal-settings` |

**管理员菜单:**
| 页面 | 路径 |
|------|------|
| 系统设置 | `/settings` |
| 用户管理 | `/admin/users` |
| 定时任务 | `/admin/scheduled-tasks` |
| 公告管理 | `/admin/announcements` |
| 广告管理 | `/admin/ad-manage` |
| 资金流水 | `/admin/fund-flows` |
| 日志管理 | `/admin/*` (11 子页面) |

---

## 7. 核心数据流

### 7.1 消息 → 自动回复完整流程

```
1. XianyuAsync.main() 建立 WebSocket 连接到 wss://wss-goofish.dingtalk.com/
2. 通过 TokenManager 获取 IM Token
3. WebSocket 收到加密消息
4. MessageHandler 解密消息 (xianyu_utils.decrypt)
5. MessageHandler 分类:
   - 聊天消息 → 去重 → 防抖 → AutoReplyService.process_message()
6. AutoReplyService 处理链:
   a. 跳过系统消息
   b. 检查消息过滤规则 (xy_message_filters)
   c. 检查暂停状态
   d. 消息去重 (xy_accounts.message_expire_time)
   e. 关键词匹配 (xy_keyword_rules):
      - 先查商品专属规则 (item_id 匹配)
      - 再查通用规则
      - 支持文本/图片回复
   f. 若无关键词命中, 检查 AI 是否启用:
      - AIReplyEngine 意图检测 (本地关键词)
      - 构建对话上下文 (xy_ai_chat_messages)
      - 调用 AI API (OpenAI/Claude/Gemini/DashScope)
      - 保存对话记录
   g. 若 AI 未启用, 使用默认回复 (xy_default_replies)
7. 回复内容变量替换 ({send_user_name}, {item_title}...)
8. 通过 WebSocket 发送回复消息
9. 记录到 xy_auto_reply_message_logs
10. 触发消息通知 (钉钉/飞书/邮件等)
```

### 7.2 订单 → 自动发货流程

```
1. WebSocket 收到卡片更新消息 (买家付款)
2. MessageHandler 识别为卡片更新消息
3. 提取订单信息 (订单号, 商品ID, 买家ID)
4. AutoDeliveryHandler 处理:
   a. 禁止发货规则引擎检查:
      - 加载 xy_delivery_block_rules (按优先级)
      - 依次检查: 信用/已有订单/未确认/黑名单
      - 命中则阻止发货 (可选自动关闭订单)
   b. 卡券匹配 (xy_card_item_relations):
      - 查找商品关联的可用卡券
      - 支持自有卡券 + 对接卡券
   c. 获取发货内容:
      - text: 直接使用卡券文本
      - data: 逐条发送数据
      - image: 发送图片
      - api: 调用外部 API
      - yifan_api: 委托亦凡 API
   d. 延迟等待 (xy_cards.delay_seconds)
   e. 发送发货消息
   f. 确认发货 (xy_accounts.confirm_before_send)
   g. 记录到 xy_orders
```

---

## 8. 配置系统

### 8.1 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MYSQL_HOST/PORT/USER/PASSWORD/DATABASE` | MySQL 连接 | - |
| `REDIS_HOST/PORT/PASSWORD/DB` | Redis 连接 | - |
| `BACKEND_WEB_PORT` | API 端口 | 8089 |
| `WEBSOCKET_PORT` | WS 端口 | 8090 |
| `SCHEDULER_PORT` | 调度端口 | 8091 |
| `WEBSOCKET_SERVICE_URL` | WS 服务地址 | http://websocket:8090 |
| `SCHEDULER_SERVICE_URL` | 调度服务地址 | http://scheduler:8091 |
| `BACKEND_WEB_SERVICE_URL` | API 服务地址 | http://backend-web:8089 |
| `BROWSER_HEADLESS` | Playwright 无头模式 | true |
| `CORS_ORIGINS` | CORS 白名单 | * |
| `LOG_LEVEL` | 日志级别 | INFO |
| `SQL_ECHO` | SQL 日志 | true |

### 8.2 系统设置 (数据库)

`xy_system_settings` 表存储运行时可调配置:
- `jwt_secret_key` — JWT 密钥 (自动生成)
- `login_captcha_enabled` — 登录验证码开关
- AI 相关设置 (模型/API Key/服务商类型等)

### 8.3 用户设置

`xy_user_settings` 表存储用户级配置:
- 通知渠道配置
- 菜单可见性
- 导航隐藏键

---

## 9. 代码质量

### 9.1 代码规模

| 模块 | 关键文件行数 |
|------|-------------|
| `xianyu_async.py` | 2,703 行 |
| `auto_delivery_handler.py` | 3,176 行 |
| `auto_reply_service.py` | 1,882 行 |
| `ai_reply_engine.py` | 996 行 |
| `message_handler.py` | 644 行 |
| `connection_manager.py` | 398 行 |

### 9.2 测试

**无测试文件**. 项目中未发现任何 test/spec 文件. 这是主要的质量风险点.

### 9.3 文档

- **README.md**: 详细 (441 行), 包含功能概览、技术栈、快速开始、配置说明、安全建议
- **代码注释**: 中文 docstring 较完整, 每个模块有功能说明
- **API 文档**: FastAPI 自动生成 `/docs` (Swagger UI)
- **数据库 Schema**: 完整的 SQL 文件, 每个字段有中文注释

### 9.4 架构优点

- **微服务拆分合理**: API/消息/调度职责清晰分离
- **共享代码库 (common/)**: 模型/工具/服务复用
- **自动迁移**: 启动时自动建表、补齐缺失字段、初始化默认数据
- **JWT 密钥数据库托管**: 无需手动配置, 自动生成强随机密钥
- **多 AI 服务商支持**: 统一抽象层, 易于扩展
- **规则引擎**: 禁止发货规则支持优先级排序, 首条命中即停
- **完善的日志**: Loguru + 独立日志文件 + 数据库日志表
- **Docker 部署**: 完整的 compose 编排 + 健康检查

### 9.5 架构风险

- **无测试**: 零测试覆盖
- **大文件**: `auto_delivery_handler.py` (3176 行) 和 `xianyu_async.py` (2703 行) 过大
- **硬编码**: 部分系统消息列表硬编码在代码中 (如 `SYSTEM_MESSAGES_TO_SKIP`)
- **密码明文存储**: `xy_accounts.login_password` 使用 TEXT 类型存储 (虽有加密)
- **无外键约束**: 所有关系由代码维护, 数据一致性风险

---

## 10. 总结

这是一个功能完善的闲鱼自动化管理系统, 核心价值在于:

1. **多账号管理**: 支持多个闲鱼账号同时在线, Cookie 自动维护
2. **智能自动回复**: 关键词 + AI + 默认回复三级策略
3. **自动发货**: 支持卡券/虚拟商品, 禁止发货规则引擎
4. **分销体系**: 二级分销、代理订单、结算链路
5. **定时任务**: 15 个定时任务覆盖补发货/评价/擦亮/备份等
6. **多通知渠道**: 7 种推送渠道
7. **商品发布**: 素材库 + 批量发布 + 随机地址池

**关键数据流**: 闲鱼 WebSocket → 消息解密/分类 → 自动回复引擎 (关键词→AI→默认) → 回复发送 → 日志记录 → 通知推送
