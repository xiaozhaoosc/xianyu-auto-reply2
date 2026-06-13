package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 发布日志
 */
@Getter
@Setter
@TableName("xy_publish_logs")
public class XyPublishLog extends BaseEntity {

    /** 用户ID */
    private Long userId;

    /** 账号ID */
    private String accountId;

    /** 商品标题 */
    private String title;

    /** 商品描述 */
    private String description;

    /** 商品价格 */
    private String price;

    /** 素材ID */
    private Long materialId;

    /** 批次ID */
    private String batchId;

    /** 发布状态 */
    private String status;

    /** 商品链接 */
    private String itemUrl;

    /** 商品ID */
    private String itemId;

    /** 错误信息 */
    private String errorMessage;

    /** 解析后的地址ID */
    private Long resolvedAddressId;

    /** 解析后的地址文本 */
    private String resolvedAddressText;

    /** 地址来源 */
    private String addressSource;
}
