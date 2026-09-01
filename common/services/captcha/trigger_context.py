"""
滑块告警触发场景标注（进程内上下文注册表）

用途：滑块验证的人工通知/Feishu 告警能说明"是哪个任务/入口触发的本次验证"，

解决"一天弹多次滑块但不知道谁干的"的问题。

设计说明：
- 各刷新入口（Cookie刷新循环 / Token种子循环 / 启动获取Token / 重连前获取Token /
  scheduler 远程委托等）在发起刷新前调用 set_trigger_source 登记来源；
- 滑块人工等待入口（slider_stealth._wait_for_manual_verification）发通知前
  pop_trigger_source 取走本次来源写进通知文案；
- 跨线程安全（浏览器任务在外部线程池执行），同进程内共享；
- 登记有过期时间，过期的残留登记不允许命中后续无关的滑块（fail-open 回退默认文案）。
"""
from __future__ import annotations

import threading
import time
from typing import Optional, Tuple

_lock = threading.Lock()
_sources: dict[str, Tuple[str, float]] = {}

# 登记有效期：超过该时间未消费就当过期（避免一次登记被N小时后的无关滑块误吞）
_TTL_S = 3600

DEFAULT_SOURCE = "Token刷新（自动链路，未标注入口）"


def set_trigger_source(account_id: str, label: str) -> None:
    """登记某账号即将触发的滑块验证来源。"""
    if not account_id or not label:
        return
    with _lock:
        _sources[str(account_id)] = (label, time.time())


def peek_trigger_source(account_id: str) -> str:
    """非破坏性地读取当前登记来源（用于风控日志等旁观用途）。"""
    with _lock:
        item = _sources.get(str(account_id))
        if not item:
            return DEFAULT_SOURCE
        label, ts = item
        if time.time() - ts > _TTL_S:
            return DEFAULT_SOURCE
        return label


def pop_trigger_source(account_id: str, default: Optional[str] = None) -> str:
    """取走并清除某账号的最新登记来源（一次滑块流程只消费一次）。"""
    with _lock:
        item = _sources.pop(str(account_id), None)
    if not item:
        return default or DEFAULT_SOURCE
    label, ts = item
    if time.time() - ts > _TTL_S:
        return default or DEFAULT_SOURCE
    return label
