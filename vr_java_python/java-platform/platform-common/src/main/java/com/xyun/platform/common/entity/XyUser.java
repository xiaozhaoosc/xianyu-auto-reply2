package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 闲鱼用户实体
 */
@Getter
@Setter
@TableName(value = "xy_users", autoResultMap = true)
public class XyUser extends BaseEntity {

    /** 外部标识ID（第三方系统用户ID） */
    @TableField("external_id")
    private String externalId;

    /** 用户名 */
    private String username;

    /** 邮箱 */
    private String email;

    /** 手机号 */
    private String phone;

    /** 密码哈希 */
    @TableField("password_hash")
    private String passwordHash;

    /** 状态：ACTIVE-活跃 / INACTIVE-未激活 / SUSPENDED-封禁 / DELETED-已删除 */
    private String status;

    /** 角色：ADMIN-管理员 / OPERATOR-运营 / MEMBER-普通成员 */
    private String role;

    /** 账号数量上限 */
    @TableField("account_limit")
    private Integer accountLimit;

    /** 最后登录时间 */
    @TableField("last_login_at")
    private LocalDateTime lastLoginAt;

    /** 连续登录失败次数 */
    @TableField("login_fail_count")
    private Integer loginFailCount;

    /** 登录锁定截止时间 */
    @TableField("login_locked_until")
    private LocalDateTime loginLockedUntil;

    /** 对接编码 */
    @TableField("dock_code")
    private String dockCode;

    /** 密钥 */
    @TableField("secret_key")
    private String secretKey;
}
