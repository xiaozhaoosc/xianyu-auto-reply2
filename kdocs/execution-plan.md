# 闲鱼自动回复系统 — 平台化混合架构升级执行计划

> 版本：v1.0 | 日期：2026-06-13 | 作者：架构组
>
> 本文档定义从 Python 单体到 Java + Python 混合架构平台的详细执行计划，包含分阶段任务、里程碑、风险与验收标准。

---

## 目录

1. [总体策略](#1-总体策略)
2. [Phase 0：基础设施准备（2 周）](#2-phase-0基础设施准备2-周)
3. [Phase 1：Java 平台基础搭建（4 周）](#3-phase-1java-平台基础搭建4-周)
4. [Phase 2：数据模型迁移（4 周）](#4-phase-2数据模型迁移4-周)
5. [Phase 3：gRPC 桥接层 + Python 集成（4 周）](#5-phase-3grpc-桥接层--python-集成4-周)
6. [Phase 4：规则引擎 + 业务逻辑迁移（6 周）](#6-phase-4规则引擎--业务逻辑迁移6-周)
7. [Phase 5：前端迁移 + 移动端（6 周）](#7-phase-5前端迁移--移动端6-周)
8. [Phase 6：定时任务迁移（2 周）](#8-phase-6定时任务迁移2-周)
9. [Phase 7：返佣系统迁移（4 周）](#9-phase-7返佣系统迁移4-周)
10. [Phase 8：测试、联调、灰度（4 周）](#10-phase-8测试联调灰度4-周)
11. [风险矩阵](#11-风险矩阵)
12. [验收标准](#12-验收标准)

---

## 1. 总体策略

### 1.1 核心原则

```
┌─────────────────────────────────────────────────────────────┐
│                    渐进式迁移策略                              │
│                                                              │
│  现有 Python 代码 ──────── 不动 ──────── 继续生产运行          │
│       │                                                      │
│       └──→ 新代码写入 vr_java_python/ 目录                   │
│                │                                             │
│                ├── Phase 1-2: Java 建底座（独立运行）          │
│                ├── Phase 3-4: 桥接 Python + 业务逻辑          │
│                ├── Phase 5-6: 前端 + 定时任务                 │
│                ├── Phase 7: 返佣系统                          │
│                └── Phase 8: 测试 + 灰度                       │
│                                                              │
│  每个 Phase 结束时：可独立运行、可回滚、可验收                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 时间线总览

```
Phase 0: ██░░░░░░░░  2w  基础设施准备
Phase 1: ████░░░░░░  4w  Java 平台基础
Phase 2: ████░░░░░░  4w  数据模型迁移
Phase 3: ████░░░░░░  4w  gRPC + Python 集成
Phase 4: ██████░░░░  6w  规则引擎 + 业务逻辑
Phase 5: ██████░░░░  6w  前端迁移 + 移动端
Phase 6: ██░░░░░░░░  2w  定时任务迁移
Phase 7: ████░░░░░░  4w  返佣系统迁移
Phase 8: ████░░░░░░  4w  测试 + 灰度
        ──────────────────
        总计: 36 周 (约 9 个月)
```

---

## 2. Phase 0：基础设施准备（2 周）

### 目标
搭建开发环境，初始化项目骨架，建立 CI/CD 流水线。

### 任务清单

| 任务 | 负责人 | 工时 | 产出 |
|------|:--:|:--:|------|
| 创建 `vr_java_python/` 目录结构 | 架构 | 2h | 完整目录骨架 |
| 初始化 Maven 多模块项目 | 后端 | 4h | `pom.xml` + 模块结构 |
| 初始化 SmartAdmin 基座 | 后端 | 8h | 可运行的 Java 管理后台 |
| 配置 Docker Compose 开发环境 | 后端 | 4h | MySQL + Redis + MinIO |
| 配置 CI/CD (GitHub Actions) | 后端 | 4h | 自动构建 + 测试 |
| 建立代码规范检查 (Checkstyle + ESLint) | 全栈 | 4h | 代码规范配置 |
| 初始化 Python 运行时目录 | 后端 | 2h | `python-runtime/` 骨架 |
| 初始化前端目录 | 前端 | 4h | SmartAdmin 前端改造 |
| 编写开发环境搭建文档 | 架构 | 2h | README + 开发指南 |

### 验收标准
- [ ] `mvn clean install` 全模块编译通过
- [ ] SmartAdmin 管理后台可访问（默认页面）
- [ ] Docker Compose 一键启动全部基础设施
- [ ] CI/CD 自动构建通过

---

## 3. Phase 1：Java 平台基础搭建（4 周）

### 目标
基于 SmartAdmin 实现用户管理、角色权限、多租户、系统配置等基础能力。

### 任务清单

| 任务 | 工时 | 产出 |
|------|:--:|------|
| 用户管理模块（CRUD + 分页 + 搜索） | 8h | `/api/v2/users` |
| 角色管理模块（RBAC） | 8h | `/api/v2/roles` |
| 权限分配（菜单 + 按钮 + 数据权限） | 8h | Sa-Token 权限配置 |
| 多租户基础（租户隔离 + 上下文） | 16h | 租户拦截器 + 行级隔离 |
| 系统配置模块（全局参数） | 8h | `/api/v2/settings` |
| 操作日志（AOP 切面） | 8h | 自动记录 CUD 操作 |
| 激活码管理（生成 + 验证 + 续期） | 16h | `/api/v2/licenses` |
| 公告管理 | 4h | `/api/v2/announcements` |
| 单元测试（核心 Service） | 8h | 覆盖率 > 60% |

### 验收标准
- [ ] 5 种角色可正常创建、授权、登录
- [ ] 多租户数据隔离验证通过
- [ ] 激活码生成/验证/续期流程完整
- [ ] 操作日志自动记录所有 CUD 操作

---

## 4. Phase 2：数据模型迁移（4 周）

### 目标
将 54 张 MySQL 表映射为 Java Entity + MyBatis-Plus Mapper，实现类型安全的数据访问层。

### 迁移策略

```
优先级排序：
  P0 (10 张): 用户、账号、商品、卡券、关键词规则、AI 设置、订单、发货规则、黑名单、默认回复
  P1 (15 张): 消息日志、发货日志、评价日志、对接记录、代理订单、卡券关联、AI 聊天、登录日志
  P2 (余下): 广告、通知、小红花、返佣相关表
```

### 任务清单

| 任务 | 工时 | 产出 |
|------|:--:|------|
| P0 表 Entity + Mapper 生成 | 16h | 10 张核心表映射 |
| P0 表 Service 层实现 | 24h | 核心业务 Service |
| P1 表 Entity + Mapper 生成 | 16h | 15 张业务表映射 |
| P1 表 Service 层实现 | 24h | 业务 Service |
| P2 表 Entity + Mapper 生成 | 16h | 剩余表映射 |
| 账号管理 API（CRUD + 状态） | 16h | `/api/v2/accounts` |
| 商品管理 API | 16h | `/api/v2/items` |
| 卡券管理 API | 16h | `/api/v2/cards` |
| 关键词规则 API | 8h | `/api/v2/keyword-rules` |
| AI 设置 API | 8h | `/api/v2/ai-settings` |
| 集成测试（核心 API） | 16h | TestContainers |

### 验收标准
- [ ] 54 张表全部映射为 Entity + Mapper
- [ ] 核心 CRUD API 全部可用
- [ ] MyBatis-Plus 代码生成器输出符合规范
- [ ] 集成测试通过率 100%

---

## 5. Phase 3：gRPC 桥接层 + Python 集成（4 周）

### 目标
建立 Java ↔ Python 的 gRPC 通信通道，Python 运行时通过 gRPC 获取规则和配置，写入日志。

### 任务清单

| 任务 | 工时 | 产出 |
|------|:--:|------|
| 定义 Proto 文件（account/rule/message/delivery） | 8h | 4 个 proto 文件 |
| Java gRPC Server 实现 | 16h | gRPC 服务端 |
| Python gRPC Client 实现 | 16h | gRPC 客户端 |
| Python grpc_client 集成到现有代码 | 16h | 替换直连 DB |
| Redis 缓存层实现（规则 + 配置） | 16h | 缓存读写 |
| 规则变更时刷新 Redis（Java 侧） | 8h | 缓存刷新 |
| Python 读取 Redis 替代 gRPC 高频调用 | 8h | 降延迟 |
| 端到端通信测试 | 16h | 通信验证 |
| 异常处理与重试机制 | 8h | 容错逻辑 |

### 核心集成点

```
Python 代码变更点：
  auto_reply_service.py:
    - 删除: from sqlalchemy import select ... (直连 DB 查规则)
    + 新增: from grpc_client import get_keyword_rules, get_ai_settings

  auto_delivery_handler.py:
    - 删除: from common.models.xy_delivery_block_rule import ...
    + 新增: from grpc_client import load_delivery_rules, match_card, write_delivery_log

  xianyu_async.py:
    - 删除: 直连 DB 写登录日志
    + 新增: from grpc_client import write_login_log
```

### 验收标准
- [ ] gRPC 通信延迟 < 5ms（本地）
- [ ] Python 所有数据库直连替换为 gRPC/Redis
- [ ] Redis 缓存命中率 > 95%
- [ ] 异常重试 3 次后降级处理

---

## 6. Phase 4：规则引擎 + 业务逻辑迁移（6 周）

### 目标
用 Drools 声明式规则替代硬编码的 if-else 发货拦截规则，实现规则可配置、可热加载。

### 任务清单

| 任务 | 工时 | 产出 |
|------|:--:|------|
| Drools 环境搭建与集成 | 8h | KieContainer 配置 |
| 买家信用规则 DRL | 8h | `buyer_credit.drl` |
| 历史订单规则 DRL | 8h | `buyer_has_order.drl` |
| 未确认收货规则 DRL | 8h | `buyer_unconfirmed.drl` |
| 个人黑名单规则 DRL | 8h | `personal_blacklist.drl` |
| 卡券匹配规则 DRL | 8h | `card_match.drl` |
| 规则管理 API（CRUD + 启用/禁用） | 16h | `/api/v2/delivery-rules` |
| 规则管理前端页面 | 16h | 可视化规则编辑 |
| 规则测试工具（模拟订单检查） | 8h | 规则调试 |
| 消息回复策略规则 | 16h | 回复规则 DRL |
| Python 发货流程集成规则引擎 | 16h | gRPC 调用规则检查 |
| 规则执行日志 | 8h | 为什么拦截/通过 |
| 端到端回归测试 | 16h | 所有发货场景 |

### 规则迁移对照

| 现有 Python 规则 | Drools 规则 | 优先级 |
|------|------|:--:|
| `buyer_credit_rule.py` | `buyer_credit.drl` | 1 |
| `buyer_has_order_rule.py` | `buyer_has_order.drl` | 2 |
| `buyer_unconfirmed_rule.py` | `buyer_unconfirmed.drl` | 3 |
| `personal_blacklist_rule.py` | `personal_blacklist.drl` | 4 |
| 无（硬编码在 handler 中） | `card_match.drl` | 10 |
| 全局开关（`delivery_disabled` 字段） | `delivery_disabled.drl` | 99 |

### 验收标准
- [ ] 6 个规则全部迁移为 Drools DRL
- [ ] 规则执行结果与 Python 硬编码一致
- [ ] 管理后台可编辑规则参数（阈值、排除列表）
- [ ] 规则变更后无需重启即可生效

---

## 7. Phase 5：前端迁移 + 移动端（6 周）

### 目标
将现有 React + TailwindCSS 前端迁移到 Vue 3 + Ant Design Vue，并基于 UniApp 开发 H5 移动端。

### 任务清单

| 任务 | 工时 | 产出 |
|------|:--:|------|
| SmartAdmin 前端改造（品牌/主题） | 8h | 定制主题 |
| 用户管理页面 | 8h | Vue 3 页面 |
| 账号管理页面（含状态监控） | 16h | 实时状态 |
| 商品管理页面（含批量操作） | 16h | 商品列表 + 批量 |
| 卡券管理页面（含对接） | 16h | 卡券 CRUD + 对接 |
| 关键词规则页面 | 8h | 规则编辑 |
| 发货规则页面 | 8h | 可视化规则 |
| AI 设置页面 | 8h | 模型配置 |
| 消息日志页面 | 8h | 日志查询 |
| 订单管理页面 | 8h | 订单列表 |
| 数据报表页面（ECharts） | 16h | 可视化报表 |
| 系统管理页面 | 8h | 配置 + 日志 |
| UniApp 移动端框架搭建 | 8h | H5 基础框架 |
| 移动端核心页面（3 个） | 16h | 工作台/消息/订单 |
| 小程序适配 | 16h | 微信小程序 |
| API 对接 + 联调 | 16h | 前后端联调 |

### 页面迁移对照

| 现有 React 页面 | 新 Vue 3 页面 | 代码生成 |
|------|------|:--:|
| 用户管理 | `views/system/user/` | ● 自动生成 |
| 账号管理 | `views/account/list.vue` | 手写 |
| 商品管理 | `views/item/list.vue` | 手写 |
| 卡券管理 | `views/card/list.vue` | 手写 |
| 关键词规则 | `views/rule/keyword.vue` | 手写 |
| 发货规则 | `views/rule/delivery.vue` | 手写 |
| AI 设置 | `views/setting/ai.vue` | 手写 |
| 消息日志 | `views/log/message.vue` | ● 自动生成 |
| 订单管理 | `views/order/list.vue` | ● 自动生成 |
| 数据报表 | `views/report/` | 手写 |
| 系统配置 | `views/system/setting.vue` | ● 自动生成 |
| 操作日志 | `views/system/log.vue` | ● 自动生成 |
| 公告管理 | `views/system/announcement.vue` | ● 自动生成 |

> ● 表示 SmartAdmin 代码生成器可自动生成

### 验收标准
- [ ] 全部管理后台页面完成迁移
- [ ] H5 移动端核心功能可用
- [ ] 微信小程序审核通过
- [ ] 前后端 API 联调通过

---

## 8. Phase 6：定时任务迁移（2 周）

### 目标
将 APScheduler 定时任务迁移到 Quartz，实现可视化管理。

### 任务清单

| 任务 | 工时 | 产出 |
|------|:--:|------|
| Quartz 配置（集群模式） | 8h | 调度配置 |
| Cookie 刷新任务 | 8h | 调 Python gRPC |
| 商品列表拉取任务 | 4h | 闲鱼 API 同步 |
| 订单拉取任务 | 4h | 闲鱼 API 同步 |
| 商品自动擦亮任务 | 4h | 调 Python gRPC |
| 自动评价任务 | 4h | 调 Python gRPC |
| 数据库备份任务 | 4h | 本地 + 云端 |
| 过期数据清理任务 | 4h | 自动清理 |
| 任务管理前端页面 | 8h | 可视化调度 |
| 任务执行日志 | 4h | 执行历史 |

### 验收标准
- [ ] 15 个定时任务全部迁移到 Quartz
- [ ] 管理后台可查看/启停/手动触发任务
- [ ] 任务执行失败自动重试 + 告警

---

## 9. Phase 7：返佣系统迁移（4 周）

### 目标
将 promotion/ 子系统完整迁移到 Java 平台层。

### 任务清单

| 任务 | 工时 | 产出 |
|------|:--:|------|
| 返佣表 Entity 映射（~23 张 `fy_*` 表） | 16h | Entity + Mapper |
| 选品库 API | 8h | `/api/v2/promotion/catalog` |
| 素材库 API | 8h | `/api/v2/promotion/materials` |
| 发布/删除规则 API | 8h | `/api/v2/promotion/rules` |
| 代理订单 API | 8h | `/api/v2/promotion/orders` |
| 分销结算 API | 16h | 佣金计算 |
| 下级管理 API | 8h | `/api/v2/promotion/agents` |
| 返佣规则 DRL | 8h | `promotion_commission.drl` |
| 返佣前端页面 | 16h | Vue 3 页面 |
| 集成测试 | 8h | 完整返佣流程 |

### 验收标准
- [ ] 选品 → 发布 → 销售 → 结算完整链路通过
- [ ] 多级分销佣金计算正确
- [ ] 返佣前端页面完整可用

---

## 10. Phase 8：测试、联调、灰度（4 周）

### 目标
全链路测试验证，灰度发布，确保新系统稳定运行。

### 任务清单

| 任务 | 工时 | 产出 |
|------|:--:|------|
| 单元测试补充（覆盖率 > 70%） | 16h | 测试报告 |
| 集成测试（TestContainers） | 16h | 测试报告 |
| 端到端测试（核心流程） | 16h | 测试用例 |
| 性能测试（JMeter） | 8h | 性能报告 |
| 安全测试（渗透测试） | 8h | 安全报告 |
| 灰度方案设计 | 4h | 灰度策略 |
| 灰度部署（10% → 50% → 100%） | 8h | 逐步切换 |
| 监控告警配置 | 8h | Prometheus + Grafana |
| 文档完善（运维手册 + API 文档） | 16h | 完整文档 |
| 生产环境部署 | 8h | 生产上线 |

### 灰度策略

```
Week 1: 内部测试账号（10% 流量）
Week 2: 信任用户（30% 流量）
Week 3: 扩大灰度（50% 流量）
Week 4: 全量切换（100% 流量）

每个阶段观察指标：
  · 错误率 < 0.1%
  · 消息处理延迟 < 3s
  · 发货成功率 > 99%
  · 用户投诉 < 基线
```

### 验收标准
- [ ] 全链路测试通过率 100%
- [ ] 性能指标达标（见 PRD 非功能性需求）
- [ ] 安全测试无高危漏洞
- [ ] 灰度各阶段无 P0 故障
- [ ] 完整运维文档 + API 文档

---

## 11. 风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 | 责任人 |
|------|:--:|:--:|------|:--:|
| gRPC 通信延迟不达标 | 中 | 高 | 高频读走 Redis 缓存，定期压测 | 后端 |
| React → Vue 迁移遗漏功能 | 中 | 中 | 逐页迁移 + 功能对照表 | 前端 |
| Drools 规则行为与 Python 不一致 | 中 | 高 | 双轨运行对比，自动化回归测试 | 后端 |
| Python 代码改动引入回归 Bug | 高 | 中 | gRPC 替换点最小化，单元测试覆盖 | 全栈 |
| 多端适配工作量超预期 | 中 | 中 | UniApp 复用，核心页面优先 | 前端 |
| 团队学习曲线（Java + Drools） | 中 | 低 | 内部培训 + 结对编程 | 架构 |
| 生产环境切换故障 | 低 | 极高 | 灰度发布 + 快速回滚方案 | 运维 |

---

## 12. 验收标准

### 12.1 功能验收

- [ ] 所有 PRD 中 P0/P1 功能完整实现
- [ ] 现有 Python 系统功能无回归
- [ ] 新系统功能与 PRD 一致

### 12.2 性能验收

- [ ] 消息处理延迟 < 3 秒 (P95)
- [ ] 自动发货延迟 < 5 秒 (P95)
- [ ] API 响应时间 < 200ms (P95)
- [ ] 并发 500 账号稳定运行

### 12.3 质量验收

- [ ] 单元测试覆盖率 > 70%
- [ ] 集成测试通过率 100%
- [ ] 安全测试无高危漏洞
- [ ] 代码规范检查通过

### 12.4 文档验收

- [ ] 架构设计文档完整
- [ ] API 文档（Swagger/Knife4j）
- [ ] 运维部署手册
- [ ] 开发者指南