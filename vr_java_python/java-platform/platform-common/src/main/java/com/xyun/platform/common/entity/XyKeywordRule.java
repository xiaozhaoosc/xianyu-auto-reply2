package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 闲鱼关键词规则实体
 */
@Getter
@Setter
@TableName("xy_keyword_rules")
public class XyKeywordRule extends BaseEntity {

    /** 所属用户ID */
    @TableField("owner_id")
    private Long ownerId;

    /** 所属账号ID */
    @TableField("account_id")
    private Long accountId;

    /** 关键词 */
    private String keyword;

    /** 回复内容 */
    @TableField("reply_content")
    private String replyContent;

    /** 回复类型 */
    @TableField("reply_type")
    private String replyType;

    /** 回复图片地址 */
    @TableField("image_url")
    private String imageUrl;

    /** 关联商品ID */
    @TableField("item_id")
    private String itemId;

    /** 优先级（数值越大优先级越高） */
    private Integer priority;

    /** 是否启用 */
    @TableField("is_active")
    private Boolean isActive;
}
