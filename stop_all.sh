#!/bin/bash
# 按端口停止 Frontend(9000)/Scheduler(8091)/WebSocket(8090)/Backend-Web(8089)

PORTS=(9000 8091 8090 8089)
NAMES=("Frontend" "Scheduler" "WebSocket" "Backend-Web")

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${NAMES[$i]}
    PIDS=$(lsof -t -i:${PORT} 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo "停止 ${NAME} (端口 ${PORT}, PID: ${PIDS})"
        kill ${PIDS} 2>/dev/null
        sleep 1
        PIDS=$(lsof -t -i:${PORT} 2>/dev/null)
        if [ -n "$PIDS" ]; then
            echo "  强制杀掉: ${PIDS}"
            kill -9 ${PIDS} 2>/dev/null
        fi
        echo "  ${NAME} 已停止"
    else
        echo "${NAME} (端口 ${PORT}) 未运行"
    fi
done

echo "全部服务已停止"
