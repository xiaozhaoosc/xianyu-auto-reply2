package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 共享扫码会话实体
 */
@Getter
@Setter
@TableName("xy_shared_scan_sessions")
public class XySharedScanSession extends BaseEntity {

    /** 会话标识 */
    private String sessionId;

    /** 所有者用户 ID */
    private Long ownerId;

    /** 所有者用户名 */
    private String ownerUsername;

    /** 会话状态 */
    private String status;

    /** 过期时间 */
    private LocalDateTime expiresAt;
}
