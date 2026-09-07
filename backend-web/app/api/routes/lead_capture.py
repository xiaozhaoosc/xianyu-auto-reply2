"""
线索池模块接口

功能：
1. 线索采集任务的分页查询与 CRUD（interval_minutes ≥30、max_items_per_round ≤10 强校验）
2. 线索商品池 / 线索评论的分页查询
3. 人工动作记录（打开商品/复制话术/标记跟进/忽略）与建议话术（仅人工参考，无发送通道）
4. Phase 0 探针：单商品评论读取（Redis 锁 60s 一次）

红线：本模块不提供任何自动发送评论/私信的接口。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db_session
from app.core.config import get_settings
from app.core.http_client import get_http_client
from app.services.lead_capture_service import LeadCaptureService, _task_to_dict
from common.models.user import User
from common.schemas.common import ApiResponse
from common.utils.auth_scope import resolve_owner_scope

router = APIRouter(prefix="/lead-capture", tags=["线索池"])


class LeadTaskCreateRequest(BaseModel):
    """创建线索采集任务请求"""

    name: str = Field(..., min_length=1, max_length=100, description="任务名称")
    source_type: str = Field("monitor", description="候选来源：monitor-复用商品监控采集池（推荐），keyword-独立关键词搜索")
    keyword: Optional[str] = Field(None, max_length=200, description="source_type=keyword 时的搜索词")
    monitor_task_id: Optional[int] = Field(None, description="source_type=monitor 时关联的商品监控任务ID")
    price_min: Optional[float] = Field(None, ge=0, description="候选商品价格区间最低值")
    price_max: Optional[float] = Field(None, ge=0, description="候选商品价格区间最高值")
    interval_minutes: int = Field(60, ge=30, le=1440, description="扫描间隔分钟（风控下限30分钟）")
    max_items_per_round: int = Field(5, ge=1, le=10, description="每轮扫描商品数上限（风控上限10）")
    include_weak: bool = Field(False, description="是否入库弱意向评论")
    account_ids: List[str] = Field(default_factory=list, description="读取用账号ID列表（只读借用Cookie）")
    rescan_cooldown_hours: int = Field(24, ge=1, le=168, description="同一商品两次评论扫描最小间隔小时")
    is_enabled: bool = Field(True, description="是否启用")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class LeadTaskUpdateRequest(BaseModel):
    """更新线索采集任务请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    source_type: Optional[str] = Field(None, description="候选来源：monitor/keyword")
    keyword: Optional[str] = Field(None, max_length=200)
    monitor_task_id: Optional[int] = Field(None)
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    interval_minutes: Optional[int] = Field(None, ge=30, le=1440, description="扫描间隔分钟（风控下限30分钟）")
    max_items_per_round: Optional[int] = Field(None, ge=1, le=10, description="每轮扫描商品数上限（风控上限10）")
    include_weak: Optional[bool] = Field(None)
    account_ids: Optional[List[str]] = Field(None)
    rescan_cooldown_hours: Optional[int] = Field(None, ge=1, le=168)
    is_enabled: Optional[bool] = Field(None)
    remark: Optional[str] = Field(None, max_length=500)


class LeadTaskStatusUpdateRequest(BaseModel):
    """更新线索采集任务启停状态请求"""

    is_enabled: bool = Field(..., description="是否启用")


class LeadItemStatusUpdateRequest(BaseModel):
    """更新线索商品状态请求"""

    status: str = Field(..., description="商品状态：active-观察中，archived-已归档（归档后不再扫描）")


class LeadCommentActionRequest(BaseModel):
    """记录线索评论人工动作请求"""

    action_type: str = Field(..., description="动作类型：opened-打开商品页，copied-复制话术，ignored-忽略，followed-标记跟进")
    suggested_reply: Optional[str] = Field(None, max_length=1000, description="当时复制的建议话术（供复盘）")
    note: Optional[str] = Field(None, max_length=500, description="备注")


class LeadProbeRequest(BaseModel):
    """Phase 0 探针请求（单商品评论读取，仅人工验证用）"""

    item_id: str = Field(..., min_length=1, max_length=64, description="闲鱼商品ID")
    account_id: str = Field(..., min_length=1, max_length=80, description="读取用账号ID")


# ----------------------------------------------------------------------
# 任务配置
# ----------------------------------------------------------------------


@router.get("/tasks", response_model=ApiResponse)
async def list_lead_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    keyword: Optional[str] = Query(None, description="按任务名称筛选"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """分页查询线索采集任务列表"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    data = await svc.list_tasks(owner_id=owner_id, page=page, page_size=page_size, keyword=keyword, is_enabled=is_enabled)
    return ApiResponse(success=True, message="查询成功", data=data)


@router.post("/tasks", response_model=ApiResponse)
async def create_lead_task(
    req: LeadTaskCreateRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """创建线索采集任务（间隔最低30分钟、每轮最多10个商品，风控强校验）"""
    owner_id, _ = resolve_owner_scope(current_user)
    if owner_id is None:
        owner_id = current_user.id
    if req.source_type == "keyword" and not req.keyword:
        return ApiResponse(success=False, message="source_type=keyword 时搜索词不能为空")
    if req.source_type == "monitor" and not req.monitor_task_id:
        return ApiResponse(success=False, message="source_type=monitor 时必须关联商品监控任务")
    if not req.account_ids:
        return ApiResponse(success=False, message="至少选择一个读取账号")

    svc = LeadCaptureService(session)
    error = svc._validate_risk_limits(
        interval_minutes=req.interval_minutes,
        max_items_per_round=req.max_items_per_round,
    )
    if error:
        return ApiResponse(success=False, message=error)

    task = await svc.create_task(owner_id, req.model_dump())
    return ApiResponse(success=True, message="任务创建成功", data={"task": _task_to_dict(task)})


@router.put("/tasks/{task_id}", response_model=ApiResponse)
async def update_lead_task(
    task_id: int,
    req: LeadTaskUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """更新线索采集任务（间隔与每轮上限做风控强校验）"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    task = await svc.get(owner_id, task_id)
    if not task:
        return ApiResponse(success=False, message="任务不存在")

    error = svc._validate_risk_limits(
        interval_minutes=req.interval_minutes,
        max_items_per_round=req.max_items_per_round,
    )
    if error:
        return ApiResponse(success=False, message=error)

    if req.source_type == "keyword" and req.keyword is not None and not req.keyword.strip():
        return ApiResponse(success=False, message="source_type=keyword 时搜索词不能为空")

    update_data = req.model_dump(exclude_unset=True)
    if req.source_type == "monitor" and "monitor_task_id" in update_data and update_data["monitor_task_id"] is None:
        # monitor 来源必须有监控任务，未提供时保持原值
        update_data.pop("monitor_task_id")

    task = await svc.update_task(task, update_data)
    return ApiResponse(success=True, message="任务更新成功", data={"task": _task_to_dict(task)})


@router.post("/tasks/{task_id}/status", response_model=ApiResponse)
async def update_lead_task_status(
    task_id: int,
    req: LeadTaskStatusUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """更新线索采集任务启停状态"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    task = await svc.get(owner_id, task_id)
    if not task:
        return ApiResponse(success=False, message="任务不存在")
    task = await svc.update_status(task, req.is_enabled)
    return ApiResponse(success=True, message="任务状态更新成功", data={"task": _task_to_dict(task)})


@router.delete("/tasks/{task_id}", response_model=ApiResponse)
async def delete_lead_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """删除线索采集任务（软删除）"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    task = await svc.get(owner_id, task_id)
    if not task:
        return ApiResponse(success=False, message="任务不存在")
    await svc.delete_task(task)
    return ApiResponse(success=True, message="任务已删除")


@router.post("/tasks/{task_id}/run", response_model=ApiResponse)
async def run_lead_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """手动执行单个线索采集任务的扫描（立即执行一次，忽略间隔，日志记为手动触发）"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    task = await svc.get(owner_id, task_id)
    if not task:
        return ApiResponse(success=False, message="任务不存在")
    if not task.is_enabled:
        return ApiResponse(success=False, message="任务已停用，请先启用后再手动扫描")

    settings = get_settings()
    http_client = get_http_client()
    url = f"{settings.scheduler_service_url}/internal/tasks/lead_comment_scan/run/{task_id}"
    try:
        resp = await http_client.post(url)
    except Exception as exc:  # noqa: BLE001
        return ApiResponse(success=False, message=f"调用扫描服务失败：{exc}")
    if not isinstance(resp, dict) or not resp.get("success"):
        msg = resp.get("message") if isinstance(resp, dict) else None
        return ApiResponse(success=False, message=msg or "扫描执行失败")
    return ApiResponse(success=True, message=resp.get("message") or "扫描已执行")


# ----------------------------------------------------------------------
# 线索数据（只读展示）
# ----------------------------------------------------------------------


@router.get("/items", response_model=ApiResponse)
async def list_lead_items(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    status: Optional[str] = Query(None, description="商品状态：active/archived"),
    keyword: Optional[str] = Query(None, description="按商品标题筛选"),
    min_demand_score: Optional[int] = Query(None, ge=0, description="需求热度分下限"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """分页查询线索商品池（按需求热度分降序）"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    data = await svc.list_items(
        owner_id=owner_id,
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword,
        min_demand_score=min_demand_score,
    )
    return ApiResponse(success=True, message="查询成功", data=data)


@router.post("/items/{item_db_id}/status", response_model=ApiResponse)
async def update_lead_item_status(
    item_db_id: int,
    req: LeadItemStatusUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """更新线索商品状态（归档后不再扫描）"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    item = await svc.update_item_status(owner_id, item_db_id, req.status)
    if not item:
        return ApiResponse(success=False, message="线索商品不存在或状态值非法")
    from app.services.lead_capture_service import _item_to_dict

    return ApiResponse(success=True, message="状态更新成功", data={"item": _item_to_dict(item)})


@router.get("/items/{item_db_id}/comments", response_model=ApiResponse)
async def list_lead_item_comments(
    item_db_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    intent_level: Optional[str] = Query(None, description="意向层级：strong/medium/weak"),
    status: Optional[str] = Query(None, description="处理状态：new/reviewed/ignored/followed"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """查询某线索商品下的评论列表"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    data = await svc.list_comments(
        owner_id=owner_id,
        page=page,
        page_size=page_size,
        intent_level=intent_level,
        status=status,
        lead_item_id=item_db_id,
    )
    return ApiResponse(success=True, message="查询成功", data=data)


@router.get("/comments", response_model=ApiResponse)
async def list_lead_comments(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    intent_level: Optional[str] = Query(None, description="意向层级：strong/medium/weak"),
    status: Optional[str] = Query(None, description="处理状态：new/reviewed/ignored/followed"),
    keyword: Optional[str] = Query(None, description="按评论内容筛选"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """分页查询高意向评论流（附带所属商品摘要）"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    data = await svc.list_comments(
        owner_id=owner_id,
        page=page,
        page_size=page_size,
        intent_level=intent_level,
        status=status,
        keyword=keyword,
        with_item=True,
    )
    return ApiResponse(success=True, message="查询成功", data=data)


@router.post("/comments/{comment_id}/action", response_model=ApiResponse)
async def record_lead_comment_action(
    comment_id: int,
    req: LeadCommentActionRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """记录线索评论的人工动作（opened/copied/ignored/followed），followed 为终态防重复跟进"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    comment = await svc.get_comment(owner_id, comment_id)
    if not comment:
        return ApiResponse(success=False, message="评论不存在")
    try:
        data = await svc.record_action(
            comment,
            action_type=req.action_type,
            operator=current_user.username,
            suggested_reply=req.suggested_reply,
            note=req.note,
        )
    except ValueError as exc:
        return ApiResponse(success=False, message=str(exc))
    return ApiResponse(success=True, message="动作已记录", data=data)


@router.get("/comments/{comment_id}/suggestions", response_model=ApiResponse)
async def get_lead_comment_suggestions(
    comment_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """生成建议话术（纯本地模板，仅人工参考，系统不提供任何发送通道）"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    data = await svc.get_suggestions(owner_id, comment_id)
    if not data:
        return ApiResponse(success=False, message="评论不存在")
    return ApiResponse(success=True, message="生成成功", data=data)


# ----------------------------------------------------------------------
# 扫描日志与总览
# ----------------------------------------------------------------------


@router.get("/logs", response_model=ApiResponse)
async def list_lead_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    task_id: Optional[int] = Query(None, description="按任务筛选"),
    status: Optional[str] = Query(None, description="按执行状态筛选：success/failed/partial/risk_stopped"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """分页查询线索扫描执行日志"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    data = await svc.list_logs(owner_id=owner_id, page=page, page_size=page_size, task_id=task_id, status=status)
    return ApiResponse(success=True, message="查询成功", data=data)


@router.get("/overview", response_model=ApiResponse)
async def lead_overview(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """线索池总览统计（任务/商品/评论计数 + 今日新增 + 近7天趋势）"""
    owner_id, _ = resolve_owner_scope(current_user)
    svc = LeadCaptureService(session)
    data = await svc.overview(owner_id)
    return ApiResponse(success=True, message="查询成功", data=data)


# ----------------------------------------------------------------------
# Phase 0 探针（仅人工验证用）
# ----------------------------------------------------------------------


@router.post("/probe", response_model=ApiResponse)
async def lead_probe(
    req: LeadProbeRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Phase 0 可行性探针：单商品评论读取（每次调用间隔 ≥60 秒）。

    仅用于人工验证评论区低频读取是否稳定；不写库、不计入全局日上限。
    """
    owner_id, _ = resolve_owner_scope(current_user)
    if owner_id is None:
        owner_id = current_user.id
    svc = LeadCaptureService(session)
    data = await svc.probe(owner_id, req.item_id, req.account_id)
    if not data.get("success"):
        return ApiResponse(success=False, message=data.get("error") or "探针执行失败", data=data)
    return ApiResponse(success=True, message="探针执行完成", data=data)
