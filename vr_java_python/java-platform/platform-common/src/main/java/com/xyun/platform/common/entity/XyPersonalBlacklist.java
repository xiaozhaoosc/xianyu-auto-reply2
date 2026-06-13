package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 个人黑名单
 */
@Getter
@Setter
@TableName("xy_personal_blacklist")
public class XyPersonalBlacklist extends BaseEntity {

    /** 所属用户ID */
    private Long ownerId;

    /** 账号ID */
    private String accountId;

    /** 买家ID */
    private String buyerId;

    /** 买家昵称 */
    private String buyerNick;

    /** 商品ID */
    private String itemId;

    /** 拉黑原因 */
    private String reason;

    /** 是否启用 */
    private Boolean isEnabled;
}
