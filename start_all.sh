#!/bin/bash
# 在独立窗口启动全部 4 个服务（含 .browsers 环境变量）

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PLAYWRIGHT_BROWSERS_PATH="${PROJECT_DIR}/.browsers"
export NO_PROXY="localhost,127.0.0.1"
# 清除可能干扰的系统代理（Playwright 滑块浏览器已加 --no-proxy-server，此处保险）
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy
export BROWSER_HEADLESS=false

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
        cd "${dir}" && nohup ${cmd} > "logs/$(basename ${dir}).log" 2>&1 &
    fi
    sleep 1
}

# 1. Backend-Web (8089)
start_service "Backend-Web" "${PROJECT_DIR}/backend-web" \
    "PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH} NO_PROXY=${NO_PROXY} ${VENV_PYTHON} main.py"

# 2. Scheduler (8091)
start_service "Scheduler" "${PROJECT_DIR}/scheduler" \
    "PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH} NO_PROXY=${NO_PROXY} ${VENV_PYTHON} main.py"

# 3. WebSocket (8090)
start_service "WebSocket" "${PROJECT_DIR}/websocket" \
    "PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH} NO_PROXY=${NO_PROXY} BROWSER_HEADLESS=false ${VENV_PYTHON} main.py"

# 4. Frontend (9000)
start_service "Frontend" "${PROJECT_DIR}/frontend" \
    "npm run dev"

echo ""
echo "全部服务已启动："
echo "  Backend-Web: http://localhost:8089"
echo "  Scheduler:   http://localhost:8091"
echo "  WebSocket:   http://localhost:8090"
echo "  Frontend:    http://localhost:9000"
