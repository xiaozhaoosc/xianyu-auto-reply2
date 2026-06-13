package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 风控日志
 */
@Getter
@Setter
@TableName("xy_risk_control_logs")
public class XyRiskControlLog extends BaseEntity {

    /** 所属用户ID */
    private Long ownerId;

    /** 关联账号ID */
    private Long accountId;

    /** 账号标识 */
    private String accountIdentifier;

    /** 事件类型 */
    private String eventType;

    /** 事件描述 */
    private String eventDescription;

    /** 处理结果 */
    private String processingResult;

    /** 处理状态 */
    private String processingStatus;

    /** 验证码引擎 */
    private String captchaEngine;

    /** 错误信息 */
    private String errorMessage;
}
