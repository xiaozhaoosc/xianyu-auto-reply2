"""
amap_inputtips_service 的网页后端兼容导出。

功能：
1. 保留原 app.services 导入路径；
2. 统一复用 common 中的实现，避免跨服务复制业务逻辑。
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from loguru import logger

# 注意：本模块会被 backend_web_loader 动态加载到 scheduler/websocket 进程，
# 那里 `app` 解析为各进程自己的包（app.core API 不一致），因此这里不用
# app.core.http_client，直接独立构造 httpx 客户端，保持上下文无关。
import httpx


REQUEST_TIMEOUT_SECONDS = 20
AMAP_INPUTTIPS_URL = "https://restapi.amap.com/v3/assistant/inputtips"
AMAP_WEB_KEY = "c9b68d4ce9a2a97f22a4a439404488ca"
AMAP_APP_NAME = "https://seller.goofish.com"
AMAP_ORIGIN = "https://seller.goofish.com"


class AmapInputTipsError(RuntimeError):
    """高德输入提示接口请求失败或返回业务错误。"""


def _as_text(value: Any) -> str:
    """将高德响应字段安全转换为字符串，过滤空数组等非文本占位值。"""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    return ""


def _parse_tip(raw_tip: Any) -> dict[str, str] | None:
    """解析单条高德 POI 提示，无名称的无效记录不返回。"""
    if not isinstance(raw_tip, dict):
        return None

    name = _as_text(raw_tip.get("name"))
    if not name:
        return None
    district = _as_text(raw_tip.get("district"))
    address = _as_text(raw_tip.get("address"))
    detail_text = "".join(part for part in (district, address) if part)
    expected_parts = [part for part in (name, detail_text) if part]

    return {
        "id": _as_text(raw_tip.get("id")),
        "name": name,
        "district": district,
        "adcode": _as_text(raw_tip.get("adcode")),
        "location": _as_text(raw_tip.get("location")),
        "address": address,
        "typecode": _as_text(raw_tip.get("typecode")),
        "city": _as_text(raw_tip.get("city")),
        "search_keyword": name,
        "expected_text": " / ".join(expected_parts),
    }


class AmapInputTipsService:
    """调用高德 inputtips 接口搜索宝贝所在地。"""

    async def search(self, keywords: str, city: str = "全国") -> dict[str, Any]:
        """
        根据关键词查询高德 POI 输入提示。

        Args:
            keywords: 用户输入的所在地关键词。
            city: 搜索城市，默认全国且不限制城市范围。
        Returns:
            包含高德实际返回提示列表和数量的字典。
        Raises:
            AmapInputTipsError: 请求失败或高德返回失败时抛出。
        """
        normalized_keywords = keywords.strip()
        if not normalized_keywords:
            raise AmapInputTipsError("请输入所在地关键词")

        params = {
            "s": "rsv3",
            "key": AMAP_WEB_KEY,
            "platform": "JS",
            "logversion": "2.0",
            "sdkversion": "2.0",
            "appname": AMAP_APP_NAME,
            "keywords": normalized_keywords,
            "city": city.strip() or "全国",
            "citylimit": "false",
            "datatype": "all",
        }
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "origin": AMAP_ORIGIN,
            "referer": f"{AMAP_ORIGIN.rstrip('/')}/",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/146.0.0.0 Safari/537.36"
            ),
        }

        try:
            async with httpx.AsyncClient(
                timeout=None,
                follow_redirects=True,
                trust_env=False,
            ) as client:
                resp = await asyncio.wait_for(
                    client.get(
                        AMAP_INPUTTIPS_URL,
                        params=params,
                        headers=headers,
                    ),
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
            resp.raise_for_status()
            body = resp.json()
        except asyncio.TimeoutError as exc:
            logger.warning(f"高德所在地搜索超时: keywords={normalized_keywords}")
            raise AmapInputTipsError("所在地搜索超时，请稍后重试") from exc
        except Exception as exc:
            logger.warning(f"高德所在地搜索请求失败: keywords={normalized_keywords}, error={exc}")
            raise AmapInputTipsError("所在地搜索接口请求失败，请稍后重试") from exc
from common.services.amap_inputtips_service import (
    REQUEST_TIMEOUT_SECONDS,
    AMAP_INPUTTIPS_URL,
    AMAP_WEB_KEY,
    AMAP_APP_NAME,
    AMAP_ORIGIN,
    AmapInputTipsError,
    _as_text,
    _parse_tip,
    AmapInputTipsService,
)

__all__ = [
    "REQUEST_TIMEOUT_SECONDS",
    "AMAP_INPUTTIPS_URL",
    "AMAP_WEB_KEY",
    "AMAP_APP_NAME",
    "AMAP_ORIGIN",
    "AmapInputTipsError",
    "AmapInputTipsService",
]
