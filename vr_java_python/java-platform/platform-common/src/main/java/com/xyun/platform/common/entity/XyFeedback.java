package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 反馈实体
 */
@Getter
@Setter
@TableName("xy_feedbacks")
public class XyFeedback extends BaseEntity {

    /** 用户 ID */
    private Long userId;

    /** Cookie 标识 */
    private String cookieId;

    /** 反馈标题 */
    private String title;

    /** 反馈内容 */
    private String content;

    /** 反馈类型 */
    private String feedbackType;

    /** 反馈图片（JSON 格式存储） */
    private String images;

    /** 是否已解决 */
    private Boolean isResolved;

    /** 解决时间 */
    private LocalDateTime resolvedAt;

    /** 管理员回复 */
    private String adminReply;
}
