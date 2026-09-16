@echo off
chcp 65001 >nul
title 闲鱼自动回复系统 - 一键重启

echo ===============================================
echo   闲鱼自动回复系统 - 一键重启
echo ===============================================
echo.

echo [1/2] 停止全部服务...
call "%~dp0scripts\stop_service_by_port.bat" "Frontend" "9000"
call "%~dp0scripts\stop_service_by_port.bat" "Scheduler" "8091"
call "%~dp0scripts\stop_service_by_port.bat" "WebSocket" "8090"
call "%~dp0scripts\stop_service_by_port.bat" "Backend-Web" "8089"

echo.
echo 等待 3 秒释放端口...
timeout /t 3 /nobreak >nul

echo.
echo [2/2] 启动全部服务...
echo.
call "%~dp0start_all.bat"
