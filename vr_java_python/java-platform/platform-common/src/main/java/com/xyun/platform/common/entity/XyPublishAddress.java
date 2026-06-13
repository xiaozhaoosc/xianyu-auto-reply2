package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 发布地址
 */
@Getter
@Setter
@TableName("xy_publish_addresses")
public class XyPublishAddress extends BaseEntity {

    /** 地址名称 */
    private String name;

    /** 搜索关键词 */
    private String searchKeyword;

    /** 预期文本 */
    private String expectedText;

    /** 关联账号ID */
    private String accountId;

    /** 权重 */
    private Integer weight;

    /** 排序序号 */
    private Integer sortOrder;

    /** 是否启用 */
    private Boolean isEnabled;

    /** 使用次数 */
    private Integer useCount;

    /** 最后使用时间 */
    private LocalDateTime lastUsedAt;

    /** 创建人ID */
    private Long createdBy;

    /** 备注 */
    private String remark;
}
