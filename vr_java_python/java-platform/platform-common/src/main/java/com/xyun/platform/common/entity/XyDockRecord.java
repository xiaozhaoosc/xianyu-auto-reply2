package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 对接记录
 */
@Getter
@Setter
@TableName("xy_dock_records")
public class XyDockRecord extends BaseEntity {

    /** 用户ID */
    private Long userId;

    /** 卡片ID */
    private Long cardId;

    /** 对接名称 */
    private String dockName;

    /** 加价金额 */
    private String markupAmount;

    /** 备注 */
    private String remark;

    /** 发货数量 */
    private Integer deliveryCount;

    /** 状态 */
    private Boolean status;

    /** 禁用原因 */
    private String disableReason;

    /** 层级 */
    private Integer level;

    /** 上级对接ID */
    private Long parentDockId;

    /** 来源用户ID */
    private Long sourceUserId;

    /** 允许下级对接 */
    private Boolean allowSubDock;

    /** 下级对接价格 */
    private String subDockPrice;

    /** 下级对接可见性 */
    private String subDockVisibility;
}
