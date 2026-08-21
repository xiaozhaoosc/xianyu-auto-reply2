"""
滑块滑动方式运行时配置。

功能：
1. 从系统设置表读取滑块滑动方式
2. 在线程安全的进程缓存中保存当前方式
3. 为同步滑块编排器提供实时读取结果
"""
from __future__ import annotations

from threading import RLock

from loguru import logger
from sqlalchemy import select

from common.db.session import async_session_maker
from common.models.system_setting import SystemSetting


SLIDER_MODE_SETTING_KEY = "captcha.slider_mode"
SLIDER_MODE_BROWSER = "browser"
SLIDER_MODE_REAL_MOUSE = "real_mouse"
SLIDER_MODE_MANUAL = "manual"
SLIDER_MODES = {SLIDER_MODE_BROWSER, SLIDER_MODE_REAL_MOUSE, SLIDER_MODE_MANUAL}

# 人工等待窗口配置键（自动滑动失败后保持浏览器等待人工完成验证的秒数，0=不等待）
MANUAL_WAIT_SETTING_KEY = "captcha.manual_wait_seconds"

_mode_lock = RLock()
_current_mode = SLIDER_MODE_BROWSER


def normalize_slider_mode(value: object) -> str:
    """规范化滑块方式，非法值按浏览器自动滑动处理。"""
    mode = str(value or "").strip().lower()
    return mode if mode in SLIDER_MODES else SLIDER_MODE_BROWSER


def set_slider_mode(mode: object) -> str:
    """更新当前进程使用的滑块方式并返回规范值。"""
    normalized = normalize_slider_mode(mode)
    global _current_mode
    with _mode_lock:
        _current_mode = normalized
    return normalized


def get_slider_mode() -> str:
    """返回当前进程缓存的滑块方式。"""
    with _mode_lock:
        return _current_mode


def is_real_mouse_slider_mode(mode: object | None = None) -> bool:
    """指定方式或当前缓存是否使用真实鼠标滑动。"""
    selected_mode = get_slider_mode() if mode is None else normalize_slider_mode(mode)
    return selected_mode == SLIDER_MODE_REAL_MOUSE


def is_manual_slider_mode(mode: object | None = None) -> bool:
    """指定方式或当前缓存是否使用纯手动模式（跳过自动滑动，等待人工）。"""
    selected_mode = get_slider_mode() if mode is None else normalize_slider_mode(mode)
    return selected_mode == SLIDER_MODE_MANUAL


async def refresh_slider_mode_from_database() -> str:
    """从数据库刷新滑块方式，读取失败时保留当前值。"""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(SystemSetting.value).where(
                    SystemSetting.key == SLIDER_MODE_SETTING_KEY
                )
            )
            stored_mode = result.scalar_one_or_none()
        previous_mode = get_slider_mode()
        current_mode = set_slider_mode(stored_mode)
        if current_mode != previous_mode:
            logger.info(f"滑块滑动方式已实时切换为: {current_mode}")
        return current_mode
    except Exception as exc:
        logger.error(f"从数据库刷新滑块滑动方式失败，继续使用当前方式: {exc}")
        return get_slider_mode()


async def load_manual_wait_seconds() -> int:
    """从数据库读取人工等待窗口秒数；读取失败或非法时返回 0（不等待）。"""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(SystemSetting.value).where(
                    SystemSetting.key == MANUAL_WAIT_SETTING_KEY
                )
            )
            stored_value = result.scalar_one_or_none()
        try:
            seconds = int(float(str(stored_value or "0")))
        except (TypeError, ValueError):
            seconds = 0
        return max(0, seconds)
    except Exception as exc:
        logger.error(f"读取人工等待窗口配置失败，按 0（不等待）处理: {exc}")
        return 0


async def load_slider_notify_config() -> tuple:
    """从数据库读取 SMTP 配置和滑块通知邮箱。

    Returns:
        (smtp_config dict | None, notify_email str)
        smtp_config 格式: {smtp_server, smtp_port, email_user, email_password}
        若 SMTP 配置不完整或通知邮箱为空，smtp_config 返回 None。
    """
    SMTP_KEYS = ["smtp_server", "smtp_port", "smtp_user", "smtp_password"]
    NOTIFY_KEY = "captcha.slider_notify_email"
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(SystemSetting.key, SystemSetting.value).where(
                    SystemSetting.key.in_(SMTP_KEYS + [NOTIFY_KEY])
                )
            )
            rows = {row[0]: row[1] for row in result.all()}
        notify_email = (rows.get(NOTIFY_KEY) or "").strip()
        if not notify_email:
            return None, ""
        smtp_server = (rows.get("smtp_server") or "").strip()
        smtp_user = (rows.get("smtp_user") or "").strip()
        smtp_password = (rows.get("smtp_password") or "").strip()
        try:
            smtp_port = int(rows.get("smtp_port") or 465)
        except (TypeError, ValueError):
            smtp_port = 465
        if not all([smtp_server, smtp_user, smtp_password]):
            logger.warning("滑块通知 SMTP 配置不完整，跳过邮件通知")
            return None, notify_email
        smtp_config = {
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "email_user": smtp_user,
            "email_password": smtp_password,
        }
        return smtp_config, notify_email
    except Exception as exc:
        logger.error(f"读取滑块通知配置失败: {exc}")
        return None, ""
