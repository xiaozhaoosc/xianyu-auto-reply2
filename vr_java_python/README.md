# 闲鱼智能运营平台 v2.0

基于 **Spring Boot 3 + JDK 21 + Vue 3** 的 Java 平台层 + Python 运行时引擎混合架构。

## 技术栈

| 层 | 技术 |
|------|------|
| Java 平台 | Spring Boot 3.5 + JDK 21 + MyBatis-Plus + Sa-Token |
| 定时任务 | JobRunr（嵌入式，无需独立部署） |
| 规则引擎 | Drools 9.x |
| 通信桥接 | gRPC + Redis 缓存 |
| Python 运行时 | FastAPI + Playwright + AI Engine |
| 前端 | Vue 3 + Ant Design Vue（SmartAdmin） |
| 移动端 | UniApp（H5 + 小程序） |
| 数据库 | MySQL 8.0 + Redis 7 |

## 模块结构

```
java-platform/
├── platform-common/      # 公共模块：Entity / DTO / VO
├── platform-server/      # 管理后台 REST API :8089
├── platform-scheduler/   # JobRunr 定时任务 :8091
├── platform-promotion/   # 返佣系统 :8092
├── platform-rules/       # Drools 规则引擎
└── platform-grpc/        # gRPC 桥接层 :9090

python-runtime/
├── websocket_service/    # 闲鱼 WS 连接 + 消息处理
└── playwright_service/   # 浏览器自动化
```

## 快速开始

```bash
# 编译
cd java-platform && mvn clean install -DskipTests

# 启动（需先启动 MySQL + Redis）
java -jar platform-server/target/platform-server-2.0.0-SNAPSHOT.jar
java -jar platform-scheduler/target/platform-scheduler-2.0.0-SNAPSHOT.jar

# Docker Compose 一键启动
docker compose up -d
```