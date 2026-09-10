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
RESUME_MAX_GAP_S = int(os.getenv("WS_SYNC_RESUME_MAX_GAP_S", "21600"))
# 进程启动后的「首次建连」用更窄的窗口：此时内存去重集合是空的，若让服务端
# 补推较长历史，理论上存在重复回复买家的风险（风控红线）。等本进程已经收过帧
# （去重集合非空），窗口才放宽到 RESUME_MAX_GAP_S。
# 依据（2026-09-10 实测）：服务端本就会重复下发同一条消息（同一 message id 在
# 日志里出现 2~3 次），进程内靠 processed_message_ids 去重；包节奏约 1~3 小时
# 一个，故宽窗口取 6h 才有实际覆盖，窄窗口保守取 1800s。
RESUME_FIRST_GAP_S = int(os.getenv("WS_SYNC_RESUME_FIRST_GAP_S", "1800"))
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

# pts 量级归一化：服务器可能给 ms(1.7e12) 或 µs(1.7e15)，统一按 ms 存/算
_MS_UPPER = 10 ** 13      # 超过此值视为 µs 量级
_TS_LOWER = 1_500_000_000_000    # ~2047-07 之前的 ms 时间戳下限（排除小计数器）
_TS_UPPER = 2_000_000_000_000    # ~2033-05 之后的 ms 视为异常

# 每个账号每种帧只打一次"帧结构观测"
_FRAME_SHAPE_LOGGED: set = set()
# 每个账号每个命中源只打一次"命中取证"，用于确认 pts 真实字段
_SOURCE_LOGGED: set = set()


def normalize_pts_ms(value: Any) -> Optional[int]:
    """把 pts 归一化到毫秒量级（µs 值 //1000），失败返回 None"""
    raw = _as_positive_int(value)
    if not raw:
        return None
    return raw // 1000 if raw >= _MS_UPPER else raw


def looks_like_timestamp_ms(value: Any) -> bool:
    """判断归一化后的 pts 是否像"墙钟时间戳(ms)"（用于时效校验）"""
    v = _as_positive_int(value)
    return bool(v) and _TS_LOWER <= v <= _TS_UPPER


def _sanitize_headers(headers: Any) -> dict:
    """帧 headers 脱敏（token/cookie 等绝不落日志）"""
    if not isinstance(headers, dict):
        return {}
    drop = {"token", "cookie", "authorization", "cache-header"}
    return {k: v for k, v in headers.items() if k.lower() not in drop}


def describe_hit(message_data: Any) -> str:
    """命中 pts 时的取证描述：脱敏 headers + 首条非密文字段"""
    try:
        if not isinstance(message_data, dict):
            return ""
        headers = _sanitize_headers(message_data.get("headers"))
        plain = ""
        body = message_data.get("body")
        if isinstance(body, dict):
            package = body.get("syncPushPackage")
            if isinstance(package, dict) and isinstance(package.get("data"), list) and package["data"]:
                first = package["data"][0]
                if isinstance(first, dict):
                    plain = str({k: v for k, v in first.items() if k != "data"})[:200]
        return f"脱敏header={headers} 首条非密文字段={plain}"
    except Exception:
        return ""


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
        pts_ms = normalize_pts_ms(best_pts)
        if not pts_ms:
            return None
        return {
            "pts": int(pts_ms),
            "raw_pts": int(best_pts),
            "seq": int(seq) if seq else None,
            "source": best_source,
        }
    except Exception as e:  # pragma: no cover - 兜底
        logger.debug(f"[sync-pts] 提取检查点异常(忽略): {e}")
        return None


def describe_frame_shape(message_data: Any) -> str:
    """给"提取不到 pts"的帧生成简短结构描述，用于反推协议字段名"""
    try:
        if not isinstance(message_data, dict):
            return f"type={type(message_data).__name__}"
        lwp = message_data.get("lwp") or ""
        headers = message_data.get("headers")
        header_keys = sorted(headers.keys()) if isinstance(headers, dict) else []
        body = message_data.get("body")
        body_keys = sorted(body.keys()) if isinstance(body, dict) else []
        item_keys = []
        item_plain = {}
        if isinstance(body, dict):
            package = body.get("syncPushPackage")
            if isinstance(package, dict) and isinstance(package.get("data"), list):
                first = package["data"][0] if package["data"] else None
                if isinstance(first, dict):
                    item_keys = sorted(first.keys())
                    # 非密文字段原样带出（pts/seq/时间戳等常在这里）
                    item_plain = {k: v for k, v in first.items() if k != "data"}
        return (
            f"lwp={lwp} header键={header_keys} body键={body_keys} "
            f"首条data键={item_keys} 首条非密文字段={item_plain}"
        )
    except Exception:
        return "结构描述失败"


def _frame_kind(message_data: Any) -> str:
    """给帧分类，用于实现每种帧只观测一次"""
    try:
        if not isinstance(message_data, dict):
            return "非dict"
        body = message_data.get("body")
        if isinstance(body, dict) and "syncPushPackage" in body:
            return "syncPushPackage"
        lwp = message_data.get("lwp")
        return f"lwp={lwp}" if lwp else "无lwp"
    except Exception:
        return "未知"


def log_frame_shape_once(account_id: str, message_data: Any) -> None:
    """每账号每种帧仅记录一次结构（含 lwp 与非密文字段），便于确认 pts 实际字段名"""
    try:
        kind = _frame_kind(message_data)
        marker = f"{account_id}|{kind}"
        if marker in _FRAME_SHAPE_LOGGED:
            return
        _FRAME_SHAPE_LOGGED.add(marker)
        logger.info(f"【{account_id}】[sync-pts] 帧结构观测({kind}): {describe_frame_shape(message_data)}")
    except Exception:
        pass


def decide_resume(
    checkpoint: Optional[Dict[str, Any]],
    now: Optional[float] = None,
    gap_limit_s: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """判断检查点能否用于续传（纯函数，便于单测）。

    Args:
        checkpoint: ``load_checkpoint`` 的返回值，形如
            ``{"pts":..., "seq":..., "saved_ts":...}``
        gap_limit_s: 覆盖默认窗口。进程内重连传 ``RESUME_MAX_GAP_S``（宽），
            进程启动后首次建连传 ``RESUME_FIRST_GAP_S``（窄，因内存去重集合为空）。

    Returns:
        可续传时返回 ``{"pts":..., "seq":..., "sync":..., "gap_s":...}``，否则 None
    """
    if not RESUME_ENABLED or RESUME_MODE == "off" or not checkpoint:
        return None
    limit_s = RESUME_MAX_GAP_S if gap_limit_s is None else int(gap_limit_s)
    # 归一化放这里（而不是只在提取侧）：Redis 里可能存着历史版本写入的 µs 量级值，
    # 读取侧不归一化就会绕过下面的时效校验（2026-09-10 演练实测踩到）
    pts = normalize_pts_ms(checkpoint.get("pts"))
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
    if gap_s > limit_s:
        return None
    # 时效校验（2026-09-10 演练实测补的防线）：
    # 若 pts 本身是墙钟时间戳(ms)，必须与"现在"同窗口——否则说明提取到的
    # 不是真正的同步 pts（例如某帧里的旧时间戳），续传会把游标推到错误位置。
    if looks_like_timestamp_ms(pts):
        drift_s = abs(now - pts / 1000.0)
        if drift_s > limit_s:
            logger.warning(
                f"[sync-pts] 检查点 pts={pts} 距现在 {round(drift_s)}s，"
                f"超出窗口({limit_s}s)，判定为无效检查点，放弃续传"
            )
            return None
    seq = _as_positive_int(checkpoint.get("seq")) or 0
    # 上线值用服务器自己的原始量级（raw），而不是我们归一化后的 ms×1000 猜测——
    # 原实现发的是 ms×1000，恰好等于 µs，与帧里的原始 pts 量级一致，故优先 raw。
    wire_pts = _as_positive_int(checkpoint.get("raw_pts")) or (pts * RESUME_PTS_SCALE)
    return {
        "pts": pts,
        "raw_pts": wire_pts,
        "seq": seq,
        "sync": f"{wire_pts},{seq};0;0;",
        "ack_pts": wire_pts,
        "use_sync_header": RESUME_MODE == "both",
        "gap_s": round(gap_s, 1),
    }


# ---------------------------------------------------------------- Redis 读写

def _key(account_id: str) -> str:
    return f"{SYNC_PTS_KEY_PREFIX}{account_id}"


async def save_checkpoint(
    account_id: str, pts: int, seq: Optional[int] = None, raw_pts: Optional[int] = None
) -> bool:
    """持久化检查点（fail-open，异常返回 False）

    value 格式：``<pts_ms>,<seq>,<saved_ts>,<raw_pts>``
    —— pts_ms 用于时效校验/比较；raw_pts 是服务器原始量级，重连时原样上线。
    """
    try:
        pts_ms = normalize_pts_ms(pts)
        if not pts_ms:
            return False
        from common.db.redis_client import get_redis_client

        rc = await get_redis_client()
        raw = _as_positive_int(raw_pts) or _as_positive_int(pts) or pts_ms
        value = f"{pts_ms},{_as_positive_int(seq) or 0},{time.time():.3f},{raw}"
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
        raw_value = await rc.get(_key(account_id))
        if not raw_value:
            return None
        parts = str(raw_value).split(",")
        pts = normalize_pts_ms(parts[0]) if parts else None
        if not pts:
            return None
        seq = _as_positive_int(parts[1]) if len(parts) > 1 else None
        saved_ts = None
        if len(parts) > 2:
            try:
                saved_ts = float(parts[2])
            except ValueError:
                saved_ts = None
        raw_pts = _as_positive_int(parts[3]) if len(parts) > 3 else None
        return {"pts": pts, "seq": seq, "saved_ts": saved_ts, "raw_pts": raw_pts}
    except Exception as e:
        logger.debug(f"【{account_id}】[sync-pts] 读取检查点失败(不影响主流程): {e}")
        return None


async def build_resume_state(
    account_id: str, gap_limit_s: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """建连时调用：读取并校验检查点，返回可直接用于注册的续传参数

    Args:
        gap_limit_s: 窗口覆盖。调用方按「本进程是否已收过帧」决定传
            ``RESUME_MAX_GAP_S``（宽）还是 ``RESUME_FIRST_GAP_S``（窄）。
    """
    try:
        checkpoint = await load_checkpoint(account_id)
        state = decide_resume(checkpoint, gap_limit_s=gap_limit_s)
        limit_s = RESUME_MAX_GAP_S if gap_limit_s is None else int(gap_limit_s)
        if state:
            logger.info(
                f"【{account_id}】[sync-pts] 断连 {state['gap_s']}s，"
                f"重连续传检查点 pts={state['pts']} seq={state['seq']} "
                f"sync={state['sync']} (窗口{limit_s}s)"
            )
        elif checkpoint:
            logger.info(
                f"【{account_id}】[sync-pts] 检查点 pts={checkpoint.get('pts')} "
                f"超出续传窗口({limit_s}s)，本次清零重来"
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
        saved = await save_checkpoint(
            account_id, got["pts"], got.get("seq"), got.get("raw_pts")
        )
        if saved:
            marker = f"{account_id}|{got.get('source')}"
            if marker not in _SOURCE_LOGGED:
                _SOURCE_LOGGED.add(marker)
                logger.info(
                    f"【{account_id}】[sync-pts] 命中源={got.get('source')} "
                    f"pts={got['pts']}(原始{got.get('raw_pts')}) seq={got.get('seq')} "
                    f"{describe_hit(message_data)}"
                )
        return got if saved else None
    except Exception as e:
        logger.debug(f"【{account_id}】[sync-pts] 收帧侧处理失败(忽略): {e}")
        return None
