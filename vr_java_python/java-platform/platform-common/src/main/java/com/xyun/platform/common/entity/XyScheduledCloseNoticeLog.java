package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 定时关闭通知日志
 */
@Getter
@Setter
@TableName("xy_scheduled_close_notice_log")
public class XyScheduledCloseNoticeLog extends BaseEntity {

    /** 批次ID */
    private String batchId;

    /** 账号ID */
    private String accountId;

    /** 执行状态 */
    private String status;

    /** 错误信息 */
    private String errorMessage;
}
