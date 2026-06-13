package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 激活码日志实体
 */
@Getter
@Setter
@TableName("xy_activation_logs")
public class XyActivationLog extends BaseEntity {

    /** 机器标识 */
    private String machineId;

    /** 激活码类型 */
    private String codeType;

    /** 生成的激活码 */
    private String generatedCode;

    /** 有效天数 */
    private Integer days;

    /** IP 地址 */
    private String ipAddress;
}
