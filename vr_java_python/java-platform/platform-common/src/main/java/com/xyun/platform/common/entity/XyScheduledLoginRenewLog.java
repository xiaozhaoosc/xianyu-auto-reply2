package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 定时登录续期日志
 */
@Getter
@Setter
@TableName("xy_scheduled_login_renew_log")
public class XyScheduledLoginRenewLog extends BaseEntity {

    /** 批次ID */
    private String batchId;

    /** 账号ID */
    private String accountId;

    /** 执行状态 */
    private String status;

    /** 错误信息 */
    private String errorMessage;
}
