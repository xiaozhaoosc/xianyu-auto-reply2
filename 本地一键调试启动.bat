@echo off
title Xianyu Auto Reply - Dev Startup Launcher
chcp 65001 >nul

echo ==================================================
echo   Xianyu Auto Reply System - Local Dev Launcher
echo ==================================================

:: 1. Ensure Docker MySQL & Redis are running (Idempotent)
echo [*] Checking MySQL and Redis container status...
docker compose -f docker-compose.dev-db.yml up -d
if %errorlevel% neq 0 (
    echo [!] Failed to start docker containers. Please make sure Docker is running.
    pause
    exit /b 1
)

:: 2. Sync .env configuration file to all backend projects
echo [*] Syncing env file .env to subprojects...
if exist ".env" (
    copy /y ".env" "backend-web\.env" >nul
    copy /y ".env" "websocket\.env" >nul
    copy /y ".env" "scheduler\.env" >nul
    copy /y ".env" "promotion\backend\.env" >nul
    echo [+] Environment config synced successfully!
) else (
    echo [!] Warning: .env file not found!
)

:: 3. Automatically clean up processes occupying debug ports and close their hosting terminal windows
echo [*] Cleaning up old debug processes and closing old terminal windows...
powershell -Command "foreach($port in @(8089, 8090, 8091, 8092, 9000, 9001)){$conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue; if($conn){foreach($c in $conn){$pid = $c.OwningProcess; $proc = Get-CimInstance Win32_Process -Filter ('ProcessId = ' + $pid) -ErrorAction SilentlyContinue; if($proc -and $proc.ParentProcessId){$parent = Get-Process -Id $proc.ParentProcessId -ErrorAction SilentlyContinue; if($parent -and @('cmd','powershell','pwsh') -contains $parent.ProcessName){Stop-Process -Id $proc.ParentProcessId -Force -ErrorAction SilentlyContinue}}; Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue}}}"
echo [+] Ports and old terminal windows cleanup completed!

:: 4. Launch 6 services concurrently in separate windows for interactive debugging
echo [*] Launching 6 debug windows...

:: 1. Backend-Web API
start "Backend-Web :8089" cmd /k "chcp 65001 >nul && title [Backend-Web :8089] && cd /d backend-web && ..\venv\Scripts\python.exe main.py"

:: 2. WebSocket Core
start "WebSocket :8090" cmd /k "chcp 65001 >nul && title [WebSocket :8090] && cd /d websocket && ..\venv\Scripts\python.exe main.py"

:: 3. Scheduler Task
start "Scheduler :8091" cmd /k "chcp 65001 >nul && title [Scheduler :8091] && cd /d scheduler && ..\venv\Scripts\python.exe main.py"

:: 4. Promotion Backend (Corrected python path to ..\..\venv)
start "Promotion-Backend :8092" cmd /k "chcp 65001 >nul && title [Promotion-Backend :8092] && cd /d promotion\backend && ..\..\venv\Scripts\python.exe main.py"

:: 5. Frontend Portal
start "Frontend :9000" cmd /k "chcp 65001 >nul && title [Frontend :9000] && cd /d frontend && npm run dev"

:: 6. Promotion Frontend
start "Promotion-Frontend :9001" cmd /k "chcp 65001 >nul && title [Promotion-Frontend :9001] && cd /d promotion\frontend && npm run dev"

echo ==================================================
echo [+] All 6 debug terminals launched in separate windows!
echo [*] Portal: http://localhost:9000 (admin / admin123)
echo [*] Promotion: http://localhost:9001
echo [*] API Docs: http://localhost:8089/docs
echo ==================================================
