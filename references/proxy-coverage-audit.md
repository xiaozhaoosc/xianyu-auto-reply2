# 代理覆盖审计（2026-06-15 更新）

## 架构

代理通过三层注入：
1. **WebSocket 连接** — `connection_manager.py` 使用 `python_socks.Proxy` 创建代理 socket
2. **主 HTTP Session** — `xianyu_async.py:create_session()` 使用 `aiohttp_socks.ProxyConnector`
3. **散落的 HTTP 调用** — 通过 `common/utils/proxy_connector.py` 共享工具

### 共享代理工具：`common/utils/proxy_connector.py`

提供两个工厂函数：
- `create_aiohttp_session()` — 创建带代理的 aiohttp ClientSession（用于 aiohttp 调用）
- `get_httpx_proxy()` — 返回 httpx 兼容的代理 URL 字符串（用于 httpx 调用）

两者共享同一缓存（5分钟TTL），从 `xy_system_settings` 表读取 `proxy.enabled` + `proxy.api_url`。

## ✅ 使用代理的接口（全部已覆盖）

### aiohttp 路径（`create_aiohttp_session()`）

| 功能 | 文件 | 说明 |
|------|------|------|
| 主 HTTP Session | `xianyu_async.py:create_session()` | `_build_session_connector()` |
| Token 刷新 | `cookie_token_manager.py` | `create_aiohttp_session()` |
| 评价提交 | `rate_service.py` | `create_aiohttp_session()` |
| 订单详情(发货) | `auto_delivery_handler.py` | `create_aiohttp_session()` |
| 评价列表 | `auto_delivery_handler.py` | `create_aiohttp_session()` |
| 卖家关闭订单 | `auto_delivery_handler.py` | `create_aiohttp_session()` |
| 卡券 API 调用 | `auto_delivery_handler.py` | `create_aiohttp_session()` |
| 订单列表 | `order_service.py` | `create_aiohttp_session()` |
| 订单详情(查询) | `order_service.py` | `create_aiohttp_session()` |
| 图片下载 | `xianyu_async.py` | `create_aiohttp_session()` |
| 买家信用检查 | `buyer_credit_rule.py` | `create_aiohttp_session()` |
| 头像查询 | `avatar_service.py` | `create_aiohttp_session()` |
| 黑名单查询 | `official_blacklist_service.py` | `create_aiohttp_session()` |
| IM Token 获取 | `im_client.py` | `create_aiohttp_session()` |
| 数据分析 | `data_analysis_service.py` | `create_aiohttp_session()` |
| 通知(钉钉/飞书/Bark/Webhook/微信/Telegram) | `notification_utils.py` (6处) | `create_aiohttp_session()` |
| 淘宝联盟 | `taobao_alliance_service.py` | `create_aiohttp_session()` |
| 商品删除 | `item_delete_api_service.py` | `create_aiohttp_session()` |
| 擦亮/小红花/登录续期 | `polish_task.py`, `red_flower_task.py`, `login_renew_task.py` | `create_aiohttp_session()` |
| 关闭通知 | `xianyu_utils.py` | `create_aiohttp_session()` |
| 昵称查询 | `fish_nick_utils.py` | `create_aiohttp_session()` |
| 卡券内容获取 | `card_delivery_content.py` | `create_aiohttp_session()` |
| 亦凡发货 API | `yifan_api_handler.py` | `ProxyConnector` |

### httpx 路径（`get_httpx_proxy()`）

| 功能 | 文件 | 说明 |
|------|------|------|
| QR 登录 | `qr_login/manager.py` | `_ensure_proxy()` → `proxy=self.proxy`（4处 httpx 调用） |
| 极验 CAPTCHA | `geetest/geetest_lib.py` | `_get_proxy()` → `proxy=proxy`（2处 httpx 调用） |
| 卡券 API 发货 | `card_service.py:_call_card_api()` | 直接调用 `get_httpx_proxy()` |

### WebSocket 路径

| 功能 | 文件 | 说明 |
|------|------|------|
| WebSocket 长连接 | `connection_manager.py` | `python_socks.Proxy` |

## 不需要代理的 httpx 调用（内部/外部 AI）

| 功能 | 文件 | 原因 |
|------|------|------|
| 密码登录代理 | `password_login.py` | 内部 Docker→WebSocket 服务调用 |
| Cookie 刷新代理 | `cookie_refresh.py` | 内部 Docker→WebSocket 服务调用 |
| AI 回复引擎 | `ai_reply_engine.py` | 调用 OpenAI/Claude 等 AI API（非闲鱼） |
| AI Provider | `ai_provider_service.py` | 调用 AI API（非闲鱼） |
| 版本检查 | `version_service.py` | 调用 GitHub API |
| 飞书同步脚本 | `scripts/sync_to_feishu.py` | 运维脚本，非运行时 |
| 支付宝 | `alipay_service.py` | 支付网关，非闲鱼 |
| 同步 cookie_refresh | `common/utils/cookie_refresh.py` | 内部 Docker→WebSocket 服务调用 |

## 修改文件清单

### 2026-06-14 首次覆盖（35处 aiohttp 调用）
- 新增 `common/utils/proxy_connector.py`
- 修改 19 个文件替换裸 `aiohttp.ClientSession()`

### 2026-06-15 扩展 httpx 覆盖
- **`common/utils/proxy_connector.py`** — 新增 `get_httpx_proxy()` 函数
- **`qr_login/manager.py`** — 新增 `_ensure_proxy()` 方法，在 `generate_qr_code()` 入口调用
- **`geetest/geetest_lib.py`** — 新增 `_get_proxy()` 方法，2处 httpx 调用添加 `proxy` 参数
- **`card_service.py`** — `_call_card_api()` 添加 `get_httpx_proxy()` 调用
