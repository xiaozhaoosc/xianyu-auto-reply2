"""
Goofish 定时采集路由模块

提供 Goofish 定时采集任务的 CRUD、启动/停止、立即执行接口
前端API路径: /api/v1/goofish/crawler/jobs
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db_session as get_db
from app.services.goofish_crawler import get_goofish_crawl_manager
from common.models.goofish_crawl_item import GoofishCrawlItem
from common.models.goofish_crawl_job import GoofishCrawlJob
from common.models.user import User
from common.schemas.common import ApiResponse

from common.utils.time_utils import safe_isoformat
router = APIRouter(prefix="/goofish/crawler", tags=["Goofish定时采集"])
goofish_crawl_manager = get_goofish_crawl_manager()


class GoofishCrawlJobCreate(BaseModel):
    """创建采集任务请求"""
    cookie_id: str = Field(..., description="账号ID")
    keyword: str = Field(..., description="搜索关键词")
    interval_seconds: int = Field(900, ge=60, le=86400, description="执行间隔（秒）")
    start_page: int = Field(1, ge=1, le=50, description="起始页码")
    pages: int = Field(1, ge=1, le=10, description="抓取页数")
    page_size: int = Field(20, ge=1, le=50, description="每页数量")
    fetch_detail: bool = Field(True, description="是否抓取详情")
    detail_limit: int = Field(20, ge=0, le=50, description="详情抓取数量限制")
    enabled: bool = Field(True, description="是否启用")


# ==================== 任务列表 ====================

@router.get("/jobs")
async def list_jobs(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取采集任务列表"""
    try:
        # 查询当前用户的任务
        stmt = (
            select(GoofishCrawlJob)
            .where(GoofishCrawlJob.owner_id == current_user.id)
            .order_by(desc(GoofishCrawlJob.created_at))
        )
        result = await db.execute(stmt)
        jobs = result.scalars().all()
        
        # 获取每个任务的采集数量和最新采集时间
        running_job_ids = set(goofish_crawl_manager.get_running_tasks())
        job_list = []
        for job in jobs:
            # 查询采集数量
            count_stmt = select(func.count(GoofishCrawlItem.id)).where(
                GoofishCrawlItem.job_id == job.id
            )
            count_result = await db.execute(count_stmt)
            item_count = count_result.scalar() or 0
            
            # 查询最新采集时间
            latest_stmt = (
                select(GoofishCrawlItem.fetched_at)
                .where(GoofishCrawlItem.job_id == job.id)
                .order_by(desc(GoofishCrawlItem.fetched_at))
                .limit(1)
            )
            latest_result = await db.execute(latest_stmt)
            latest_fetched = latest_result.scalar()
            
            job_list.append({
                "id": job.id,
                "cookie_id": job.cookie_id,
                "keyword": job.keyword,
                "interval_seconds": job.interval_seconds,
                "start_page": job.start_page,
                "pages": job.pages,
                "page_size": job.page_size,
                "fetch_detail": job.fetch_detail,
                "detail_limit": job.detail_limit,
                "enabled": job.enabled,
                "running": job.id in running_job_ids,
                "last_run_at": safe_isoformat(job.last_run_at),
                "last_error": job.last_error,
                "item_count": item_count,
                "latest_item_fetched_at": safe_isoformat(latest_fetched),
            })
        
        return {"jobs": job_list}
        
    except Exception as e:
        logger.error(f"获取采集任务列表失败: {e}")
        return {"jobs": []}


# ==================== 创建任务 ====================

@router.post("/jobs")
async def create_job(
    payload: GoofishCrawlJobCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建采集任务"""
    try:
        job = GoofishCrawlJob(
            owner_id=current_user.id,
            cookie_id=payload.cookie_id,
            keyword=payload.keyword,
            interval_seconds=payload.interval_seconds,
            start_page=payload.start_page,
            pages=payload.pages,
            page_size=payload.page_size,
            fetch_detail=payload.fetch_detail,
            detail_limit=payload.detail_limit,
            enabled=payload.enabled,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        logger.info(f"创建采集任务成功: job_id={job.id}, keyword={payload.keyword}")
        return {"success": True, "job_id": job.id, "message": "创建成功"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"创建采集任务失败: {e}")
        return ApiResponse(success=False, message=f"创建失败: {str(e)}")


# ==================== 启动任务 ====================

@router.post("/jobs/{job_id}/start")
async def start_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """启动采集任务（设置enabled=True）"""
    try:
        stmt = select(GoofishCrawlJob).where(
            GoofishCrawlJob.id == job_id,
            GoofishCrawlJob.owner_id == current_user.id,
        )
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return ApiResponse(success=False, message="任务不存在")

        job.enabled = True
        await db.commit()
        goofish_crawl_manager.start_job(job_id=job_id)

        logger.info(f"启动采集任务: job_id={job_id}")
        return ApiResponse(success=True, message="任务已启动")

    except Exception as e:
        await db.rollback()
        logger.error(f"启动采集任务失败: {e}")
        return ApiResponse(success=False, message=f"启动失败: {str(e)}")


# ==================== 停止任务 ====================

@router.post("/jobs/{job_id}/stop")
async def stop_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """停止采集任务（设置enabled=False）"""
    try:
        stmt = select(GoofishCrawlJob).where(
            GoofishCrawlJob.id == job_id,
            GoofishCrawlJob.owner_id == current_user.id,
        )
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return ApiResponse(success=False, message="任务不存在")

        job.enabled = False
        await db.commit()
        await goofish_crawl_manager.stop_job(job_id=job_id)

        logger.info(f"停止采集任务: job_id={job_id}")
        return ApiResponse(success=True, message="任务已停止")

    except Exception as e:
        await db.rollback()
        logger.error(f"停止采集任务失败: {e}")
        return ApiResponse(success=False, message=f"停止失败: {str(e)}")


# ==================== 获取任务状态 ====================

@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取采集任务状态"""
    try:
        stmt = select(GoofishCrawlJob).where(
            GoofishCrawlJob.id == job_id,
            GoofishCrawlJob.owner_id == current_user.id,
        )
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return ApiResponse(success=False, message="任务不存在")

        return {
            "id": job.id,
            "enabled": job.enabled,
            "running": goofish_crawl_manager.is_running(job.id),
            "last_run_at": safe_isoformat(job.last_run_at),
            "last_error": job.last_error,
        }
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return ApiResponse(success=False, message=f"获取失败: {str(e)}")



# ==================== 立即执行一次 ====================

@router.post("/jobs/{job_id}/run-once")
async def run_once_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """立即执行一次采集任务"""
    try:
        # 查询任务
        stmt = select(GoofishCrawlJob).where(
            GoofishCrawlJob.id == job_id,
            GoofishCrawlJob.owner_id == current_user.id,
        )
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return {"success": False, "error": "任务不存在", "upserted": 0, "total": 0}
        
        # 查询账号Cookie
        from common.models.xy_account import XYAccount
        account_stmt = select(XYAccount).where(XYAccount.account_id == job.cookie_id)
        account_result = await db.execute(account_stmt)
        account = account_result.scalar_one_or_none()
        
        if not account or not account.cookie:
            job.last_error = "账号Cookie不可用"
            await db.commit()
            return {"success": False, "error": "账号Cookie不可用", "upserted": 0, "total": 0}
        
        # 执行采集
        try:
            from app.services.compass.goofish_compass import GoofishCompassService, GoofishCompassConfig
            
            config = GoofishCompassConfig(
                headless=not account.show_browser,
                detail_concurrency=3,
                navigation_timeout_ms=30000,
                network_idle_timeout_ms=15000,
                detail_response_timeout_ms=7000,
            )
            
            service = GoofishCompassService(
                user_id=str(account.id),
                cookie_value=account.cookie,
                config=config,
            )
            
            search_result = await service.search(
                keyword=job.keyword,
                start_page=job.start_page,
                pages=job.pages,
                page_size=job.page_size,
                fetch_detail=job.fetch_detail,
                detail_limit=job.detail_limit,
            )
            
            if search_result.get("error"):
                job.last_error = search_result["error"]
                job.last_run_at = datetime.now(timezone.utc)
                await db.commit()
                return {
                    "success": False,
                    "error": search_result["error"],
                    "upserted": 0,
                    "total": 0,
                }
            
            # 保存采集结果
            items = search_result.get("items", [])
            upserted = 0
            
            for item_data in items:
                item_id = item_data.get("item_id")
                if not item_id:
                    continue
                
                # 检查是否已存在
                existing_stmt = select(GoofishCrawlItem).where(
                    GoofishCrawlItem.job_id == job.id,
                    GoofishCrawlItem.item_id == str(item_id),
                )
                existing_result = await db.execute(existing_stmt)
                existing_item = existing_result.scalar_one_or_none()
                
                now = datetime.now(timezone.utc)
                
                if existing_item:
                    # 更新现有记录
                    existing_item.title = item_data.get("title")
                    existing_item.price = item_data.get("price")
                    existing_item.area = item_data.get("area")
                    existing_item.seller_name = item_data.get("seller_name")
                    existing_item.item_url = item_data.get("item_url")
                    existing_item.main_image = item_data.get("main_image")
                    existing_item.publish_time = item_data.get("publish_time")
                    existing_item.want_count = item_data.get("want_count")
                    existing_item.view_count = item_data.get("view_count")
                    existing_item.description = item_data.get("description")
                    existing_item.detail_error = item_data.get("detail_error")
                    existing_item.fetched_at = now
                else:
                    # 创建新记录
                    new_item = GoofishCrawlItem(
                        job_id=job.id,
                        item_id=str(item_id),
                        title=item_data.get("title"),
                        price=item_data.get("price"),
                        area=item_data.get("area"),
                        seller_name=item_data.get("seller_name"),
                        item_url=item_data.get("item_url"),
                        main_image=item_data.get("main_image"),
                        publish_time=item_data.get("publish_time"),
                        want_count=item_data.get("want_count"),
                        view_count=item_data.get("view_count"),
                        description=item_data.get("description"),
                        detail_error=item_data.get("detail_error"),
                        fetched_at=now,
                    )
                    db.add(new_item)
                
                upserted += 1
            
            # 更新任务状态
            job.last_run_at = datetime.now(timezone.utc)
            job.last_error = None
            await db.commit()
            
            logger.info(f"采集任务 {job_id} 执行完成: 抓取 {len(items)} 条, 写入 {upserted} 条")
            return {
                "success": True,
                "upserted": upserted,
                "total": len(items),
            }
            
        except ImportError as e:
            error_msg = "采集服务不可用，请检查依赖"
            logger.error(f"采集服务导入失败: {e}")
            job.last_error = error_msg
            job.last_run_at = datetime.now(timezone.utc)
            await db.commit()
            return {"success": False, "error": error_msg, "upserted": 0, "total": 0}
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"执行采集任务失败: {e}")
            job.last_error = error_msg
            job.last_run_at = datetime.now(timezone.utc)
            await db.commit()
            return {"success": False, "error": error_msg, "upserted": 0, "total": 0}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"立即执行采集任务失败: {e}")
        return {"success": False, "error": str(e), "upserted": 0, "total": 0}


# ==================== 获取采集结果 ====================

@router.get("/jobs/{job_id}/items")
async def list_job_items(
    job_id: int,
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取任务的采集结果"""
    try:
        # 验证任务归属
        job_stmt = select(GoofishCrawlJob).where(
            GoofishCrawlJob.id == job_id,
            GoofishCrawlJob.owner_id == current_user.id,
        )
        job_result = await db.execute(job_stmt)
        job = job_result.scalar_one_or_none()
        
        if not job:
            return {"items": []}
        
        # 查询采集结果
        stmt = (
            select(GoofishCrawlItem)
            .where(GoofishCrawlItem.job_id == job_id)
            .order_by(desc(GoofishCrawlItem.fetched_at))
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        item_list = []
        for item in items:
            item_list.append({
                "job_id": item.job_id,
                "item_id": item.item_id,
                "title": item.title,
                "price": item.price,
                "area": item.area,
                "seller_name": item.seller_name,
                "item_url": item.item_url,
                "main_image": item.main_image,
                "publish_time": item.publish_time,
                "want_count": item.want_count,
                "view_count": item.view_count,
                "description": item.description,
                "detail_error": item.detail_error,
                "fetched_at": safe_isoformat(item.fetched_at),
            })
        
        return {"items": item_list}
        
    except Exception as e:
        logger.error(f"获取采集结果失败: {e}")
        return {"items": []}


# ==================== 按卖家采集 ====================

class FetchBySellerRequest(BaseModel):
    """按卖家 userId 采集请求"""
    user_ids: List[str] = Field(..., min_length=1, max_length=10, description="卖家 userId 列表，最多 10 个")
    cookie_id: str = Field(..., description="用于采集的账号 ID")
    min_want_count: int = Field(0, ge=0, description="最小想要人数筛选")
    min_view_count: int = Field(0, ge=0, description="最小浏览量筛选")
    max_pages: int = Field(5, ge=1, le=20, description="每个卖家最大翻页数")


@router.post("/fetch-by-seller")
async def fetch_by_seller(
    payload: FetchBySellerRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """通过卖家 userId 采集其主页商品，支持想要人数/浏览量筛选"""
    try:
        from common.models.xy_account import XYAccount
        account_stmt = select(XYAccount).where(XYAccount.account_id == payload.cookie_id)
        account_result = await db.execute(account_stmt)
        account = account_result.scalar_one_or_none()

        if not account or not account.cookie:
            return ApiResponse(success=False, message="账号 Cookie 不可用")

        from app.services.compass.goofish_compass import GoofishCompassService, GoofishCompassConfig

        config = GoofishCompassConfig(
            headless=not account.show_browser,
            navigation_timeout_ms=30000,
            network_idle_timeout_ms=15000,
        )

        service = GoofishCompassService(
            user_id=str(account.id),
            cookie_value=account.cookie,
            config=config,
        )

        all_items = []
        all_errors = []

        for uid in payload.user_ids:
            result = await service.fetch_by_seller(
                user_id=uid,
                min_want_count=payload.min_want_count,
                min_view_count=payload.min_view_count,
                max_pages=payload.max_pages,
            )
            if result.get("error"):
                all_errors.append({"user_id": uid, "error": result["error"]})
            else:
                all_items.extend(result.get("items", []))

        return ApiResponse(
            success=len(all_items) > 0,
            message=f"采集完成：成功 {len(all_items)} 个商品，失败 {len(all_errors)} 个卖家",
            data={
                "items": all_items,
                "errors": all_errors,
                "success_count": len(all_items),
                "error_count": len(all_errors),
            },
        )

    except Exception as e:
        logger.error(f"按卖家采集异常: {e}")
        return ApiResponse(success=False, message=f"采集失败: {str(e)}")


# ==================== 采集结果导入素材库 ====================

class ImportToMaterialsRequest(BaseModel):
    """导入素材库请求"""
    job_id: int = Field(..., description="采集任务 ID")
    item_ids: List[str] = Field(default=[], description="指定导入的 item_id 列表，为空则导入全部")
    min_want_count: int = Field(0, ge=0, description="最小想要人数筛选")
    min_view_count: int = Field(0, ge=0, description="最小浏览量筛选")


@router.post("/import-to-materials")
async def import_to_materials(
    payload: ImportToMaterialsRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """将采集结果导入素材库"""
    try:
        from common.models.product_material import ProductMaterial

        # 查询采集结果
        stmt = select(GoofishCrawlItem).where(GoofishCrawlItem.job_id == payload.job_id)
        result = await db.execute(stmt)
        items = result.scalars().all()

        if not items:
            return ApiResponse(success=False, message="没有找到采集结果")

        # 筛选
        filtered = []
        for item in items:
            if payload.item_ids and item.item_id not in payload.item_ids:
                continue
            if payload.min_want_count > 0 and (item.want_count or 0) < payload.min_want_count:
                continue
            if payload.min_view_count > 0 and (item.view_count or 0) < payload.min_view_count:
                continue
            filtered.append(item)

        if not filtered:
            return ApiResponse(success=False, message="筛选后没有符合条件的商品")

        # 导入素材库
        imported = 0
        for item in filtered:
            material = ProductMaterial(
                user_id=current_user.id,
                title=item.title or "",
                description=item.description or "",
                price=0,
                images=[item.main_image] if item.main_image else [],
                delivery_method="express",
                postage=0,
                address=item.area,
                condition="全新",
                remark=f"采集导入 | 想要{item.want_count or 0} | 浏览{item.view_count or 0}",
            )
            db.add(material)
            imported += 1

        await db.commit()
        return ApiResponse(
            success=True,
            message=f"成功导入 {imported} 个商品到素材库",
            data={"imported": imported, "total": len(filtered)},
        )

    except Exception as e:
        logger.error(f"导入素材库失败: {e}")
        return ApiResponse(success=False, message=f"导入失败: {str(e)}")


# ==================== 按 ID 采集 ====================

class FetchByIdRequest(BaseModel):
    """按 item_id 采集请求"""
    item_ids: List[str] = Field(..., min_length=1, max_length=20, description="item_id 列表，最多 20 个")
    cookie_id: str = Field(..., description="用于采集的账号 ID")


@router.post("/fetch-by-id")
async def fetch_by_id(
    payload: FetchByIdRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """通过 item_id 直接采集商品详情"""
    try:
        # 查询账号 Cookie
        from common.models.xy_account import XYAccount
        account_stmt = select(XYAccount).where(XYAccount.account_id == payload.cookie_id)
        account_result = await db.execute(account_stmt)
        account = account_result.scalar_one_or_none()

        if not account or not account.cookie:
            return ApiResponse(success=False, message="账号 Cookie 不可用")

        from app.services.compass.goofish_compass import GoofishCompassService, GoofishCompassConfig

        config = GoofishCompassConfig(
            headless=not account.show_browser,
            navigation_timeout_ms=30000,
            network_idle_timeout_ms=15000,
            detail_response_timeout_ms=7000,
        )

        service = GoofishCompassService(
            user_id=str(account.id),
            cookie_value=account.cookie,
            config=config,
        )

        results = []
        errors = []

        for item_id in payload.item_ids:
            result = await service.fetch_by_item_id(item_id)
            if result.get("error"):
                errors.append({"item_id": item_id, "error": result["error"]})
            else:
                items = result.get("items", [])
                results.extend(items)

        return ApiResponse(
            success=len(results) > 0,
            message=f"采集完成：成功 {len(results)} 个，失败 {len(errors)} 个",
            data={
                "items": results,
                "errors": errors,
                "success_count": len(results),
                "error_count": len(errors),
            },
        )

    except Exception as e:
        logger.error(f"按ID采集异常: {e}")
        return ApiResponse(success=False, message=f"采集失败: {str(e)}")


# ==================== 采集结果导入素材库 ====================

class ImportToMaterialRequest(BaseModel):
    """采集结果导入素材库请求"""
    item_ids: Optional[List[str]] = Field(None, description="指定导入的 item_id 列表，为空则导入全部")
    min_want_count: int = Field(0, ge=0, description="最小想要人数筛选")
    min_view_count: int = Field(0, ge=0, description="最小浏览量筛选")


@router.post("/jobs/{job_id}/import-materials")
async def import_to_materials(
    job_id: int,
    payload: ImportToMaterialRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """将采集结果导入素材库，支持按想要人数/浏览量筛选"""
    try:
        # 验证任务归属
        job_stmt = select(GoofishCrawlJob).where(
            GoofishCrawlJob.id == job_id,
            GoofishCrawlJob.owner_id == current_user.id,
        )
        job_result = await db.execute(job_stmt)
        job = job_result.scalar_one_or_none()
        if not job:
            return ApiResponse(success=False, message="任务不存在")

        # 查询采集结果
        conditions = [GoofishCrawlItem.job_id == job_id]
        if payload.item_ids:
            conditions.append(GoofishCrawlItem.item_id.in_(payload.item_ids))
        if payload.min_want_count > 0:
            conditions.append(GoofishCrawlItem.want_count >= payload.min_want_count)
        if payload.min_view_count > 0:
            conditions.append(GoofishCrawlItem.view_count >= payload.min_view_count)

        items_stmt = select(GoofishCrawlItem).where(*conditions)
        items_result = await db.execute(items_stmt)
        crawl_items = items_result.scalars().all()

        if not crawl_items:
            return ApiResponse(success=False, message="没有符合条件的采集结果")

        # 导入素材库
        from common.models.product_material import ProductMaterial
        imported = 0
        skipped = 0

        for ci in crawl_items:
            if not ci.title:
                skipped += 1
                continue

            # 检查是否已导入（按标题去重）
            dup_stmt = select(ProductMaterial).where(
                ProductMaterial.user_id == current_user.id,
                ProductMaterial.title == ci.title,
            )
            dup_result = await db.execute(dup_stmt)
            if dup_result.scalar_one_or_none():
                skipped += 1
                continue

            # 解析价格
            price = 0.0
            if ci.price:
                try:
                    price = float(ci.price.replace("￥", "").replace("¥", "").strip())
                except (ValueError, TypeError):
                    price = 0.0

            # 构建图片列表
            images = []
            if ci.main_image:
                images.append(ci.main_image)

            material = ProductMaterial(
                user_id=current_user.id,
                title=ci.title,
                description=ci.description or "",
                price=price if price > 0 else 0.01,
                images=images,
                delivery_method="express",
                postage=0,
                address=ci.area,
                condition="全新",
                remark=f"[采集导入] item_id={ci.item_id}, 想要{ci.want_count or 0}, 浏览{ci.view_count or 0}",
            )
            db.add(material)
            imported += 1

        await db.commit()

        logger.info(f"采集结果导入素材库: job_id={job_id}, imported={imported}, skipped={skipped}")
        return ApiResponse(
            success=True,
            message=f"导入完成：成功 {imported} 条，跳过 {skipped} 条（标题重复或为空）",
            data={"imported": imported, "skipped": skipped, "total": len(crawl_items)},
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"导入素材库失败: {e}")
        return ApiResponse(success=False, message=f"导入失败: {str(e)}")


# ==================== 删除任务 ====================

@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除采集任务（同时删除采集结果）"""
    try:
        # 查询任务
        stmt = select(GoofishCrawlJob).where(
            GoofishCrawlJob.id == job_id,
            GoofishCrawlJob.owner_id == current_user.id,
        )
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return ApiResponse(success=False, message="任务不存在")

        # 删除采集结果
        from sqlalchemy import delete
        delete_items_stmt = delete(GoofishCrawlItem).where(
            GoofishCrawlItem.job_id == job_id
        )
        await db.execute(delete_items_stmt)
        
        # 删除任务
        await db.delete(job)
        await db.commit()
        
        logger.info(f"删除采集任务: job_id={job_id}")
        return ApiResponse(success=True, message="删除成功")

    except Exception as e:
        await db.rollback()
        logger.error(f"删除采集任务失败: {e}")
        return ApiResponse(success=False, message=f"删除失败: {str(e)}")
