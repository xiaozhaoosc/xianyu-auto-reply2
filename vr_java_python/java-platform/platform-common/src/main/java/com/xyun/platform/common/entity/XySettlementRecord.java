package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 结算记录实体
 */
@Getter
@Setter
@TableName("xy_settlement_records")
public class XySettlementRecord extends BaseEntity {

    /** 用户 ID */
    private Long userId;

    /** 支付宝账号 */
    private String alipayId;

    /** 收款方式 */
    private String paymentType;

    /** 收款二维码 */
    private String paymentQrcode;

    /** 结算金额 */
    private String amount;

    /** 结算状态 */
    private String status;

    /** 备注 */
    private String remark;

    /** 驳回原因 */
    private String rejectReason;
}
