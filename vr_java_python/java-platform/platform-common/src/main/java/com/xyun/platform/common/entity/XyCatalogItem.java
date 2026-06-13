package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import lombok.Getter;
import lombok.Setter;

/**
 * 闲鱼商品目录项实体
 */
@Getter
@Setter
@TableName(value = "xy_catalog_items", autoResultMap = true)
public class XyCatalogItem extends BaseEntity {

    /** 所属用户ID */
    @TableField("owner_id")
    private Long ownerId;

    /** 所属账号ID */
    @TableField("account_id")
    private Long accountId;

    /** 商品ID */
    @TableField("item_id")
    private String itemId;

    /** 商品标题 */
    private String title;

    /** 商品价格 */
    private String price;

    /** AI提示词 */
    @TableField("ai_prompt")
    private String aiPrompt;

    /** 是否已擦亮 */
    @TableField("is_polished")
    private Boolean isPolished;

    /** 元数据（JSON） */
    @TableField(typeHandler = JacksonTypeHandler.class)
    private String metadata;
}
