#!/bin/bash
# 重启全部服务：先停止 → 等 3 秒 → 再启动

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========== 停止全部服务 =========="
bash "${SCRIPT_DIR}/stop_all.sh"

echo ""
echo "等待 3 秒释放端口..."
sleep 3

echo ""
echo "========== 启动全部服务 =========="
bash "${SCRIPT_DIR}/start_all.sh"
