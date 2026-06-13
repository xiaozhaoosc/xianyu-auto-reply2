package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 代理订单
 */
@Getter
@Setter
@TableName("xy_agent_orders")
public class XyAgentOrder extends BaseEntity {

    /** 用户ID */
    private Long userId;

    /** 订单号 */
    private String orderNo;

    /** 商品ID */
    private String itemId;

    /** 卡片ID */
    private Long cardId;

    /** 对接记录ID */
    private Long dockRecordId;

    /** 对接层级 */
    private Integer dockLevel;

    /** 售价 */
    private String salePrice;

    /** 对接价 */
    private String dockPrice;

    /** 卡片价 */
    private String cardPrice;

    /** 二级成本 */
    private String level2Cost;

    /** 利润 */
    private String profit;

    /** 手续费金额 */
    private String feeAmount;

    /** 手续费支付方 */
    private String feePayer;

    /** 上游用户ID */
    private Long upstreamUserId;

    /** 上游对接记录ID */
    private Long upstreamDockRecordId;

    /** 归属用户ID */
    private Long ownerUserId;

    /** 发货内容 */
    private String deliveryContent;

    /** 买家ID */
    private String buyerId;

    /** 订单状态 */
    private String status;

    /** 结算备注 */
    private String settleRemark;
}
