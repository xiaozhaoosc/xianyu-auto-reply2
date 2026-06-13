package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 闲鱼爬取任务
 */
@Getter
@Setter
@TableName("xy_goofish_crawl_jobs")
public class XyGoofishCrawlJob extends BaseEntity {

    /** 所属用户ID */
    private Long ownerId;

    /** Cookie ID */
    private String cookieId;

    /** 搜索关键词 */
    private String keyword;

    /** 爬取间隔（秒） */
    private Integer intervalSeconds;

    /** 起始页码 */
    private Integer startPage;

    /** 爬取页数 */
    private Integer pages;

    /** 每页数量 */
    private Integer pageSize;

    /** 是否抓取详情 */
    private Boolean fetchDetail;

    /** 详情抓取上限 */
    private Integer detailLimit;

    /** 是否启用 */
    private Boolean enabled;

    /** 上次执行时间 */
    private LocalDateTime lastRunAt;

    /** 上次错误信息 */
    private String lastError;
}
