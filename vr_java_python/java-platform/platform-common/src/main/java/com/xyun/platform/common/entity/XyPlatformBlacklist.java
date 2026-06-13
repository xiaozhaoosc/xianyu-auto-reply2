package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 平台黑名单
 */
@Getter
@Setter
@TableName("xy_platform_blacklist")
public class XyPlatformBlacklist extends BaseEntity {

    /** 所属用户ID */
    private Long ownerId;

    /** 买家ID */
    private String buyerId;

    /** 买家昵称 */
    private String buyerNick;
}
