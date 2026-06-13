package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 账号登录日志
 */
@Getter
@Setter
@TableName("xy_account_login_logs")
public class XyAccountLoginLog extends BaseEntity {

    /** 所属用户ID */
    private Long ownerId;

    /** 账号ID */
    private Long accountId;

    /** 账号标识 */
    private String accountIdentifier;

    /** 用户名 */
    private String username;

    /** 触发原因 */
    private String triggerReason;

    /** 登录状态 */
    private String loginStatus;

    /** 失败原因 */
    private String failureReason;

    /** 错误信息 */
    private String errorMessage;

    /** 更新的Cookie名称 */
    private String updatedCookieNames;

    /** 耗时（毫秒） */
    private Integer durationMs;
}
