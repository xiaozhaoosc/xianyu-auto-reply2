package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import lombok.Getter;
import lombok.Setter;

/**
 * 闲鱼发货拦截规则实体
 */
@Getter
@Setter
@TableName(value = "xy_delivery_block_rules", autoResultMap = true)
public class XyDeliveryBlockRule extends BaseEntity {

    /** 账号ID */
    @TableField("account_id")
    private String accountId;

    /** 规则编码 */
    @TableField("rule_code")
    private String ruleCode;

    /** 是否启用 */
    private Boolean enabled;

    /** 优先级（数值越大优先级越高） */
    private Integer priority;

    /** 拦截原因 */
    @TableField("block_reason")
    private String blockReason;

    /** 是否自动关闭订单 */
    @TableField("auto_close_order")
    private Boolean autoCloseOrder;

    /** 关闭后仅发卡 */
    @TableField("only_card_after_close")
    private Boolean onlyCardAfterClose;

    /** 排除商品ID列表（JSON） */
    @TableField(value = "excluded_item_ids", typeHandler = JacksonTypeHandler.class)
    private String excludedItemIds;

    /** 规则配置（JSON） */
    @TableField(typeHandler = JacksonTypeHandler.class)
    private String config;
}
