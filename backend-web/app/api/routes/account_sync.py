"""
多账号商品同步 API 路由

功能：
1. 从源账号同步商品到目标账号
2. 支持筛选条件
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from common.models.user import User
from common.schemas.common import ApiResponse

router = APIRouter(tags=["账号同步"])


class AccountSyncRequest(BaseModel):
    """账号同步请求"""
    source_account_id: str = Field(..., description="源账号 ID")
    target_account_ids: List[str] = Field(..., min_length=1, description="目标账号 ID 列表")
    keyword_filter: Optional[str] = Field(None, description="标题关键词筛选")
    min_price: Optional[float] = Field(None, description="最低价格")
    max_price: Optional[float] = Field(None, description="最高价格")
    sync_mode: str = Field("material", description="同步模式: material=素材库中转")


@router.post("/sync")
async def sync_accounts(
    payload: AccountSyncRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """同步商品：从源账号 → 目标账号"""
    try:
        from app.services.account_sync_service import AccountSyncService

        svc = AccountSyncService(db)
        result = await svc.sync_items_between_accounts(
            user_id=current_user.id,
            source_account_id=payload.source_account_id,
            target_account_ids=payload.target_account_ids,
            keyword_filter=payload.keyword_filter,
            min_price=payload.min_price,
            max_price=payload.max_price,
            sync_mode=payload.sync_mode,
        )

        if result.get("success"):
            return ApiResponse(
                success=True,
                message=result.get("message", "同步完成"),
                data=result.get("data"),
            )
        else:
            return ApiResponse(
                success=False,
                message=result.get("message", "同步失败"),
            )

    except Exception as e:
        logger.error(f"账号同步失败: {e}")
        return ApiResponse(success=False, message=f"同步失败: {str(e)}")
