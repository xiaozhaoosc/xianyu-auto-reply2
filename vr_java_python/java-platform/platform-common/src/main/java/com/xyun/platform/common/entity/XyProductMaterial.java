package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.math.BigDecimal;

/**
 * 商品素材实体
 */
@Getter
@Setter
@TableName("xy_product_materials")
public class XyProductMaterial extends BaseEntity {

    /** 用户 ID */
    private Long userId;

    /** 商品标题 */
    private String title;

    /** 商品描述 */
    private String description;

    /** 售价 */
    private BigDecimal price;

    /** 原价 */
    private BigDecimal originalPrice;

    /** 分类 */
    private String category;

    /** 商品图片（JSON 格式存储） */
    private String images;

    /** 发货方式 */
    private String deliveryMethod;

    /** 邮费 */
    private BigDecimal postage;

    /** 收货地址 */
    private String address;

    /** 品牌 */
    private String brand;

    /** 成色/状况 */
    private String condition;

    /** 备注 */
    private String remark;
}
