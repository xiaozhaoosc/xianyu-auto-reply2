@echo off
chcp 65001 >nul
title 闲鱼自动回复系统 - 停止全部服务

echo ===============================================
echo   正在停止全部服务...
echo ===============================================
echo.

call "%~dp0scripts\stop_service_by_port.bat" "Frontend" "9000"
call "%~dp0scripts\stop_service_by_port.bat" "Scheduler" "8091"
call "%~dp0scripts\stop_service_by_port.bat" "WebSocket" "8090"
call "%~dp0scripts\stop_service_by_port.bat" "Backend-Web" "8089"

echo.
echo ===============================================
echo   全部服务已停止
echo ===============================================
pause
