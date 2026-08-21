# 问题诊断报告：自动发货失败 & AI 回复无响应

- 诊断日期：2026-08-16
- 部署版本：c5d969f（本地=远端，0 落后）
- 运行环境：v3.yaml 部署（backend-web:8089 / websocket:8090 / scheduler:8091 / frontend:9000），全部 healthy
- 账号：2221611389164（唯一账号）

---

## 一、自动发货失败（需手动发货）

### 1.1 现象

- 8/16 12:36:36 数据库出现新失败订单：
  - `3316370378122057871`（item 1064188441063，已绑定卡券）→ `refunded`，fail_reason=`订单状态节点解析失败`（**这是今天 11:58:34 的新订单**，买家随后退款，属真实损失案例）
  - `3316352631154063984`（item 1068790350644）→ `refunded`，fail_reason=`未找到匹配的卡券`
- 用户反馈：依然发货失败，需要手动发货。

### 1.2 根因（今天新订单实测链路，scheduler.log + websocket.log）

11:59:09 补发货处理订单 3316370378122057871：

1. **check_can_ship 通过**（"订单已付款，可以发货"）。
2. **代码 Bug（红色警告）**：`scheduler/app/services/scheduler/redelivery_task.py:485` 调用
   `checker._parse_order_detail_response(order_no, raw_detail)`，
   但该方法定义在 `OrderStatusChecker` 的**兄弟类** `OrderDetailService` 上
   （`common/services/order_service.py:1593` 定义类，`:1858` 定义方法），
   `OrderStatusChecker`（`:1963`）**没有该方法** →
   `AttributeError: 'OrderStatusChecker' object has no attribute '_parse_order_detail_response'`，
   订单规格补全失败（此步仅警告，未阻断流程）。
   - 该 Bug 上游同样存在（git log 最近的 redelivery_task 提交 8f66a06/89abcad 均未修复）。
3. **致命点——创建会话失败**：订单缺 `chat_id` → scheduler 调 websocket 内部 API 创建会话
   → 闲鱼 API 响应 **`code: 400`，无 cid**（websocket.log:748295，请求
   `/r/SingleChatConversation/create`）→ 写入占位 `FAILED_2220591057178` chat_id。
4. **后续死循环**：11:59:17 ~ 12:00:45 每 5 秒重试，全部因"会话创建失败（占位ID），跳过发货"
   直接跳过（`xy_scheduled_redelivery_log` 共 15 条 failed 记录）。
5. 12:00:52 起 fail_reason 变为"订单状态节点解析失败"——买家已退款，check_can_ship 再查
   订单详情时 API 响应无 orderStatusVO 组件（`_extract_order_status_nodes` 返回 None）。

### 1.3 卡券链路复核（用户确认 + 数据库证据）

**卡券匹配与关联本身工作正常，不是本次故障原因：**
- `1064188441063`（lora炼丹）关联卡券 id=3，且有大量成功先例：
  `delivery_method=auto` 的订单中 `shipped` 717 单、`completed` 157 单、`refunded` 12 单、
  `refunding` 19 单（近几笔成功单：8/12 多笔 1071703906627 → shipped 且 delivery_content 非空）。
- 数据库复核 `xy_card_item_relations`（23 条）确认各商品与卡券关联齐全；
  之前报告"1064188441063 已绑定卡券"属实，今天 11:58 新订单（1064188441063）失败原因
  **不是卡券问题**。
- 唯一的例外：`1068790350644`（订单 3316352631154063984，fail_reason="未找到匹配的卡券"）
  在关联表中**确实无任何绑定**——但用户表示该商品应已关联/有可匹配卡券，
  需要在前端"商品-卡券绑定"页核对 1068790350644（此单为 8/11 下单，与 8/16 故障非同一单）。

**结论：用户反馈成立——退款是因为系统未发货（发货链路失败），而非卡券缺失。**

### 1.4 建议修复（待用户决策，本次未改动代码）

1. 修 `redelivery_task.py:485`：改用 `OrderDetailService`（含 `_parse_order_detail_response`）
   或捕获 AttributeError 直接跳过规格补全（规格不影响发货成功与否）。
2. 创建会话 code 400 需单独排查：可能是买家侧风控/账号被限，也可能是 token 问题；
   可改为重试机制或暴露手动创建会话入口。
3. 核对前端"商品-卡券绑定"页中 `1068790350644` 的关联状态（数据库中无绑定记录）。

---

## 二、AI 回复没有

### 2.1 配置状态（已生效）

`xy_accounts.metadata.ai_reply_settings`：
- `ai_enabled=true`，`provider_type=openai_compatible`
- `base_url=https://llm-b128191lrqvvmumf.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`（阿里云百炼）
- `model_name=qwen3.7-plus`，`api_key=sk-ws-***`（昨晚手动提供的 token 已正确写入）
- 自定义 prompts 已配置

### 2.2 根因

**账号开启了 `ai_reply_block_ordered_users=1`（已下单用户禁止 AI 回复）**：
- `websocket/app/services/xianyu/auto_reply_service.py:1802`：
  `用户 xxx 已下单，跳过AI回复（ai_reply_block_ordered_users=True）`
- 失败的买家（2220591057178）正是已下单用户，因此 AI 一律不回复。
- 这也是 xy_ai_chat_messages 最后一条记录停在 8/12 的原因（AI 配置之后才打开，
  且 8/12 之后大部分消息来自已下单用户）。

### 2.3 建议

- 若希望已下单用户也走 AI 回复，把该开关改为 0（前端账号设置页）。
- 若担心已下单用户售后话术，AI prompts 中已内置售后话术规范（问原因→声明虚拟特性→引导确认），
  可按需调整。

---

## 三、附加发现（与故障相关但非直接原因）

### 3.1 主 Token 已过期且无法自动刷新

- `xy_token_cache` id=130（user_id=2221611389164）：expire_at `2026-08-16 05:55:46`（已过期）
- id=131（user_id=chat_2221611389164，聊天侧）：expire_at `2026-08-16 17:50:15`（仍有效）
- **聊天 token 有效 → 在线聊天正常；主 token 过期 → 发货/订单 API 受影响**
- 系统设置 `captcha.local_slider_disabled=true`（"本机滑块不处理已开启"），
  且 `captcha.slider_mode=browser`、`captcha.local_slider_disabled` 导致自动刷新无法过滑块，
  日志每 3 分钟一次：`本机滑块不处理已开启，暂时使用已过期Token缓存尝试连接`
- 8/16 05:54:20 用户手动过滑块（solve_captcha），05:55:03 仍返回
  `FAIL_SYS_USER_VALIDATE`（"哎哟喂,被挤爆啦,请稍后重试"）→ 主 token 未能刷新。
- 建议：改 `captcha.local_slider_disabled=false` 或联系作者排查滑块；并确认昨晚手动
  提供的 token 是否写到了正确的 user_id 行（主 token 与 chat token 是两行）。

### 3.2 定时更新历史

- 8/12、8/13、8/14 凌晨自动更新连续失败（pull 冲突/fetch 失败），8/14 实际运行旧版 5d690ac；
- 8/15 03:00 起恢复（"代码已是最新 c5d969fb"），8/16 03:00 正常。

---

## 四、结论一句话

**发货失败 = ①创建会话闲鱼返回 code 400（占位 chat_id 导致永久跳过发货）为主因，②redelivery_task 调错类方法为辅因；卡券匹配/关联正常（717 shipped 成功先例），退款系因系统未发货；AI 无回复 = ai_reply_block_ordered_users 开关拦截了已下单用户，配置本身正常。**
