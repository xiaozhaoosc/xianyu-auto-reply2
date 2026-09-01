"""
商品跨账号迁移API

功能：
1. 预览源账号中"有卡券关联"的商品（只搬这类，无卡券商品不予理会）
2. 创建迁移批次：拉取商品素材(标题/价格/类目/图集) + 复制卡券 + 建立卡券映射
3. 批次控制：开始/暂停/恢复/取消（发布后由 scheduler 按批次随机间隔逐个发布）
4. 任务编辑：发布前可修改标题/价格/描述

风控设计：
- 素材只走 mtop.idle.web.xyh.item.list（系统日常在用的安全接口），不触碰详情接口(USER_VALIDATE)
- 发布节奏由 scheduler 控制：每发完一个商品，随机 3~10 分钟后再发下一个
"""
from __future__ import annotations

import json
import random
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.services.account_service import AccountService
from common.models.user import User
from common.models.xy_account import XYAccount
from common.models.xy_catalog_item import XYCatalogItem
from common.models.card import Card
from common.models.card_item_relation import CardItemRelation
from common.models.migration import MigrationBatch, MigrationTask, MigrationCardMap
from common.schemas.common import ApiResponse
from common.utils.auth_scope import resolve_owner_scope

router = APIRouter(tags=["migration"])


# ---------------- 请求/响应模型 ----------------

class SourceItemOut(BaseModel):
    item_id: str
    title: str | None = None
    price: str | None = None
    card_count: int = 0
    card_names: List[str] = []


class BatchCreateRequest(BaseModel):
    source_account_id: str = Field(..., description="源闲鱼账号ID")
    target_account_id: str = Field(..., description="目标闲鱼账号ID")
    item_ids: Optional[List[str]] = Field(None, description="只迁移这些商品(空=全部有卡券的)")
    description_template: Optional[str] = Field(
        None, description="描述模板，支持 {title} 占位符；留空用默认模板"
    )
    min_interval: int = Field(180, ge=60, le=86400, description="最小间隔秒(默认3分钟)")
    max_interval: int = Field(600, ge=60, le=86400, description="最大间隔秒(默认10分钟)")


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    price: Optional[str] = None
    description: Optional[str] = None
    # 类目覆盖：{cat_name, channel_cat_id, channel_cat_name}；发布时锁定该类目（不改标题）
    category_override: Optional[dict] = None
    clear_category_override: bool = Field(False, description="设为 true 时清除类目覆盖")


DEFAULT_DESCRIPTION_TEMPLATE = "{title}\n\n下单后自动发货，无需等待。\n虚拟商品售出不退，请确认后再拍。"


# ---------------- 工具函数 ----------------

def _render_description(template: str | None, title: str) -> str:
    tpl = template or DEFAULT_DESCRIPTION_TEMPLATE
    try:
        return tpl.replace("{title}", title)
    except Exception:
        return f"{title}\n\n{tpl}"


def _effective_owner(current_user: User) -> int:
    """迁移功能按账号所有者隔离。

    resolve_owner_scope 对管理员返回 None（看全量），但迁移的查询/写库都需要
    具体 owner_id；系统内账号均挂在所属用户（当前即 admin）名下，故管理员落到自身 id。
    """
    owner_id, _ = resolve_owner_scope(current_user)
    return owner_id if owner_id is not None else current_user.id


async def _get_account_by_xianyu_id(
    db: AsyncSession, owner_id: int, xianyu_account_id: str
) -> XYAccount | None:
    result = await db.execute(
        select(XYAccount).where(
            XYAccount.account_id == xianyu_account_id,
            XYAccount.owner_id == owner_id,
        )
    )
    return result.scalar_one_or_none()


def _parse_image_infos(items: list[dict]) -> dict[str, dict]:
    """从 item.list 结果提取 item_id → {images, title, price, category_id}"""
    out: dict[str, dict] = {}
    for it in items or []:
        item_id = str(it.get("id") or "")
        if not item_id:
            continue
        images: list[str] = []
        detail_params = it.get("detail_params") or {}
        raw = detail_params.get("imageInfos")
        if raw:
            try:
                infos = json.loads(raw) if isinstance(raw, str) else raw
                for info in infos or []:
                    url = (info or {}).get("url")
                    if url:
                        images.append(url)
            except Exception:
                pass
        if not images:
            pic = (it.get("pic_info") or {}).get("picUrl")
            if pic:
                images.append(pic)
        out[item_id] = {
            "images": images,
            "title": it.get("title") or detail_params.get("title") or "",
            "price": str(it.get("price") or detail_params.get("soldPrice") or ""),
            "category_id": str(it.get("category_id") or ""),
        }
    return out


# ---------------- 路由 ----------------

@router.get("/source-items")
async def list_source_items(
    source_account_id: str,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """预览源账号中有卡券关联的商品（迁移候选清单）"""
    owner_id = _effective_owner(current_user)
    account = await _get_account_by_xianyu_id(db, owner_id, source_account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="源账号不存在")

    # 有卡券关联的商品及其卡券
    stmt = (
        select(XYCatalogItem, CardItemRelation, Card)
        .join(CardItemRelation, CardItemRelation.item_id == XYCatalogItem.item_id)
        .join(Card, Card.id == CardItemRelation.card_id)
        .where(XYCatalogItem.account_pk == account.id)
    )
    rows = (await db.execute(stmt)).all()

    grouped: dict[str, SourceItemOut] = {}
    for catalog_item, _rel, card in rows:
        entry = grouped.setdefault(
            catalog_item.item_id,
            SourceItemOut(
                item_id=catalog_item.item_id,
                title=catalog_item.title,
                price=catalog_item.price,
                card_count=0,
                card_names=[],
            ),
        )
        entry.card_count += 1
        if card and card.name and card.name not in entry.card_names:
            entry.card_names.append(card.name)

    items = sorted(grouped.values(), key=lambda x: x.item_id)
    return ApiResponse(success=True, data={"total": len(items), "items": [i.model_dump() for i in items]})


@router.post("/batches")
async def create_batch(
    req: BatchCreateRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """创建迁移批次：复制卡券 + 生成迁移任务（不发布，需再调用 start）"""
    owner_id = _effective_owner(current_user)

    if req.source_account_id == req.target_account_id:
        raise HTTPException(status_code=400, detail="源账号与目标账号不能相同")
    if req.min_interval > req.max_interval:
        raise HTTPException(status_code=400, detail="min_interval 不能大于 max_interval")

    source = await _get_account_by_xianyu_id(db, owner_id, req.source_account_id)
    target = await _get_account_by_xianyu_id(db, owner_id, req.target_account_id)
    if not source:
        raise HTTPException(status_code=404, detail="源账号不存在")
    if not target:
        raise HTTPException(status_code=404, detail="目标账号不存在")
    if not source.cookie:
        raise HTTPException(status_code=400, detail="源账号cookie为空，无法拉取商品素材")

    # 1) 选中有卡券关联的商品（只搬这类）
    rel_stmt = (
        select(XYCatalogItem.item_id, XYCatalogItem.title, XYCatalogItem.price, CardItemRelation.card_id)
        .join(CardItemRelation, CardItemRelation.item_id == XYCatalogItem.item_id)
        .where(XYCatalogItem.account_pk == source.id)
    )
    rel_rows = (await db.execute(rel_stmt)).all()
    item_ids_with_cards = sorted({r[0] for r in rel_rows})
    if req.item_ids:
        wanted = set(req.item_ids)
        item_ids_with_cards = [i for i in item_ids_with_cards if i in wanted]
    if not item_ids_with_cards:
        return ApiResponse(success=False, message="源账号没有带卡券关联的商品可迁移")

    source_card_ids = sorted({r[3] for r in rel_rows if r[0] in set(item_ids_with_cards)})

    # 2) 拉商品素材（item.list，安全接口）
    from common.utils.item_info_manager import ItemInfoManager

    materials: dict[str, dict] = {}
    try:
        mgr = ItemInfoManager(cookie_id=str(source.account_id), cookies_str=source.cookie)
        try:
            all_items = await mgr.get_all_items(page_size=20, max_pages=20, myid=str(source.account_id))
            if isinstance(all_items, dict):
                all_items = all_items.get("items") or []
            materials = _parse_image_infos(all_items)
        finally:
            await mgr.close()
    except Exception as e:
        logger.warning(f"[迁移] 拉取源账号商品列表失败，将用本地目录兜底: {e}")

    # 3) 复制卡券（同 user 下新建），记录映射
    batch = MigrationBatch(
        owner_id=owner_id,
        source_account_id=req.source_account_id,
        target_account_id=req.target_account_id,
        status="prepared",
        description_template=req.description_template or DEFAULT_DESCRIPTION_TEMPLATE,
        min_interval=req.min_interval,
        max_interval=req.max_interval,
    )
    db.add(batch)
    await db.flush()  # 拿 batch.id

    card_result = await db.execute(select(Card).where(Card.id.in_(source_card_ids)))
    source_cards = card_result.scalars().all()
    card_map: dict[int, int] = {}
    for c in source_cards:
        new_card = Card(
            user_id=c.user_id,
            item_id=None,
            name=c.name,
            type=c.type,
            description=c.description,
            enabled=c.enabled,
            delay_seconds=c.delay_seconds,
            delivery_count=0,
            price=c.price,
            is_dockable=c.is_dockable,
            fee_payer=c.fee_payer,
            min_price=c.min_price,
            dock_visibility=c.dock_visibility,
            is_multi_spec=c.is_multi_spec,
            spec_name=c.spec_name,
            spec_value=c.spec_value,
            api_config=c.api_config,
            text_content=c.text_content,
            data_content=c.data_content,
            image_url=c.image_url,
            image_urls=c.image_urls,
        )
        db.add(new_card)
        await db.flush()
        card_map[c.id] = new_card.id
        db.add(MigrationCardMap(
            batch_id=batch.id, source_card_id=c.id, new_card_id=new_card.id, card_name=c.name,
        ))

    # 4) 生成任务
    created = 0
    missing_material: list[str] = []
    for item_id in item_ids_with_cards:
        mat = materials.get(item_id)
        if not mat or not mat.get("images"):
            missing_material.append(item_id)
        title = (mat or {}).get("title") or next((r[1] for r in rel_rows if r[0] == item_id), "") or item_id
        price = (mat or {}).get("price") or next((r[2] for r in rel_rows if r[0] == item_id), None)
        db.add(MigrationTask(
            batch_id=batch.id,
            source_item_id=item_id,
            title=title,
            price=price,
            category_id=(mat or {}).get("category_id"),
            description=_render_description(batch.description_template, title),
            images_json=json.dumps((mat or {}).get("images") or [], ensure_ascii=False),
            status="pending",
        ))
        created += 1

    batch.total = created
    await db.commit()

    if missing_material:
        logger.warning(f"[迁移] 批次{batch.id} 有 {len(missing_material)} 个商品未从列表接口取到图集，发布时会失败需跳过: {missing_material[:5]}")

    return ApiResponse(success=True, 
        data={
            "batch_id": batch.id,
            "total": created,
            "cards_copied": len(card_map),
            "missing_material_count": len(missing_material),
            "missing_material_items": missing_material[:20],
        },
        message=f"批次已创建：{created} 个商品、{len(card_map)} 张卡券已复制",
    )


@router.get("/batches")
async def list_batches(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_session),
):
    owner_id = _effective_owner(current_user)
    result = await db.execute(
        select(MigrationBatch).where(MigrationBatch.owner_id == owner_id).order_by(MigrationBatch.id.desc())
    )
    batches = result.scalars().all()
    now = datetime.now()
    data = []
    for b in batches:
        data.append({
            "id": b.id,
            "source_account_id": b.source_account_id,
            "target_account_id": b.target_account_id,
            "status": b.status,
            "total": b.total,
            "published": b.published,
            "failed": b.failed,
            "min_interval": b.min_interval,
            "max_interval": b.max_interval,
            "next_run_at": b.next_run_at.isoformat() if b.next_run_at else None,
            "next_run_in_seconds": max(0, int((b.next_run_at - now).total_seconds())) if b.next_run_at and b.status == "running" else None,
            "last_error": b.last_error,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "started_at": b.started_at.isoformat() if b.started_at else None,
            "finished_at": b.finished_at.isoformat() if b.finished_at else None,
        })
    return ApiResponse(success=True, data={"batches": data})


@router.get("/batches/{batch_id}")
async def get_batch(
    batch_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_session),
):
    owner_id = _effective_owner(current_user)
    batch = (await db.execute(
        select(MigrationBatch).where(MigrationBatch.id == batch_id, MigrationBatch.owner_id == owner_id)
    )).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    tasks = (await db.execute(
        select(MigrationTask).where(MigrationTask.batch_id == batch_id).order_by(MigrationTask.id)
    )).scalars().all()
    card_maps = (await db.execute(
        select(MigrationCardMap).where(MigrationCardMap.batch_id == batch_id)
    )).scalars().all()

    def _task_out(t: MigrationTask) -> dict:
        images = []
        try:
            images = json.loads(t.images_json or "[]")
        except Exception:
            pass
        return {
            "id": t.id,
            "source_item_id": t.source_item_id,
            "title": t.title,
            "price": t.price,
            "category_id": t.category_id,
            "category_override": _parse_override(t.category_override_json),
            "description": t.description,
            "image_count": len(images),
            "first_image": images[0] if images else None,
            "status": t.status,
            "new_item_id": t.new_item_id,
            "error": t.error,
            "attempts": t.attempts,
            "published_at": t.published_at.isoformat() if t.published_at else None,
        }

    now = datetime.now()
    return ApiResponse(success=True, data={
        "batch": {
            "id": batch.id,
            "source_account_id": batch.source_account_id,
            "target_account_id": batch.target_account_id,
            "status": batch.status,
            "total": batch.total,
            "published": batch.published,
            "failed": batch.failed,
            "description_template": batch.description_template,
            "min_interval": batch.min_interval,
            "max_interval": batch.max_interval,
            "next_run_at": batch.next_run_at.isoformat() if batch.next_run_at else None,
            "next_run_in_seconds": max(0, int((batch.next_run_at - now).total_seconds())) if batch.next_run_at and batch.status == "running" else None,
            "last_error": batch.last_error,
        },
        "tasks": [_task_out(t) for t in tasks],
        "cards_copied": len(card_maps),
    })


@router.post("/batches/{batch_id}/start")
async def start_batch(
    batch_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_session),
):
    owner_id = _effective_owner(current_user)
    batch = (await db.execute(
        select(MigrationBatch).where(MigrationBatch.id == batch_id, MigrationBatch.owner_id == owner_id)
    )).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")
    if batch.status not in ("prepared", "paused"):
        return ApiResponse(success=False, message=f"当前状态 {batch.status} 不能启动")

    pending = (await db.execute(
        select(func.count(MigrationTask.id)).where(
            MigrationTask.batch_id == batch_id, MigrationTask.status == "pending"
        )
    )).scalar() or 0
    if pending == 0:
        return ApiResponse(success=False, message="没有待发布的商品")

    batch.status = "running"
    batch.last_error = None
    if not batch.started_at:
        batch.started_at = datetime.now()
    # 首次发布也走随机间隔，不立即发
    batch.next_run_at = datetime.now().replace(microsecond=0) + _random_delta(batch)
    await db.commit()
    logger.info(f"[迁移] 批次{batch_id} 已启动，首次发布约在 {batch.next_run_at}")
    return ApiResponse(success=True, 
        data={"batch_id": batch_id, "next_run_at": batch.next_run_at.isoformat()},
        message=f"迁移已启动，首次发布将在 {batch.min_interval}~{batch.max_interval} 秒后随机触发",
    )


@router.post("/batches/{batch_id}/pause")
async def pause_batch(
    batch_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_session),
):
    owner_id = _effective_owner(current_user)
    batch = (await db.execute(
        select(MigrationBatch).where(MigrationBatch.id == batch_id, MigrationBatch.owner_id == owner_id)
    )).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")
    if batch.status != "running":
        return ApiResponse(success=False, message=f"当前状态 {batch.status} 不能暂停")
    batch.status = "paused"
    await db.commit()
    return ApiResponse(success=True, message="已暂停（正在发布中的商品会发完当前这个）")


@router.post("/batches/{batch_id}/cancel")
async def cancel_batch(
    batch_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_session),
):
    owner_id = _effective_owner(current_user)
    batch = (await db.execute(
        select(MigrationBatch).where(MigrationBatch.id == batch_id, MigrationBatch.owner_id == owner_id)
    )).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")
    if batch.status in ("done", "cancelled"):
        return ApiResponse(success=False, message=f"当前状态 {batch.status} 不能取消")
    batch.status = "cancelled"
    batch.finished_at = datetime.now()
    # 未发布的标记为 skipped
    pending_tasks = (await db.execute(
        select(MigrationTask).where(MigrationTask.batch_id == batch_id, MigrationTask.status == "pending")
    )).scalars().all()
    for t in pending_tasks:
        t.status = "skipped"
    await db.commit()
    return ApiResponse(success=True, message=f"已取消，{len(pending_tasks)} 个未发布商品标记为跳过")


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: int,
    req: TaskUpdateRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """发布前编辑任务（仅 pending 状态可改）"""
    owner_id = _effective_owner(current_user)
    task = (await db.execute(
        select(MigrationTask)
        .join(MigrationBatch, MigrationBatch.id == MigrationTask.batch_id)
        .where(MigrationTask.id == task_id, MigrationBatch.owner_id == owner_id)
    )).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status not in ("pending", "failed"):
        return ApiResponse(success=False, message="仅待发布或失败状态可编辑")
    if req.title is not None:
        task.title = req.title
    if req.price is not None:
        task.price = req.price
    if req.description is not None:
        task.description = req.description
    if req.clear_category_override:
        task.category_override_json = None
    elif req.category_override is not None:
        cat_name = str(req.category_override.get("cat_name") or "").strip()
        channel_cat_id = str(req.category_override.get("channel_cat_id") or "").strip()
        channel_cat_name = str(req.category_override.get("channel_cat_name") or "").strip() or cat_name
        if not (cat_name and channel_cat_id):
            return ApiResponse(success=False, message="类目覆盖缺少 cat_name / channel_cat_id")
        task.category_override_json = json.dumps(
            {"cat_name": cat_name, "channel_cat_id": channel_cat_id, "channel_cat_name": channel_cat_name},
            ensure_ascii=False,
        )
    await db.commit()
    return ApiResponse(success=True, message="已保存")


def _parse_override(raw: Optional[str]) -> Optional[dict]:
    """解析任务上的类目覆盖JSON；无效返回 None"""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


# 闲鱼类目名中常要求 ISBN 条码的字样（用于前端提示，非硬判断）
_BOOK_LIKE_KEYWORDS = ("图书", "书籍", "教材", "小说", "散文", "文学", "杂志", "报刊", "童书", "绘本")


@router.get("/tasks/{task_id}/category-candidates")
async def task_category_candidates(
    task_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """获取该任务（基于标题/描述）的类目候选列表，供编辑向导选择覆盖类目。

    仅一轮推荐，结果瞬时不落库；选定后由发布流程重新走两阶段协议。
    """
    owner_id = _effective_owner(current_user)
    row = (await db.execute(
        select(MigrationTask, MigrationBatch)
        .join(MigrationBatch, MigrationBatch.id == MigrationTask.batch_id)
        .where(MigrationTask.id == task_id, MigrationBatch.owner_id == owner_id)
    )).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="任务不存在")
    task, batch = row
    if task.status not in ("pending", "failed"):
        return ApiResponse(success=False, message="仅待发布或失败状态支持更换类目")

    account = (await db.execute(
        select(XYAccount).where(XYAccount.account_id == batch.target_account_id)
    )).scalar_one_or_none()
    if not account:
        return ApiResponse(success=False, message="目标账号不存在")

    from app.services.platform_category_service import PlatformCategoryService, CategoryRecommendationError
    try:
        result = await PlatformCategoryService().recommend(
            title=task.title,
            description=task.description or task.title,
            cookie=account.cookie,
            account_id=account.account_id,
            owner_id=None,
        )
    except CategoryRecommendationError as e:
        return ApiResponse(success=False, message=str(e))

    candidates = []
    for c in result.get("candidates") or []:
        name = c.get("cat_name") or c.get("channel_cat_name") or ""
        candidates.append({
            "cat_id": c.get("cat_id"),
            "cat_name": c.get("cat_name"),
            "channel_cat_id": c.get("channel_cat_id"),
            "channel_cat_name": c.get("channel_cat_name"),
            "tb_cat_id": c.get("tb_cat_id"),
            "is_selected": bool(c.get("is_selected")),
            "may_need_isbn": any(k in name for k in _BOOK_LIKE_KEYWORDS),
        })
    return ApiResponse(success=True, data={"candidates": candidates})


@router.post("/tasks/{task_id}/retry")
async def retry_task(
    task_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_session),
):
    """将 failed/skipped 任务重置为 pending 重发，并唤醒批次重新排队。"""
    owner_id = _effective_owner(current_user)
    row = (await db.execute(
        select(MigrationTask, MigrationBatch)
        .join(MigrationBatch, MigrationBatch.id == MigrationTask.batch_id)
        .where(MigrationTask.id == task_id, MigrationBatch.owner_id == owner_id)
    )).one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="任务不存在")
    task, batch = row
    if task.status not in ("failed", "skipped"):
        return ApiResponse(success=False, message=f"当前状态 {task.status} 无需重试")

    task.status = "pending"
    task.attempts = 0
    task.error = None
    task.new_item_id = None
    task.published_at = None

    # 批次恢复运行并尽快发车；失败数按库中实际重算
    failed_count = (await db.execute(
        select(func.count(MigrationTask.id)).where(
            MigrationTask.batch_id == batch.id, MigrationTask.status.in_(["failed", "skipped"])
        )
    )).scalar() or 0
    batch.failed = failed_count
    if batch.status != "cancelled":
        batch.status = "running"
        batch.finished_at = None
        batch.next_run_at = datetime.now()
        batch.last_error = None
    await db.commit()
    logger.info(f"[迁移] 任务{task_id} 已重置重试，批次{batch.id} 状态={batch.status}")
    return ApiResponse(success=True, message="已重置为待发布，迁移循环将尽快重新发车")


from datetime import timedelta  # noqa: E402


def _random_delta(batch: MigrationBatch) -> timedelta:
    lo = min(batch.min_interval, batch.max_interval)
    hi = max(batch.min_interval, batch.max_interval)
    return timedelta(seconds=random.randint(lo, hi))
