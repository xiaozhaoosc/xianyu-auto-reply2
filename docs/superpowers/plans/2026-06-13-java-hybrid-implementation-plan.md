# 闲鱼平台化 — Java 混合架构实施计划

> 分支：`dv_java` | 新目录：`vr_java_python/` | 模式：无人值守静默执行

## Phase 0: 基础设施准备

### Task 0.1: 创建 dv_java 分支
- 创建 `dv_java` 分支
- 创建 `vr_java_python/` 目录
- 创建 `docs/superpowers/plans/` 目录

### Task 0.2: 初始化 Java 平台项目骨架
- 创建 Maven 多模块父 POM（vr_java_python/java-platform/pom.xml）
- 创建 6 个子模块：platform-common, platform-server, platform-scheduler, platform-promotion, platform-rules, platform-grpc
- 配置依赖：Spring Boot 3.5.x, MyBatis-Plus 3.5.15, Sa-Token 1.40.0, JobRunr 7.x, Drools 9.x, gRPC 1.68+

### Task 0.3: 创建 platform-common 模块
- 配置 application.yml
- 创建基础包结构：entity/, dto/, vo/, enums/, exception/, util/
- 添加 Flyway 配置

### Task 0.4: 创建 platform-server 模块
- 创建 Spring Boot 启动类
- 配置 Sa-Token 认证
- 创建全局异常处理
- 添加 /health 端点

### Task 0.5: 创建 platform-scheduler 模块
- 创建 Spring Boot 启动类
- 集成 JobRunr（application.yml 配置 + @Recurring 示例）
- 添加 /health 端点

### Task 0.6: 创建 platform-grpc 模块
- 创建 gRPC Server 配置
- 编写 account.proto、rule.proto、message.proto、delivery.proto

### Task 0.7: 创建 python-runtime 目录
- 创建 python-runtime/ 目录结构
- 复制现有 websocket/ 核心代码到 python-runtime/

### Task 0.8: 提交并推送
- git add + commit
- git push origin dv_java

## Phase 1: 数据模型迁移

### Task 1.1: 核心表 Entity（P0，10 张表）
- xy_users, xy_accounts, xy_catalog_items, xy_cards, xy_card_item_relations
- xy_keyword_rules, xy_delivery_block_rules, xy_ai_settings, xy_orders, xy_default_replies

### Task 1.2: 业务表 Entity（P1，15 张表）
- xy_messages, xy_auto_reply_message_logs, xy_delivery_logs, xy_rate_logs, xy_red_flower_logs
- xy_ai_chat_messages, xy_account_login_logs, xy_dock_records, xy_agent_orders
- xy_blacklist, xy_auto_rate_configs, xy_notifications, xy_ai_presets
- xy_webhook_configs, xy_item_polish_logs

### Task 1.3: 其他表 Entity（P2，约 29 张表）
- 剩余返佣表 fy_* 前缀

### Task 1.4: 数据库迁移脚本
- Flyway V1__init_schema.sql

## Phase 2-7: 后续阶段（逐步展开）