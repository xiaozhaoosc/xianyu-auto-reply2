package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 闲鱼爬取商品
 */
@Getter
@Setter
@TableName("xy_goofish_crawl_items")
public class XyGoofishCrawlItem extends BaseEntity {

    /** 所属任务ID */
    private Long jobId;

    /** 商品ID */
    private String itemId;

    /** 商品标题 */
    private String title;

    /** 商品价格 */
    private String price;

    /** 商品地区 */
    private String area;

    /** 卖家名称 */
    private String sellerName;

    /** 商品链接 */
    private String itemUrl;

    /** 主图URL */
    private String mainImage;

    /** 发布时间 */
    private String publishTime;

    /** 想要人数 */
    private Integer wantCount;

    /** 浏览次数 */
    private Integer viewCount;

    /** 商品描述 */
    private String description;

    /** 详情抓取错误 */
    private String detailError;

    /** 原始JSON数据 */
    private String rawJson;

    /** 抓取时间 */
    private LocalDateTime fetchedAt;
}
