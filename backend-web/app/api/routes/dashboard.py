"""飞书云文档小组件看板数据接口

只读聚合接口，供飞书云文档小组件（纯前端，无后端能力）拉取店铺状态。

背景：
    飞书 User Access Token 自 2024-01-22 起不能直调 OpenAPI，小组件本身也没有
    后端能力，因此业务数据必须由本服务中转。本模块只做聚合计数，不返回任何
    订单明细/买家信息/卡密内容，避免小组件侧泄露敏感数据。

鉴权：
    通过 .env 的 DASHBOARD_API_KEY 配置访问密钥（不入库不入代码）。
      - 已配置：请求必须带 X-Dashboard-Key 头且匹配，否则 401
      - 未配置：视为本地开发模式，放行并打印告警

    注意：BaseConfig 用 pydantic-settings 的 env_file 读 .env，值只进 settings 对象、
    不会写入 os.environ，因此必须优先从 settings 取；os.getenv 仅作为运维直接注入
    进程环境变量时的兜底。
"""
from __future__ import annotations

import os
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status as http_status
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.config import get_settings
from common.models.card import Card
from common.models.listing_monitor_item import ListingMonitorItem
from common.models.xy_account import XYAccount
from common.models.xy_catalog_item import XYCatalogItem
from common.models.xy_order import XYOrder
from common.schemas.common import ApiResponse

router = APIRouter(prefix="/dashboard", tags=["飞书看板"])

_API_KEY_ENV = "DASHBOARD_API_KEY"


def _expected_key() -> str:
    """取期望密钥：settings(.env) 优先，进程环境变量兜底"""
    from_settings = (get_settings().dashboard_api_key or "").strip()
    if from_settings:
        return from_settings
    return os.getenv(_API_KEY_ENV, "").strip()


def _verify_key(provided: str | None) -> None:
    """校验看板访问密钥

    Args:
        provided: 请求头 X-Dashboard-Key 的值

    Raises:
        HTTPException: 已配置密钥但请求未提供或不匹配时抛 401
    """
    expected = _expected_key()
    if not expected:
        logger.warning(
            f"{_API_KEY_ENV} 未配置，/dashboard/summary 当前无鉴权（仅限本地开发）"
        )
        return
    if not provided or provided != expected:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="看板密钥无效",
        )


async def _count(db: AsyncSession, stmt) -> int:
    """执行计数语句并返回整数结果"""
    result = await db.execute(stmt)
    return int(result.scalar() or 0)


@router.get("/summary")
async def get_dashboard_summary(
    db: AsyncSession = Depends(deps.get_db_session),
    x_dashboard_key: str | None = Header(default=None, alias="X-Dashboard-Key"),
) -> ApiResponse:
    """店铺状态聚合概览

    返回订单状态分布、发货失败单量与四项库存/账号指标，全部为聚合计数。

    Returns:
        ApiResponse: data 结构如下
            total_orders: 订单总数
            statuses: [{key: 状态码, count: 数量}]
            delivery_fail_count: 发货失败原因非空的订单数
            metrics: [{label, value, unit}]
            updated_at: 数据生成时间（本地时区）
    """
    _verify_key(x_dashboard_key)

    # 订单状态分布（单次分组查询，避免 N 次 count）
    status_rows = await db.execute(
        select(XYOrder.status, func.count(XYOrder.id)).group_by(XYOrder.status)
    )
    statuses = [
        {"key": row[0], "count": int(row[1])}
        for row in status_rows.all()
        if row[0]
    ]
    statuses.sort(key=lambda item: item["count"], reverse=True)
    total_orders = sum(item["count"] for item in statuses)

    # 发货失败：原因字段非空且非空串
    delivery_fail_count = await _count(
        db,
        select(func.count(XYOrder.id)).where(
            XYOrder.delivery_fail_reason.is_not(None),
            XYOrder.delivery_fail_reason != "",
        ),
    )

    monitor_items = await _count(db, select(func.count(ListingMonitorItem.id)))
    catalog_items = await _count(db, select(func.count(XYCatalogItem.id)))
    enabled_cards = await _count(
        db, select(func.count(Card.id)).where(Card.enabled.is_(True))
    )
    active_accounts = await _count(
        db, select(func.count(XYAccount.id)).where(XYAccount.status == "active")
    )

    return ApiResponse(
        success=True,
        message="ok",
        data={
            "total_orders": total_orders,
            "statuses": statuses,
            "delivery_fail_count": delivery_fail_count,
            "metrics": [
                {"label": "监控商品", "value": monitor_items, "unit": "个"},
                {"label": "商品目录", "value": catalog_items, "unit": "款"},
                {"label": "卡密库存", "value": enabled_cards, "unit": "张"},
                {"label": "在线账号", "value": active_accounts, "unit": "个"},
            ],
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )
