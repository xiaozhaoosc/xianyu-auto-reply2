"""
线索池模块业务服务

功能：
1. 线索采集任务的 CRUD（含风控硬校验：interval_minutes 最低30分钟、max_items_per_round 最高10）
2. 线索商品池 / 线索评论的分页查询与统计
3. 人工动作记录（opened/copied/ignored/followed）与建议话术生成（纯本地模板，无发送通道）
4. Phase 0 探针：单商品评论读取（Redis 锁 60s 一次，仅人工验证用）

模块红线：不提供任何自动发送评论/私信的能力。
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.redis_client import get_redis_client
from common.models.lead_capture import (
    LeadAction,
    LeadCaptureTask,
    LeadComment,
    LeadItem,
    LeadScanLog,
)
from common.models.xy_account import XYAccount
from common.services.lead_intent import build_suggestions
from common.services.xianyu_detail_client import XianyuItemDetailClient
from common.utils.time_utils import get_beijing_now_naive

# 风控硬校验常量（创建/更新接口拒绝越界值）
MIN_INTERVAL_MINUTES = 30
MAX_ITEMS_PER_ROUND = 10
MAX_COMMENT_PAGES = 1

# 探针调用最小间隔（秒）
PROBE_LOCK_SECONDS = 60
_PROBE_LOCK_KEY = "lead:probe:lock"

# 评论状态机：followed 为终态（同一评论只允许人工跟进一次）
_COMMENT_TERMINAL_STATUSES = {"followed"}
_VALID_ACTION_TYPES = {"opened", "copied", "ignored", "followed"}
_VALID_COMMENT_STATUSES = {"new", "reviewed", "ignored", "followed"}
_VALID_ITEM_STATUSES = {"active", "archived"}


def _task_to_dict(task: LeadCaptureTask) -> Dict[str, Any]:
    """将线索采集任务模型转换为前端可用的字典。"""
    return {
        "id": task.id,
        "owner_id": task.owner_id,
        "name": task.name,
        "source_type": task.source_type,
        "keyword": task.keyword,
        "monitor_task_id": task.monitor_task_id,
        "price_min": float(task.price_min) if task.price_min is not None else None,
        "price_max": float(task.price_max) if task.price_max is not None else None,
        "interval_minutes": task.interval_minutes,
        "max_items_per_round": task.max_items_per_round,
        "comment_pages_per_item": task.comment_pages_per_item,
        "include_weak": bool(task.include_weak),
        "account_ids": list(task.account_ids or []),
        "rescan_cooldown_hours": task.rescan_cooldown_hours,
        "is_enabled": bool(task.is_enabled),
        "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
        "remark": task.remark,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


def _item_to_dict(item: LeadItem) -> Dict[str, Any]:
    """将线索商品模型转换为前端可用的字典。"""
    return {
        "id": item.id,
        "owner_id": item.owner_id,
        "item_id": item.item_id,
        "title": item.title,
        "price": item.price,
        "seller_nick": item.seller_nick,
        "seller_user_id": item.seller_user_id,
        "item_url": item.item_url,
        "pic_url": item.pic_url,
        "want_count": item.want_count,
        "comment_count": item.comment_count,
        "strong_count": item.strong_count,
        "medium_count": item.medium_count,
        "demand_score": item.demand_score,
        "first_seen_at": item.first_seen_at.isoformat() if item.first_seen_at else None,
        "last_seen_at": item.last_seen_at.isoformat() if item.last_seen_at else None,
        "last_comment_scan_at": item.last_comment_scan_at.isoformat() if item.last_comment_scan_at else None,
        "status": item.status,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _comment_to_dict(comment: LeadComment, item: Optional[LeadItem] = None) -> Dict[str, Any]:
    """将线索评论模型转换为前端可用的字典（可附带所属商品摘要）。"""
    data = {
        "id": comment.id,
        "owner_id": comment.owner_id,
        "lead_item_id": comment.lead_item_id,
        "comment_id": comment.comment_id,
        "commenter_name": comment.commenter_name,
        "commenter_user_id": comment.commenter_user_id,
        "content": comment.content,
        "comment_time": comment.comment_time.isoformat() if comment.comment_time else None,
        "intent_level": comment.intent_level,
        "intent_keywords": list(comment.intent_keywords or []),
        "status": comment.status,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }
    if item is not None:
        data["item"] = {
            "item_id": item.item_id,
            "title": item.title,
            "price": item.price,
            "item_url": item.item_url,
            "pic_url": item.pic_url,
            "seller_nick": item.seller_nick,
            "demand_score": item.demand_score,
        }
    return data


class LeadCaptureService:
    """线索池模块服务（基于 AsyncSession，由路由层注入）"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------
    # 任务 CRUD
    # ------------------------------------------------------------------

    def _scope_conditions(self, owner_id: Optional[int]) -> List[Any]:
        """数据隔离条件：管理员（owner_id=None）查全量，普通用户仅本人。"""
        conditions: List[Any] = [LeadCaptureTask.is_deleted.is_(False)]
        if owner_id is not None:
            conditions.append(LeadCaptureTask.owner_id == owner_id)
        return conditions

    @staticmethod
    def _validate_risk_limits(
        interval_minutes: Optional[int] = None,
        max_items_per_round: Optional[int] = None,
        comment_pages_per_item: Optional[int] = None,
    ) -> Optional[str]:
        """风控硬校验：越界直接拒绝，返回错误信息（None 表示通过）。"""
        if interval_minutes is not None and interval_minutes < MIN_INTERVAL_MINUTES:
            return f"扫描间隔不能低于 {MIN_INTERVAL_MINUTES} 分钟（风控下限）"
        if max_items_per_round is not None and max_items_per_round > MAX_ITEMS_PER_ROUND:
            return f"每轮扫描商品数不能超过 {MAX_ITEMS_PER_ROUND}（风控上限）"
        if comment_pages_per_item is not None and comment_pages_per_item > MAX_COMMENT_PAGES:
            return f"每商品评论页数当前仅支持 {MAX_COMMENT_PAGES} 页"
        return None

    async def list_tasks(
        self,
        owner_id: Optional[int],
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        is_enabled: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """分页查询线索采集任务列表。"""
        conditions = self._scope_conditions(owner_id)
        if keyword:
            conditions.append(LeadCaptureTask.name.like(f"%{keyword}%"))
        if is_enabled is not None:
            conditions.append(LeadCaptureTask.is_enabled.is_(bool(is_enabled)))

        total = (await self.session.execute(select(func.count()).select_from(LeadCaptureTask).where(*conditions))).scalar() or 0
        stmt = (
            select(LeadCaptureTask)
            .where(*conditions)
            .order_by(LeadCaptureTask.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list((await self.session.execute(stmt)).scalars().all())
        return {
            "list": [_task_to_dict(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get(self, owner_id: Optional[int], task_id: int) -> Optional[LeadCaptureTask]:
        """按主键查询线索采集任务（带数据隔离与软删除过滤）。"""
        conditions = self._scope_conditions(owner_id)
        conditions.append(LeadCaptureTask.id == task_id)
        stmt = select(LeadCaptureTask).where(*conditions)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_task(self, owner_id: int, data: Dict[str, Any]) -> LeadCaptureTask:
        """创建线索采集任务（调用前须先通过 _validate_risk_limits 校验）。"""
        task = LeadCaptureTask(
            owner_id=owner_id,
            name=(data.get("name") or "").strip()[:100] or "未命名任务",
            source_type=data.get("source_type") or "monitor",
            keyword=(data.get("keyword") or "").strip()[:200] or None,
            monitor_task_id=data.get("monitor_task_id"),
            price_min=data.get("price_min"),
            price_max=data.get("price_max"),
            interval_minutes=data.get("interval_minutes") or 60,
            max_items_per_round=data.get("max_items_per_round") or 5,
            comment_pages_per_item=1,
            include_weak=bool(data.get("include_weak", False)),
            account_ids=list(data.get("account_ids") or []),
            rescan_cooldown_hours=data.get("rescan_cooldown_hours") or 24,
            is_enabled=bool(data.get("is_enabled", True)),
            remark=(data.get("remark") or "").strip()[:500] or None,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def update_task(self, task: LeadCaptureTask, data: Dict[str, Any]) -> LeadCaptureTask:
        """更新线索采集任务（调用前须先通过 _validate_risk_limits 校验）。"""
        if "name" in data and data["name"] is not None:
            task.name = str(data["name"]).strip()[:100]
        if "source_type" in data and data["source_type"] is not None:
            task.source_type = data["source_type"]
        if "keyword" in data:
            task.keyword = (data["keyword"] or "").strip()[:200] or None if data["keyword"] is not None else None
        if "monitor_task_id" in data:
            task.monitor_task_id = data["monitor_task_id"]
        if "price_min" in data:
            task.price_min = data["price_min"]
        if "price_max" in data:
            task.price_max = data["price_max"]
        if "interval_minutes" in data and data["interval_minutes"] is not None:
            task.interval_minutes = data["interval_minutes"]
        if "max_items_per_round" in data and data["max_items_per_round"] is not None:
            task.max_items_per_round = data["max_items_per_round"]
        if "include_weak" in data and data["include_weak"] is not None:
            task.include_weak = bool(data["include_weak"])
        if "account_ids" in data and data["account_ids"] is not None:
            task.account_ids = list(data["account_ids"])
        if "rescan_cooldown_hours" in data and data["rescan_cooldown_hours"] is not None:
            task.rescan_cooldown_hours = data["rescan_cooldown_hours"]
        if "is_enabled" in data and data["is_enabled"] is not None:
            task.is_enabled = bool(data["is_enabled"])
        if "remark" in data:
            task.remark = (data["remark"] or "").strip()[:500] or None if data["remark"] is not None else None
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete_task(self, task: LeadCaptureTask) -> None:
        """软删除线索采集任务。"""
        task.is_deleted = True
        task.is_enabled = False
        await self.session.commit()

    async def update_status(self, task: LeadCaptureTask, is_enabled: bool) -> LeadCaptureTask:
        """更新任务启停状态。"""
        task.is_enabled = bool(is_enabled)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    # ------------------------------------------------------------------
    # 线索商品池
    # ------------------------------------------------------------------

    async def list_items(
        self,
        owner_id: Optional[int],
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        min_demand_score: Optional[int] = None,
    ) -> Dict[str, Any]:
        """分页查询线索商品池（按需求热度分降序）。"""
        conditions: List[Any] = []
        if owner_id is not None:
            conditions.append(LeadItem.owner_id == owner_id)
        if status:
            conditions.append(LeadItem.status == status)
        if keyword:
            conditions.append(LeadItem.title.like(f"%{keyword}%"))
        if min_demand_score is not None:
            conditions.append(LeadItem.demand_score >= min_demand_score)

        total = (await self.session.execute(select(func.count()).select_from(LeadItem).where(*conditions))).scalar() or 0
        stmt = (
            select(LeadItem)
            .where(*conditions)
            .order_by(LeadItem.demand_score.desc(), LeadItem.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list((await self.session.execute(stmt)).scalars().all())
        return {
            "list": [_item_to_dict(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def update_item_status(self, owner_id: Optional[int], item_db_id: int, status: str) -> Optional[LeadItem]:
        """更新线索商品状态（active-观察中 / archived-已归档，归档后不再扫描）。"""
        if status not in _VALID_ITEM_STATUSES:
            return None
        conditions: List[Any] = [LeadItem.id == item_db_id]
        if owner_id is not None:
            conditions.append(LeadItem.owner_id == owner_id)
        item = (await self.session.execute(select(LeadItem).where(*conditions))).scalar_one_or_none()
        if not item:
            return None
        item.status = status
        await self.session.commit()
        await self.session.refresh(item)
        return item

    # ------------------------------------------------------------------
    # 线索评论
    # ------------------------------------------------------------------

    async def _comment_conditions(
        self,
        owner_id: Optional[int],
        intent_level: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        lead_item_id: Optional[int] = None,
    ) -> List[Any]:
        conditions: List[Any] = []
        if owner_id is not None:
            conditions.append(LeadComment.owner_id == owner_id)
        if intent_level:
            conditions.append(LeadComment.intent_level == intent_level)
        if status:
            conditions.append(LeadComment.status == status)
        if keyword:
            conditions.append(LeadComment.content.like(f"%{keyword}%"))
        if lead_item_id is not None:
            conditions.append(LeadComment.lead_item_id == lead_item_id)
        return conditions

    async def list_comments(
        self,
        owner_id: Optional[int],
        page: int = 1,
        page_size: int = 20,
        intent_level: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        lead_item_id: Optional[int] = None,
        with_item: bool = False,
    ) -> Dict[str, Any]:
        """分页查询线索评论（默认按入库时间倒序；with_item 时附带商品摘要）。"""
        conditions = await self._comment_conditions(owner_id, intent_level, status, keyword, lead_item_id)
        total = (await self.session.execute(select(func.count()).select_from(LeadComment).where(*conditions))).scalar() or 0
        stmt = (
            select(LeadComment)
            .where(*conditions)
            .order_by(LeadComment.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list((await self.session.execute(stmt)).scalars().all())

        items_map: Dict[int, LeadItem] = {}
        if with_item and rows:
            item_ids = {row.lead_item_id for row in rows}
            item_rows = (
                await self.session.execute(select(LeadItem).where(LeadItem.id.in_(item_ids)))
            ).scalars().all()
            items_map = {row.id: row for row in item_rows}

        return {
            "list": [_comment_to_dict(row, items_map.get(row.lead_item_id) if with_item else None) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_comment(self, owner_id: Optional[int], comment_db_id: int) -> Optional[LeadComment]:
        """按主键查询线索评论（带数据隔离）。"""
        conditions: List[Any] = [LeadComment.id == comment_db_id]
        if owner_id is not None:
            conditions.append(LeadComment.owner_id == owner_id)
        return (await self.session.execute(select(LeadComment).where(*conditions))).scalar_one_or_none()

    async def record_action(
        self,
        comment: LeadComment,
        action_type: str,
        operator: Optional[str] = None,
        suggested_reply: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """记录人工动作流水，并联动更新评论处理状态。

        - followed：评论置为 followed（终态，同一评论只允许跟进一次）
        - ignored：评论置为 ignored
        - opened / copied：仅记录流水，不改评论状态
        """
        if action_type not in _VALID_ACTION_TYPES:
            raise ValueError(f"不支持的动作类型: {action_type}")

        if action_type == "followed":
            if comment.status in _COMMENT_TERMINAL_STATUSES:
                raise ValueError("该评论已人工跟进过（followed 为终态，不可重复跟进）")
            comment.status = "followed"
        elif action_type == "ignored":
            comment.status = "ignored"

        action = LeadAction(
            owner_id=comment.owner_id,
            lead_comment_id=comment.id,
            action_type=action_type,
            suggested_reply=(suggested_reply or "")[:1000] or None,
            operator=(operator or "")[:64] or None,
            note=(note or "")[:500] or None,
        )
        self.session.add(action)
        await self.session.commit()
        return {
            "action_id": action.id,
            "comment_id": comment.id,
            "action_type": action_type,
            "comment_status": comment.status,
        }

    async def get_suggestions(self, owner_id: Optional[int], comment_db_id: int) -> Dict[str, Any]:
        """根据评论所属商品生成建议话术（纯本地模板拼接，无任何发送通道）。"""
        comment = await self.get_comment(owner_id, comment_db_id)
        if not comment:
            return {}
        item = (
            await self.session.execute(select(LeadItem).where(LeadItem.id == comment.lead_item_id))
        ).scalar_one_or_none()
        suggestions = build_suggestions(item.title if item else None, item.price if item else None)
        return {
            "comment_id": comment.id,
            "suggestions": suggestions,
        }

    # ------------------------------------------------------------------
    # 扫描日志
    # ------------------------------------------------------------------

    async def list_logs(
        self,
        owner_id: Optional[int],
        page: int = 1,
        page_size: int = 20,
        task_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """分页查询线索扫描执行日志。"""
        conditions: List[Any] = []
        if owner_id is not None:
            conditions.append(LeadScanLog.owner_id == owner_id)
        if task_id is not None:
            conditions.append(LeadScanLog.task_id == task_id)
        if status:
            conditions.append(LeadScanLog.status == status)

        total = (await self.session.execute(select(func.count()).select_from(LeadScanLog).where(*conditions))).scalar() or 0
        stmt = (
            select(LeadScanLog)
            .where(*conditions)
            .order_by(LeadScanLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list((await self.session.execute(stmt)).scalars().all())
        return {
            "list": [
                {
                    "id": row.id,
                    "task_id": row.task_id,
                    "task_name": row.task_name,
                    "trigger_type": row.trigger_type,
                    "account_id": row.account_id,
                    "scanned_count": row.scanned_count,
                    "comment_fetched": row.comment_fetched,
                    "comment_new": row.comment_new,
                    "strong_new": row.strong_new,
                    "risk_triggered": bool(row.risk_triggered),
                    "status": row.status,
                    "message": row.message,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    # ------------------------------------------------------------------
    # 总览统计
    # ------------------------------------------------------------------

    async def overview(self, owner_id: Optional[int]) -> Dict[str, Any]:
        """线索池总览统计：任务/商品/评论计数 + 今日新增 + 近7天趋势。"""
        task_cond: List[Any] = [LeadCaptureTask.is_deleted.is_(False)]
        item_cond: List[Any] = []
        comment_cond: List[Any] = []
        if owner_id is not None:
            task_cond.append(LeadCaptureTask.owner_id == owner_id)
            item_cond.append(LeadItem.owner_id == owner_id)
            comment_cond.append(LeadComment.owner_id == owner_id)

        total_tasks = (await self.session.execute(select(func.count()).select_from(LeadCaptureTask).where(*task_cond))).scalar() or 0
        enabled_tasks = (
            await self.session.execute(
                select(func.count()).select_from(LeadCaptureTask).where(*task_cond, LeadCaptureTask.is_enabled.is_(True))
            )
        ).scalar() or 0

        total_items = (await self.session.execute(select(func.count()).select_from(LeadItem).where(*item_cond))).scalar() or 0
        active_items = (
            await self.session.execute(
                select(func.count()).select_from(LeadItem).where(*item_cond, LeadItem.status == "active")
            )
        ).scalar() or 0

        total_comments = (await self.session.execute(select(func.count()).select_from(LeadComment).where(*comment_cond))).scalar() or 0
        pending_comments = (
            await self.session.execute(
                select(func.count()).select_from(LeadComment).where(*comment_cond, LeadComment.status == "new")
            )
        ).scalar() or 0
        strong_comments = (
            await self.session.execute(
                select(func.count()).select_from(LeadComment).where(*comment_cond, LeadComment.intent_level == "strong")
            )
        ).scalar() or 0
        followed_comments = (
            await self.session.execute(
                select(func.count()).select_from(LeadComment).where(*comment_cond, LeadComment.status == "followed")
            )
        ).scalar() or 0

        now = get_beijing_now_naive()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_new_comments = (
            await self.session.execute(
                select(func.count())
                .select_from(LeadComment)
                .where(*comment_cond, LeadComment.created_at >= today_start)
            )
        ).scalar() or 0
        today_new_strong = (
            await self.session.execute(
                select(func.count())
                .select_from(LeadComment)
                .where(*comment_cond, LeadComment.created_at >= today_start, LeadComment.intent_level == "strong")
            )
        ).scalar() or 0

        # 近7天评论新增趋势（按日聚合）
        week_start = today_start - timedelta(days=6)
        trend_rows = (
            await self.session.execute(
                select(
                    func.date(LeadComment.created_at).label("day"),
                    LeadComment.intent_level,
                    func.count(),
                )
                .where(*comment_cond, LeadComment.created_at >= week_start)
                .group_by("day", LeadComment.intent_level)
            )
        ).all()
        trend: Dict[str, Dict[str, int]] = {}
        for day, level, cnt in trend_rows:
            day_key = str(day)
            trend.setdefault(day_key, {"strong": 0, "medium": 0, "weak": 0})
            if level in ("strong", "medium", "weak"):
                trend[day_key][level] = int(cnt)
        trend_list = [
            {"date": day, **counts}
            for day, counts in sorted(trend.items())
        ]

        return {
            "total_tasks": total_tasks,
            "enabled_tasks": enabled_tasks,
            "total_items": total_items,
            "active_items": active_items,
            "total_comments": total_comments,
            "pending_comments": pending_comments,
            "strong_comments": strong_comments,
            "followed_comments": followed_comments,
            "today_new_comments": today_new_comments,
            "today_new_strong": today_new_strong,
            "trend": trend_list,
        }

    # ------------------------------------------------------------------
    # Phase 0 探针
    # ------------------------------------------------------------------

    async def probe(self, owner_id: int, item_id: str, account_id: str) -> Dict[str, Any]:
        """Phase 0 可行性探针：用指定账号读取单个商品评论区（每次调用间隔 ≥60s）。

        仅用于人工验证「不登录/低频读取是否稳定」，不写库、不计入全局日上限。
        返回评论样例（脱敏）与风控信息，供前端展示。
        """
        item_id = (item_id or "").strip()
        account_id = (account_id or "").strip()
        if not item_id or not account_id:
            return {"success": False, "error": "商品ID与账号ID均不能为空"}

        try:
            client = await get_redis_client()
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": f"Redis 不可用，探针锁无法生效：{exc}"}

        # 60s 一次的探针限流锁
        got_lock = await client.set(_PROBE_LOCK_KEY, "1", ex=PROBE_LOCK_SECONDS, nx=True)
        if not got_lock:
            return {"success": False, "error": f"探针调用过于频繁，请间隔 {PROBE_LOCK_SECONDS} 秒以上再试"}

        account = (
            await self.session.execute(select(XYAccount).where(XYAccount.account_id == account_id))
        ).scalar_one_or_none()
        if not account or not account.cookie:
            return {"success": False, "error": "账号不存在或 Cookie 为空"}
        if owner_id is not None and account.owner_id != owner_id:
            return {"success": False, "error": "无权使用该账号"}

        detail_client = XianyuItemDetailClient(account.account_id, account.cookie, owner_id=account.owner_id)
        result = await detail_client.fetch_comments(item_id, page=1, page_size=20)

        comments = result.get("comments", [])
        # 脱敏：昵称只保留首尾字符
        def _mask(name: Optional[str]) -> Optional[str]:
            if not name:
                return name
            if len(name) <= 2:
                return name[0] + "*"
            return name[0] + "*" * (len(name) - 2) + name[-1]

        masked = [
            {
                "commenter_name": _mask(c.get("commenter_name")),
                "content": (c.get("content") or "")[:200],
                "comment_time": c.get("comment_time"),
            }
            for c in comments[:5]
        ]

        return {
            "success": bool(result.get("success")),
            "error": result.get("error") or "",
            "risk_triggered": bool(result.get("risk_triggered")),
            "punish_url": result.get("punish_url") or "",
            "item_invalid": bool(result.get("item_invalid")),
            "account_invalid": bool(result.get("account_invalid")),
            "comment_count": len(comments),
            "total": result.get("total", 0),
            "sample_comments": masked,
            "raw_keys": list((result.get("raw") or {}).keys()) if isinstance(result.get("raw"), dict) else [],
        }
