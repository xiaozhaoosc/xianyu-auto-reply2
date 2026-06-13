package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 定时Cookie刷新日志
 */
@Getter
@Setter
@TableName("xy_scheduled_cookies_refresh_log")
public class XyScheduledCookiesRefreshLog extends BaseEntity {

    /** 批次ID */
    private String batchId;

    /** 账号ID */
    private String accountId;

    /** 执行状态 */
    private String status;

    /** 更新的Cookie数量 */
    private Integer updatedCookieCount;

    /** 下次过期时间 */
    private LocalDateTime nextExpireAt;

    /** 错误信息 */
    private String errorMessage;
}
