package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 定时API Cookie续期日志
 */
@Getter
@Setter
@TableName("xy_scheduled_api_cookie_renew_log")
public class XyScheduledApiCookieRenewLog extends BaseEntity {

    /** 批次ID */
    private String batchId;

    /** 账号ID */
    private String accountId;

    /** 执行状态 */
    private String status;

    /** 更新的Cookie数量 */
    private Integer updatedCookieCount;

    /** 更新的Cookie名称 */
    private String updatedCookieNames;

    /** 响应内容 */
    private String responseContent;

    /** 错误信息 */
    private String errorMessage;
}
