package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 聊天快捷短语实体
 */
@Getter
@Setter
@TableName("xy_chat_quick_phrases")
public class XyChatQuickPhrase extends BaseEntity {

    /** 所属用户 ID */
    private Long ownerId;

    /** 短语标题 */
    private String title;

    /** 短语内容 */
    private String content;

    /** 排序序号 */
    private Integer sortOrder;
}
