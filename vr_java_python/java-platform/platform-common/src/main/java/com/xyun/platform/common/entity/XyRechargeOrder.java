package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 充值订单实体
 */
@Getter
@Setter
@TableName("xy_recharge_orders")
public class XyRechargeOrder extends BaseEntity {

    /** 订单编号 */
    private String orderNo;

    /** 用户 ID */
    private Long userId;

    /** 充值金额 */
    private String amount;

    /** 订单状态 */
    private String status;

    /** 交易流水号 */
    private String tradeNo;

    /** 支付二维码 */
    private String qrCode;

    /** 支付时间 */
    private LocalDateTime paidAt;
}
