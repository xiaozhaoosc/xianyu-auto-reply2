package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 定时任务配置
 */
@Getter
@Setter
@TableName("xy_scheduled_tasks")
public class XyScheduledTask extends BaseEntity {

    /** 任务编码 */
    private String taskCode;

    /** 任务名称 */
    private String taskName;

    /** 执行间隔（秒） */
    private Integer intervalSeconds;

    /** 是否启用 */
    private Boolean enabled;

    /** 任务描述 */
    private String description;
}
