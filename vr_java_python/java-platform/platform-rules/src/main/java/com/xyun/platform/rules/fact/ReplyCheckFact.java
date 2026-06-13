package com.xyun.platform.rules.fact;

import lombok.Getter;
import lombok.Setter;

/**
 * 回复检查事实 — Drools 规则引擎输入
 */
@Getter
@Setter
public class ReplyCheckFact {
    /** 账号ID */
    private String accountId;
    /** 买家ID */
    private String buyerId;
    /** 商品ID */
    private String itemId;
    /** 收到的消息 */
    private String message;
    /** 命中的关键词 */
    private String matchedKeyword;
    /** 回复策略: keyword/ai/default/none */
    private String replyStrategy;
    /** 回复内容 */
    private String replyContent;
}
