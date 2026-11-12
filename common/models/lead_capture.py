"""
线索池模块数据模型

功能：
1. 定义线索池模块的 5 张表结构（xy_lead_capture_tasks / xy_lead_items / xy_lead_comments / xy_lead_actions / xy_lead_scan_logs）
2. 只读监控别人商品评论区的高意向需求，形成线索池，不含任何自动触达能力
3. 支持多用户数据隔离（owner_id）与软删除（is_deleted，仅任务表有）

模块红线（详见 lead_comment_scan_task）：
- 不自动发评论、不批量私信、不模板化触达
- 采集节奏由任务字段与代码常量双重限制
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from common.db.base_class import Base, TimestampMixin


class LeadCaptureTask(TimestampMixin, Base):
    """线索采集任务配置表"""

    __tablename__ = "xy_lead_capture_tasks"
    __table_args__ = (
        Index("idx_lct_owner_enabled", "owner_id", "is_enabled"),
        Index("idx_lct_owner_deleted", "owner_id", "is_deleted"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    owner_id: Mapped[int | None] = mapped_column(BigInteger, index=True, comment="归属用户ID，用于多用户数据隔离")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="任务名称")
    # 候选商品来源：monitor-复用商品监控采集池（推荐，零额外搜索请求），keyword-独立关键词搜索
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="monitor", server_default="monitor",
        comment="候选来源：monitor-复用商品监控采集池，keyword-独立关键词搜索",
    )
    keyword: Mapped[str | None] = mapped_column(String(200), comment="source_type=keyword 时的搜索词")
    monitor_task_id: Mapped[int | None] = mapped_column(
        BigInteger, comment="source_type=monitor 时关联的 xy_listing_monitor_tasks.id，取其采集商品作候选池"
    )
    price_min: Mapped[float | None] = mapped_column(Numeric(12, 2), comment="候选商品价格区间最低值")
    price_max: Mapped[float | None] = mapped_column(Numeric(12, 2), comment="候选商品价格区间最高值")
    # 风控硬参数（代码层强校验下限/上限，见 lead_capture_service 的校验常量）
    interval_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60, server_default="60",
        comment="扫描间隔分钟（最低30，创建/更新接口强校验）",
    )
    max_items_per_round: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5",
        comment="每轮扫描商品数上限（最高10）",
    )
    comment_pages_per_item: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1",
        comment="每商品每次读取评论页数（当前固定1，预留字段）",
    )
    include_weak: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0",
        comment="是否入库弱意向评论（默认只存 strong/medium）",
    )
    account_ids: Mapped[list | None] = mapped_column(JSON, comment="读取用账号ID列表（只读借用Cookie，不发消息）")
    rescan_cooldown_hours: Mapped[int] = mapped_column(
        Integer, nullable=False, default=24, server_default="24",
        comment="同一商品两次评论扫描的最小间隔小时",
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1", comment="是否启用任务")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0", comment="是否已删除（软删除）")
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="最近一次执行时间")
    remark: Mapped[str | None] = mapped_column(String(500), comment="备注")


class LeadItem(TimestampMixin, Base):
    """线索商品池表（被监控的别人商品聚合视图）"""

    __tablename__ = "xy_lead_items"
    __table_args__ = (
        UniqueConstraint("owner_id", "item_id", name="uk_li_owner_item"),
        Index("idx_li_status_heat", "owner_id", "status", "strong_count"),
        Index("idx_li_last_scan", "owner_id", "last_comment_scan_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    owner_id: Mapped[int | None] = mapped_column(BigInteger, comment="归属用户ID")
    item_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="闲鱼商品ID")
    title: Mapped[str | None] = mapped_column(String(500), comment="商品标题")
    price: Mapped[str | None] = mapped_column(String(32), comment="商品价格（展示文本）")
    seller_nick: Mapped[str | None] = mapped_column(String(120), comment="卖家昵称")
    seller_user_id: Mapped[str | None] = mapped_column(String(64), comment="卖家真实用户ID")
    item_url: Mapped[str | None] = mapped_column(String(1000), comment="商品详情页URL")
    pic_url: Mapped[str | None] = mapped_column(String(1000), comment="商品主图URL")
    want_count: Mapped[str | None] = mapped_column(String(32), comment="想要数（展示文本）")
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0", comment="已采集评论数")
    strong_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0", comment="强意向评论数")
    medium_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0", comment="中意向评论数")
    demand_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
        comment="需求热度分 = strong*3 + medium*1，前端按此排序",
    )
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="首次发现时间")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="最近一次扫描到时间")
    last_comment_scan_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="最近一次评论扫描时间（rescan_cooldown 依据）"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active",
        comment="商品状态：active-观察中，archived-已归档",
    )


class LeadComment(TimestampMixin, Base):
    """线索评论表（核心表：高意向需求评论）"""

    __tablename__ = "xy_lead_comments"
    __table_args__ = (
        UniqueConstraint("owner_id", "dedupe_hash", name="uk_lc_dedupe"),
        Index("idx_lc_item_intent", "lead_item_id", "intent_level", "status"),
        Index("idx_lc_owner_status", "owner_id", "status"),
        Index("idx_lc_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    owner_id: Mapped[int | None] = mapped_column(BigInteger, comment="归属用户ID")
    lead_item_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="关联 xy_lead_items.id")
    comment_id: Mapped[str | None] = mapped_column(String(64), comment="平台评论ID（取不到时为空）")
    commenter_name: Mapped[str | None] = mapped_column(String(120), comment="评论人昵称")
    commenter_user_id: Mapped[str | None] = mapped_column(String(64), comment="评论人用户ID")
    content: Mapped[str] = mapped_column(String(1000), nullable=False, comment="评论内容")
    comment_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="评论发布时间")
    intent_level: Mapped[str] = mapped_column(
        String(10), nullable=False, default="weak", server_default="weak",
        comment="意向层级：strong-明确求购，medium-规格价格咨询，weak-闲聊砍价",
    )
    intent_keywords: Mapped[list | None] = mapped_column(JSON, comment="命中的关键词列表")
    dedupe_hash: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="md5(item_id + commenter_user_id + 归一化content)，防重复入库",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="new", server_default="new",
        comment="处理状态：new-未处理，reviewed-已看过，ignored-忽略，followed-已人工跟进（终态，不可重复跟进）",
    )


class LeadAction(TimestampMixin, Base):
    """线索人工动作流水表"""

    __tablename__ = "xy_lead_actions"
    __table_args__ = (
        Index("idx_la_comment", "lead_comment_id"),
        Index("idx_la_owner", "owner_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    owner_id: Mapped[int | None] = mapped_column(BigInteger, comment="归属用户ID")
    lead_comment_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="关联 xy_lead_comments.id")
    action_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="动作类型：opened-打开商品页，copied-复制话术，ignored-忽略，followed-标记跟进",
    )
    suggested_reply: Mapped[str | None] = mapped_column(String(1000), comment="当时展示/复制的建议话术（供复盘）")
    operator: Mapped[str | None] = mapped_column(String(64), comment="操作人用户名")
    note: Mapped[str | None] = mapped_column(String(500), comment="备注")


class LeadScanLog(TimestampMixin, Base):
    """线索扫描执行日志表（结构对齐 xy_listing_monitor_logs）"""

    __tablename__ = "xy_lead_scan_logs"
    __table_args__ = (
        Index("idx_lsl_task", "task_id"),
        Index("idx_lsl_owner", "owner_id"),
        Index("idx_lsl_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="关联的线索采集任务ID")
    owner_id: Mapped[int | None] = mapped_column(BigInteger, comment="归属用户ID")
    task_name: Mapped[str | None] = mapped_column(String(100), comment="任务名称")
    trigger_type: Mapped[str] = mapped_column(
        String(10), nullable=False, default="auto", server_default="auto",
        comment="触发方式：auto-定时自动，manual-手动",
    )
    account_id: Mapped[str | None] = mapped_column(String(80), comment="本次使用的读取账号ID")
    scanned_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0", comment="本次扫描的商品数")
    comment_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0", comment="本次获取的评论数")
    comment_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0", comment="本次新增入库的评论数")
    strong_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0", comment="本次新增的强意向评论数")
    risk_triggered: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0",
        comment="本次执行是否触发风控（触发即停）",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="success", server_default="success",
        comment="执行状态：success-成功，failed-失败，partial-部分成功，risk_stopped-触发风控提前终止",
    )
    message: Mapped[str | None] = mapped_column(String(1000), comment="执行结果说明")
