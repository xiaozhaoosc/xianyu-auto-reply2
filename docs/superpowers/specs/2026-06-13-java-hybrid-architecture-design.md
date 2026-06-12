# 闲鱼平台化 — Java 混合架构设计文档

> 版本：v1.0 | 日期：2026-06-13
> 基于 kdocs 设计文档，结合最新调研的最终设计决策。

## 1. 设计决策

| 决策项 | 最终选择 | 理由 |
|------|------|------|
| 整体架构 | **Java 平台层 + Python 运行时引擎** | 浏览器自动化必须保留 Python |
| Java 底座 | **SmartAdmin** | Spring Boot 3 + MyBatis-Plus + Sa-Token + 代码生成器 |
| 定时任务 | **JobRunr** | 嵌入式 JAR 包，无需独立部署，自带 Dashboard，OSS 免费版支持 100 个定时任务 |
| 规则引擎 | **Drools** | 声明式替代 6 种 Python 硬编码 if-else 规则 |
| 前端 | **Vue 3 全部迁移** | SmartAdmin 自带，代码生成器加速 CRUD 页面 |
| Python 运行时 | **保留不动** | Playwright + AI 引擎 + 闲鱼 WebSocket 连接 |
| 通信方式 | **gRPC + Redis 缓存** | 高频读走 Redis，写走 gRPC |
| 数据库 | **复用现有 MySQL 54 张表** | Flyway 管理迁移，不动现有表结构 |
| 新目录 | `vr_java_python/` | 与现有代码平级，独立演进 |
| 分支 | `dv_java` | 从当前分支切出，独立演进 |

## 2. 系统架构

```
客户端层:  PC Web / H5 / 小程序 / App
              ↓ HTTPS
网关层:    Nginx :443 (反向代理)
              ↓
Java 平台层:  Spring Boot 3 + JDK 21 (虚拟线程)
├── platform-server     :8089  REST API (账号/商品/卡券/规则/报表)
├── platform-scheduler  :8091  JobRunr 定时任务 (13个)
├── platform-promotion  :8092  返佣系统
├── platform-rules              Drools 规则引擎
└── platform-grpc       :9090  gRPC Server
              ↕ gRPC + Redis
Python 运行时:  FastAPI
├── websocket_service   :8090  闲鱼 WS 连接 + 消息处理 + AI 回复 + 自动发货
└── playwright_service         浏览器自动化 (登录/Cookie/发布)
              ↓
基础设施:   MySQL 8.0 / Redis 7 / MinIO
```

## 3. 执行阶段

| Phase | 内容 | 预估 |
|:--:|------|:--:|
| 0 | 基础设施：创建分支、初始化 SmartAdmin + JobRunr | 1 天 |
| 1 | 数据模型：54 张表 Entity + Mapper | 2 天 |
| 2 | gRPC 桥接：Proto 定义 + Java Server + Python Client | 3 天 |
| 3 | 业务 API：账号/商品/卡券/关键词 REST API + Drools 规则 | 4 天 |
| 4 | 前端迁移：React → Vue 3，30+ 页面 | 6 天 |
| 5 | 定时任务：APScheduler → JobRunr，13 个任务 | 2 天 |
| 6 | 返佣系统：promotion/ 迁移到 Java | 3 天 |
| 7 | 测试联调：全链路测试 + 打包验证 | 2 天 |

## 4. 技术栈明细

| 组件 | 版本 | 说明 |
|------|------|------|
| JDK | 21 LTS | 虚拟线程 GA |
| Spring Boot | 3.5.x | 自动配置 |
| MyBatis-Plus | 3.5.15 | Lambda 查询 + 代码生成 |
| Sa-Token | 1.40.0 | 权限认证 |
| JobRunr | 7.x | 定时任务调度 |
| Drools | 9.x | 规则引擎 |
| gRPC | 1.68+ | 跨语言通信 |
| Flyway | 10.x | 数据库迁移 |
| Vue 3 | 3.5+ | 前端框架 |
| Ant Design Vue | 4.x | UI 组件库 |
| UniApp | 最新 | 移动端/H5/小程序 |