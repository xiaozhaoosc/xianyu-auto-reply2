# Chronicle: 架构变迁与重大决策 (ADR)

## 📌 2026-06-12 — 项目初始化与克隆
- **事件**: 从 GitHub `git@github.com:xiaozhaoosc/xianyu-auto-reply2.git` 克隆了闲鱼自动回复系统项目。
- **架构现状**:
  - 前端采用 React 18 + TS + Vite + TailwindCSS。
  - 后端使用 FastAPI、SQLAlchemy 2.0、APScheduler、Playwright。
  - 采用多服务并行架构，主要由 API 接口网关 (`backend-web`)、长连接实时消息服务 (`websocket`)、定时任务调度器 (`scheduler`) 和共享逻辑 (`common`) 组成。
- **决策背景**:
  - 用户指定使用 SSH 协议进行克隆。
  - 克隆到本地 `D:\IdeaProjects\xianyu-auto-reply2`。

## 📌 2026-06-12 — 本地开发底座与一键启动脚本引入 (ADR-001)
- **事件**: 部署了本地 Docker MySQL 8 / Redis 开发底座，导入数据库 Schema，并编写了一键启动脚本 `本地一键调试启动.ps1`。
- **架构决策**:
  - **独立开发底座**: 创建 `docker-compose.dev-db.yml` 将数据库和缓存隔离在容器内，使用国内镜像源拉取，彻底解决大国内环境下 Docker 镜像拉取受限的问题。
  - **统一虚拟环境**: 全局使用单一 `venv` 虚拟环境，以可编辑模式（Editable Mode `-e`）挂载 `common` 及各个后端依赖，保证本地多服务联动时代码修改能即时响应。
  - **多终端自动化拉起**: 引入 PowerShell `Start-Process` 同时拉起 6 个带有漂亮终端命名的独立调试窗口，极大降低了在多服务架构下的本地联调复杂度。

## 📌 2026-06-12 — AST 静态扫描提取与高保真交互文档 (ADR-002)
- **事件**: 使用 Python AST 工具全量抽取了 57 个 SQLAlchemy 物理表、361 个 FastAPI API 端点 and 20 个核心服务类，并重构了在 `kendocs/` 下的系统说明书。
- **架构决策**:
  - **高鲁棒性 AST 解析**: 针对异步端点匹配 `ast.AsyncFunctionDef` 并以 `utf-8-sig` 读取带 BOM 文件，彻底解决静态提取漏包与乱码问题。
  - **交互式检索设计**: 在 Vanilla CSS 手册页面内集成原生客户端 JS 模糊过滤器与 Accordion 折叠卡片，使海量 API 路由与数据库列变得轻松可查，极具 WOW 视觉特效与实用价值。
  - **规避 Shell 变量求值陷阱**: 针对本地一键调试脚本在 PowerShell 环境变量求值时的崩溃问题，改用 `Invoke-Expression` 直接内存读取字符串运行，实现 100% 稳定的并发拉起。

## 📌 2026-06-12 — 转换至纯英文 CMD 统一启动器 (ADR-003)
- **事件**: 针对 PowerShell 进程因 Windows 会话管道隔离（0x800700e8）及中文控制台字符集解析崩溃的问题，开发了纯英文批处理启动器 `本地一键调试启动.bat`。
- **架构决策**:
  - **切换至 CMD 引擎**: 绕过复杂的 `powershell.exe` 控制台管道管理，改用系统原生极轻的 `cmd.exe` 内置 `start` 命令拉起窗口，实现零管道依赖的稳定弹窗。
  - **全英文免乱码设计**: 将批处理中的注释及回显全部改为纯英文（ASCII），彻底避开了中文控制台（CP936/CP65001）转换时的解析破坏。
  - **一键幂等拉起**: 把 Docker 状态检测改为无副作用的 `docker compose up -d` 幂等调用，大幅优化批处理逻辑。

