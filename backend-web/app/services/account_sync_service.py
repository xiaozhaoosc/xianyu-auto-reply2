"""
多账号商品同步服务

功能：
1. 从源账号获取商品列表
2. 将商品发布到目标账号
3. 支持筛选条件（标题关键词、价格范围）
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models.xy_account import XYAccount
from common.models.xy_catalog_item import XYCatalogItem
from common.models.product_material import ProductMaterial
from common.services.item_service import ItemService


class AccountSyncService:
    """多账号商品同步服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def sync_items_between_accounts(
        self,
        user_id: int,
        source_account_id: str,
        target_account_ids: List[str],
        keyword_filter: str = None,
        min_price: float = None,
        max_price: float = None,
        sync_mode: str = "material",  # material = 通过素材库中转, direct = 直接发布
    ) -> Dict[str, Any]:
        """
        同步商品：从源账号 → 目标账号
        
        Args:
            user_id: 用户ID
            source_account_id: 源账号ID
            target_account_ids: 目标账号ID列表
            keyword_filter: 标题关键词筛选
            min_price: 最低价格筛选
            max_price: 最高价格筛选
            sync_mode: 同步模式 (material/direct)
        """
        # 1. 获取源账号
        source_account = await self._get_account(source_account_id, user_id)
        if not source_account:
            return {"success": False, "message": "源账号不存在"}

        # 2. 获取源账号的商品列表
        item_svc = ItemService(self.session)
        source_items = await item_svc.list_items(owner_id=user_id, account_id=source_account_id)
        
        if not source_items:
            return {"success": False, "message": "源账号没有商品"}

        # 3. 筛选商品
        filtered_items = self._filter_items(
            source_items,
            keyword_filter=keyword_filter,
            min_price=min_price,
            max_price=max_price,
        )

        if not filtered_items:
            return {"success": False, "message": "筛选后没有符合条件的商品"}

        # 4. 获取目标账号
        target_accounts = []
        for tid in target_account_ids:
            account = await self._get_account(tid, user_id)
            if account and account.cookie:
                target_accounts.append(account)
            else:
                logger.warning(f"目标账号 {tid} 不存在或无 Cookie，跳过")

        if not target_accounts:
            return {"success": False, "message": "没有可用的目标账号"}

        # 5. 执行同步
        if sync_mode == "material":
            result = await self._sync_via_materials(
                user_id=user_id,
                source_items=filtered_items,
                target_accounts=target_accounts,
            )
        else:
            result = {"success": False, "message": "直接发布模式暂未实现，请使用素材库中转模式"}

        return result

    def _filter_items(
        self,
        items: List[dict],
        keyword_filter: str = None,
        min_price: float = None,
        max_price: float = None,
    ) -> List[dict]:
        """筛选商品"""
        filtered = []
        for item in items:
            # 关键词筛选
            if keyword_filter:
                title = item.get("title", "")
                if keyword_filter.lower() not in title.lower():
                    continue

            # 价格筛选
            price = item.get("price")
            if price is not None:
                try:
                    price_num = float(price)
                    if min_price is not None and price_num < min_price:
                        continue
                    if max_price is not None and price_num > max_price:
                        continue
                except (ValueError, TypeError):
                    pass

            filtered.append(item)

        return filtered

    async def _sync_via_materials(
        self,
        user_id: int,
        source_items: List[dict],
        target_accounts: List[XYAccount],
    ) -> Dict[str, Any]:
        """通过素材库中转同步商品"""
        # 1. 将源商品转为素材
        material_ids = []
        for item in source_items:
            # 检查是否已存在同名素材
            existing = await self.session.execute(
                select(ProductMaterial).where(
                    ProductMaterial.user_id == user_id,
                    ProductMaterial.title == item.get("title", ""),
                )
            )
            existing_material = existing.scalar_one_or_none()

            if existing_material:
                material_ids.append(existing_material.id)
                continue

            # 创建新素材
            metadata = item.get("metadata_json") or {}
            images = metadata.get("images", []) if isinstance(metadata, dict) else []

            material = ProductMaterial(
                user_id=user_id,
                title=item.get("title", ""),
                description=item.get("description", "") or metadata.get("description", ""),
                price=float(item.get("price", 0) or 0),
                original_price=float(metadata.get("original_price", 0) or 0) or None,
                category=metadata.get("category"),
                images=images[:9],  # 最多9张图
                delivery_method=metadata.get("delivery_method", "express"),
                postage=float(metadata.get("postage", 0) or 0),
                address=metadata.get("address"),
                brand=metadata.get("brand"),
                condition=metadata.get("condition", "全新"),
                remark=f"同步自账号商品 | item_id={item.get('item_id', '')}",
            )
            self.session.add(material)
            await self.session.commit()
            await self.session.refresh(material)
            material_ids.append(material.id)

        # 2. 调用批量发布
        from app.services.publish_execution_service import PublishExecutorService
        publish_svc = PublishExecutorService(self.session)

        materials_data = []
        for mid in material_ids:
            stmt = select(ProductMaterial).where(ProductMaterial.id == mid)
            result = await self.session.execute(stmt)
            mat = result.scalar_one_or_none()
            if mat:
                materials_data.append(self._material_to_dict(mat))

        if not materials_data:
            return {"success": False, "message": "没有可同步的素材"}

        target_account_ids = [a.account_id for a in target_accounts]
        batch_id = f"sync_{uuid.uuid4().hex[:8]}"

        publish_result = await publish_svc.batch_publish(
            user_id=user_id,
            account_ids=target_account_ids,
            materials=materials_data,
            batch_id=batch_id,
        )

        return {
            "success": True,
            "message": f"同步完成：{publish_result.get('success_count', 0)} 成功，{publish_result.get('failed_count', 0)} 失败",
            "data": {
                "batch_id": batch_id,
                "source_items_count": len(source_items),
                "materials_created": len(material_ids),
                "target_accounts_count": len(target_accounts),
                "publish_result": publish_result,
            },
        }

    def _material_to_dict(self, material: ProductMaterial) -> dict:
        """素材转字典"""
        return {
            "id": material.id,
            "title": material.title,
            "description": material.description,
            "price": material.price,
            "original_price": material.original_price,
            "category": material.category,
            "images": material.images or [],
            "delivery_method": material.delivery_method,
            "postage": material.postage,
            "address": material.address,
            "brand": material.brand,
            "condition": material.condition,
        }

    async def _get_account(self, account_id: str, user_id: int) -> Optional[XYAccount]:
        """获取账号"""
        stmt = select(XYAccount).where(
            XYAccount.account_id == account_id,
            XYAccount.owner_id == user_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()
