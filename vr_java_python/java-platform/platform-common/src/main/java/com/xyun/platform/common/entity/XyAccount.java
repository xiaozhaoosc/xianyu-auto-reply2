package com.xyun.platform.common.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 闲鱼账号实体
 */
@Getter
@Setter
@TableName(value = "xy_accounts", autoResultMap = true)
public class XyAccount extends BaseEntity {

    /** 所属用户ID */
    @TableField("owner_id")
    private Long ownerId;

    /** 账号标识 */
    @TableField("account_id")
    private String accountId;

    /** 显示名称 */
    @TableField("display_name")
    private String displayName;

    /** UNB标识 */
    private String unb;

    /** Cookie凭证 */
    private String cookie;

    /** 登录方式 */
    @TableField("login_method")
    private String loginMethod;

    /** 账号状态 */
    private String status;

    /** 登录用户名 */
    private String username;

    /** 登录密码 */
    @TableField("login_password")
    private String loginPassword;

    /** 备注 */
    private String remark;

    /** 暂停时长（秒） */
    @TableField("pause_duration")
    private Integer pauseDuration;

    /** 是否自动确认收货 */
    @TableField("auto_confirm")
    private Boolean autoConfirm;

    /** 是否显示浏览器 */
    @TableField("show_browser")
    private Boolean showBrowser;

    /** 元数据（JSON） */
    @TableField(typeHandler = JacksonTypeHandler.class)
    private String metadata;

    /** 最后登录时间 */
    @TableField("last_login_at")
    private LocalDateTime lastLoginAt;

    /** 最后刷新时间 */
    @TableField("last_refresh_at")
    private LocalDateTime lastRefreshAt;

    /** 代理类型 */
    @TableField("proxy_type")
    private String proxyType;

    /** 代理主机 */
    @TableField("proxy_host")
    private String proxyHost;

    /** 代理端口 */
    @TableField("proxy_port")
    private Integer proxyPort;

    /** 代理用户名 */
    @TableField("proxy_user")
    private String proxyUser;

    /** 代理密码 */
    @TableField("proxy_pass")
    private String proxyPass;

    /** 消息过期时间（秒） */
    @TableField("message_expire_time")
    private Integer messageExpireTime;

    /** 回复延迟秒数 */
    @TableField("reply_delay_seconds")
    private Integer replyDelaySeconds;

    /** 禁用原因 */
    @TableField("disable_reason")
    private String disableReason;

    /** 是否开启定时发货 */
    @TableField("scheduled_redelivery")
    private Boolean scheduledRedelivery;

    /** 是否开启定时上架 */
    @TableField("scheduled_rate")
    private Boolean scheduledRate;

    /** 是否自动擦亮 */
    @TableField("auto_polish")
    private Boolean autoPolish;

    /** 发送前是否确认 */
    @TableField("confirm_before_send")
    private Boolean confirmBeforeSend;

    /** 确认前是否发送 */
    @TableField("send_before_confirm")
    private Boolean sendBeforeConfirm;

    /** 是否自动送红花 */
    @TableField("auto_red_flower")
    private Boolean autoRedFlower;

    /** 是否禁用发货 */
    @TableField("delivery_disabled")
    private Boolean deliveryDisabled;

    /** 发货禁用原因 */
    @TableField("delivery_disabled_reason")
    private String deliveryDisabledReason;

    /** 是否自动关闭订单 */
    @TableField("auto_close_order")
    private Boolean autoCloseOrder;

    /** 关闭订单后仅发卡 */
    @TableField("delivery_only_card_after_close")
    private Boolean deliveryOnlyCardAfterClose;

    /** 发货禁用排除商品ID列表（JSON） */
    @TableField(value = "delivery_disabled_excluded_items", typeHandler = JacksonTypeHandler.class)
    private String deliveryDisabledExcludedItems;

    /** AI回复是否屏蔽已下单用户 */
    @TableField("ai_reply_block_ordered_users")
    private Boolean aiReplyBlockOrderedUsers;
}
