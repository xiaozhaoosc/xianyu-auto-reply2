"""WS 同步检查点（pts）持久化 + 重连续传

背景（2026-09-10 僵尸连接事故的"第二层根因"）：
    ``xianyu_async.init()`` 每次建连都把同步状态清零：

        /reg      headers.sync = "0,0;0;0;"    ← 声明"我没有任何同步检查点"
        ackDiff   pts = now*1000, highPts = 0  ← 把游标直接 ack 到"现在"

    于是每次重连都是"失忆式重注册"：断连窗口内到达的买家消息，服务端没有
    义务补推 → 消息永久丢失。第一层根因（同一 token 重复 /reg 变僵尸）已在
    fix/create-chat-cid-cache 修复；本模块补第二层。

本模块职责：
    1. 收帧侧：从业务帧里提取同步检查点 pts，按账号持久化到 Redis
       key   = ws:sync_pts:<account_id>
       value = "<pts>,<seq>,<saved_ts>"
    2. 建连侧：重连时读回检查点，**新鲜**（距现在 ≤ RESUME_MAX_GAP_S）则续传
       （ackDiff.pts = 检查点 pts，/reg 的 sync 头带上检查点），否则维持
       原来的"清零重来"。

安全设计（本仓红线）：
    - 全程 fail-open：任何异常只打日志、返回 None，绝不抛出、绝不阻断注册
    - 只"缩短断连窗口"，不回放历史：间隔超过 RESUME_MAX_GAP_S 一律放弃续传
    - 重复推送不会重复回复：message_handler 已有 messageId 去重
    - 一键回退：WS_SYNC_RESUME_ENABLED=0 即恢复旧行为
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from loguru import logger

# ---------------------------------------------------------------- 配置

SYNC_PTS_KEY_PREFIX = "ws:sync_pts:"
SYNC_PTS_TTL_S = int(os.getenv("WS_SYNC_PTS_TTL_S", str(7 * 86400)))
# 检查点超过这个间隔就认为"太久远"，放弃续传（避免服务端一次推巨量积压）
RESUME_MAX_GAP_S = int(os.getenv("WS_SYNC_RESUME_MAX_GAP_S", "1800"))
RESUME_ENABLED = os.getenv("WS_SYNC_RESUME_ENABLED", "1").strip().lower() not in (
    "0",
    "false",
    "no",
    "off",
)

# 续传作用范围：
#   off      —— 完全关闭，恢复"每次建连清零"的旧行为
#   ackdiff  —— 保守模式：只改 /r/SyncStatus/ackDiff 的 pts/highPts，/reg 的 sync 头保持清零
#   both     —— 默认：/reg 的 sync 头与 ackDiff 都用检查点（续传最完整）
RESUME_MODE = os.getenv("WS_SYNC_RESUME_MODE", "both").strip().lower() or "both"

# 检查点 pts 在 ackDiff 里的缩放系数：原实现用的是 ms×1000（即微秒量级），
# 检查点是从帧里原样提取的（ms 量级），故同样 ×1000 保持量级一致；置 1 则原样发送。
RESUME_PTS_SCALE = int(os.getenv("WS_SYNC_RESUME_PTS_SCALE", "1000")) or 1

# 可能承载 pts 的字段名（不同版本协议叫法不一，全部兜住）
_PTS_FIELDS = ("pts", "highPts", "syncPts", "lastPts", "maxPts")
_SEQ_FIELDS = ("seq", "lastSeq", "syncSeq")

# 每个账号只打一次"帧结构观测"日志，避免刷屏
_FRAME_SHAPE_LOGGED: set = set()


# ---------------------------------------------------------------- 纯函数

def _as_positive_int(value: Any) -> Optional[int]:
    """宽松转正整数，失败返回 None（不抛异常）"""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float):
        iv = int(value)
        return iv if iv > 0 else None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            iv = int(s)
        except ValueError:
            try:
                iv = int(float(s))
            except ValueError:
                return None
        return iv if iv > 0 else None
    return None


def parse_sync_header(value: Any) -> Optional[int]:
    """解析 LWP sync 检查点串（形如 "1789012345678,5;0;0;"），返回首个整数 pts。

    全 0 串（"0,0;0;0;"）表示"无检查点"，返回 None。
    """
    return _parse_sync_header_full(value)[0]


def _parse_sync_header_full(value: Any) -> tuple:
    """解析 sync 串，返回 (pts|None, seq|None)

    格式："<pts>,<seq>;<a>;<b>;" —— pts/seq 任一为 0 或缺失都按"无"处理。
    """
    if not isinstance(value, str) or not value.strip():
        return None, None
    head = value.strip().split(";")[0]
    parts = head.split(",")
    pts = _as_positive_int(parts[0]) if parts else None
    seq = _as_positive_int(parts[1]) if len(parts) > 1 else None
    return pts, seq


def _scan_fields(container: Any, fields) -> Optional[int]:
    """在 dict 里找第一个命中 fields 的正整数"""
    if not isinstance(container, dict):
        return None
    for field in fields:
        got = _as_positive_int(container.get(field))
        if got:
            return got
    return None


def extract_sync_checkpoint(message_data: Any) -> Optional[Dict[str, Any]]:
    """从收到的原始帧里提取同步检查点。

    返回 ``{"pts": int, "seq": int|None, "source": str}``；提取不到返回 None。

    识别顺序（headers 优先，其次逐条同步包；pts 取最大值）：
      1. headers 里的 pts / highPts / syncPts / lastPts / maxPts
      2. headers.sync 串的首个整数（形如 "1789...,5;0;0;"）
      3. body.syncPushPackage.data[i] 上的 pts / seq
    """
    try:
        if not isinstance(message_data, dict):
            return None

        best_pts: Optional[int] = None
        best_source = ""
        seq: Optional[int] = None

        headers = message_data.get("headers")
        if isinstance(headers, dict):
            hit = _scan_fields(headers, _PTS_FIELDS)
            if hit:
                best_pts, best_source = hit, "headers.pts"
            else:
                hit, sync_seq = _parse_sync_header_full(headers.get("sync"))
                if hit:
                    best_pts, best_source = hit, "headers.sync"
                    seq = sync_seq
            header_seq = _scan_fields(headers, _SEQ_FIELDS)
            if header_seq:
                seq = header_seq

        body = message_data.get("body")
        if isinstance(body, dict):
            package = body.get("syncPushPackage")
            if isinstance(package, dict):
                data_list = package.get("data")
                if isinstance(data_list, list):
                    for item in data_list:
                        if not isinstance(item, dict):
                            continue
                        hit = _scan_fields(item, _PTS_FIELDS)
                        if hit and (best_pts is None or hit > best_pts):
                            best_pts, best_source = hit, "syncPushPackage.data.pts"
                        if seq is None:
                            seq = _scan_fields(item, _SEQ_FIELDS)
                    if best_pts is None:
                        hit = _scan_fields(package, _PTS_FIELDS)
                        if hit:
                            best_pts, best_source = hit, "syncPushPackage.pts"

        if not best_pts:
            return None
        return {"pts": int(best_pts), "seq": int(seq) if seq else None, "source": best_source}
    except Exception as e:  # pragma: no cover - 兜底
        logger.debug(f"[sync-pts] 提取检查点异常(忽略): {e}")
        return None


def describe_frame_shape(message_data: Any) -> str:
    """给"提取不到 pts"的帧生成简短结构描述，用于反推协议字段名"""
    try:
        if not isinstance(message_data, dict):
            return f"type={type(message_data).__name__}"
        headers = message_data.get("headers")
        header_keys = sorted(headers.keys()) if isinstance(headers, dict) else []
        body = message_data.get("body")
        body_keys = sorted(body.keys()) if isinstance(body, dict) else []
        item_keys = []
        if isinstance(body, dict):
            package = body.get("syncPushPackage")
            if isinstance(package, dict) and isinstance(package.get("data"), list):
                first = package["data"][0] if package["data"] else None
                if isinstance(first, dict):
                    item_keys = sorted(first.keys())
        return f"header键={header_keys} body键={body_keys} 首条data键={item_keys}"
    except Exception:
        return "结构描述失败"


def log_frame_shape_once(account_id: str, message_data: Any) -> None:
    """每账号仅记录一次帧结构，便于确认 pts 实际字段名"""
    try:
        if account_id in _FRAME_SHAPE_LOGGED:
            return
        _FRAME_SHAPE_LOGGED.add(account_id)
        logger.info(f"【{account_id}】[sync-pts] 帧结构观测(仅一次): {describe_frame_shape(message_data)}")
    except Exception:
        pass


def decide_resume(checkpoint: Optional[Dict[str, Any]], now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """判断检查点能否用于续传（纯函数，便于单测）。

    Args:
        checkpoint: ``load_checkpoint`` 的返回值，形如
            ``{"pts":..., "seq":..., "saved_ts":...}``

    Returns:
        可续传时返回 ``{"pts":..., "seq":..., "sync":..., "gap_s":...}``，否则 None
    """
    if not RESUME_ENABLED or RESUME_MODE == "off" or not checkpoint:
        return None
    pts = _as_positive_int(checkpoint.get("pts"))
    if not pts:
        return None
    saved_ts = checkpoint.get("saved_ts")
    try:
        saved_ts = float(saved_ts)
    except (TypeError, ValueError):
        return None
    now = time.time() if now is None else now
    gap_s = now - saved_ts
    if gap_s < 0:
        gap_s = 0.0
    if gap_s > RESUME_MAX_GAP_S:
        return None
    seq = _as_positive_int(checkpoint.get("seq")) or 0
    return {
        "pts": pts,
        "seq": seq,
        "sync": f"{pts},{seq};0;0;",
        "ack_pts": pts * RESUME_PTS_SCALE,
        "use_sync_header": RESUME_MODE == "both",
        "gap_s": round(gap_s, 1),
    }


# ---------------------------------------------------------------- Redis 读写

def _key(account_id: str) -> str:
    return f"{SYNC_PTS_KEY_PREFIX}{account_id}"


async def save_checkpoint(account_id: str, pts: int, seq: Optional[int] = None) -> bool:
    """持久化检查点（fail-open，异常返回 False）"""
    try:
        pts = _as_positive_int(pts)
        if not pts:
            return False
        from common.db.redis_client import get_redis_client

        rc = await get_redis_client()
        value = f"{pts},{_as_positive_int(seq) or 0},{time.time():.3f}"
        await rc.set(_key(account_id), value, ex=SYNC_PTS_TTL_S)
        return True
    except Exception as e:
        logger.debug(f"【{account_id}】[sync-pts] 保存检查点失败(不影响主流程): {e}")
        return False


async def load_checkpoint(account_id: str) -> Optional[Dict[str, Any]]:
    """读取检查点（fail-open，异常/无值返回 None）"""
    try:
        from common.db.redis_client import get_redis_client

        rc = await get_redis_client()
        raw = await rc.get(_key(account_id))
        if not raw:
            return None
        parts = str(raw).split(",")
        pts = _as_positive_int(parts[0]) if parts else None
        if not pts:
            return None
        seq = _as_positive_int(parts[1]) if len(parts) > 1 else None
        saved_ts = None
        if len(parts) > 2:
            try:
                saved_ts = float(parts[2])
            except ValueError:
                saved_ts = None
        return {"pts": pts, "seq": seq, "saved_ts": saved_ts}
    except Exception as e:
        logger.debug(f"【{account_id}】[sync-pts] 读取检查点失败(不影响主流程): {e}")
        return None


async def build_resume_state(account_id: str) -> Optional[Dict[str, Any]]:
    """建连时调用：读取并校验检查点，返回可直接用于注册的续传参数"""
    try:
        checkpoint = await load_checkpoint(account_id)
        state = decide_resume(checkpoint)
        if state:
            logger.info(
                f"【{account_id}】[sync-pts] 断连 {state['gap_s']}s，"
                f"重连续传检查点 pts={state['pts']} seq={state['seq']}"
            )
        elif checkpoint:
            logger.info(
                f"【{account_id}】[sync-pts] 检查点 pts={checkpoint.get('pts')} "
                f"超出续传窗口({RESUME_MAX_GAP_S}s)，本次清零重来"
            )
        return state
    except Exception as e:
        logger.debug(f"【{account_id}】[sync-pts] 计算续传状态失败(不影响注册): {e}")
        return None


async def record_from_frame(account_id: str, message_data: Any) -> Optional[Dict[str, Any]]:
    """收帧侧入口：提取 + 持久化。返回提取结果（无则 None）

    由 message_handler 每条业务帧调用；非同步包帧通常提取不到，属正常。
    """
    try:
        got = extract_sync_checkpoint(message_data)
        if not got:
            log_frame_shape_once(account_id, message_data)
            return None
        saved = await save_checkpoint(account_id, got["pts"], got.get("seq"))
        return got if saved else None
    except Exception as e:
        logger.debug(f"【{account_id}】[sync-pts] 收帧侧处理失败(忽略): {e}")
        return None
