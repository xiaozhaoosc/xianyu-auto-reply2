package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * Token缓存
 */
@Getter
@Setter
@TableName("xy_token_cache")
public class XyTokenCache extends BaseEntity {

    /** 用户ID */
    private String userId;

    /** Token值 */
    private String token;

    /** 设备ID */
    private String deviceId;

    /** 过期时间 */
    private LocalDateTime expireAt;
}
