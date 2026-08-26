#!/usr/bin/env python3
"""闲鱼店铺聚合数据 → 飞书多维表格（方案3：反转数据流）

为什么要反转：云文档小组件是纯前端，飞书对它启用了 CSP 服务器域名白名单
（官方《云文档小组件-安全配置》：非白名单域名的请求一律拦截，且要求 https 域名
+ 后台配置 + 发新版本审核）。本机后端只有 http://127.0.0.1:8089，永远进不了白名单，
所以由服务端主动把数据写进飞书，看板直接看飞书原生多维表格 —— 零暴露、零跨域。

设计原则：
  · 成功时**完全静默**（无输出、退出码0），便于挂 systemd timer / cron 不打扰用户
  · 失败时输出一行原因并返回非0，让上层告警能捕获
  · 密钥只从 backend-web/.env 读，不写进任何日志或命令行可见处

用法：
  python3 xianyu_dashboard_to_base.py            # 静默同步一次
  python3 xianyu_dashboard_to_base.py --verbose   # 打印取到的数据与写入结果
  python3 xianyu_dashboard_to_base.py --dry-run   # 只取数不写飞书
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ---- 配置 ----
ENV_FILE = Path(
    "/home/ken4zhao/Documents/online/xianyu-auto-reply2/xianyu-auto-reply"
    "/backend-web/.env"
)
API_URL = "http://127.0.0.1:8089/api/v1/dashboard/summary"
BASE_TOKEN = "A5xAbN1KcabYeXsjNmfc6AwVnub"
TABLE_ID = "tblzh2uOzxlAiy7R"

# lark-cli 装在 nvm 的 node 24 下；systemd 环境没有 nvm 的 PATH，必须写绝对路径
LARK_CLI_FALLBACK = "/home/ken4zhao/.nvm/versions/node/v24.16.0/bin/lark-cli"

# 后端状态码 → 表字段名
STATUS_TO_FIELD = {
    "pending_ship": "待发货",
    "shipped": "已发货",
    "completed": "已完成",
    "cancelled": "已取消",
    "refunded": "已退款",
    "refunding": "退款中",
}
# 后端 metrics 标签 → 表字段名（同名直通，列出来是为了显式化契约）
METRIC_TO_FIELD = {
    "监控商品": "监控商品",
    "商品目录": "商品目录",
    "卡密库存": "卡密库存",
    "在线账号": "在线账号",
}

VERBOSE = "--verbose" in sys.argv
DRY_RUN = "--dry-run" in sys.argv


def log(msg: str) -> None:
    if VERBOSE:
        print(msg)


def fail(msg: str) -> None:
    """失败时才输出——静默设计的关键，让 timer 只在异常时惊动人"""
    print(f"[xianyu→base] {msg}", file=sys.stderr)
    sys.exit(1)


def read_api_key() -> str:
    """只从 .env 读密钥。pydantic-settings 的 env_file 不写 os.environ，
    所以不能指望从进程环境拿到（这个坑之前踩过）。"""
    if not ENV_FILE.exists():
        fail(f".env 不存在: {ENV_FILE}")
    for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line.startswith("DASHBOARD_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    fail("在 .env 里没找到 DASHBOARD_API_KEY")
    return ""


def fetch_summary(key: str) -> dict:
    req = urllib.request.Request(API_URL, headers={"X-Dashboard-Key": key})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        fail(f"接口 HTTP {e.code}（401=密钥不对；确认 .env 与运行进程一致）")
    except Exception as e:  # noqa: BLE001
        fail(f"接口请求失败: {type(e).__name__}: {e}")
    return body.get("data") or body


def build_row(payload: dict) -> tuple[list[str], list]:
    total = int(payload.get("total_orders") or 0)
    fail_count = int(payload.get("delivery_fail_count") or 0)
    fail_rate = round(fail_count / total * 100, 1) if total else 0.0

    row = {
        "快照时间": payload.get("updated_at") or time.strftime("%Y-%m-%d %H:%M:%S"),
        "订单总数": total,
        "发货失败": fail_count,
        "失败占比%": fail_rate,
        "采集时刻": int(time.time() * 1000),  # 飞书日期字段要毫秒时间戳
    }
    for f in STATUS_TO_FIELD.values():
        row[f] = 0
    for s in payload.get("statuses") or []:
        field = STATUS_TO_FIELD.get(s.get("key"))
        if field:
            row[field] = int(s.get("count") or 0)
        else:
            log(f"  未映射的状态码（已忽略）: {s.get('key')}")
    for f in METRIC_TO_FIELD.values():
        row[f] = 0
    for m in payload.get("metrics") or []:
        field = METRIC_TO_FIELD.get((m.get("label") or "").strip())
        if field:
            row[field] = int(m.get("value") or 0)
        else:
            log(f"  未映射的指标（已忽略）: {m.get('label')}")

    names = list(row.keys())
    return names, [row[n] for n in names]


def write_to_base(names: list[str], values: list) -> None:
    cli = shutil.which("lark-cli") or LARK_CLI_FALLBACK
    if not Path(cli).exists():
        fail(f"lark-cli 不存在: {cli}")
    spec = json.dumps({"fields": names, "rows": [values]}, ensure_ascii=False)
    cmd = [
        cli, "base", "+record-batch-create",
        "--base-token", BASE_TOKEN,
        "--table-id", TABLE_ID,
        "--as", "bot",
        "--json", spec,
    ]
    env = dict(os.environ)
    env.setdefault("HOME", "/home/ken4zhao")  # lark-cli 凭据在 $HOME 下，HOME 分叉会读不到
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, env=env
        )
    except subprocess.TimeoutExpired:
        fail("lark-cli 写入超时(120s)")
    out = (proc.stdout or "") + (proc.stderr or "")
    if '"ok": true' not in out:
        # 只截取错误段，避免把整个响应（可能含 token）打进日志
        brief = " ".join(
            ln.strip() for ln in out.splitlines()
            if '"message"' in ln or '"type"' in ln
        )[:300]
        fail(f"写入飞书失败: {brief or out[:200]}")
    log("  写入成功")


def main() -> int:
    key = read_api_key()
    payload = fetch_summary(key)
    names, values = build_row(payload)
    log("取到数据:")
    for n, v in zip(names, values):
        log(f"  {n}: {v}")
    if DRY_RUN:
        log("--dry-run：不写飞书")
        return 0
    write_to_base(names, values)
    return 0


if __name__ == "__main__":
    sys.exit(main())
