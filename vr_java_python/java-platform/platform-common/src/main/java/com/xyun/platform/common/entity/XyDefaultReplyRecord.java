package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 默认回复记录
 */
@Getter
@Setter
@TableName("xy_default_reply_records")
public class XyDefaultReplyRecord extends BaseEntity {

    /** 账号ID */
    private String accountId;

    /** 商品ID */
    private String itemId;

    /** 用户ID */
    private String userId;
}
