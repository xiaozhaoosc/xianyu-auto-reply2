#!/bin/bash
echo "========================================"
echo " 闲鱼智能运营平台 v2.0 启动脚本"
echo "========================================"

echo "[1/3] 编译 Java 项目..."
cd java-platform
mvn clean package -DskipTests -q || { echo "编译失败！"; exit 1; }

echo "[2/3] 启动后端服务..."
mkdir -p ../logs
nohup java -jar platform-server/target/platform-server-2.0.0-SNAPSHOT.jar > ../logs/server.log 2>&1 &
sleep 5
nohup java -jar platform-scheduler/target/platform-scheduler-2.0.0-SNAPSHOT.jar > ../logs/scheduler.log 2>&1 &
sleep 3
nohup java -jar platform-promotion/target/platform-promotion-2.0.0-SNAPSHOT.jar > ../logs/promotion.log 2>&1 &

echo "[3/3] 启动前端..."
cd ../frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &

echo ""
echo "========================================"
echo " 所有服务已启动！"
echo " 前端: http://localhost:9000"
echo " 后端 API: http://localhost:8089"
echo " JobRunr Dashboard: http://localhost:8000"
echo "========================================"
