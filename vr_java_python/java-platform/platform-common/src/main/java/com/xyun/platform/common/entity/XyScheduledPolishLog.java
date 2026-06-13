package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 定时擦亮日志
 */
@Getter
@Setter
@TableName("xy_scheduled_polish_log")
public class XyScheduledPolishLog extends BaseEntity {

    /** 批次ID */
    private String batchId;

    /** 账号ID */
    private String accountId;

    /** 商品ID */
    private String itemId;

    /** 执行状态 */
    private String status;

    /** 错误信息 */
    private String errorMessage;
}
