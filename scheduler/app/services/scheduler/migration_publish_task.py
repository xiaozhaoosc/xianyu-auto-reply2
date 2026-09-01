"""
商品迁移发布任务

功能：
1. 扫描状态为 running 且到点(next_run_at<=now)的迁移批次
2. 每个批次每轮发布 1 个 pending 商品（API 发布，无浏览器）
3. 发布间隔随机化：每发完一个，随机 min~max 秒后再发下一个
4. 发布成功后：新商品同步入商品目录 + 按卡券映射重建"卡券-商品"关联
5. 风控刹车：检测到滑块/USER_VALIDATE/captcha 特征 → 批次自动暂停，绝不硬闯
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from typing import Any, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.session import async_session_maker
from common.models.xy_account import XYAccount
from common.models.card_item_relation import CardItemRelation
from common.models.migration import MigrationBatch, MigrationTask, MigrationCardMap

# 风控特征关键词：命中即暂停批次
RISK_KEYWORDS = (
    "USER_VALIDATE",
    "滑块",
    "captcha",
    "验证码",
    "FAIL_SYS_SESSION",
    "登录",
    "account_invalid",
    "FAIL_SYS_TOKEN",
)


def _now() -> datetime:
    return datetime.now().replace(microsecond=0)


def _random_next_run(batch: MigrationBatch) -> datetime:
    lo = min(batch.min_interval, batch.max_interval)
    hi = max(batch.min_interval, batch.max_interval)
    delta = random.randint(lo, hi)
    return _now() + timedelta(seconds=delta)


def _is_risk_error(message: str | None, account_invalid: bool = False) -> bool:
    if account_invalid:
        return True
    if not message:
        return False
    return any(kw in message for kw in RISK_KEYWORDS)


class MigrationPublishTask:
    """迁移发布任务：按批次随机间隔逐个发布迁移商品"""

    async def execute(self) -> str:
        """主入口：处理所有到点的运行中批次"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(MigrationBatch).where(
                    MigrationBatch.status == "running",
                    MigrationBatch.next_run_at <= _now(),
                )
            )
            batches = result.scalars().all()

        if not batches:
            return "无到点迁移批次"

        processed = []
        for batch_info in batches:
            try:
                outcome = await self._process_batch(batch_info.id)
                processed.append(f"批次{batch_info.id}:{outcome}")
            except Exception as e:
                logger.error(f"[迁移发布] 批次{batch_info.id} 处理异常: {e}")
                processed.append(f"批次{batch_info.id}:异常({e})")
        return "; ".join(processed) if processed else "无处理"

    async def _process_batch(self, batch_id: int) -> str:
        """处理单个批次：发布下一个 pending 商品，然后随机排下一发"""
        async with async_session_maker() as session:
            batch = await session.get(MigrationBatch, batch_id)
            if not batch or batch.status != "running":
                return "批次已不在运行态"

            task = (await session.execute(
                select(MigrationTask)
                .where(MigrationTask.batch_id == batch_id, MigrationTask.status == "pending")
                .order_by(MigrationTask.id)
                .limit(1)
            )).scalar_one_or_none()

            if not task:
                batch.status = "done"
                batch.finished_at = _now()
                batch.next_run_at = None
                await session.commit()
                logger.info(f"[迁移发布] 批次{batch_id} 全部完成: 成功{batch.published} 失败{batch.failed}")
                return "全部完成"

            outcome = await self._publish_one(session, batch, task)
            # 无论成败，排下一发（暂停/完成态除外）
            refreshed = await session.get(MigrationBatch, batch_id)
            if refreshed and refreshed.status == "running":
                refreshed.next_run_at = _random_next_run(refreshed)
                await session.commit()
            return outcome

    async def _publish_one(self, session: AsyncSession, batch: MigrationBatch, task: MigrationTask) -> str:
        """执行单商品发布（API 方式，不开浏览器）"""
        task.status = "publishing"
        task.attempts = (task.attempts or 0) + 1
        await session.commit()

        # 目标账号
        account = (await session.execute(
            select(XYAccount).where(
                XYAccount.account_id == batch.target_account_id,
                XYAccount.owner_id == batch.owner_id,
            )
        )).scalar_one_or_none()
        if not account or not account.cookie:
            await self._fail(session, batch, task, "目标账号不存在或cookie为空")
            return "目标账号不可用"

        images = []
        try:
            images = json.loads(task.images_json or "[]")
        except Exception:
            pass
        images = [u for u in images if isinstance(u, str) and u.startswith("http")]
        if not images:
            # 无图商品无法发布：无素材时直接跳过不算失败重试
            task.status = "skipped"
            task.error = "无可用商品图片素材"
            task.published_at = _now()
            await session.commit()
            return f"跳过({task.source_item_id}无图)"

        # 地址：随机地址库轮询（与既有发布链路一致）
        from common.services.publish_address_service import PublishAddressService
        address_svc = PublishAddressService(session)
        try:
            resolved = await address_svc.resolve_publish_address(
                account_id=batch.target_account_id,
                item_data={},
            )
            address_text = resolved.resolved_address_text
        except Exception as e:
            await self._fail(session, batch, task, f"地址解析失败: {e}")
            return "地址解析失败"

        # 类目：推荐接口按标题+描述取首个候选
        category_fields = await self._resolve_category(account, task)
        if category_fields is None:
            await self._fail(session, batch, task, "类目推荐失败（可能触发风控或登录失效）", risk_hint=True)
            return "类目推荐失败"

        price: Any = task.price
        try:
            price = float(str(task.price).replace("¥", "").strip())
        except Exception:
            price = 0.01
        if price <= 0:
            price = 0.01

        item_data = {
            "title": task.title,
            "description": task.description or task.title,
            "price": price,
            "original_price": price,
            "images": images,
            "quantity": 999,
            "shipping_method": "free",
            "address": address_text,
            **category_fields,
        }

        # 发布（纯API，无浏览器）
        from common.services.xianyu_publish_service import publish_single_item
        try:
            result = await publish_single_item(
                item_data=item_data,
                cookie=account.cookie,
                static_root=None,
                account_id=account.account_id,
                owner_id=batch.owner_id,
            )
        except Exception as e:
            await self._fail(session, batch, task, f"发布异常: {e}", risk_hint=_is_risk_error(str(e)))
            return f"发布异常({str(e)[:60]})"

        # cookie 回写
        new_cookie = result.get("cookies_str")
        if new_cookie and new_cookie != account.cookie:
            account.cookie = new_cookie

        if not result.get("success"):
            msg = result.get("message") or "发布失败"
            await self._fail(
                session, batch, task, msg,
                risk_hint=_is_risk_error(msg, result.get("account_invalid", False)),
            )
            return f"失败({msg[:60]})"

        new_item_id = result.get("item_id")
        task.status = "done"
        task.new_item_id = new_item_id
        task.error = None
        task.published_at = _now()
        batch.published = (batch.published or 0) + 1
        await session.commit()

        # 重建卡券关联 + 同步商品入目录
        if new_item_id:
            await self._rebuild_card_relations(session, batch, task, new_item_id)
        await self._sync_target_item(session, batch, account, new_item_id, task)

        logger.info(
            f"[迁移发布] 批次{batch.id} 商品 {task.source_item_id} → {new_item_id or '?'} 发布成功 "
            f"({batch.published}/{batch.total})"
        )
        return f"成功({task.source_item_id}→{new_item_id})"

    async def _resolve_category(self, account: XYAccount, task: MigrationTask) -> dict | None:
        """调用类目推荐接口，取首选候选。失败返回 None

        若任务带 category_override_json，则走两阶段协议锁定用户指定类目：
        第一次推荐拿 card_list → build_category_selection 选中覆盖类目 → 第二次
        推荐回传完整字段（tb_cat_id/leaf_id 由平台补齐）。不改标题，只改类目选定。
        """
        try:
            from common.services.backend_web_loader import load_backend_web_class
            svc_class = load_backend_web_class(
                module_name="common.services._shared_platform_category_service",
                relative_path="backend-web/app/services/platform_category_service.py",
                class_name="PlatformCategoryService",
            )
            svc = svc_class()

            override: dict | None = None
            raw_override = getattr(task, "category_override_json", None)
            if raw_override:
                try:
                    override = json.loads(raw_override)
                except Exception:
                    logger.warning(f"[迁移发布] category_override JSON 解析失败，忽略覆盖: {raw_override[:100]}")

            first = await svc.recommend(
                title=task.title,
                description=task.description or task.title,
                cookie=account.cookie,
                account_id=account.account_id,
                owner_id=None,
            )
            candidates = first.get("candidates") or []
            if not candidates:
                return None

            if override:
                from common.services.backend_web_loader import _load_backend_web_module
                sel_mod = _load_backend_web_module(
                    "app.services.platform_category_selection",
                    "backend-web/app/services/platform_category_selection.py",
                )
                try:
                    selection = sel_mod.build_category_selection(first.get("card_list") or [], override)
                except Exception as e:
                    logger.warning(f"[迁移发布] 类目覆盖失效(候选已变化): {override} err={e}")
                    return None
                second = await svc.recommend(
                    title=task.title,
                    description=task.description or task.title,
                    cookie=account.cookie,
                    account_id=account.account_id,
                    owner_id=None,
                    **selection,
                )
                candidates = second.get("candidates") or candidates
                pick = next((c for c in candidates if c.get("is_selected")), None)
                if pick is None:
                    logger.warning("[迁移发布] 类目覆盖后未拿到选中候选")
                    return None
                logger.info(f"[迁移发布] 使用类目覆盖: {override.get('cat_name')} → "
                            f"tb_cat_id={pick.get('tb_cat_id')} cat_id={pick.get('cat_id')}")
            else:
                pick = next((c for c in candidates if c.get("is_selected")), None) or candidates[0]

            if not (pick.get("cat_id") and pick.get("channel_cat_id")):
                logger.warning(f"[迁移发布] 类目候选字段不完整: {pick}")
                return None
            if not pick.get("tb_cat_id"):
                # 频道类目没有淘宝叶子类目属正常（如 电子资料），放行由载荷构造为 null
                logger.info(f"[迁移发布] 类目无 tb_cat_id(频道类目): {pick.get('cat_name')} cat_id={pick.get('cat_id')}")
            return {
                "platform_category_id": pick.get("cat_id"),
                "platform_category_name": pick.get("cat_name"),
                "platform_channel_category_id": pick.get("channel_cat_id"),
                "platform_channel_category_name": pick.get("channel_cat_name"),
                "platform_leaf_id": pick.get("leaf_id"),
                "platform_tb_category_id": pick.get("tb_cat_id"),
                "platform_category_path": pick.get("path") or [],
                "platform_attributes": [],
            }
        except Exception as e:
            logger.warning(f"[迁移发布] 类目推荐异常[{account.account_id}]: {e}")
            return None

    async def _rebuild_card_relations(
        self, session: AsyncSession, batch: MigrationBatch, task: MigrationTask, new_item_id: str
    ) -> None:
        """源商品绑过的卡券 → 映射后的新卡券绑到新商品"""
        try:
            source_rels = (await session.execute(
                select(CardItemRelation).where(CardItemRelation.item_id == task.source_item_id)
            )).scalars().all()
            if not source_rels:
                return

            maps = (await session.execute(
                select(MigrationCardMap).where(MigrationCardMap.batch_id == batch.id)
            )).scalars().all()
            card_map = {m.source_card_id: m.new_card_id for m in maps}

            created = 0
            for rel in source_rels:
                new_card_id = card_map.get(rel.card_id)
                if not new_card_id:
                    continue
                exists = (await session.execute(
                    select(CardItemRelation).where(
                        CardItemRelation.card_id == new_card_id,
                        CardItemRelation.item_id == new_item_id,
                        CardItemRelation.dock_record_id == 0,
                    )
                )).scalar_one_or_none()
                if exists:
                    continue
                session.add(CardItemRelation(
                    user_id=rel.user_id,
                    card_id=new_card_id,
                    item_id=new_item_id,
                    source="own",
                    dock_record_id=0,
                ))
                created += 1
            await session.commit()
            logger.info(f"[迁移发布] 批次{batch.id} 商品{new_item_id} 重建卡券关联 {created} 条")
        except Exception as e:
            logger.error(f"[迁移发布] 批次{batch.id} 重建卡券关联失败: {e}")
            await session.rollback()

    async def _sync_target_item(
        self, session: AsyncSession, batch: MigrationBatch, account: XYAccount,
        new_item_id: str | None, task: MigrationTask,
    ) -> None:
        """把新商品登记进本地商品目录（不主动调闲鱼同步，避免额外请求）"""
        if not new_item_id:
            return
        try:
            from common.models.xy_catalog_item import XYCatalogItem
            exists = (await session.execute(
                select(XYCatalogItem).where(
                    XYCatalogItem.account_pk == account.id,
                    XYCatalogItem.item_id == new_item_id,
                )
            )).scalar_one_or_none()
            if exists:
                return
            session.add(XYCatalogItem(
                owner_id=batch.owner_id,
                account_pk=account.id,
                item_id=new_item_id,
                title=task.title,
                price=str(task.price) if task.price else None,
                metadata_json={"migrated_from": task.source_item_id, "migration_batch_id": batch.id},
                created_at=_now(),
            ))
            await session.commit()
        except Exception as e:
            logger.warning(f"[迁移发布] 新商品目录登记失败(不影响主流程): {e}")
            await session.rollback()

    async def _fail(
        self, session: AsyncSession, batch: MigrationBatch, task: MigrationTask,
        message: str, risk_hint: bool = False,
    ) -> None:
        """失败处理：达标次数→failed；命中风控→批次暂停"""
        if (task.attempts or 0) >= (task.max_attempts or 2):
            task.status = "failed"
            task.error = message[:500]
            batch.failed = (batch.failed or 0) + 1
        else:
            task.status = "pending"
            task.error = f"第{task.attempts}次失败: {message[:200]}"

        if risk_hint:
            batch.status = "paused"
            batch.last_error = f"[风控刹车] {message[:200]}（人工确认后可在页面恢复）"
            task.status = "pending"  # 恢复后可重试
            logger.warning(f"[迁移发布] 批次{batch.id} 触发风控特征，已自动暂停: {message[:100]}")
        await session.commit()
