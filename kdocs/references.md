# 闲鱼自动回复系统 — 参考资料与辅助文档索引

> 版本：v1.0 | 日期：2026-06-13 | 作者：架构组
>
> 本文档汇总平台化重构过程中所需的全部参考资料，包括现有代码分析、技术选型依据、框架文档、设计参考等。

---

## 目录

1. [现有项目代码分析](#1-现有项目代码分析)
2. [技术选型参考资料](#2-技术选型参考资料)
3. [框架与工具文档](#3-框架与工具文档)
4. [规则引擎设计参考](#4-规则引擎设计参考)
5. [gRPC 通信参考](#5-grpc-通信参考)
6. [多终端开发参考](#6-多终端开发参考)
7. [安全与合规参考](#7-安全与合规参考)
8. [部署与运维参考](#8-部署与运维参考)

---

## 1. 现有项目代码分析

### 1.1 项目结构速查

| 目录 | 说明 | 关键文件 |
|------|------|------|
| `websocket/` | 闲鱼实时连接与消息处理 | `main.py`, `xianyu_async.py`, `auto_reply_service.py`, `auto_delivery_handler.py` |
| `backend-web/` | API 网关与管理后台 | `main.py`, `items.py` |
| `scheduler/` | 定时任务调度 | `main.py`, `scheduler_service.py` |
| `promotion/` | 返佣子系统 | `backend/`, `frontend/` |
| `common/` | 共享代码库 | `models/`, `schemas/`, `db/`, `redis/` |
| `launcher/` | Windows 桌面启动器 | `main.py` (Nuitka 打包) |
| `scripts/` | CI/CD 脚本 | `Jenkinsfile`, 打包脚本 |

### 1.2 核心代码文件速查

| 文件 | 行数 | 职责 | 迁移策略 |
|------|:--:|------|------|
| `auto_delivery_handler.py` | 3,176 | 自动发货全流程 | 保留 Python |
| `xianyu_async.py` | 2,703 | 闲鱼 WebSocket 生命周期 | 保留 Python |
| `auto_reply_service.py` | 1,882 | 关键词匹配 + AI 回复 | 保留 Python |
| `ai_reply_engine.py` | 996 | AI 多模型调用 | 保留 Python |
| `message_handler.py` | 644 | 消息解密/分类/去重 | 保留 Python |
| `rule_engine.py` | 155 | 发货规则引擎 | 迁移到 Drools |
| `buyer_credit_rule.py` | 58 | 买家信用规则 | 迁移到 Drools |
| `buyer_has_order_rule.py` | 52 | 历史订单规则 | 迁移到 Drools |
| `buyer_unconfirmed_rule.py` | 59 | 未确认收货规则 | 迁移到 Drools |
| `personal_blacklist_rule.py` | 69 | 个人黑名单规则 | 迁移到 Drools |

### 1.3 定时任务清单

| 任务文件名 | 任务说明 | 迁移 |
|------|------|:--:|
| `cookies_refresh_task.py` | 通过 Playwright 刷新 Cookie | Quartz |
| `api_cookie_renew_task.py` | 通过 API 续期 Cookie | Quartz |
| `fetch_items_task.py` | 拉取闲鱼商品列表 | Quartz |
| `fetch_orders_task.py` | 拉取订单列表 | Quartz |
| `polish_task.py` | 商品自动擦亮 | Quartz |
| `rate_task.py` | 自动评价 | Quartz |
| `red_flower_task.py` | 自动求小红花 | Quartz |
| `redelivery_task.py` | 补发/重发 | Quartz |
| `close_notice_task.py` | 关闭订单通知 | Quartz |
| `day_switch_task.py` | 日切换处理 | Quartz |
| `db_backup_task.py` | 数据库备份 | Quartz |
| `cleanup_browser_data_task.py` | 清理浏览器数据 | Quartz |
| `login_renew_task.py` | 登录续期 | Quartz |

### 1.4 数据库表完整清单（54 张表）

#### 核心业务表（`xy_` 前缀，31 张）

| 序号 | 表名 | 说明 | 迁移 |
|:--:|------|------|:--:|
| 1 | `xy_users` | 系统用户表 | Java |
| 2 | `xy_activation_logs` | 激活码日志 | Java |
| 3 | `xy_advertisements` | 广告表 | Java |
| 4 | `xy_agent_orders` | 代理订单 | Java |
| 5 | `xy_ai_chat_messages` | AI 聊天消息 | Python（写） |
| 6 | `xy_announcements` | 公告 | Java |
| 7 | `xy_auto_rate_configs` | 自动评价配置 | Java |
| 8 | `xy_auto_reply_message_logs` | 自动回复日志 | Python（写） |
| 9 | `xy_card_item_relations` | 卡券商品关联 | Java |
| 10 | `xy_cards` | 卡券表 | Java |
| 11 | `xy_catalog_items` | 商品目录 | Java |
| 12 | `xy_accounts` | 闲鱼账号 | Java |
| 13 | `xy_default_replies` | 默认回复 | Java |
| 14 | `xy_dock_records` | 对接记录 | Java |
| 15 | `xy_messages` | 消息表 | Python（写） |
| 16 | `xy_orders` | 订单表 | Java |
| 17 | `xy_delivery_logs` | 发货日志 | Python（写） |
| 18 | `xy_keyword_rules` | 关键词规则 | Java |
| 19 | `xy_account_login_logs` | 登录日志 | Java |
| 20 | `xy_ai_settings` | AI 设置 | Java |
| 21 | `xy_ai_presets` | AI 预设 | Java |
| 22 | `xy_delivery_block_rules` | 发货拦截规则 | Java |
| 23 | `xy_notifications` | 通知表 | Java |
| 24 | `xy_rate_logs` | 评价日志 | Python（写） |
| 25 | `xy_red_flower_logs` | 小红花日志 | Python（写） |
| 26 | `xy_blacklist` | 黑名单 | Java |
| 27 | `xy_system_config` | 系统配置 | Java |
| 28 | `xy_operation_logs` | 操作日志 | Java |
| 29 | `xy_webhook_configs` | Webhook 配置 | Java |
| 30 | `xy_item_polish_logs` | 擦亮日志 | Java |
| 31 | `xy_delivery_retry_logs` | 发货重试日志 | Python（写） |

#### 返佣系统表（`fy_` 前缀，约 23 张）

| 表名 | 说明 | 迁移 |
|------|------|:--:|
| `fy_products` | 选品库 | Java |
| `fy_product_materials` | 素材库 | Java |
| `fy_publish_rules` | 发布规则 | Java |
| `fy_agent_relations` | 代理关系 | Java |
| `fy_commission_configs` | 佣金配置 | Java |
| `fy_commission_records` | 佣金记录 | Java |
| `fy_*` (其余) | 其他返佣表 | Java |

---

## 2. 技术选型参考资料

### 2.1 技术选型报告（已生成）

- 文件：`kdocs/tech-selection-report/tech-selection-report.html`
- 内容：Python vs Go vs Rust vs Java 四语言适配度分析
- 结论：Java + Python 混合架构最优

### 2.2 SmartAdmin 框架

| 资源 | 链接 |
|------|------|
| 官网 | https://www.smartadmin.vip/ |
| 在线预览 | https://preview.smartadmin.vip/ |
| Gitee 仓库 | https://gitee.com/lab1024/smart-admin |
| 代码规范 | https://www.smartadmin.vip/views/doc/standard/basic.html |
| 亮点功能 | https://www.smartadmin.vip/views/start/FunctionFeature.html |

### 2.3 若依（备选框架）

| 资源 | 链接 |
|------|------|
| 官网 | http://ruoyi.vip |
| 文档 | http://doc.ruoyi.vip |
| RuoYi-App | https://gitee.com/y_project/RuoYi-App |
| H5 体验 | http://h5.ruoyi.vip |

### 2.4 JDK 版本选择依据

| 版本 | 关键特性 | 推荐度 |
|------|------|:--:|
| JDK 17 | Spring Boot 3 最低要求，虚拟线程 Preview | ★★★ |
| **JDK 21** | **虚拟线程 GA，结构化并发 Preview，2029 年支持** | ★★★★★ |
| JDK 25 | 最新 LTS，结构化并发 GA，生态追赶中 | ★★★★ |

---

## 3. 框架与工具文档

### 3.1 Spring Boot 3

| 资源 | 链接 |
|------|------|
| 官方文档 | https://docs.spring.io/spring-boot/docs/3.5.x/reference/ |
| 虚拟线程指南 | https://spring.io/blog/2023/11/23/spring-boot-3-2-0-available-now |
| 升级指南 | https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide |

### 3.2 MyBatis-Plus

| 资源 | 链接 |
|------|------|
| 官方文档 | https://baomidou.com/ |
| 代码生成器 | https://baomidou.com/pages/981406/ |
| 分页插件 | https://baomidou.com/pages/97710a/ |

### 3.3 Sa-Token

| 资源 | 链接 |
|------|------|
| 官方文档 | https://sa-token.cc/ |
| 与 Spring Boot 集成 | https://sa-token.cc/doc.html#/start/example |
| 权限注解 | https://sa-token.cc/doc.html#/use/at-check |

### 3.4 Quartz

| 资源 | 链接 |
|------|------|
| 官方文档 | http://www.quartz-scheduler.org/documentation/ |
| Spring Boot 集成 | https://docs.spring.io/spring-boot/docs/3.5.x/reference/io/quartz.html |

### 3.5 Flyway

| 资源 | 链接 |
|------|------|
| 官方文档 | https://flywaydb.org/documentation/ |
| Spring Boot 集成 | https://docs.spring.io/spring-boot/docs/3.5.x/howto/data-initialization.html |

---

## 4. 规则引擎设计参考

### 4.1 Drools

| 资源 | 链接 |
|------|------|
| 官方文档 | https://docs.drools.org/ |
| DRL 语法指南 | https://docs.drools.org/latest/drools-docs/drools/language-reference/ |
| Spring Boot 集成 | https://docs.drools.org/latest/drools-docs/drools/spring-boot/ |
| 决策表 (Excel) | https://docs.drools.org/latest/drools-docs/drools/decision-tables/ |

### 4.2 现有规则迁移对照

```drools
// 示例：买家信用规则迁移
// 现有 Python 代码：
//   if buyer_credit_score < threshold:
//       return RuleCheckResult(block=True, reason="买家信用不足")

// 迁移后 Drools 规则：
rule "Buyer Credit Check"
    when
        $ctx : DeliveryContext(
            buyerCreditScore < creditThreshold,
            excludedItems not contains itemId
        )
    then
        $ctx.setBlocked(true);
        $ctx.setBlockReason("买家信用不足");
end
```

### 4.3 规则参数配置表设计

```sql
CREATE TABLE `xy_delivery_block_rules` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `account_id` varchar(80) NOT NULL COMMENT '账号ID',
  `rule_code` varchar(50) NOT NULL COMMENT '规则编码',
  `enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `priority` int DEFAULT '0' COMMENT '优先级',
  `block_reason` varchar(500) COMMENT '拦截原因',
  `auto_close_order` tinyint(1) DEFAULT '0' COMMENT '是否自动关单',
  `only_card_after_close` tinyint(1) DEFAULT '0' COMMENT '仅发卡后关单',
  `excluded_item_ids` json DEFAULT NULL COMMENT '排除商品',
  `config` json DEFAULT NULL COMMENT '规则参数',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_account_rule` (`account_id`, `rule_code`)
);
```

---

## 5. gRPC 通信参考

### 5.1 Proto 定义规范

```protobuf
// 命名规范
syntax = "proto3";
package xyun.platform;                          // 包名：项目.模块
option java_package = "com.xyun.platform.grpc";  // Java 包名
option java_multiple_files = true;               // 多文件生成

// 消息命名：名词 + Request/Response
message AccountRequest {
  string account_id = 1;
  int64 owner_id = 2;
}

// 服务命名：名词 + Service
service AccountService {
  rpc GetAccount (AccountRequest) returns (AccountResponse);
}
```

### 5.2 gRPC 版本对照

| 组件 | 版本 | 说明 |
|------|------|------|
| gRPC Java | 1.68.x | 服务端 + 客户端 |
| gRPC Python | 1.68.x | 客户端 |
| Protobuf | 3.25.x | 序列化 |
| protoc | 3.25.x | 编译器 |

### 5.3 参考资料

| 资源 | 链接 |
|------|------|
| gRPC 官方文档 | https://grpc.io/docs/ |
| gRPC Java 教程 | https://grpc.io/docs/languages/java/ |
| gRPC Python 教程 | https://grpc.io/docs/languages/python/ |
| Proto 3 语法 | https://protobuf.dev/programming-guides/proto3/ |

---

## 6. 多终端开发参考

### 6.1 Vue 3 前端

| 资源 | 链接 |
|------|------|
| Vue 3 官方文档 | https://vuejs.org/ |
| Vite 5 官方文档 | https://vitejs.dev/ |
| Ant Design Vue 4.x | https://www.antdv.com/ |
| Pinia 状态管理 | https://pinia.vuejs.org/ |
| TypeScript 手册 | https://www.typescriptlang.org/docs/ |

### 6.2 UniApp 移动端

| 资源 | 链接 |
|------|------|
| UniApp 官方文档 | https://uniapp.dcloud.net.cn/ |
| uni-ui 组件库 | https://uniapp.dcloud.net.cn/component/uniui/uni-ui.html |
| H5 发布 | https://uniapp.dcloud.net.cn/tutorial/h5-publish.html |
| 小程序发布 | https://uniapp.dcloud.net.cn/tutorial/mp-publish.html |
| App 打包 | https://uniapp.dcloud.net.cn/tutorial/app-publish.html |

### 6.3 设计规范

| 资源 | 链接 |
|------|------|
| Ant Design 设计规范 | https://ant.design/docs/spec/introduce-cn |
| SmartAdmin 前端规范 | https://www.smartadmin.vip/views/doc/standard/basic.html |

---

## 7. 安全与合规参考

### 7.1 三级等保

| 资源 | 链接 |
|------|------|
| SmartAdmin 安全体系 | https://www.smartadmin.vip/views/level3protect/basic.html |
| 网络安全等级保护 | https://www.djbh.net/ |

### 7.2 加密方案

| 场景 | 算法 | 说明 |
|------|------|------|
| Cookie 存储 | AES-256-GCM | 密钥分离，加盐 |
| 密码存储 | BCrypt | 12 轮迭代 |
| API 传输加密 | SM4（国密） | SmartAdmin 内置 |
| JWT 签名 | HMAC-SHA256 | 密钥定期轮换 |
| 数据脱敏 | 自定义注解 | 手机号/身份证/Key |

### 7.3 安全最佳实践

- OWASP Top 10：https://owasp.org/www-project-top-ten/
- Spring Security 最佳实践：https://spring.io/security

---

## 8. 部署与运维参考

### 8.1 Docker

| 资源 | 链接 |
|------|------|
| Docker 官方文档 | https://docs.docker.com/ |
| Docker Compose | https://docs.docker.com/compose/ |
| Dockerfile 最佳实践 | https://docs.docker.com/develop/develop-images/dockerfile_best-practices/ |

### 8.2 监控

| 资源 | 链接 |
|------|------|
| Prometheus | https://prometheus.io/docs/ |
| Grafana | https://grafana.com/docs/ |
| Spring Boot Actuator | https://docs.spring.io/spring-boot/docs/3.5.x/reference/actuator/ |

### 8.3 日志

| 资源 | 链接 |
|------|------|
| SLF4J + Logback | https://logback.qos.ch/ |
| ELK Stack | https://www.elastic.co/guide/ |

---

## 附录 A：GLOSSARY — 术语对照表

| 术语 | 英文 | 说明 |
|------|------|------|
| 闲鱼 | Xianyu / Idle Fish | 阿里巴巴旗下二手交易平台 |
| 卡券 | Card | 虚拟发货内容（文本/API/图片/数据） |
| 对接 | Dock | 卡券共享给下级代理使用 |
| 返佣 | Commission / Promotion | 代理分销佣金 |
| 擦亮 | Polish | 刷新商品发布时间，保持曝光 |
| 滑块验证码 | Slider CAPTCHA | 闲鱼登录时的滑动验证 |
| 小红花 | Red Flower | 闲鱼交易好评 |
| 租户 | Tenant | 多租户架构中的独立客户 |
| 激活码 | License Key | 软件授权码 |
| 续期码 | Renewal Code | 延长授权有效期 |

---

## 附录 B：文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 技术选型报告 | `kdocs/tech-selection-report/tech-selection-report.html` | 四语言适配度分析 |
| 产品需求文档 | `kdocs/prd.md` | 平台化功能需求 |
| 架构设计文档 | `kdocs/architecture.md` | 系统架构 + 流程图 |
| 执行计划 | `kdocs/execution-plan.md` | 分阶段实施计划 |
| 参考资料（本文档） | `kdocs/references.md` | 参考资料汇总 |