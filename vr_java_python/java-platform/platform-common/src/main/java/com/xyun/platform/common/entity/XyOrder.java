package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import lombok.Getter;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 闲鱼订单实体
 */
@Getter
@Setter
@TableName(value = "xy_orders", autoResultMap = true)
public class XyOrder extends BaseEntity {

    /** 所属用户ID */
    @TableField("owner_id")
    private Long ownerId;

    /** 订单编号 */
    @TableField("order_no")
    private String orderNo;

    /** 订单状态 */
    private String status;

    /** 买家昵称 */
    @TableField("buyer_nick")
    private String buyerNick;

    /** 买家闲鱼昵称 */
    @TableField("buyer_fish_nick")
    private String buyerFishNick;

    /** 买家ID */
    @TableField("buyer_id")
    private String buyerId;

    /** 会话ID */
    @TableField("chat_id")
    private String chatId;

    /** 商品ID */
    @TableField("item_id")
    private String itemId;

    /** 规格名称 */
    @TableField("spec_name")
    private String specName;

    /** 规格值 */
    @TableField("spec_value")
    private String specValue;

    /** 数量 */
    private Integer quantity;

    /** 金额 */
    private BigDecimal amount;

    /** 币种 */
    private String currency;

    /** 账号ID */
    @TableField("account_id")
    private String accountId;

    /** 账号名称 */
    @TableField("account_name")
    private String accountName;

    /** 是否砍价订单 */
    @TableField("is_bargain")
    private Boolean isBargain;

    /** 收货人姓名 */
    @TableField("receiver_name")
    private String receiverName;

    /** 收货人电话 */
    @TableField("receiver_phone")
    private String receiverPhone;

    /** 收货地址 */
    @TableField("receiver_address")
    private String receiverAddress;

    /** 是否已评价 */
    @TableField("is_rated")
    private Boolean isRated;

    /** 是否送红花 */
    @TableField("is_red_flower")
    private Boolean isRedFlower;

    /** 发货方式 */
    @TableField("delivery_method")
    private String deliveryMethod;

    /** 发货内容 */
    @TableField("delivery_content")
    private String deliveryContent;

    /** 发货失败原因 */
    @TableField("delivery_fail_reason")
    private String deliveryFailReason;

    /** 商品快照（JSON） */
    @TableField(value = "item_snapshot", typeHandler = JacksonTypeHandler.class)
    private String itemSnapshot;

    /** 元数据（JSON） */
    @TableField(typeHandler = JacksonTypeHandler.class)
    private String metadata;

    /** 来源 */
    private String source;

    /** 下单时间 */
    @TableField("placed_at")
    private LocalDateTime placedAt;

    /** 同步时间 */
    @TableField("synced_at")
    private LocalDateTime syncedAt;
}
