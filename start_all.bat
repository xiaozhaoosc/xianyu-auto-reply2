@echo off
rem ============================================================
rem  Start all 4 services in separate windows (with .browsers env)
rem  Backend-Web:8089  Scheduler:8091  WebSocket:8090  Frontend:9000
rem ============================================================

setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0"
rem strip trailing backslash
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

set "PLAYWRIGHT_BROWSERS_PATH=%PROJECT_DIR%\.browsers"
set "NO_PROXY=localhost,127.0.0.1"
rem clear possibly interfering system proxy (Playwright slider browser already uses --no-proxy-server)
set "HTTP_PROXY="
set "HTTPS_PROXY="
set "ALL_PROXY="
set "http_proxy="
set "https_proxy="
set "BROWSER_HEADLESS=false"
rem Token refresh interval in seconds, keep consistent with websocket/.env (20h=72000)
if not defined TOKEN_REFRESH_INTERVAL set "TOKEN_REFRESH_INTERVAL=72000"

rem 数据库/Redis 连接由各服务目录下的 .env 提供（参考各服务 .env.example）。
rem 本脚本不内置任何主机、账号或口令；如需覆盖，请在运行前于外部环境设置 MYSQL_* / REDIS_* 变量。
if not defined HOST set "HOST=0.0.0.0"

set "VENV_PYTHON=%PROJECT_DIR%\.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo venv Python not found: %VENV_PYTHON%
    echo Create it first: python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
    exit /b 1
)

rem 1. Backend-Web (8089)
echo Starting Backend-Web (8089)...
start "Backend-Web (8089)" /d "%PROJECT_DIR%\backend-web" cmd /k ""%VENV_PYTHON%" main.py"

rem Wait for Backend-Web health before starting dependent services.
rem Scheduler/WebSocket load the internal API token that backend initializes on first run.
echo Waiting for Backend-Web to become healthy...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; for($i=0;$i -lt 90;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 'http://127.0.0.1:8089/health'; if($r.StatusCode -eq 200){ $ok=$true; break } } catch {}; Start-Sleep -Seconds 2 }; if(-not $ok){ exit 1 }"
if errorlevel 1 echo WARNING: Backend-Web not ready in 180s; Scheduler/WebSocket may fail on internal token init.

rem 2. Scheduler (8091)
echo Starting Scheduler (8091)...
start "Scheduler (8091)" /d "%PROJECT_DIR%\scheduler" cmd /k ""%VENV_PYTHON%" main.py"

rem 3. WebSocket (8090)
echo Starting WebSocket (8090)...
start "WebSocket (8090)" /d "%PROJECT_DIR%\websocket" cmd /k ""%VENV_PYTHON%" main.py"

rem 4. Frontend (9000)
echo Starting Frontend (9000)...
start "Frontend (9000)" /d "%PROJECT_DIR%\frontend" cmd /k "npm run dev"

echo.
echo All services started:
echo   Backend-Web: http://localhost:8089
echo   Scheduler:   http://localhost:8091
echo   WebSocket:   http://localhost:8090
echo   Frontend:    http://localhost:9000
pause
