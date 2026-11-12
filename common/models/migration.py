"""商品迁移模型

功能：
1. 跨账号商品+卡券迁移批次（xy_migration_batches）
2. 单商品迁移任务（xy_migration_tasks）—— 由 scheduler 按随机间隔逐个发布
3. 卡券新旧ID映射（xy_migration_card_maps）—— 批次创建时复制卡券后记录映射
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from common.db.base_class import Base


class MigrationBatch(Base):
    """迁移批次表"""

    __tablename__ = "xy_migration_batches"
    __table_args__ = (
        Index("idx_mig_batch_owner_status", "owner_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="批次ID")
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="所属用户ID")
    source_account_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="源闲鱼账号ID")
    target_account_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="目标闲鱼账号ID")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="prepared",
        comment="状态: prepared/running/paused/done/cancelled",
    )
    description_template: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述模板(支持{title}占位符)")
    total: Mapped[int] = mapped_column(Integer, default=0, comment="商品总数")
    published: Mapped[int] = mapped_column(Integer, default=0, comment="已发布数")
    failed: Mapped[int] = mapped_column(Integer, default=0, comment="失败数")
    min_interval: Mapped[int] = mapped_column(Integer, default=180, comment="最小间隔秒")
    max_interval: Mapped[int] = mapped_column(Integer, default=600, comment="最大间隔秒")
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="下一次发布时间")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True, comment="最近错误(风控自动暂停原因)")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="开始时间")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="完成时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=datetime.now, comment="更新时间")


class MigrationTask(Base):
    """单商品迁移任务表"""

    __tablename__ = "xy_migration_tasks"
    __table_args__ = (
        Index("idx_mig_task_batch_status", "batch_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    batch_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="批次ID")
    source_item_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="源商品ID")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="商品标题")
    price: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="价格")
    category_id: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="类目ID")
    category_override_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="类目覆盖(JSON)：{cat_name,channel_cat_id,channel_cat_name}，非空则发布时用两阶段协议锁定该类目，不再走自动推荐首选")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="发布描述(可编辑)")
    images_json: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True, comment="原始CDN图片URL列表(JSON)")
    local_images_json: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True, comment="本地化图片路径列表(JSON)")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="状态: pending/publishing/done/failed/skipped",
    )
    new_item_id: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="发布后的新商品ID")
    error: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    attempts: Mapped[int] = mapped_column(Integer, default=0, comment="已尝试次数")
    max_attempts: Mapped[int] = mapped_column(Integer, default=2, comment="最大尝试次数")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="发布完成时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=datetime.now, comment="更新时间")


class MigrationCardMap(Base):
    """卡券新旧ID映射表"""

    __tablename__ = "xy_migration_card_maps"
    __table_args__ = (
        Index("idx_mig_cardmap_batch", "batch_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    batch_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="批次ID")
    source_card_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="源卡券ID")
    new_card_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="新卡券ID")
    card_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="卡券名称")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
