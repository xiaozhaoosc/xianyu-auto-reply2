package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDate;

/**
 * 广告实体
 */
@Getter
@Setter
@TableName("xy_advertisements")
public class XyAdvertisement extends BaseEntity {

    /** 用户 ID */
    private Long userId;

    /** 广告标题 */
    private String title;

    /** 广告内容 */
    private String content;

    /** 广告链接 */
    private String link;

    /** 过期日期 */
    private LocalDate expireDate;

    /** 广告图片地址 */
    private String imageUrl;

    /** 广告类型 */
    private String adType;

    /** 购买月数 */
    private Integer months;

    /** 总金额 */
    private String totalAmount;

    /** 状态 */
    private String status;
}
