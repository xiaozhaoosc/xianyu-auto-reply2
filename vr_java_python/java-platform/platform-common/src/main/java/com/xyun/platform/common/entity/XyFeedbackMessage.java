package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 反馈消息实体
 */
@Getter
@Setter
@TableName("xy_feedback_messages")
public class XyFeedbackMessage extends BaseEntity {

    /** 所属反馈 ID */
    private Long feedbackId;

    /** 发送用户 ID */
    private Long userId;

    /** 消息内容 */
    private String content;

    /** 是否为管理员消息 */
    private Boolean isAdmin;
}
