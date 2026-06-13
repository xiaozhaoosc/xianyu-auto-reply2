package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 闲鱼默认回复实体
 */
@Getter
@Setter
@TableName("xy_default_replies")
public class XyDefaultReply extends BaseEntity {

    /** 账号ID */
    @TableField("account_id")
    private String accountId;

    /** 商品ID */
    @TableField("item_id")
    private String itemId;

    /** 是否启用 */
    private Boolean enabled;

    /** 回复类型 */
    @TableField("reply_type")
    private String replyType;

    /** 回复内容 */
    @TableField("reply_content")
    private String replyContent;

    /** 回复图片地址 */
    @TableField("reply_image")
    private String replyImage;

    /** API地址 */
    @TableField("api_url")
    private String apiUrl;

    /** API超时时间（秒） */
    @TableField("api_timeout")
    private Integer apiTimeout;

    /** 是否仅回复一次 */
    @TableField("reply_once")
    private Boolean replyOnce;
}
