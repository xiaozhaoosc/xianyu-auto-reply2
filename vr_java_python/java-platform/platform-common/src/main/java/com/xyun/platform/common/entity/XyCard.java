package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 闲鱼发卡实体
 */
@Getter
@Setter
@TableName(value = "xy_cards", autoResultMap = true)
public class XyCard extends BaseEntity {

    /** 所属用户ID */
    @TableField("user_id")
    private Long userId;

    /** 关联商品ID */
    @TableField("item_id")
    private String itemId;

    /** 卡密名称 */
    private String name;

    /** 卡密类型 */
    private String type;

    /** 卡密描述 */
    private String description;

    /** 是否启用 */
    private Boolean enabled;

    /** 发卡延迟秒数 */
    @TableField("delay_seconds")
    private Integer delaySeconds;

    /** 已发货数量 */
    @TableField("delivery_count")
    private Integer deliveryCount;

    /** 价格 */
    private String price;

    /** 是否可对接 */
    @TableField("is_dockable")
    private Boolean isDockable;

    /** 手续费支付方 */
    @TableField("fee_payer")
    private String feePayer;

    /** 最低价格 */
    @TableField("min_price")
    private String minPrice;

    /** 对接可见性 */
    @TableField("dock_visibility")
    private String dockVisibility;

    /** 是否多规格 */
    @TableField("is_multi_spec")
    private Boolean isMultiSpec;

    /** 规格名称 */
    @TableField("spec_name")
    private String specName;

    /** 规格值 */
    @TableField("spec_value")
    private String specValue;

    /** API配置 */
    @TableField("api_config")
    private String apiConfig;

    /** 文本内容 */
    @TableField("text_content")
    private String textContent;

    /** 数据内容 */
    @TableField("data_content")
    private String dataContent;

    /** 图片地址 */
    @TableField("image_url")
    private String imageUrl;

    /** 多图地址（逗号分隔） */
    @TableField("image_urls")
    private String imageUrls;
}
