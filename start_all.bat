@echo off
chcp 65001 >nul
title 闲鱼自动回复系统 - 一键启动

set "PROJECT_ROOT=%~dp0"
set "PLAYWRIGHT_BROWSERS_PATH=%PROJECT_ROOT%.browsers"

echo ===============================================
echo   闲鱼自动回复系统 - 一键启动
echo ===============================================
echo.
echo 项目根目录: %PROJECT_ROOT%
echo Playwright 浏览器: %PLAYWRIGHT_BROWSERS_PATH%
echo.

echo [1/4] 启动 Backend-Web (端口 8089)...
start "Backend-Web (8089)" /D "%PROJECT_ROOT%backend-web" cmd /k "set PLAYWRIGHT_BROWSERS_PATH=%PROJECT_ROOT%.browsers && .\.venv\Scripts\python.exe main.py"

echo [2/4] 启动 WebSocket (端口 8090)...
start "WebSocket (8090)" /D "%PROJECT_ROOT%websocket" cmd /k "set PLAYWRIGHT_BROWSERS_PATH=%PROJECT_ROOT%.browsers && .\.venv\Scripts\python.exe main.py"

echo [3/4] 启动 Scheduler (端口 8091)...
start "Scheduler (8091)" /D "%PROJECT_ROOT%scheduler" cmd /k "set PLAYWRIGHT_BROWSERS_PATH=%PROJECT_ROOT%.browsers && .\.venv\Scripts\python.exe main.py"

echo [4/4] 启动 Frontend (端口 9000)...
start "Frontend (9000)" /D "%PROJECT_ROOT%frontend" cmd /k "npm run dev"

echo.
echo ===============================================
echo   全部服务已在新窗口启动
echo.
echo   Backend-Web : http://localhost:8089/docs
echo   Frontend    : http://localhost:9000
echo   默认账号     : admin / admin123
echo.
echo   各服务在独立窗口运行，关闭窗口即停止该服务。
echo   如需一次性停止全部服务，运行: 停止所有服务.bat
echo ===============================================
echo.
echo 本窗口可关闭。服务启动需要约 30-60 秒（含数据库初始化）。
pause
