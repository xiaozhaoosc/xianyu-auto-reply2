package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 确认收货消息配置
 */
@Getter
@Setter
@TableName("xy_confirm_receipt_messages")
public class XyConfirmReceiptMessage extends BaseEntity {

    /** 账号ID */
    private String accountId;

    /** 是否启用 */
    private Boolean enabled;

    /** 消息内容 */
    private String messageContent;

    /** 消息图片 */
    private String messageImage;
}
