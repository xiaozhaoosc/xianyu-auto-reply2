"""
线索评论扫描定时任务

功能：
1. 读取所有启用状态的线索采集任务（xy_lead_capture_tasks）
2. 组装候选商品池：source_type=monitor 复用商品监控采集结果（零额外搜索请求，推荐），
   source_type=keyword 用任务账号调闲鱼搜索接口取第 1 页
3. 对候选商品逐个低频读取评论区（复用 XianyuItemDetailClient.fetch_comments），
   意图分层后 upsert 到线索池（xy_lead_items / xy_lead_comments），并写扫描日志（xy_lead_scan_logs）

模块红线（触发即停，不做任何补救性重试）：
- 触发风控（滑块/验证）→ 账号加入冷却 + 本轮立即终止，不调用远程过风控
- 全局详情请求日上限 DAILY_DETAIL_CAP（Redis INCR 计数，跨任务共享），达到后本轮直接结束
- 同一商品两次评论扫描最小间隔由任务 rescan_cooldown_hours 控制
- 只读：本任务不产生任何评论/私信/下单动作
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy import delete, func, select

from common.db.redis_client import get_redis_client
from common.db.session import async_session_maker
from common.models.lead_capture import (
    LeadCaptureTask,
    LeadComment,
    LeadItem,
    LeadScanLog,
)
from common.models.listing_monitor_item import ListingMonitorItem
from common.models.xy_account import XYAccount
from common.services.account_cooldown import account_cooldown_manager
from common.services.lead_intent import (
    INTENT_MEDIUM,
    INTENT_STRONG,
    INTENT_WEIGHTS,
    build_dedupe_hash,
    classify_intent,
)
from common.services.xianyu_detail_client import XianyuItemDetailClient
from common.services.xianyu_search_client import XianyuSearchClient, parse_search_item
from common.utils.time_utils import BEIJING_TZ, get_beijing_now_naive

# 全局详情请求日上限：跨任务共享，达到后当天不再扫描
DAILY_DETAIL_CAP = 50

# 同一轮扫描中相邻两个商品之间的随机间隔（秒）
ITEM_SLEEP_RANGE = (20, 35)

# 候选池从商品监控采集表取数的条数上限（取最新 N 条再过滤）
MONITOR_CANDIDATE_LIMIT = 50

_INACTIVE_STATUSES = {"inactive", "disabled", "suspended", "deleted"}


def _redis_day_key() -> str:
    """全局详情请求计数的 Redis key（北京时间按日）。"""
    day = get_beijing_now_naive().strftime("%Y%m%d")
    return f"lead:scan:detail:{day}"


def _parse_comment_time(raw: Optional[str]) -> Optional[datetime]:
    """解析评论时间：毫秒时间戳或常见格式字符串，失败返回 None。"""
    if not raw:
        return None
    text = str(raw).strip()
    try:
        ms = int(text)
        if ms > 10_000_000_000:  # 毫秒级时间戳
            return datetime.fromtimestamp(ms / 1000, tz=BEIJING_TZ).replace(tzinfo=None)
        if ms > 10_000_000:  # 秒级时间戳
            return datetime.fromtimestamp(ms, tz=BEIJING_TZ).replace(tzinfo=None)
    except (TypeError, ValueError, OSError, OverflowError):
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _parse_price_text(price: Optional[str]) -> Optional[float]:
    """把价格展示文本解析为 float（'235' / '¥235.00' 等），失败返回 None。"""
    if not price:
        return None
    try:
        return float(str(price).replace("¥", "").replace("￥", "").strip())
    except (TypeError, ValueError):
        return None


class LeadCommentScanTaskService:
    """线索评论扫描定时任务服务"""

    # 扫描日志保留天数，超过该天数的日志在每次任务执行时主动清理
    LOG_RETENTION_DAYS = 10

    def __init__(self, task_name: str = "线索评论扫描任务"):
        self.task_name = task_name
        self._lock = asyncio.Lock()

    async def execute(self, force: bool = False, trigger_type: str = "auto") -> None:
        """执行线索评论扫描任务：遍历所有启用的采集任务并扫描。

        Args:
            force: 是否强制执行（手动触发时为 True，忽略每个任务自身的间隔）。
            trigger_type: 触发方式，auto-定时自动，manual-手动。

        并发保护：同一时刻只允许一个扫描执行（含定时与手动），正在执行时本次直接跳过。
        """
        if self._lock.locked():
            logger.info(f"【{self.task_name}】已有扫描任务正在执行，跳过本次（force={force}）")
            return
        async with self._lock:
            await self._execute_inner(force, trigger_type)

    async def _execute_inner(self, force: bool, trigger_type: str) -> None:
        logger.info(f"【{self.task_name}】开始执行（force={force}，trigger_type={trigger_type}）")
        start_time = datetime.now()

        await self._cleanup_expired_logs()

        try:
            tasks = await self._get_enabled_tasks()
            if not tasks:
                logger.info(f"【{self.task_name}】没有启用的线索采集任务，结束")
                return

            now_naive = get_beijing_now_naive()
            due_tasks = [t for t in tasks if force or self._is_due(t, now_naive)]
            if not due_tasks:
                logger.info(f"【{self.task_name}】启用任务 {len(tasks)} 个，本次无到期任务，结束")
                return

            logger.info(f"【{self.task_name}】启用任务 {len(tasks)} 个，本次执行 {len(due_tasks)} 个")
            for task in due_tasks:
                try:
                    await self._process_task(task, trigger_type=trigger_type)
                except Exception as exc:  # noqa: BLE001
                    logger.error(f"【{self.task_name}】线索采集任务 {task.id} 执行异常: {exc}")

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"【{self.task_name}】执行完成，共处理 {len(due_tasks)} 个任务，耗时 {elapsed:.2f}秒")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"【{self.task_name}】执行异常: {exc}")

    async def run_single(self, task_id: int, trigger_type: str = "manual") -> dict:
        """手动执行单个线索采集任务的扫描（忽略间隔，立即执行一次）。

        Returns: {"success": bool, "message": str}
        """
        logger.info(f"【{self.task_name}】手动执行单个任务 task_id={task_id}")
        if self._lock.locked():
            return {"success": False, "message": "扫描任务正在执行中，请稍后再试"}
        async with self._lock:
            async with async_session_maker() as session:
                task = (
                    await session.execute(
                        select(LeadCaptureTask).where(
                            LeadCaptureTask.id == task_id,
                            LeadCaptureTask.is_deleted.is_(False),
                            LeadCaptureTask.is_enabled.is_(True),
                        )
                    )
                ).scalar_one_or_none()
            if not task:
                return {"success": False, "message": "线索采集任务不存在、已删除或未启用"}
            try:
                await self._process_task(task, trigger_type=trigger_type)
                return {"success": True, "message": "扫描已执行"}
            except Exception as exc:  # noqa: BLE001
                logger.error(f"【{self.task_name}】手动执行任务 {task_id} 异常: {exc}")
                return {"success": False, "message": f"扫描执行失败: {exc}"}

    @staticmethod
    def _is_due(task: LeadCaptureTask, now_naive: datetime) -> bool:
        """根据任务自身的 interval_minutes 判断是否到期需要执行。"""
        if task.last_run_at is None:
            return True
        last_run = task.last_run_at
        if last_run.tzinfo is not None:
            last_run = last_run.replace(tzinfo=None)
        interval_minutes = task.interval_minutes if task.interval_minutes and task.interval_minutes > 0 else 60
        elapsed_seconds = (now_naive - last_run).total_seconds()
        return elapsed_seconds >= interval_minutes * 60

    async def _get_enabled_tasks(self) -> List[LeadCaptureTask]:
        """读取所有启用、未删除的线索采集任务。"""
        async with async_session_maker() as session:
            stmt = select(LeadCaptureTask).where(
                LeadCaptureTask.is_deleted.is_(False),
                LeadCaptureTask.is_enabled.is_(True),
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def _cleanup_expired_logs(self) -> None:
        """主动清理过期的扫描日志（保留 LOG_RETENTION_DAYS 天）。"""
        try:
            cutoff_time = get_beijing_now_naive() - timedelta(days=self.LOG_RETENTION_DAYS)
            async with async_session_maker() as session:
                stmt = delete(LeadScanLog).where(LeadScanLog.created_at < cutoff_time)
                result = await session.execute(stmt)
                await session.commit()
                deleted_count = result.rowcount or 0
            if deleted_count > 0:
                logger.info(
                    f"【{self.task_name}】已清理 {deleted_count} 条 {self.LOG_RETENTION_DAYS} 天前的扫描日志"
                )
        except Exception as e:  # noqa: BLE001
            logger.error(f"【{self.task_name}】清理过期日志失败: {e}")

    async def _load_accounts(self, account_ids: List[str]) -> List[XYAccount]:
        """按任务配置的账号ID列表加载可用账号（过滤禁用/无Cookie）。"""
        if not account_ids:
            return []
        async with async_session_maker() as session:
            stmt = select(XYAccount).where(XYAccount.account_id.in_(account_ids))
            rows = list((await session.execute(stmt)).scalars().all())
        by_id = {row.account_id: row for row in rows}
        ordered: List[XYAccount] = []
        for account_id in account_ids:
            acc = by_id.get(account_id)
            if not acc or not acc.cookie:
                continue
            if (acc.status or "active").strip().lower() in _INACTIVE_STATUSES:
                continue
            ordered.append(acc)
        return ordered

    async def _load_monitor_candidates(self, task: LeadCaptureTask) -> List[dict]:
        """source_type=monitor：从商品监控采集表取该监控任务最新商品作候选池。"""
        if not task.monitor_task_id:
            return []
        async with async_session_maker() as session:
            stmt = (
                select(ListingMonitorItem)
                .where(ListingMonitorItem.monitor_task_id == task.monitor_task_id)
                .order_by(ListingMonitorItem.publish_time.desc().nullslast(), ListingMonitorItem.id.desc())
                .limit(MONITOR_CANDIDATE_LIMIT)
            )
            rows = list((await session.execute(stmt)).scalars().all())
        return [
            {
                "item_id": row.item_id,
                "title": row.title,
                "price": row.price,
                "pic_url": row.pic_url,
                "seller_nick": row.seller_nick,
                "seller_user_id": row.seller_user_id,
                "want_count": row.want_count,
            }
            for row in rows
        ]

    async def _search_keyword_candidates(self, task: LeadCaptureTask, accounts: List[XYAccount]) -> List[dict]:
        """source_type=keyword：用任务账号调闲鱼搜索接口取第 1 页作候选池（仅此一处产生搜索请求）。"""
        if not task.keyword or not accounts:
            return []
        client = XianyuSearchClient(accounts[0].account_id, accounts[0].cookie, owner_id=accounts[0].owner_id)
        res = await client.search(
            page_number=1,
            keyword=task.keyword,
            sort_field="create",
            sort_value="desc",
            rows_per_page=30,
            price_min=float(task.price_min) if task.price_min is not None else None,
            price_max=float(task.price_max) if task.price_max is not None else None,
        )
        accounts[0].cookie = client.cookies_str
        if not res.get("success"):
            logger.warning(f"【{self.task_name}】任务 {task.id} 关键词搜索失败: {res.get('error')}")
            return []
        candidates = []
        for entry in res.get("items", []):
            parsed = parse_search_item(entry)
            if parsed:
                candidates.append(
                    {
                        "item_id": parsed.get("item_id"),
                        "title": parsed.get("title"),
                        "price": parsed.get("price"),
                        "pic_url": parsed.get("pic_url"),
                        "seller_nick": parsed.get("seller_nick"),
                        "seller_user_id": parsed.get("seller_user_id"),
                        "want_count": parsed.get("want_count"),
                    }
                )
        return [c for c in candidates if c.get("item_id")]

    async def _get_daily_used(self) -> int:
        """读取全局详情请求当日已用次数（Redis 不可用时返回 0，放行由风控兜底）。"""
        try:
            client = await get_redis_client()
            value = await client.get(_redis_day_key())
            return int(value) if value else 0
        except Exception as e:  # noqa: BLE001
            logger.warning(f"【{self.task_name}】读取全局日上限计数失败（按0处理）: {e}")
            return 0

    async def _incr_daily_used(self) -> int:
        """全局详情请求计数 +1，返回自增后的值；key 2 天过期。"""
        client = await get_redis_client()
        key = _redis_day_key()
        value = await client.incr(key)
        if value == 1:
            await client.expire(key, 2 * 24 * 3600)
        return int(value)

    async def _upsert_lead_items(self, task: LeadCaptureTask, candidates: List[dict]) -> Dict[str, LeadItem]:
        """候选商品 upsert 到线索商品池；返回 item_id -> LeadItem 映射（含归档商品）。"""
        now = get_beijing_now_naive()
        result_map: Dict[str, LeadItem] = {}
        if not candidates:
            return result_map
        async with async_session_maker() as session:
            item_ids = [c["item_id"] for c in candidates]
            existing_rows = (
                await session.execute(
                    select(LeadItem).where(
                        LeadItem.owner_id == task.owner_id,
                        LeadItem.item_id.in_(item_ids),
                    )
                )
            ).scalars().all()
            existing_map = {row.item_id: row for row in existing_rows}

            for cand in candidates:
                row = existing_map.get(cand["item_id"])
                if row:
                    # 归档商品保留（用户已明确不关心，扫描阶段再过滤），只刷新基础信息
                    if cand.get("title"):
                        row.title = (cand.get("title") or "")[:500]
                    if cand.get("price") is not None:
                        row.price = str(cand.get("price"))[:32]
                    if cand.get("pic_url"):
                        row.pic_url = (cand.get("pic_url") or "")[:1000]
                    if cand.get("seller_nick"):
                        row.seller_nick = (cand.get("seller_nick") or "")[:120]
                    if not row.seller_user_id and cand.get("seller_user_id"):
                        row.seller_user_id = str(cand.get("seller_user_id"))[:64]
                    if cand.get("want_count") is not None:
                        row.want_count = str(cand.get("want_count"))[:32]
                    row.item_url = f"https://www.goofish.com/item?id={row.item_id}"
                    row.last_seen_at = now
                else:
                    row = LeadItem(
                        owner_id=task.owner_id,
                        item_id=cand["item_id"],
                        title=(cand.get("title") or "")[:500],
                        price=str(cand.get("price"))[:32] if cand.get("price") is not None else None,
                        seller_nick=(cand.get("seller_nick") or "")[:120] or None,
                        seller_user_id=str(cand.get("seller_user_id"))[:64] if cand.get("seller_user_id") else None,
                        item_url=f"https://www.goofish.com/item?id={cand['item_id']}",
                        pic_url=(cand.get("pic_url") or "")[:1000] or None,
                        want_count=str(cand.get("want_count"))[:32] if cand.get("want_count") is not None else None,
                        first_seen_at=now,
                        last_seen_at=now,
                        status="active",
                    )
                    session.add(row)
                result_map[cand["item_id"]] = row
            await session.commit()
            # commit 后 row 可用于后续读取；重新查询以获取生效的 id
        return result_map

    async def _process_task(self, task: LeadCaptureTask, trigger_type: str = "auto") -> None:
        """处理单个线索采集任务：组候选池 → 逐商品读评论 → 入库 → 写日志。"""
        accounts = await self._load_accounts(list(task.account_ids or []))

        status = "success"
        message_parts: List[str] = []
        scanned = 0
        comment_fetched = 0
        comment_new = 0
        strong_new = 0
        used_account_id: Optional[str] = None
        risk_triggered = False

        if not accounts:
            status = "failed"
            message_parts.append("无可用读取账号（不存在/禁用/Cookie为空）")
            logger.warning(f"【{self.task_name}】任务 {task.id}({task.name}) 无可用读取账号")
        else:
            # 1) 组装候选池
            if task.source_type == "keyword":
                candidates = await self._search_keyword_candidates(task, accounts)
            else:
                candidates = await self._load_monitor_candidates(task)

            # 价格区间过滤（monitor 来源；keyword 来源搜索接口已过滤）
            if task.source_type == "monitor" and (task.price_min is not None or task.price_max is not None):
                def _in_range(cand: dict) -> bool:
                    price = _parse_price_text(cand.get("price"))
                    if price is None:
                        return True
                    if task.price_min is not None and price < float(task.price_min):
                        return False
                    if task.price_max is not None and price > float(task.price_max):
                        return False
                    return True

                candidates = [c for c in candidates if _in_range(c)]

            if not candidates:
                message_parts.append("候选商品池为空")
            else:
                # 2) 候选 upsert 线索商品池
                lead_items = await self._upsert_lead_items(task, candidates)

                # 3) 过滤：归档商品跳过 + rescan 冷却内跳过
                now_naive = get_beijing_now_naive()
                cooldown_hours = task.rescan_cooldown_hours if task.rescan_cooldown_hours and task.rescan_cooldown_hours > 0 else 24
                cooldown_delta = timedelta(hours=cooldown_hours)

                pending: List[LeadItem] = []
                for cand in candidates:
                    row = lead_items.get(cand["item_id"])
                    if not row:
                        continue
                    if row.status == "archived":
                        continue
                    if row.last_comment_scan_at is not None:
                        last_scan = row.last_comment_scan_at
                        if last_scan.tzinfo is not None:
                            last_scan = last_scan.replace(tzinfo=None)
                        if now_naive - last_scan < cooldown_delta:
                            continue
                    pending.append(row)

                # 4) 截断到每轮上限
                max_items = max(1, min(task.max_items_per_round or 5, 10))
                pending = pending[:max_items]

                if not pending:
                    message_parts.append("候选均在重扫冷却期或已归档，本轮无可扫描商品")
                else:
                    # 5) 全局日上限预检
                    daily_used = await self._get_daily_used()
                    if daily_used >= DAILY_DETAIL_CAP:
                        message_parts.append(f"全局详情请求已达日上限 {DAILY_DETAIL_CAP}，本轮跳过")
                    else:
                        for idx, lead_item in enumerate(pending):
                            # 每个商品扫描前再检查一次日上限
                            daily_used = await self._get_daily_used()
                            if daily_used >= DAILY_DETAIL_CAP:
                                message_parts.append(f"全局详情请求达到日上限 {DAILY_DETAIL_CAP}，剩余商品下轮再扫")
                                status = "partial" if scanned > 0 else status
                                break

                            # 取第一个未冷却账号逐个尝试
                            scan_result = await self._scan_one_item(task, accounts, lead_item)
                            if scan_result.get("risk_triggered"):
                                risk_triggered = True
                                status = "risk_stopped"
                                message_parts.append(
                                    f"账号 {scan_result.get('account_id')} 触发风控，本轮立即终止"
                                )
                                break

                            used_account_id = scan_result.get("account_id") or used_account_id
                            if scan_result.get("item_invalid"):
                                message_parts.append(f"商品 {lead_item.item_id} 已下架或不可读，跳过")
                                continue

                            scanned += 1
                            comment_fetched += scan_result.get("fetched", 0)
                            comment_new += scan_result.get("new", 0)
                            strong_new += scan_result.get("strong_new", 0)

                            # 6) 商品间随机间隔（最后一个不等）
                            if idx != len(pending) - 1:
                                await asyncio.sleep(random.uniform(*ITEM_SLEEP_RANGE))

        # 7) 写日志 + 更新执行时间
        if status == "success":
            message_parts.append(
                f"扫描{scanned}个商品，获取评论{comment_fetched}条，新增{comment_new}条（强意向{strong_new}条）"
            )
        await self._write_log(
            task=task,
            trigger_type=trigger_type,
            account_id=used_account_id,
            scanned=scanned,
            comment_fetched=comment_fetched,
            comment_new=comment_new,
            strong_new=strong_new,
            risk_triggered=risk_triggered,
            status=status,
            message="；".join(message_parts)[:1000],
        )
        await self._update_last_run(task.id)
        logger.info(
            f"【{self.task_name}】任务 {task.id}({task.name}) 完成："
            f"扫描={scanned}，评论新增={comment_new}，强意向={strong_new}，状态={status}"
        )

    async def _scan_one_item(
        self,
        task: LeadCaptureTask,
        accounts: List[XYAccount],
        lead_item: LeadItem,
    ) -> dict:
        """扫描单个商品的评论区。

        Returns:
            {
              risk_triggered: bool,   # 触发风控（调用方应立即终止本轮）
              account_id: str|None,   # 实际使用的账号
              item_invalid: bool,      # 商品级明确失败（下架等），跳过
              fetched: int, new: int, strong_new: int,
            }
        """
        result = {"risk_triggered": False, "account_id": None, "item_invalid": False, "fetched": 0, "new": 0, "strong_new": 0}

        used: int | None = None
        for offset in range(len(accounts)):
            idx = offset
            acc = accounts[idx]
            if account_cooldown_manager.is_cooling(acc.account_id):
                continue

            # 全局日上限计数（每个商品实际只算 1 次详情请求；多账号重试不重复计数）
            if offset == 0:
                await self._incr_daily_used()

            client = XianyuItemDetailClient(acc.account_id, acc.cookie, owner_id=acc.owner_id)
            res = await client.fetch_comments(lead_item.item_id, page=1, page_size=20)
            acc.cookie = client.cookies_str  # 令牌刷新回写

            if res.get("success"):
                used = idx
                result["account_id"] = acc.account_id
                new_count, strong_count = await self._save_comments(task, lead_item.id, res.get("comments", []), include_weak=bool(task.include_weak))
                result["fetched"] = len(res.get("comments", []))
                result["new"] = new_count
                result["strong_new"] = strong_count
                await self._refresh_item_stats(lead_item.id)
                await self._touch_item_scan_time(lead_item.id)
                return result

            if res.get("risk_triggered"):
                # 红线：触发风控 → 账号冷却 + 立即终止，不重试、不走远程过风控
                account_cooldown_manager.add(acc.account_id)
                logger.warning(
                    f"【{self.task_name}】商品 {lead_item.item_id} 账号 {acc.account_id} 触发风控"
                    f"（{res.get('error')}），账号加入冷却，本轮终止"
                )
                result["risk_triggered"] = True
                result["account_id"] = acc.account_id
                return result

            if res.get("item_invalid"):
                result["item_invalid"] = True
                return result

            # 账号失效（Session过期等）：标记后尝试下一个账号
            if res.get("account_invalid"):
                logger.warning(
                    f"【{self.task_name}】商品 {lead_item.item_id} 账号 {acc.account_id} 不可用"
                    f"（{res.get('error')}），尝试下一个账号"
                )
                continue

            # 临时失败（网络异常等）：尝试下一个账号
            logger.warning(f"【{self.task_name}】商品 {lead_item.item_id} 读取评论失败: {res.get('error')}，尝试下一个账号")
            continue

        if used is None:
            logger.warning(f"【{self.task_name}】商品 {lead_item.item_id} 所有账号均读取失败")
        return result

    async def _save_comments(
        self,
        task: LeadCaptureTask,
        lead_item_db_id: int,
        comments: List[dict],
        include_weak: bool,
    ) -> tuple[int, int]:
        """评论意图分层后 upsert 到 xy_lead_comments（dedupe_hash 去重），返回 (新增数, 强意向新增数)。"""
        new_count = 0
        strong_count = 0
        if not comments:
            return 0, 0

        now = get_beijing_now_naive()
        async with async_session_maker() as session:
            for entry in comments:
                content = (entry.get("content") or "").strip()
                if not content:
                    continue
                intent_level, hit_keywords = classify_intent(content)
                if intent_level == "weak" and not include_weak:
                    continue

                dedupe = build_dedupe_hash(
                    str(lead_item_db_id), entry.get("commenter_user_id"), content
                )
                exists = (
                    await session.execute(
                        select(LeadComment.id).where(
                            LeadComment.owner_id == task.owner_id,
                            LeadComment.dedupe_hash == dedupe,
                        )
                    )
                ).scalar_one_or_none()
                if exists:
                    continue

                session.add(
                    LeadComment(
                        owner_id=task.owner_id,
                        lead_item_id=lead_item_db_id,
                        comment_id=(str(entry.get("comment_id"))[:64] if entry.get("comment_id") else None),
                        commenter_name=(entry.get("commenter_name") or "")[:120] or None,
                        commenter_user_id=(str(entry.get("commenter_user_id"))[:64] if entry.get("commenter_user_id") else None),
                        content=content[:1000],
                        comment_time=_parse_comment_time(entry.get("comment_time")),
                        intent_level=intent_level,
                        intent_keywords=list(hit_keywords),
                        dedupe_hash=dedupe,
                        status="new",
                    )
                )
                new_count += 1
                if intent_level == INTENT_STRONG:
                    strong_count += 1
            if new_count > 0:
                await session.commit()
        return new_count, strong_count

    async def _refresh_item_stats(self, lead_item_db_id: int) -> None:
        """按 xy_lead_comments 聚合重算线索商品的评论计数与需求热度分。"""
        async with async_session_maker() as session:
            rows = (
                await session.execute(
                    select(LeadComment.intent_level, func.count(LeadComment.id))
                    .where(LeadComment.lead_item_id == lead_item_db_id)
                    .group_by(LeadComment.intent_level)
                )
            ).all()
            counts = {level: cnt for level, cnt in rows}
            strong = counts.get(INTENT_STRONG, 0)
            medium = counts.get(INTENT_MEDIUM, 0)
            total = sum(counts.values())
            score = strong * INTENT_WEIGHTS[INTENT_STRONG] + medium * INTENT_WEIGHTS[INTENT_MEDIUM]

            item = (
                await session.execute(select(LeadItem).where(LeadItem.id == lead_item_db_id))
            ).scalar_one_or_none()
            if item:
                item.comment_count = total
                item.strong_count = strong
                item.medium_count = medium
                item.demand_score = score
                await session.commit()

    async def _touch_item_scan_time(self, lead_item_db_id: int) -> None:
        """更新线索商品的最近评论扫描时间（rescan 冷却依据）。"""
        async with async_session_maker() as session:
            item = (
                await session.execute(select(LeadItem).where(LeadItem.id == lead_item_db_id))
            ).scalar_one_or_none()
            if item:
                item.last_comment_scan_at = get_beijing_now_naive()
                await session.commit()

    async def _write_log(
        self,
        task: LeadCaptureTask,
        trigger_type: str,
        account_id: Optional[str],
        scanned: int,
        comment_fetched: int,
        comment_new: int,
        strong_new: int,
        risk_triggered: bool,
        status: str,
        message: str,
    ) -> None:
        """写入一条扫描执行日志。"""
        async with async_session_maker() as session:
            session.add(
                LeadScanLog(
                    task_id=task.id,
                    owner_id=task.owner_id,
                    task_name=task.name,
                    trigger_type=trigger_type,
                    account_id=account_id,
                    scanned_count=scanned,
                    comment_fetched=comment_fetched,
                    comment_new=comment_new,
                    strong_new=strong_new,
                    risk_triggered=risk_triggered,
                    status=status,
                    message=(message or "")[:1000],
                )
            )
            await session.commit()

    async def _update_last_run(self, task_id: int) -> None:
        """更新任务最近执行时间。"""
        async with async_session_maker() as session:
            task = (
                await session.execute(select(LeadCaptureTask).where(LeadCaptureTask.id == task_id))
            ).scalar_one_or_none()
            if task:
                task.last_run_at = get_beijing_now_naive()
                await session.commit()


# 全局实例
lead_comment_scan_task_service = LeadCommentScanTaskService(task_name="线索评论扫描任务")
