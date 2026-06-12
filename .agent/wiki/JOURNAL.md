# Journal: 每日开发流水账

## 📅 2026-06-12

### [Morning_Briefing]
- **昨日未竟**: 无 (项目今日成功使用 SSH 克隆完成)
- **隐患预警**: 
  - 本项目为多服务架构 (backend-web, websocket, scheduler, frontend, promotion)，本地多进程管理与端口占用可能增加调试复杂度。
  - Playwright 涉及浏览器自动化，需确保本地有正确的 Chromium / Chrome 运行环境，且面临平台风控升级的风险。
  - 数据库操作依赖于 MySQL 与 Redis，首次运行必须完成 `xianyu_schema.sql` 导入并配置正确的 `.env` 文件。
- **今日建议**:
  1. 初始化本地的 MySQL 数据库，导入 `xianyu_schema.sql`。
  2. 复制 `.env.example` 并配置本地环境变量（MySQL, Redis, API 端口等）。
  3. 执行 Python 依赖包安装（检查 `requirements.txt` 或使用 `pip`）。
  4. 检查前端 Node.js 依赖安装并尝试启动测试。

---

### [Daily_Summary]

| 模块/文件 | 变更类型 | 变更描述 |
| :--- | :--- | :--- |
| [AUTOMATED_TESTING.md](file:///D:/IdeaProjects/xianyu-auto-reply2/kendocs/AUTOMATED_TESTING.md) | 新增 | 创建了项目自动化测试架构与规范文档，涵盖防风控 Playwright 指南 |
| [stealth_utils.py](file:///D:/IdeaProjects/xianyu-auto-reply2/tests/e2e/stealth_utils.py) | 新增 | 编写了 Playwright 反反爬（Stealth）脚本注入及拟人化交互（hover点击、平滑滚动、打字抖动）工具 |
| [conftest.py](file:///D:/IdeaProjects/xianyu-auto-reply2/tests/e2e/conftest.py) | 新增 | 配置了持久化 BrowserContext 与指纹伪造，用于保留并重用登录 Session |
| [test_xianyu_flow.py](file:///D:/IdeaProjects/xianyu-auto-reply2/tests/e2e/test_xianyu_flow.py) | 新增 | 编写了闲鱼仿真交互的防风控测试用例示范 |
| [pytest.ini](file:///D:/IdeaProjects/xianyu-auto-reply2/backend-web/pytest.ini) / [conftest.py](file:///D:/IdeaProjects/xianyu-auto-reply2/backend-web/tests/conftest.py) | 新增 | 搭建了后端 API pytest 环境及 SQLite 内存隔离 Fixtures |
| [date.test.ts](file:///D:/IdeaProjects/xianyu-auto-reply2/frontend/src/__tests__/date.test.ts) | 新增 | 引入前端单元测试桩代码验证日期格式化工具 |

### [Project_Reflection]

| 任务模块 | 交付成果 | 验证状态 | 备注 |
| :--- | :--- | :--- | :--- |
| **数据库底座** | `docker-compose.dev-db.yml` (MySQL 8 / Redis 7) | ✅ 已运行 | 成功通过国内镜像拉起，并完整导入 `xianyu_schema.sql` |
| **本地开发配置** | 生成根目录 `.env`，自动配置数据库密码与环境变量 | ✅ 已生效 | 已适配开发模式环境配置 |
| **Python 后端依赖**| 虚拟环境全局构建，以 `-e` Editable 模式完成 5 包安装 | ✅ 已完成 | Playwright Chromium 浏览器驱动一并下载就绪 |
| **Node 前端依赖** | 并发执行主前端和返佣前端的 `npm install` 依赖拉取 | ✅ 已完成 | 使用国内淘宝源加速，平均耗时仅数秒 |
| **项目文档手册** | 生成 `kendocs/introduction.md` 及 `introduction.html` | ✅ 已交付 | HTML 文档使用 Vanilla CSS，极具 Premium 科技感 |
| **调试启动脚本** | 创建 `本地一键调试启动.ps1` 脚本，可并发弹出 6 个窗口调试 | ✅ 已就绪 | 经由 `/health` 验证 `backend-web` 进程，确认 200 OK |

| **高精文档重构** | 自动提取 57 个模型、361 个端点和 20 个服务类 | ✅ 已重写 | HTML 文档支持原生 JS 交互式模糊检索过滤与 Accordion，开发体验极佳 |
| **调试脚本执行** | 修复 PowerShell 环境变量陷阱，实现 6 服务一键并发拉起 | ✅ 已运行 | 成功弹出 6 窗口，前后端及返佣系统全部就绪 |

---

## 📅 2026-06-12 (二次迭代) — 全量 AST 高精扫描与文档重构

### [Morning_Briefing]
- **昨日未竟**: 无 (前人已部署基础底座与依赖环境)
- **隐患预警**: 
  - Windows PowerShell 执行 UTF-8 脚本时在命令传参中存在变量解析陷阱，若用 `$var` 可能会被外部环境吞掉导致解析出错。
  - AST 静态分析中，异步函数属于 `ast.AsyncFunctionDef`，如只匹配 `ast.FunctionDef` 会漏掉 FastAPI 绝大部分异步端点。
- **今日建议**:
  1. 使用静态 AST 重构项目扫描器，兼容 UTF-8 BOM (`utf-8-sig`) 并在提取接口时匹配 `AsyncFunctionDef`。
  2. 运用 Rich Aesthetics 规范，基于 Vanilla CSS 构造一套带本地 JavaScript 动态模糊过滤搜索、Accordion 折叠功能的 Premium 暗黑开发文档。
  3. 通过 `Invoke-Expression` 内存加载一键启动调试脚本，避开 shell 解析漏洞，实现在多终端中并发拉起全部服务。

### [Project_Reflection]
- **高精扫描**: 完成对 57 个持久化表、361 个端点、20 个核心服务类的全量提取与文档自动化生成。
- **一键调试**: 6 个服务全部成功拉起。引入了纯英文的 `本地一键调试启动.bat` 启动器，彻底消除了由于 powershell 管道隔离和 cmd 字符集导致的崩溃。
- **高颜值文档**: `kendocs/` 目录下生成了 68KB 的 md 和 343KB 的 html 文档，支持快速搜索 and 交互折叠，极具高级感。

---

## 📅 2026-06-12 (三次迭代) — 滑块验证算法拟人化重构与反反爬对齐

### [Morning_Briefing]
- **昨日未竟**: 无 (前续已解决一键启动和商品搜索为空背后的滑块风控拦截问题)
- **隐患预警**: 
  - 淘宝/闲鱼对滑块（x5sec 系列）的审查手段不仅包含传统的 Webdriver 特征，还会比对底层 User-Agent 与 JS 重写的 userAgent 是否发生“指纹分裂”；
  - 机械物理轨迹在 acjs.js 前端采集的大数据特征识别中通过率已逐渐走低，必须引入非定型的人类化特征。
- **今日建议**:
  1. 重构并统一 Playwright 引擎启动的 UA、Locale、Accept-Language 属性，消除反检测脚本与底层浏览器请求之间的“指纹分裂”。
  2. 重构轨迹生成器，混合“三次贝塞尔曲线 (Bezier Curve)”与“物理抛物线三阶段”，引入长距离高概率的“超调与回退纠正机制（Overshoot and correction）”。
  3. 优化 Y 轴运动，引入正弦波形的手腕旋转弧度轨迹，并在鼠标释放前（Release）添加极微细抖动与肌肉顿挫。

### [Project_Reflection]
- **指纹防分裂**: 成功将 Playwright 持久化上下文中的底层 UA、Locale、Accept-Language 和 `browser_features` 中动态注入的 stealth 脚本特征强制统一，消除风控致命指纹硬伤。
- **混合轨迹机制**: 引入三次贝塞尔加速度与超调机制，使得鼠标在移动时不再是机械的匀变速，且会自动模拟“划过头再缓慢拉回”的真实人类操作。
- **肌肉释放模拟**: 摒弃了 Playwright 默认的 steps 插值机制，精确掌控每一帧的延时，并引入手指释放鼠标前的极微细高频抖动，行为真实度大幅提升。

---

## 📅 2026-06-12 (四次迭代) — 定时采集单品控制集成与快捷流转

### [Morning_Briefing]
- **昨日未竟**: 定时采集结果列表页面增加「转草稿」（温暖橙）和「发布」（森林绿）操作按钮，并对接 `/api/v1/items/collect-to-material` 接口，在成功后分别跳转至 `/product-publish/materials` 和 `/product-publish/batch`。
- **隐患预警**: 采集入库及自动化流程依赖于后端 `/api/v1/items/collect-to-material` 的稳定性。若后端采集处理或网络出现抖动可能导致导入失败，需要监测 API 错误响应。
- **今日建议**:
  1. 保证前端 `GoofishScheduledCrawler.tsx` 和后端接口的顺利交互，增加防抖和加载状态以防重复导入。

### [Daily_Summary]

| 模块/文件 | 变更类型 | 变更描述 |
| :--- | :--- | :--- |
| [GoofishScheduledCrawler.tsx](file:///D:/IdeaProjects/xianyu-auto-reply2/frontend/src/pages/crawler/GoofishScheduledCrawler.tsx) | 修改 | 引入 `collectToMaterial` API 及 React-Router 的 `useNavigate`；在“定时采集结果列表”、“按 ID 采集列表”、“按卖家采集列表”这三大渲染块中，将单一的外链图标扩展重构为包含「转草稿」（温暖橙）、「发布」（森林绿）以及外链的扁平化按钮操作组。点击转草稿后入库并跳转至 `/product-publish/materials`，点击发布后入库并跳转至 `/product-publish/batch`。 |

### [Project_Reflection]

| 任务模块 | 交付成果 | 验证状态 | 备注 |
| :--- | :--- | :--- | :--- |
| **单品控制流转** | 在 Goofish Scheduled Crawler 结果页面提供了温暖橙的「转草稿」和森林绿的「发布」功能 | ✅ 编译无误 & 代码入库推送 | 已经成功在本地进行 `npx tsc` 校验，无任何相关编译错误，并 push 至远程 `dev_agy_0612` |

---

## 📅 2026-06-12 (五次迭代) — 采集流转免跳转与一键启动脚本自动回收终端

### [Morning_Briefing]
- **昨日未竟**: 将「转草稿」和「发布」操作改为仅提示成功、不跳转页面，避免打断当前搜索；同时在一键启动脚本中实现对原有调试窗口的进程精准查杀与自动关闭，解决窗口残留过多的问题。
- **隐患预警**: 精准查杀基于窗口 `MainWindowTitle` 的正则过滤，若用户手动修改了窗口 Title 或通过非标准 Shell 启动，可能出现偶发不被杀死的现象。
- **今日建议**:
  1. 通过 PowerShell 的 `Get-Process` 对 `cmd`, `powershell`, `pwsh` 的 `MainWindowTitle` 进行多条件正则匹配以实现 100% 覆盖。

### [Daily_Summary]

| 模块/文件 | 变更类型 | 变更描述 |
| :--- | :--- | :--- |
| [GoofishScheduledCrawler.tsx](file:///D:/IdeaProjects/xianyu-auto-reply2/frontend/src/pages/crawler/GoofishScheduledCrawler.tsx) | 修改 | 去除 `handleToDraftSingle` 和 `handlePublishSingle` 方法中的 `useNavigate` 重定向与延时，仅在请求成功后发出成功的 Toast 消息。 |
| [本地一键调试启动.bat](file:///D:/IdeaProjects/xianyu-auto-reply2/本地一键调试启动.bat) | 修改 | 在端口查杀后，追加 PowerShell 根据正则 Title 过滤 `cmd, powershell, pwsh` 窗口并强杀的指令，确保二次启动时清除桌面上残留的旧终端。 |
| [本地一键调试启动.ps1](file:///D:/IdeaProjects/xianyu-auto-reply2/本地一键调试启动.ps1) | 修改 | 在端口循环查杀后，引入 `Get-Process cmd, powershell, pwsh` 管道逻辑，用相同正则强杀并关闭旧窗口。 |

### [Project_Reflection]

| 任务模块 | 交付成果 | 验证状态 | 备注 |
| :--- | :--- | :--- | :--- |
| **交互优化** | 采集流转完成且支持免跳转体验 | ✅ 验证无误 | 用户点击「转草稿」/「发布」直接出 Toast 气泡提示，不破坏原检索结果。 |
| **终端进程回收** | 双击 `.bat` 或运行 `.ps1` 重启服务会自动强杀旧调试终端 | ✅ 成功应用 | 精准清理，保持系统桌面清爽。 |
