package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 自动评价配置
 */
@Getter
@Setter
@TableName("xy_auto_rate_configs")
public class XyAutoRateConfig extends BaseEntity {

    /** 账号ID */
    private String accountId;

    /** 是否启用 */
    private Boolean enabled;

    /** 评价类型 */
    private String rateType;

    /** 评价文本内容 */
    private String textContent;

    /** 接口地址 */
    private String apiUrl;
}
