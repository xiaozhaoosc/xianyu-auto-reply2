package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * Cookie刷新调度
 */
@Getter
@Setter
@TableName("xy_cookie_refresh_schedules")
public class XyCookieRefreshSchedule extends BaseEntity {

    /** 账号ID */
    private String accountId;

    /** 过期时间 */
    private LocalDateTime expireAt;

    /** 上次刷新时间 */
    private LocalDateTime lastRefreshAt;

    /** 上次刷新状态 */
    private String lastStatus;

    /** 上次错误信息 */
    private String lastErrorMessage;
}
