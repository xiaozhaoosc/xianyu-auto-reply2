package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.IdType;
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
@TableName("xy_system_settings")
public class XySystemSetting implements Serializable {

    /** 设置键（主键，手动输入） */
    @TableId(type = IdType.INPUT)
    private String key;

    /** 设置值 */
    private String value;

    /** 设置描述 */
    private String description;

    /** 更新时间 */
    private LocalDateTime updatedAt;
}
