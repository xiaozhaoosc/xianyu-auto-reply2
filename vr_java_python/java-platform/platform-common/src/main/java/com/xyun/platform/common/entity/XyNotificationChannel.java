package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 通知渠道实体
 */
@Getter
@Setter
@TableName("xy_notification_channels")
public class XyNotificationChannel extends BaseEntity {

    /** 所属用户 ID */
    private Long ownerId;

    /** 渠道名称 */
    private String name;

    /** 渠道类型 */
    private String channelType;

    /** 渠道配置（JSON 格式存储） */
    private String config;

    /** 是否启用 */
    private Boolean enabled;
}
