# Project Wiki: 闲鱼自动回复系统 (xianyu-auto-reply2)

## 📌 项目基本信息
- **技术栈**: FastAPI + React + MySQL + Redis + Playwright + WebSocket + Docker
- **模块结构**:
  - [frontend](file:///D:/IdeaProjects/xianyu-auto-reply2/frontend): React 前端
  - [backend-web](file:///D:/IdeaProjects/xianyu-auto-reply2/backend-web): 主 FastAPI 后端服务 (Port 8089)
  - [websocket](file:///D:/IdeaProjects/xianyu-auto-reply2/websocket): WebSocket 长连接及消息处理 (Port 8090)
  - [scheduler](file:///D:/IdeaProjects/xianyu-auto-reply2/scheduler): 定时任务、自动发货、自动评价、Cookie刷新 (Port 8091)
  - [common](file:///D:/IdeaProjects/xianyu-auto-reply2/common): 共享模块 (数据库模型、工具类)
  - [promotion](file:///D:/IdeaProjects/xianyu-auto-reply2/promotion): 返佣子系统 (前后端独立)
  - [launcher](file:///D:/IdeaProjects/xianyu-auto-reply2/launcher): Windows 桌面启动器

## 🎯 当前核心任务
- [x] 克隆项目仓库 (使用 SSH `git@github.com:xiaozhaoosc/xianyu-auto-reply2.git`)
- [x] 项目自检与环境配置 (MySQL, Redis, Python 依赖安装)
- [x] 验证服务启动与可用性
- [x] 商品采集与搜索滑块风控调优
- [x] 解决并发浏览器占用与锁冲突 (ADR-005)

## 📖 Wiki 导航
- [每日日志 (JOURNAL.md)](file:///D:/IdeaProjects/xianyu-auto-reply2/.agent/wiki/JOURNAL.md)
- [架构编年史 (CHRONICLE.md)](file:///D:/IdeaProjects/xianyu-auto-reply2/.agent/wiki/CHRONICLE.md)
- [技术债账本 (DEBT_LEADGER.md)](file:///D:/IdeaProjects/xianyu-auto-reply2/.agent/wiki/DEBT_LEADGER.md)
- [建议与灵感收件箱 (INBOX.md)](file:///D:/IdeaProjects/xianyu-auto-reply2/.agent/wiki/INBOX.md)
- [滑块绕过方案技术白皮书 (taobao_slider_bypass_solutions.md)](file:///D:/IdeaProjects/xianyu-auto-reply2/.agent/wiki/taobao_slider_bypass_solutions.md)
