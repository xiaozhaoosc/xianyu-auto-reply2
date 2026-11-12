#!/bin/bash
# Xianyu 服务外部看门狗：探测端口/健康/账号在线 → 自愈重启 → 独立飞书告警
# 由 systemd user timer 每分钟调度；不依赖主系统任何组件（仅 curl + systemctl --user）
#
# 环境变量（测试用）：
#   WATCHDOG_DRY_RUN=1              只记录动作，不真重启、不真发飞书
#   WATCHDOG_FORCE_DOWN=<unit>      强制把该 unit 判为端口不通，用于演练自愈分支
#   WATCHDOG_FORCE_UNHEALTHY=<unit> 强制把该 unit 判为端口在但健康检查失败

PROJECT_DIR="/home/ken4zhao/Documents/online/xianyu-auto-reply2/xianyu-auto-reply"
LOG_FILE="${PROJECT_DIR}/logs/watchdog.log"
# 注意：这里必须写绝对路径，不能用 ${HOME}。
# systemd --user 下 HOME=/home/ken4zhao，而某些调用方（如 agent 的 shell）HOME 是别的目录，
# 用 ${HOME} 会让冷却时间戳和维护 flag 落到两个不同目录 → 维护抑制静默失效。
STATE_DIR="/home/ken4zhao/.local/state/xianyu-watchdog"
mkdir -p "$(dirname "$LOG_FILE")" "$STATE_DIR"

# 飞书 webhook（独立于主系统通知链路）
FEISHU_WEBHOOK="$(cat "${PROJECT_DIR}/deploy/systemd/feishu_webhook.txt" 2>/dev/null | head -1)"

# 告警冷却：恢复类告警压 30 分钟防风暴；
# 「自愈失败/需人工介入」是最严重的告警，只压 5 分钟，且与恢复类用不同的 key，
# 避免一条「已恢复✅」把后续真正的「❌需人工介入」吞掉 30 分钟。
COOLDOWN_RECOVERED=1800
COOLDOWN_FAILED=300
COOLDOWN_UNHEALTHY=900

# 维护抑制：运维主动重启前 touch 此文件，看门狗跳过本轮检查，避免误报。
# 设 15 分钟自动失效，防止忘记删除导致看门狗长期哑火。
MAINT_FLAG="${STATE_DIR}/maintenance"
MAINT_MAX_AGE=900

log() { echo "[$(date '+%F %T')] $*" >> "$LOG_FILE"; }

# ---- 维护窗口检查 ----
if [ -f "$MAINT_FLAG" ]; then
    flag_age=$(( $(date +%s) - $(stat -c %Y "$MAINT_FLAG" 2>/dev/null || echo 0) ))
    if [ "$flag_age" -lt "$MAINT_MAX_AGE" ]; then
        log "🔧 维护窗口中（flag 已存在 ${flag_age}s），跳过本轮检查"
        exit 0
    fi
    log "维护 flag 已超过 ${MAINT_MAX_AGE}s 自动失效，删除并恢复正常巡检"
    rm -f "$MAINT_FLAG"
fi

# $1=告警key $2=冷却秒数 $3=正文
send_feishu() {
    local key="$1" cooldown="$2" text="$3"
    local stamp_file="${STATE_DIR}/${key}.last"
    local now
    now=$(date +%s)
    if [ -f "$stamp_file" ]; then
        local last
        last=$(cat "$stamp_file" 2>/dev/null || echo 0)
        if (( now - last < cooldown )); then
            log "告警[${key}]冷却中(${cooldown}s)，跳过飞书发送"
            return
        fi
    fi
    if [ "${WATCHDOG_DRY_RUN}" = "1" ]; then
        log "[DRY_RUN] 本应发送飞书告警[${key}]: ${text}"
        return
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

# ---- 探测原语 ----
# TCP 层连通性
tcp_up() { (echo > "/dev/tcp/127.0.0.1/$1") 2>/dev/null; }

# HTTP 健康：带 -f，4xx/5xx 一律算不健康（原实现不带 -f，500 也算健康 → 假死无法发现）
http_ok() { curl -sf -o /dev/null -m 5 "http://127.0.0.1:$1$2" 2>/dev/null; }

# 等服务真正可服务：systemctl is-active 只说明进程在跑，
# 实测 backend 启动到端口可用要 7-8 秒，原实现 sleep 8 + is-active 会在边界上误报「已恢复」。
# 这里改为轮询真实端口+健康端点，最多等 45 秒。
wait_healthy() {
    local port="$1" path="$2" i
    for i in $(seq 1 45); do
        sleep 1
        if tcp_up "$port" && http_ok "$port" "$path"; then
            log "  └ ${i}s 后端口+健康检查均通过"
            return 0
        fi
    done
    return 1
}

restart_service() {
    local unit="$1" port="$2" path="$3"
    log "尝试自愈: systemctl --user restart ${unit}"
    if [ "${WATCHDOG_DRY_RUN}" = "1" ]; then
        log "[DRY_RUN] 本应执行 systemctl --user restart ${unit}，跳过并视为恢复成功"
        return 0
    fi
    systemctl --user restart "$unit" 2>>"$LOG_FILE"
    wait_healthy "$port" "$path"
}

# ---- 1. 四个服务端口 + 健康探测 ----
declare -A PORTS=(
    ["xianyu-backend"]=8089
    ["xianyu-scheduler"]=8091
    ["xianyu-websocket"]=8090
    ["xianyu-frontend"]=9000
)
# 探测路径：三个 Python 服务都有 /health；前端是 Vite dev server，
# SPA fallback 会让任意路径都返回 200，所以只探 /（等价于端口存活）。
declare -A PROBE=(
    ["xianyu-backend"]=/health
    ["xianyu-scheduler"]=/health
    ["xianyu-websocket"]=/health
    ["xianyu-frontend"]=/
)

for unit in "${!PORTS[@]}"; do
    port="${PORTS[$unit]}"
    path="${PROBE[$unit]}"

    # --- 情形 A：端口不通 → 自愈重启 ---
    if [ "${WATCHDOG_FORCE_DOWN}" = "$unit" ] || ! tcp_up "$port"; then
        # 二次确认：避免撞上服务自身正常重启的瞬间窗口
        sleep 3
        if [ "${WATCHDOG_FORCE_DOWN}" != "$unit" ] && tcp_up "$port"; then
            log "ℹ️ ${unit}(${port}) 首次探测不通，3秒复查已恢复，不告警"
            continue
        fi
        log "❌ ${unit}(${port}) 端口不通"
        if restart_service "$unit" "$port" "$path"; then
            send_feishu "${unit}_recovered" "$COOLDOWN_RECOVERED" \
                "${unit} 端口${port}失联，已自动重启恢复 ✅"
        else
            send_feishu "${unit}_failed" "$COOLDOWN_FAILED" \
                "${unit} 端口${port}失联，自动重启后45秒内仍未恢复 ❌ 需人工介入"
        fi
        continue
    fi

    # --- 情形 B：端口在但健康检查失败（假死）→ 也要自愈 ---
    if [ "${WATCHDOG_FORCE_UNHEALTHY}" = "$unit" ] || ! http_ok "$port" "$path"; then
        sleep 5
        if [ "${WATCHDOG_FORCE_UNHEALTHY}" != "$unit" ] && http_ok "$port" "$path"; then
            log "ℹ️ ${unit}(${port}${path}) 首次健康检查失败，5秒复查已恢复，不告警"
            continue
        fi
        log "⚠️ ${unit}(${port}) 端口在但 ${path} 健康检查失败（疑似假死）"
        if restart_service "$unit" "$port" "$path"; then
            send_feishu "${unit}_unhealthy" "$COOLDOWN_UNHEALTHY" \
                "${unit} 端口${port}在但健康检查失败（假死），已自动重启恢复 ✅"
        else
            send_feishu "${unit}_failed" "$COOLDOWN_FAILED" \
                "${unit} 假死且自动重启后45秒内仍未恢复 ❌ 需人工介入"
        fi
    fi
done

# ---- 2. 账号在线状态探测（websocket 存活时才有意义）----
get_online_count() {
    curl -s -m 8 http://127.0.0.1:8090/internal/accounts/connection-stats 2>/dev/null \
        | python3 -c "import sys,json;d=json.load(sys.stdin).get('data',{});print(len(d.get('connected_account_ids',[])))" 2>/dev/null
}
ONLINE=$(get_online_count)
if [ -n "$ONLINE" ] && [ "$ONLINE" -eq 0 ]; then
    # 二次确认：Token刷新/主动重连会有约1秒的 connecting 过渡窗，
    # 首次读到0可能是撞上窗口，等15秒复查，仍为0才告警
    sleep 15
    ONLINE_RETRY=$(get_online_count)
    if [ -n "$ONLINE_RETRY" ] && [ "$ONLINE_RETRY" -eq 0 ]; then
        log "⚠️ WebSocket存活但账号在线数=0（二次确认仍为0）"
        send_feishu "accounts_offline" "$COOLDOWN_RECOVERED" \
            "WebSocket服务存活但闲鱼账号全部离线（在线数=0），请检查Cookie是否过期"
    else
        log "首次读数为0系重连过渡窗，复查已恢复(${ONLINE_RETRY})，不告警"
    fi
fi

exit 0
