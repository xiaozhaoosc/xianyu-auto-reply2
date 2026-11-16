package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 系统设置（主键为 key，非自增 ID）
 */
@Getter
@Setter
@TableName(value = "xy_system_settings", autoResultMap = true)
public class XySystemSetting implements Serializable {

    /** 设置键（主键，手动输入）— key 是 MySQL 保留字，需反引号转义 */
    @TableId(value = "`key`", type = IdType.INPUT)
    private String key;

    /** 设置值 — value 是 MySQL 保留字，需反引号转义 */
    @TableField(value = "`value`")
    private String value;

    /** 设置描述 */
    private String description;

    /** 更新时间 */
    private LocalDateTime updatedAt;
}
