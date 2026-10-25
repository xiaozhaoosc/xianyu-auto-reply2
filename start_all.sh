#!/bin/bash
# 在独立窗口启动全部 4 个服务（含 .browsers 环境变量）

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PLAYWRIGHT_BROWSERS_PATH="${PROJECT_DIR}/.browsers"
export NO_PROXY="localhost,127.0.0.1"
# 清除可能干扰的系统代理（Playwright 滑块浏览器已加 --no-proxy-server，此处保险）
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy
export BROWSER_HEADLESS=false
# 服务器有图形界面时，设置 DISPLAY 让 Playwright 能打开浏览器窗口
export DISPLAY="${DISPLAY:-:10}"
# Token刷新间隔（秒），23小时=82800秒，默认20小时=72000秒
export TOKEN_REFRESH_INTERVAL="${TOKEN_REFRESH_INTERVAL:-82800}"

# 数据库/Redis 连接由各服务目录下的 .env 提供（参考各服务 .env.example）。
# 本脚本不内置任何主机、账号或口令；如需覆盖，请在运行前于外部环境导出 MYSQL_* / REDIS_* 变量。
export HOST="${HOST:-0.0.0.0}"

VENV_PYTHON="${PROJECT_DIR}/.venv/bin/python"

if [ ! -f "${VENV_PYTHON}" ]; then
    echo "未找到 venv Python: ${VENV_PYTHON}"
    echo "请先创建虚拟环境: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 检测图形终端
TERM_BIN=""
if command -v gnome-terminal &>/dev/null; then
    TERM_BIN="gnome-terminal"
elif command -v xterm &>/dev/null; then
    TERM_BIN="xterm"
fi

start_service() {
    local name="$1"
    local dir="$2"
    local cmd="$3"

    if [ -n "${TERM_BIN}" ]; then
        echo "启动 ${name} (独立窗口)..."
        if [ "${TERM_BIN}" = "gnome-terminal" ]; then
            gnome-terminal -- bash -c "cd '${dir}' && ${cmd}; echo ''; echo '[${name}] 已退出，按回车关闭'; read"
        else
            xterm -e "cd '${dir}' && ${cmd}; read" &
        fi
    else
        echo "启动 ${name} (后台)..."
        mkdir -p "${PROJECT_DIR}/logs"
        cd "${dir}" && setsid nohup ${cmd} > "${PROJECT_DIR}/logs/$(basename ${dir}).log" 2>&1 < /dev/null &
        disown
    fi
    sleep 1
}

# 1. Backend-Web (8089)
start_service "Backend-Web" "${PROJECT_DIR}/backend-web" \
    "${VENV_PYTHON} main.py"

# 等待 Backend-Web 就绪（内部 API 令牌由 backend 首次启动时初始化）
if command -v curl >/dev/null 2>&1; then
    echo "等待 Backend-Web 健康检查..."
    BACKEND_READY=0
    for _ in $(seq 1 90); do
        if curl -fsS --max-time 2 http://127.0.0.1:8089/health >/dev/null 2>&1; then
            BACKEND_READY=1
            break
        fi
        sleep 2
    done
    if [ "$BACKEND_READY" -eq 1 ]; then
        echo "Backend-Web 已就绪"
    else
        echo "WARNING: Backend-Web 180 秒内未就绪，Scheduler/WebSocket 可能因内部令牌未初始化而启动失败"
    fi
else
    echo "WARNING: 未找到 curl，跳过 Backend-Web 健康等待"
fi

# 2. Scheduler (8091)
start_service "Scheduler" "${PROJECT_DIR}/scheduler" \
    "${VENV_PYTHON} main.py"

# 3. WebSocket (8090)
start_service "WebSocket" "${PROJECT_DIR}/websocket" \
    "${VENV_PYTHON} main.py"

# 4. Frontend (9000)
start_service "Frontend" "${PROJECT_DIR}/frontend" \
    "npm run dev"

echo ""
echo "全部服务已启动："
echo "  Backend-Web: http://localhost:8089"
echo "  Scheduler:   http://localhost:8091"
echo "  WebSocket:   http://localhost:8090"
echo "  Frontend:    http://localhost:9000"
