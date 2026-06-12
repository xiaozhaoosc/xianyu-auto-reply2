# 闲鱼自动回复与运营系统 - 本地一键开发调试启动脚本
# 用法: 在 PowerShell 中运行此脚本

$host.ui.RawUI.WindowTitle = "闲鱼运营系统 - 统一启动器"

# 优雅的彩色输出
function Write-Header($msg) {
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan -Bold
    Write-Host "==================================================" -ForegroundColor Cyan
}

function Write-Info($msg) {
    Write-Host "[*] $msg" -ForegroundColor White
}

function Write-Success($msg) {
    Write-Host "[+] $msg" -ForegroundColor Green
}

function Write-Warn($msg) {
    Write-Host "[!] $msg" -ForegroundColor Yellow
}

Write-Header "闲鱼自动回复与运营系统 - 本地开发调试启动器"

# 1. 检查 Docker 开发底座状态
Write-Info "正在检查 MySQL & Redis 容器底座状态..."
$containers = docker ps --format '{{.Names}}'

$mysqlRunning = $containers -contains "xianyu-dev-mysql"
$redisRunning = $containers -contains "xianyu-dev-redis"

if (-not $mysqlRunning -or -not $redisRunning) {
    Write-Warn "检测到 MySQL 或 Redis 开发底座未启动，正在尝试为您启动..."
    docker compose -f docker-compose.dev-db.yml up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Error "启动 Docker 底座失败，请确保 Docker 正在运行！"
        exit 1
    }
    Write-Success "Docker 底座 MySQL 和 Redis 容器启动成功！"
} else {
    Write-Success "MySQL & Redis 开发底座已在后台运行中。"
}

# 2. 检查 Python 虚拟环境
$venvPath = Join-Path (Get-Location) "venv"
if (-not (Test-Path $venvPath)) {
    Write-Warn "未检测到 venv 虚拟环境，请先等待依赖安装任务完成！"
    exit 1
}

# 2.5 同步根目录 .env 配置到各子服务中
Write-Info "正在同步环境变量配置文件 .env 到各后端子项目中..."
$envFile = Join-Path (Get-Location) ".env"
if (Test-Path $envFile) {
    Copy-Item -Path $envFile -Destination (Join-Path (Get-Location) "backend-web\.env") -Force
    Copy-Item -Path $envFile -Destination (Join-Path (Get-Location) "websocket\.env") -Force
    Copy-Item -Path $envFile -Destination (Join-Path (Get-Location) "scheduler\.env") -Force
    Copy-Item -Path $envFile -Destination (Join-Path (Get-Location) "promotion\backend\.env") -Force
    Write-Success "环境变量配置文件 .env 同步完成！"
} else {
    Write-Warn "未在根目录下检测到 .env 配置文件！"
}

# 2.6 清理占用端口的旧服务进程以防端口冲突，并关闭其宿主终端窗口
Write-Info "正在清理可能占用调试端口的旧服务进程及关闭旧终端窗口..."
$ports = @(8089, 8090, 8091, 8092, 9000, 9001)
foreach ($port in $ports) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($conn) {
            foreach ($c in $conn) {
                $pid = $c.OwningProcess
                if ($pid) {
                    try {
                        # 获取父进程（如启动它的 cmd.exe 或者是 powershell.exe）并关闭对应窗口
                        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $pid" -ErrorAction SilentlyContinue
                        if ($proc -and $proc.ParentProcessId) {
                            $parent = Get-Process -Id $proc.ParentProcessId -ErrorAction SilentlyContinue
                            if ($parent -and ($parent.ProcessName -eq 'cmd' -or $parent.ProcessName -eq 'powershell' -or $parent.ProcessName -eq 'pwsh')) {
                                Stop-Process -Id $proc.ParentProcessId -Force -ErrorAction SilentlyContinue
                            }
                        }
                    } catch {
                        # 忽略父进程查杀异常
                    }
                    try {
                        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    } catch {
                        # 忽略子进程查杀异常
                    }
                }
            }
        }
    } catch {
        # 忽略连接查询异常
    }
}
Write-Success "端口及旧终端窗口自动回收完成！"

Write-Header "正在多终端窗口中拉起各项子服务..."

# 3. 启动后端 API (backend-web)
Write-Info "正在拉起终端 1：Backend-Web 服务 (端口 8089)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { title '[Backend-Web :8089]'; cd backend-web; ..\venv\Scripts\python.exe main.py }"

# 4. 启动 WebSocket (websocket)
Write-Info "正在拉起终端 2：WebSocket 通信核心 (端口 8090)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { title '[WebSocket :8090]'; cd websocket; ..\venv\Scripts\python.exe main.py }"

# 5. 启动 Scheduler (scheduler)
Write-Info "正在拉起终端 3：Scheduler 定时器 (端口 8091)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { title '[Scheduler :8091]'; cd scheduler; ..\venv\Scripts\python.exe main.py }"

# 6. 启动返佣后端 (promotion/backend)
Write-Info "正在拉起终端 4：推广返佣后端 (端口 8092)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { title '[Promotion-Backend :8092]'; cd promotion/backend; ..\venv\Scripts\python.exe main.py }"

# 7. 启动主系统前端 (frontend)
Write-Info "正在拉起终端 5：主系统前端 (端口 9000)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { title '[Frontend :9000]'; cd frontend; npm run dev }"

# 8. 启动返佣前端 (promotion/frontend)
Write-Info "正在拉起终端 6：推广返佣前端 (端口 9001)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { title '[Promotion-Frontend :9001]'; cd promotion/frontend; npm run dev }"

Write-Success "`n所有 6 个服务已分别在独立的终端窗口中拉起！"
Write-Info "您可以前往各自弹出的窗口中查阅调试日志。"
Write-Info "管理端网址: http://localhost:9000 (默认账号: admin / admin123)"
Write-Info "返佣端网址: http://localhost:9001"
Write-Info "后端 Swagger 文档: http://localhost:8089/docs"
Write-Host "==================================================" -ForegroundColor Cyan
