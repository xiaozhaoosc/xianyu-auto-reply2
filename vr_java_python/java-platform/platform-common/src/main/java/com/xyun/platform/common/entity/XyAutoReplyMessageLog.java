package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 自动回复消息日志
 */
@Getter
@Setter
@TableName("xy_auto_reply_message_logs")
public class XyAutoReplyMessageLog extends BaseEntity {

    /** 所属用户ID */
    private Long ownerId;

    /** 所属用户名 */
    private String ownerUsername;

    /** 账号PK */
    private Long accountPk;

    /** 账号ID */
    private String accountId;

    /** 账号名称 */
    private String accountName;

    /** 聊天ID */
    private String chatId;

    /** 商品ID */
    private String itemId;

    /** 商品标题 */
    private String itemTitle;

    /** 来源消息ID */
    private String sourceMessageId;

    /** 发送者用户ID */
    private String senderUserId;

    /** 发送者用户名 */
    private String senderUserName;

    /** 来源消息内容 */
    private String sourceMessage;

    /** 来源消息时间 */
    private LocalDateTime sourceMessageTime;

    /** 处理状态 */
    private String processStatus;

    /** 决策原因 */
    private String decisionReason;

    /** 回复策略 */
    private String replyStrategy;

    /** 回复模式 */
    private String replyMode;

    /** 匹配关键词 */
    private String matchedKeyword;

    /** 匹配规则类型 */
    private String matchedRuleType;

    /** 默认回复范围 */
    private String defaultReplyScope;

    /** 是否默认回复仅一次 */
    private Boolean defaultReplyOnce;

    /** AI模型名称 */
    private String aiModelName;

    /** AI供应商名称 */
    private String aiProviderName;

    /** 回复文本 */
    private String replyText;

    /** 回复图片URL */
    private String replyImageUrl;

    /** 回复片段（JSON） */
    private String replySegments;

    /** 错误信息 */
    private String errorMessage;

    /** 发送状态 */
    private String sendStatus;

    /** 发送失败原因 */
    private String sendFailReason;

    /** 原始消息JSON */
    private String rawMessageJson;

    /** 上下文快照（JSON） */
    private String contextSnapshot;

    /** 发送结果JSON */
    private String sendResultJson;
}
