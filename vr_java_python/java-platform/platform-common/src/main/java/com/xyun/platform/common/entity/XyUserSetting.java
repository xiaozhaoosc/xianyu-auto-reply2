package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 用户设置
 */
@Getter
@Setter
@TableName("xy_user_settings")
public class XyUserSetting extends BaseEntity {

    /** 用户ID */
    private Integer userId;

    /** 设置键 */
    private String key;

    /** 设置值 */
    private String value;

    /** 设置描述 */
    private String description;
}
