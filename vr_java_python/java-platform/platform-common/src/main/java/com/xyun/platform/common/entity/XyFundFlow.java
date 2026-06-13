package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 资金流水实体
 */
@Getter
@Setter
@TableName("xy_fund_flows")
public class XyFundFlow extends BaseEntity {

    /** 用户 ID */
    private Long userId;

    /** 流水类型 */
    private String type;

    /** 变动金额 */
    private String amount;

    /** 变动前余额 */
    private String balanceBefore;

    /** 变动后余额 */
    private String balanceAfter;

    /** 关联订单 ID */
    private Long orderId;

    /** 关联对接记录 ID */
    private Long dockRecordId;

    /** 描述 */
    private String description;
}
