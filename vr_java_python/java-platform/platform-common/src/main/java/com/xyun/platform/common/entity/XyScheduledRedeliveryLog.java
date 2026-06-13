package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 定时重新发货日志
 */
@Getter
@Setter
@TableName("xy_scheduled_redelivery_log")
public class XyScheduledRedeliveryLog extends BaseEntity {

    /** 批次ID */
    private String batchId;

    /** 账号ID */
    private String accountId;

    /** 订单编号 */
    private String orderNo;

    /** 执行状态 */
    private String status;

    /** 错误信息 */
    private String errorMessage;
}
