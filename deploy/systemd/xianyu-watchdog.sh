#!/bin/bash
# Xianyu 服务外部看门狗：探测端口/账号在线 → 自愈重启 → 独立飞书告警
# 由 systemd user timer 每分钟调度；不依赖主系统任何组件（仅 curl + systemctl --user）

PROJECT_DIR="/home/ken4zhao/Documents/online/xianyu-auto-reply2/xianyu-auto-reply"
LOG_FILE="${PROJECT_DIR}/logs/watchdog.log"
STATE_DIR="${HOME}/.local/state/xianyu-watchdog"
mkdir -p "$(dirname "$LOG_FILE")" "$STATE_DIR"

# 飞书 webhook（独立于主系统通知链路）
FEISHU_WEBHOOK="$(cat "${PROJECT_DIR}/deploy/systemd/feishu_webhook.txt" 2>/dev/null | head -1)"
ALERT_COOLDOWN=1800  # 同类告警冷却30分钟，防风暴

log() { echo "[$(date '+%F %T')] $*" >> "$LOG_FILE"; }

send_feishu() {
    local key="$1" text="$2"
    local stamp_file="${STATE_DIR}/${key}.last"
    local now=$(date +%s)
    if [ -f "$stamp_file" ]; then
        local last=$(cat "$stamp_file" 2>/dev/null || echo 0)
        if (( now - last < ALERT_COOLDOWN )); then
            log "告警[${key}]冷却中，跳过飞书发送"
            return
        fi
    fi
    echo "$now" > "$stamp_file"
    if [ -n "$FEISHU_WEBHOOK" ]; then
        curl -s -m 10 -X POST "$FEISHU_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"🚨 闲鱼服务看门狗\n${text}\n时间: $(date '+%F %T')\"}}" > /dev/null 2>&1 \
            && log "飞书告警已发送[${key}]" \
            || log "飞书告警发送失败[${key}]"
    else
        log "未配置webhook，仅记录告警[${key}]: ${text}"
    fi
}

restart_service() {
    local unit="$1"
    log "尝试自愈: systemctl --user restart ${unit}"
    systemctl --user restart "$unit" 2>>"$LOG_FILE"
    sleep 8
    systemctl --user is-active "$unit" > /dev/null 2>&1 && return 0 || return 1
}

# ---- 1. 四个服务端口探测 ----
declare -A PORTS=(
    ["xianyu-backend"]=8089
    ["xianyu-scheduler"]=8091
    ["xianyu-websocket"]=8090
    ["xianyu-frontend"]=9000
)
for unit in "${!PORTS[@]}"; do
    port="${PORTS[$unit]}"
    if ! curl -s -o /dev/null -m 5 "http://127.0.0.1:${port}/docs"; then
        # /docs 不一定所有服务都有，退化用端口连通性判断
        if ! (echo > /dev/tcp/127.0.0.1/${port}) 2>/dev/null; then
            log "❌ ${unit}(${port}) 端口不通"
            restart_service "${unit}" \
                && send_feishu "port_${unit}" "${unit} 端口${port}失联，已自动重启恢复 ✅" \
                || send_feishu "port_${unit}" "${unit} 端口${port}失联，自动重启仍失败 ❌ 需人工介入"
        fi
    fi
done

# ---- 2. 账号在线状态探测（websocket 存活时才有意义）----
ONLINE=$(curl -s -m 8 http://127.0.0.1:8090/internal/accounts/connection-stats 2>/dev/null \
    | python3 -c "import sys,json;d=json.load(sys.stdin).get('data',{});print(len(d.get('connected_account_ids',[])))" 2>/dev/null)
if [ -n "$ONLINE" ] && [ "$ONLINE" -eq 0 ]; then
    log "⚠️ WebSocket存活但账号在线数=0"
    send_feishu "accounts_offline" "WebSocket服务存活但闲鱼账号全部离线（在线数=0），请检查Cookie是否过期"
fi

exit 0
