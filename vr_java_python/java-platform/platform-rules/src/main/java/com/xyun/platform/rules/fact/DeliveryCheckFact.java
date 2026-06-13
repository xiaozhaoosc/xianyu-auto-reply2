package com.xyun.platform.rules.fact;

import lombok.Getter;
import lombok.Setter;

/**
 * 发货检查事实 — Drools 规则引擎输入
 */
@Getter
@Setter
public class DeliveryCheckFact {
    /** 账号ID */
    private String accountId;
    /** 买家ID */
    private String buyerId;
    /** 商品ID */
    private String itemId;
    /** 订单金额 */
    private String orderAmount;
    /** 是否已下单 */
    private boolean ordered;
    /** 是否在黑名单 */
    private boolean blacklisted;
    /** 是否禁止发货 */
    private boolean deliveryBlocked;
    /** 禁止原因 */
    private String blockReason;
    /** 是否自动关闭订单 */
    private boolean autoCloseOrder;
    /** 关闭后是否继续发卡券 */
    private boolean onlyCardAfterClose;
}
