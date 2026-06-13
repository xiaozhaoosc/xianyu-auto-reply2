package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 闲鱼AI聊天消息实体
 */
@Getter
@Setter
@TableName("xy_ai_chat_messages")
public class XyAiChatMessage extends BaseEntity {

    /** 会话ID */
    @TableField("chat_id")
    private String chatId;

    /** Cookie标识 */
    @TableField("cookie_id")
    private String cookieId;

    /** 用户ID */
    @TableField("user_id")
    private String userId;

    /** 商品ID */
    @TableField("item_id")
    private String itemId;

    /** 角色：user / assistant / system */
    private String role;

    /** 消息内容 */
    private String content;

    /** 意图识别结果 */
    private String intent;
}
