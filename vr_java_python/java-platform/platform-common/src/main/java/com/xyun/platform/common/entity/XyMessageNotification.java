package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 消息通知配置实体
 */
@Getter
@Setter
@TableName("xy_message_notifications")
public class XyMessageNotification extends BaseEntity {

    /** 所属用户 ID */
    private Long ownerId;

    /** 账户主键 */
    private Long accountPk;

    /** 账户标识 */
    private String accountIdentifier;

    /** 通知渠道 ID */
    private Long channelId;

    /** 是否启用 */
    private Boolean enabled;
}
