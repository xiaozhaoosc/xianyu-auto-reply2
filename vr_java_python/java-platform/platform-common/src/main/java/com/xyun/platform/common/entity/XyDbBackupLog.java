package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

/**
 * 数据库备份日志
 */
@Getter
@Setter
@TableName("xy_db_backup_log")
public class XyDbBackupLog extends BaseEntity {

    /** 备份状态 */
    private String status;

    /** 备份文件名 */
    private String fileName;

    /** 备份文件路径 */
    private String filePath;

    /** 备份文件大小（字节） */
    private Long fileSize;

    /** 备份表数量 */
    private Integer tableCount;

    /** 备份总行数 */
    private Long totalRows;

    /** 备份耗时（毫秒） */
    private Integer durationMs;

    /** 错误信息 */
    private String errorMessage;
}
