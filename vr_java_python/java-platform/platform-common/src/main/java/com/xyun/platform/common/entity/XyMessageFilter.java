package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 消息过滤规则
 */
@Getter
@Setter
@TableName("xy_message_filters")
public class XyMessageFilter extends BaseEntity {

    /** 账号ID */
    private String accountId;

    /** 过滤关键词 */
    private String keyword;

    /** 过滤类型 */
    private String filterType;

    /** 是否启用 */
    private Boolean enabled;
}
