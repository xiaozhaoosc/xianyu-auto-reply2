package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 闲鱼卡密-商品关联实体
 */
@Getter
@Setter
@TableName("xy_card_item_relations")
public class XyCardItemRelation extends BaseEntity {

    /** 所属用户ID */
    @TableField("user_id")
    private Long userId;

    /** 卡密ID */
    @TableField("card_id")
    private Long cardId;

    /** 商品ID */
    @TableField("item_id")
    private String itemId;

    /** 来源 */
    private String source;

    /** 对接记录ID */
    @TableField("dock_record_id")
    private Long dockRecordId;
}
