@echo off
echo ========================================
echo  闲鱼智能运营平台 v2.0 启动脚本
echo ========================================
echo.

echo [1/3] 编译 Java 项目...
cd java-platform
call mvn clean package -DskipTests -q
if %ERRORLEVEL% neq 0 (
    echo 编译失败！
    pause
    exit /b 1
)

echo [2/3] 启动后端服务...
start "Platform Server" java -jar platform-server/target/platform-server-2.0.0-SNAPSHOT-exec.jar
timeout /t 5 /nobreak >nul
start "Platform Scheduler" java -jar platform-scheduler/target/platform-scheduler-2.0.0-SNAPSHOT-exec.jar
timeout /t 3 /nobreak >nul
start "Platform Promotion" java -jar platform-promotion/target/platform-promotion-2.0.0-SNAPSHOT-exec.jar
timeout /t 3 /nobreak >nul

echo [3/3] 启动前端...
cd ..\frontend
start "Frontend Dev" cmd /c npm run dev

echo.
echo ========================================
echo  所有服务已启动！
echo  前端: http://localhost:9000
echo  后端 API: http://localhost:8089
echo  JobRunr Dashboard: http://localhost:8000
echo ========================================
