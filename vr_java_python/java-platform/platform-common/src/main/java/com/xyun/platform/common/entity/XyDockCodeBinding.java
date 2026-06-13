package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 对接码绑定
 */
@Getter
@Setter
@TableName("xy_dock_code_bindings")
public class XyDockCodeBinding extends BaseEntity {

    /** 用户ID */
    private Long userId;

    /** 对接码 */
    private String dockCode;

    /** 目标用户ID */
    private Long targetUserId;
}
