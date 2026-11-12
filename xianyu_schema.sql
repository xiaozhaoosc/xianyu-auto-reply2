-- ============================================================
-- Xianyu Auto-Reply Complete Database Schema
-- Database: xianyu_data (MySQL 8.x, InnoDB, utf8mb4_unicode_ci)
-- Source: Production MySQL (dev-mysql:3306)
-- Generated: 2026-06-11
-- Total Tables: 54
-- ============================================================

-- ============================================================
-- 1. xy_users - 用户表
-- ============================================================
CREATE TABLE `xy_users` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `external_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '外部ID',
  `username` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱',
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手机号',
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希',
  `status` enum('ACTIVE','INACTIVE','SUSPENDED','DELETED') COLLATE utf8mb4_unicode_ci DEFAULT 'ACTIVE' COMMENT '用户状态',
  `role` enum('ADMIN','OPERATOR','MEMBER') COLLATE utf8mb4_unicode_ci DEFAULT 'MEMBER' COMMENT '用户角色',
  `account_limit` int DEFAULT NULL COMMENT '可添加账号数量',
  `last_login_at` datetime DEFAULT NULL COMMENT '最后登录时间',
  `login_fail_count` int DEFAULT '0' COMMENT '登录失败次数',
  `login_locked_until` datetime DEFAULT NULL COMMENT '登录锁定截止时间',
  `dock_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '对接码',
  `secret_key` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分销秘钥',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `dock_code` (`dock_code`),
  UNIQUE KEY `secret_key` (`secret_key`),
  KEY `idx_external_id` (`external_id`),
  KEY `idx_username` (`username`),
  KEY `idx_email` (`email`),
  KEY `idx_user_created` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================================
-- 2. xy_user_settings - 用户设置表
-- ============================================================
CREATE TABLE `xy_user_settings` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '设置ID',
  `user_id` int NOT NULL COMMENT '用户ID',
  `key` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设置键',
  `value` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设置值',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '设置描述',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_key` (`user_id`,`key`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户设置表';

-- ============================================================
-- 3. xy_system_settings - 系统设置表
-- ============================================================
CREATE TABLE `xy_system_settings` (
  `key` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设置键',
  `value` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设置值',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '设置描述',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统设置表';

-- ============================================================
-- 4. xy_accounts - 闲鱼账号表
-- ============================================================
CREATE TABLE `xy_accounts` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '账号ID',
  `owner_id` bigint NOT NULL COMMENT '所属用户ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号标识',
  `display_name` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '显示名称',
  `unb` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'UNB标识',
  `cookie` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Cookie信息',
  `login_method` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '登录方式',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT '账号状态',
  `username` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '登录用户名',
  `login_password` text COLLATE utf8mb4_unicode_ci COMMENT '登录密码',
  `remark` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `pause_duration` int DEFAULT '10' COMMENT '暂停时长(分钟)',
  `auto_confirm` tinyint(1) DEFAULT '0' COMMENT '自动确认发货',
  `show_browser` tinyint(1) DEFAULT '0' COMMENT '显示浏览器',
  `metadata` json DEFAULT NULL COMMENT '元数据',
  `last_login_at` datetime DEFAULT NULL COMMENT '最后登录时间',
  `last_refresh_at` datetime DEFAULT NULL COMMENT '最后刷新时间',
  `proxy_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'none' COMMENT '代理类型',
  `proxy_host` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '代理主机',
  `proxy_port` int DEFAULT NULL COMMENT '代理端口',
  `proxy_user` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '代理用户名',
  `proxy_pass` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '代理密码',
  `message_expire_time` int DEFAULT '3600' COMMENT '相同消息等待时间(秒)',
  `reply_delay_seconds` int DEFAULT '0' COMMENT '自动回复延迟时间(秒)',
  `disable_reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '禁用原因',
  `scheduled_redelivery` tinyint(1) NOT NULL DEFAULT '0' COMMENT '定时补发货开关',
  `scheduled_rate` tinyint(1) NOT NULL DEFAULT '0' COMMENT '定时补评价开关',
  `auto_polish` tinyint(1) NOT NULL DEFAULT '0' COMMENT '商品自动擦亮开关',
  `confirm_before_send` tinyint(1) NOT NULL DEFAULT '0' COMMENT '发货成功再发卡券开关',
  `send_before_confirm` tinyint(1) NOT NULL DEFAULT '0' COMMENT '卡券发送成功再确认发货开关',
  `auto_red_flower` tinyint(1) NOT NULL DEFAULT '0' COMMENT '自动求小红花开关',
  `delivery_disabled` tinyint(1) NOT NULL DEFAULT '0' COMMENT '禁止发货开关',
  `delivery_disabled_reason` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '禁止发货原因',
  `auto_close_order` tinyint(1) NOT NULL DEFAULT '0' COMMENT '主动关闭订单开关',
  `delivery_only_card_after_close` tinyint(1) NOT NULL DEFAULT '0' COMMENT '关闭订单后继续发货（只发卡券）',
  `delivery_disabled_excluded_items` json DEFAULT NULL COMMENT '禁止发货排除商品列表',
  `ai_reply_block_ordered_users` tinyint(1) NOT NULL DEFAULT '0' COMMENT '已下单用户禁止AI回复',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_owner_id` (`owner_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_unb` (`unb`),
  KEY `idx_account_created` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='闲鱼账号表';

-- ============================================================
-- 5. xy_account_login_logs - 账号登录日志表
-- ============================================================
CREATE TABLE `xy_account_login_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `owner_id` bigint DEFAULT NULL COMMENT '所属用户ID',
  `account_id` bigint DEFAULT NULL COMMENT '关联账号ID(xy_accounts.id)',
  `account_identifier` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '业务账号ID',
  `username` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '登录用户名快照',
  `trigger_reason` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '触发登录原因',
  `login_status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT 'failed' COMMENT '登录状态',
  `failure_reason` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '失败原因',
  `error_message` text COLLATE utf8mb4_unicode_ci COMMENT '详细错误消息',
  `updated_cookie_names` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '接口续期更新的Cookie字段名',
  `duration_ms` int DEFAULT NULL COMMENT '登录流程耗时(毫秒)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_all_owner_id` (`owner_id`),
  KEY `idx_all_account_id` (`account_id`),
  KEY `idx_all_login_status` (`login_status`),
  KEY `idx_all_identifier_status_created` (`account_identifier`,`login_status`,`created_at`),
  KEY `idx_all_owner_created` (`owner_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='账号登录日志表';

-- ============================================================
-- 6. xy_activation_logs - 激活码生成日志表
-- ============================================================
CREATE TABLE `xy_activation_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `machine_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '机器码',
  `code_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '类型',
  `generated_code` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '生成的激活码/续期码',
  `days` int NOT NULL COMMENT '有效天数',
  `ip_address` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '请求IP地址',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_machine_id` (`machine_id`),
  KEY `idx_code_type` (`code_type`),
  KEY `idx_machine_type_time` (`machine_id`,`code_type`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='激活码生成日志表';

-- ============================================================
-- 7. xy_advertisements - 广告表
-- ============================================================
CREATE TABLE `xy_advertisements` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '广告ID',
  `user_id` bigint NOT NULL COMMENT '申请用户ID',
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '广告标题',
  `content` text COLLATE utf8mb4_unicode_ci COMMENT '广告正文',
  `link` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '广告链接',
  `expire_date` date DEFAULT NULL COMMENT '到期日期',
  `image_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '图片URL',
  `ad_type` enum('carousel','text') COLLATE utf8mb4_unicode_ci DEFAULT 'text' COMMENT '广告类型',
  `months` int DEFAULT NULL COMMENT '购买月数',
  `total_amount` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '广告总金额',
  `status` enum('unpaid','pending','approved') COLLATE utf8mb4_unicode_ci DEFAULT 'unpaid' COMMENT '审核状态',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_ad_type` (`ad_type`),
  KEY `idx_expire_date` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='广告表';

-- ============================================================
-- 8. xy_agent_orders - 代理订单表
-- ============================================================
CREATE TABLE `xy_agent_orders` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '下单用户ID',
  `order_no` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '闲鱼订单号',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品ID',
  `card_id` bigint NOT NULL COMMENT '使用的卡券ID',
  `dock_record_id` bigint NOT NULL COMMENT '对接记录ID',
  `dock_level` int NOT NULL COMMENT '对接层级：1=一级，2=二级',
  `sale_price` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '售价',
  `dock_price` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '对接价格(拿货价)',
  `card_price` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '卡券成本(货主对接价)',
  `level2_cost` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '二级拿货价',
  `profit` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '0.00' COMMENT '利润',
  `fee_amount` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手续费金额',
  `fee_payer` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手续费承担方',
  `upstream_user_id` bigint DEFAULT NULL COMMENT '上级用户ID',
  `upstream_dock_record_id` bigint DEFAULT NULL COMMENT '上级对接记录ID',
  `owner_user_id` bigint DEFAULT NULL COMMENT '货主用户ID',
  `delivery_content` text COLLATE utf8mb4_unicode_ci COMMENT '发货内容',
  `buyer_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '买家ID',
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'delivered' COMMENT '状态',
  `settle_remark` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '结算备注',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_order_no` (`order_no`),
  KEY `idx_dock_record_id` (`dock_record_id`),
  KEY `idx_upstream_user_id` (`upstream_user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_agent_order_created` (`created_at`),
  KEY `idx_ao_upstream_status` (`upstream_user_id`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代理订单表';

-- ============================================================
-- 9. xy_ai_chat_messages - AI聊天消息表
-- ============================================================
CREATE TABLE `xy_ai_chat_messages` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  `chat_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '聊天ID',
  `cookie_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号标识',
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户ID',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商品ID',
  `role` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色(user/assistant)',
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '消息内容',
  `intent` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '意图(price/tech/default)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_chat_id` (`chat_id`),
  KEY `idx_cookie_id` (`cookie_id`),
  KEY `ix_ai_chat_messages_chat_cookie` (`chat_id`,`cookie_id`),
  KEY `ix_ai_chat_messages_intent` (`cookie_id`,`intent`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI聊天消息表';

-- ============================================================
-- 10. xy_announcements - 公告信息表
-- ============================================================
CREATE TABLE `xy_announcements` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '公告ID',
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '公告标题',
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '公告内容',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否已删除',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='公告信息表';

-- ============================================================
-- 11. xy_auto_rate_configs - 自动评价配置表
-- ============================================================
CREATE TABLE `xy_auto_rate_configs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号ID',
  `enabled` tinyint(1) DEFAULT '0' COMMENT '是否启用自动评价',
  `rate_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'text' COMMENT '评价类型',
  `text_content` text COLLATE utf8mb4_unicode_ci COMMENT '固定评价文字内容',
  `api_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API地址',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自动评价配置表';

-- ============================================================
-- 12. xy_auto_reply_message_logs - 自动回复消息日志表
-- ============================================================
CREATE TABLE `xy_auto_reply_message_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `owner_id` bigint DEFAULT NULL COMMENT '所属系统用户ID',
  `owner_username` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '所属系统用户名',
  `account_pk` bigint DEFAULT NULL COMMENT '账号主键ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '闲鱼账号ID',
  `account_name` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '闲鱼账号显示名称',
  `chat_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '聊天会话ID',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商品ID',
  `item_title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商品标题',
  `source_message_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '源消息ID',
  `sender_user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发送方闲鱼用户ID',
  `sender_user_name` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发送方昵称',
  `source_message` text COLLATE utf8mb4_unicode_ci COMMENT '收到的消息内容',
  `source_message_time` datetime DEFAULT NULL COMMENT '收到消息时间',
  `process_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'processing' COMMENT '处理状态',
  `decision_reason` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'processing' COMMENT '决策原因',
  `reply_strategy` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'none' COMMENT '回复策略',
  `reply_mode` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'none' COMMENT '回复模式',
  `matched_keyword` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '命中的关键词',
  `matched_rule_type` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '命中的规则类型',
  `default_reply_scope` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '默认回复作用域',
  `default_reply_once` tinyint(1) NOT NULL DEFAULT '0' COMMENT '默认回复是否仅回复一次',
  `ai_model_name` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'AI模型名称',
  `ai_provider_name` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'AI服务商名称',
  `reply_text` text COLLATE utf8mb4_unicode_ci COMMENT '回复文本内容',
  `reply_image_url` varchar(1000) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '回复图片URL',
  `reply_segments` json DEFAULT NULL COMMENT '拆分后的回复分段',
  `error_message` text COLLATE utf8mb4_unicode_ci COMMENT '错误信息',
  `send_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'unknown' COMMENT '发送状态',
  `send_fail_reason` text COLLATE utf8mb4_unicode_ci COMMENT '发送失败原因',
  `raw_message_json` json DEFAULT NULL COMMENT '原始消息JSON',
  `context_snapshot` json DEFAULT NULL COMMENT '上下文快照',
  `send_result_json` json DEFAULT NULL COMMENT '发送结果快照',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_owner_id` (`owner_id`),
  KEY `idx_account_pk` (`account_pk`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_chat_id` (`chat_id`),
  KEY `idx_item_id` (`item_id`),
  KEY `idx_source_message_id` (`source_message_id`),
  KEY `idx_sender_user_id` (`sender_user_id`),
  KEY `idx_process_status` (`process_status`),
  KEY `idx_decision_reason` (`decision_reason`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_arml_account_created` (`account_id`,`created_at`),
  KEY `idx_arml_account_status_created` (`account_id`,`process_status`,`created_at`),
  KEY `idx_arml_owner_created` (`owner_id`,`created_at`),
  KEY `idx_arml_owner_status_created` (`owner_id`,`process_status`,`created_at`),
  KEY `idx_arml_status_created` (`process_status`,`created_at`),
  KEY `idx_arml_status_strategy_created` (`process_status`,`reply_strategy`,`created_at`),
  KEY `idx_arml_strategy_created` (`reply_strategy`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自动回复消息日志表';

-- ============================================================
-- 13. xy_card_item_relations - 卡券商品关联表
-- ============================================================
CREATE TABLE `xy_card_item_relations` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '所属用户ID',
  `card_id` bigint NOT NULL COMMENT '卡券ID',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品ID',
  `source` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'own' COMMENT '卡券来源',
  `dock_record_id` bigint NOT NULL DEFAULT '0' COMMENT '对接记录ID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_card_item_dock` (`card_id`,`item_id`,`dock_record_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_card_id` (`card_id`),
  KEY `idx_item_id` (`item_id`),
  KEY `idx_cir_user_item` (`user_id`,`item_id`),
  KEY `idx_cir_item_card` (`item_id`,`card_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='卡券商品关联表';

-- ============================================================
-- 14. xy_cards - 卡券表
-- ============================================================
CREATE TABLE `xy_cards` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '卡券ID',
  `user_id` bigint NOT NULL COMMENT '所属用户ID',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联商品ID',
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '卡券名称',
  `type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '卡券类型(api/text/data/image)',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '卡券描述',
  `enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `delay_seconds` int DEFAULT '0' COMMENT '延迟秒数',
  `delivery_count` int DEFAULT '0' COMMENT '发货次数',
  `price` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '对接价格',
  `is_dockable` tinyint(1) DEFAULT '0' COMMENT '是否可对接',
  `fee_payer` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手续费支付方式',
  `min_price` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '最低售价',
  `dock_visibility` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '对接可见性',
  `is_multi_spec` tinyint(1) DEFAULT '0' COMMENT '是否多规格',
  `spec_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '规格名称',
  `spec_value` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '规格值',
  `api_config` text COLLATE utf8mb4_unicode_ci COMMENT 'API配置(JSON)',
  `text_content` longtext COLLATE utf8mb4_unicode_ci,
  `data_content` longtext COLLATE utf8mb4_unicode_ci,
  `image_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '图片URL',
  `image_urls` text COLLATE utf8mb4_unicode_ci COMMENT '多图片URL列表(JSON)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_item_id` (`item_id`),
  KEY `idx_card_user_item` (`user_id`,`item_id`),
  KEY `idx_cards_dockable_enabled` (`is_dockable`,`enabled`),
  KEY `idx_cards_user_id_desc` (`user_id`,`id`),
  KEY `idx_cards_user_enabled` (`user_id`,`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='卡券表';

-- ============================================================
-- 15. xy_catalog_items - 商品目录表
-- ============================================================
CREATE TABLE `xy_catalog_items` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '商品ID',
  `owner_id` bigint NOT NULL COMMENT '所属用户ID',
  `account_id` bigint NOT NULL COMMENT '关联账号ID',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品标识',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商品标题',
  `price` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商品价格',
  `ai_prompt` text COLLATE utf8mb4_unicode_ci COMMENT '商品AI提示词',
  `is_polished` tinyint(1) DEFAULT '0' COMMENT '是否擦亮',
  `metadata` json DEFAULT NULL COMMENT '商品元数据',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_owner_id` (`owner_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_item_id` (`item_id`),
  KEY `idx_cat_account_item` (`account_id`,`item_id`),
  KEY `idx_cat_owner_created` (`owner_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品目录表';

-- ============================================================
-- 16. xy_chat_quick_phrases - 在线聊天快捷短语表
-- ============================================================
CREATE TABLE `xy_chat_quick_phrases` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `owner_id` bigint NOT NULL COMMENT '归属用户',
  `title` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '短语标题',
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '短语内容',
  `sort_order` int NOT NULL DEFAULT '0' COMMENT '排序值',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_xy_chat_quick_phrases_owner_id` (`owner_id`),
  KEY `idx_chat_quick_phrase_owner_sort` (`owner_id`,`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='在线聊天快捷短语';

-- ============================================================
-- 17. xy_confirm_receipt_messages - 确认收货消息配置表
-- ============================================================
CREATE TABLE `xy_confirm_receipt_messages` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号ID',
  `enabled` tinyint(1) DEFAULT '0' COMMENT '是否启用',
  `message_content` text COLLATE utf8mb4_unicode_ci COMMENT '消息文本内容',
  `message_image` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '消息图片URL',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='确认收货消息配置表';

-- ============================================================
-- 18. xy_cookie_refresh_schedules - Cookie续期计划表
-- ============================================================
CREATE TABLE `xy_cookie_refresh_schedules` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号ID',
  `expire_at` datetime NOT NULL COMMENT '当前Cookie续期到期时间',
  `last_refresh_at` datetime DEFAULT NULL COMMENT '最近一次续期成功时间',
  `last_status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '最近一次状态',
  `last_error_message` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '最近一次错误信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account_id` (`account_id`),
  KEY `idx_expire_at` (`expire_at`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Cookie续期计划表';

-- ============================================================
-- 19. xy_db_backup_log - 数据库备份日志表
-- ============================================================
CREATE TABLE `xy_db_backup_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态',
  `file_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备份文件名',
  `file_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备份文件绝对路径',
  `file_size` bigint DEFAULT NULL COMMENT '备份文件大小(字节)',
  `table_count` int DEFAULT NULL COMMENT '备份的数据表数量',
  `total_rows` bigint DEFAULT NULL COMMENT '备份的数据总行数',
  `duration_ms` int DEFAULT NULL COMMENT '备份耗时(毫秒)',
  `error_message` varchar(1000) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '错误信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据库备份日志表';

-- ============================================================
-- 20. xy_default_replies - 默认回复表
-- ============================================================
CREATE TABLE `xy_default_replies` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '回复ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号标识',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商品ID',
  `enabled` tinyint(1) DEFAULT '0' COMMENT '是否启用',
  `reply_type` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT 'text' COMMENT '回复类型',
  `reply_content` text COLLATE utf8mb4_unicode_ci COMMENT '回复内容',
  `reply_image` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '回复图片URL',
  `api_url` varchar(1024) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'API地址',
  `api_timeout` int DEFAULT '80' COMMENT 'API请求超时时间(秒)',
  `reply_once` tinyint(1) DEFAULT '0' COMMENT '只回复一次',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account_item` (`account_id`,`item_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_item_id` (`item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='默认回复表';

-- ============================================================
-- 21. xy_default_reply_records - 默认回复记录表
-- ============================================================
CREATE TABLE `xy_default_reply_records` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号标识',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商品ID',
  `user_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '被回复用户ID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_account_item_user` (`account_id`,`item_id`,`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='默认回复记录表';

-- ============================================================
-- 22. xy_delivery_block_rules - 禁止发货规则配置表
-- ============================================================
CREATE TABLE `xy_delivery_block_rules` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `account_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号ID',
  `rule_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '规则编码',
  `enabled` tinyint(1) NOT NULL DEFAULT '0' COMMENT '规则开关',
  `priority` int NOT NULL DEFAULT '0' COMMENT '执行优先级',
  `block_reason` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '禁止发货原因',
  `auto_close_order` tinyint(1) NOT NULL DEFAULT '0' COMMENT '命中后主动关闭订单',
  `only_card_after_close` tinyint(1) NOT NULL DEFAULT '0' COMMENT '关闭订单后继续发货(只发卡券)',
  `excluded_item_ids` json DEFAULT NULL COMMENT '排除商品列表',
  `config` json DEFAULT NULL COMMENT '规则专属参数',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account_rule` (`account_id`,`rule_code`),
  KEY `idx_account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='禁止发货规则配置表';

-- ============================================================
-- 23. xy_dock_code_bindings - 对接码绑定表
-- ============================================================
CREATE TABLE `xy_dock_code_bindings` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '绑定用户ID(分销商)',
  `dock_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '对接码',
  `target_user_id` bigint NOT NULL COMMENT '对接码拥有者用户ID(供应商)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_target` (`user_id`,`target_user_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_target_user_id` (`target_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对接码绑定表';

-- ============================================================
-- 24. xy_dock_records - 对接记录表
-- ============================================================
CREATE TABLE `xy_dock_records` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `card_id` bigint NOT NULL COMMENT '来源卡券ID',
  `dock_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '对接名称',
  `markup_amount` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '0.00' COMMENT '加价金额',
  `remark` text COLLATE utf8mb4_unicode_ci COMMENT '备注',
  `delivery_count` int NOT NULL DEFAULT '0' COMMENT '发货次数',
  `status` tinyint(1) DEFAULT '1' COMMENT '对接状态：1启用 0停用',
  `disable_reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '禁用原因',
  `level` int NOT NULL DEFAULT '1' COMMENT '分销层级：1=一级，2=二级',
  `parent_dock_id` bigint DEFAULT NULL COMMENT '上级对接记录ID',
  `source_user_id` bigint DEFAULT NULL COMMENT '上级分销商用户ID',
  `allow_sub_dock` tinyint(1) DEFAULT '0' COMMENT '是否允许下级对接',
  `sub_dock_price` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '给下级的对接价格',
  `sub_dock_visibility` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '下级对接可见性',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_card_id` (`card_id`),
  KEY `idx_parent_dock_id` (`parent_dock_id`),
  KEY `idx_dock_user_level` (`user_id`,`level`),
  KEY `idx_dock_source_level` (`source_user_id`,`level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对接记录表';

-- ============================================================
-- 25. xy_feedback_messages - 意见反馈消息表
-- ============================================================
CREATE TABLE `xy_feedback_messages` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  `feedback_id` bigint NOT NULL COMMENT '关联反馈ID',
  `user_id` bigint NOT NULL COMMENT '发送者用户ID',
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '消息内容',
  `is_admin` tinyint(1) DEFAULT '0' COMMENT '是否为管理员消息',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_feedback_id` (`feedback_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='意见反馈消息表';

-- ============================================================
-- 26. xy_feedbacks - 意见反馈表
-- ============================================================
CREATE TABLE `xy_feedbacks` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '反馈ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `cookie_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联账号ID',
  `title` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '标题',
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '内容',
  `feedback_type` enum('FEATURE','BUG','OTHER') COLLATE utf8mb4_unicode_ci DEFAULT 'OTHER' COMMENT '反馈类型',
  `images` text COLLATE utf8mb4_unicode_ci COMMENT '图片URL(JSON数组)',
  `is_resolved` tinyint(1) DEFAULT '0' COMMENT '是否已解决',
  `resolved_at` datetime DEFAULT NULL COMMENT '解决时间',
  `admin_reply` text COLLATE utf8mb4_unicode_ci COMMENT '管理员回复',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_is_resolved` (`is_resolved`),
  KEY `idx_feedback_type` (`feedback_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='意见反馈表';

-- ============================================================
-- 27. xy_fund_flows - 资金流水表
-- ============================================================
CREATE TABLE `xy_fund_flows` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '流水类型：income/expense',
  `amount` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发生额',
  `balance_before` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发生前余额',
  `balance_after` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发生后余额',
  `order_id` bigint DEFAULT NULL COMMENT '关联订单ID',
  `dock_record_id` bigint DEFAULT NULL COMMENT '关联对接记录ID',
  `description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '流水描述',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '发生时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_dock_record_id` (`dock_record_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_ff_user_id_desc` (`user_id`,`id`),
  KEY `idx_ff_user_type_id_desc` (`user_id`,`type`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='资金流水表';

-- ============================================================
-- 28. xy_goofish_crawl_items - Goofish抓取商品表
-- ============================================================
CREATE TABLE `xy_goofish_crawl_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `job_id` bigint NOT NULL,
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` text COLLATE utf8mb4_unicode_ci,
  `price` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `area` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `seller_name` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `item_url` text COLLATE utf8mb4_unicode_ci,
  `main_image` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `publish_time` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `want_count` int DEFAULT NULL,
  `view_count` int DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `detail_error` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `raw_json` json DEFAULT NULL,
  `fetched_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_job_item` (`job_id`,`item_id`),
  KEY `idx_job_id` (`job_id`),
  KEY `idx_fetched_at` (`fetched_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 29. xy_goofish_crawl_jobs - Goofish抓取任务表
-- ============================================================
CREATE TABLE `xy_goofish_crawl_jobs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `owner_id` bigint NOT NULL,
  `cookie_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `keyword` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `interval_seconds` int NOT NULL DEFAULT '900',
  `start_page` int NOT NULL DEFAULT '1',
  `pages` int NOT NULL DEFAULT '1',
  `page_size` int NOT NULL DEFAULT '20',
  `fetch_detail` tinyint(1) DEFAULT '1',
  `detail_limit` int NOT NULL DEFAULT '20',
  `enabled` tinyint(1) DEFAULT '1',
  `last_run_at` datetime DEFAULT NULL,
  `last_error` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_owner_id` (`owner_id`),
  KEY `idx_cookie_id` (`cookie_id`),
  KEY `idx_enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 30. xy_keyword_rules - 关键词规则表
-- ============================================================
CREATE TABLE `xy_keyword_rules` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '规则ID',
  `owner_id` bigint NOT NULL COMMENT '所属用户ID',
  `account_id` bigint DEFAULT NULL COMMENT '关联账号ID',
  `keyword` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关键词',
  `reply_content` text COLLATE utf8mb4_unicode_ci COMMENT '回复内容',
  `reply_type` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '回复类型(text/image)',
  `image_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '图片URL',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商品ID',
  `priority` int DEFAULT '100' COMMENT '优先级',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_owner_id` (`owner_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_keyword` (`keyword`),
  KEY `idx_kw_account_item` (`account_id`,`item_id`),
  KEY `idx_kw_account_active` (`account_id`,`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关键词规则表';

-- ============================================================
-- 31. xy_message_filters - 消息过滤规则表
-- ============================================================
CREATE TABLE `xy_message_filters` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '规则ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号标识',
  `keyword` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '过滤关键词',
  `filter_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '过滤类型',
  `enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account_keyword_type` (`account_id`,`keyword`,`filter_type`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_keyword` (`keyword`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息过滤规则表';

-- ============================================================
-- 32. xy_message_notifications - 消息通知表
-- ============================================================
CREATE TABLE `xy_message_notifications` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '通知ID',
  `owner_id` bigint NOT NULL COMMENT '所属用户ID',
  `account_pk` bigint NOT NULL COMMENT '关联账号ID',
  `account_identifier` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号标识',
  `channel_id` bigint NOT NULL COMMENT '渠道ID',
  `enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_owner_id` (`owner_id`),
  KEY `idx_account_pk` (`account_pk`),
  KEY `idx_channel_id` (`channel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息通知表';

-- ============================================================
-- 33. xy_notification_channels - 通知渠道表
-- ============================================================
CREATE TABLE `xy_notification_channels` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '渠道ID',
  `owner_id` bigint NOT NULL COMMENT '所属用户ID',
  `name` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '渠道名称',
  `channel_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '渠道类型',
  `config` json DEFAULT NULL COMMENT '渠道配置',
  `enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_owner_id` (`owner_id`),
  KEY `idx_channel_type` (`channel_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知渠道表';

-- ============================================================
-- 34. xy_orders - 订单表
-- ============================================================
CREATE TABLE `xy_orders` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '订单ID',
  `owner_id` bigint NOT NULL COMMENT '所属用户ID',
  `order_no` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '订单号',
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '订单状态',
  `buyer_nick` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '买家昵称',
  `buyer_fish_nick` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '买家闲鱼昵称',
  `buyer_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '买家ID',
  `chat_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '聊天会话ID',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商品ID',
  `spec_name` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '规格名称',
  `spec_value` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '规格值',
  `quantity` int DEFAULT '1' COMMENT '数量',
  `amount` decimal(12,2) DEFAULT NULL COMMENT '金额',
  `currency` varchar(8) COLLATE utf8mb4_unicode_ci DEFAULT 'CNY' COMMENT '货币',
  `account_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '账号标识',
  `account_name` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '账号名称',
  `is_bargain` tinyint(1) DEFAULT '0' COMMENT '是否小刀',
  `receiver_name` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '收货人姓名',
  `receiver_phone` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '收货人手机号',
  `receiver_address` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '收货地址',
  `is_rated` tinyint(1) DEFAULT '0' COMMENT '是否已评价',
  `is_red_flower` tinyint(1) DEFAULT '0' COMMENT '是否已求小红花',
  `delivery_method` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发货方式',
  `delivery_content` varchar(2000) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发货内容',
  `delivery_fail_reason` varchar(2000) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发货失败原因',
  `item_snapshot` json DEFAULT NULL COMMENT '商品快照',
  `metadata` json DEFAULT NULL COMMENT '元数据',
  `source` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '数据来源',
  `placed_at` datetime DEFAULT NULL COMMENT '下单时间',
  `synced_at` datetime DEFAULT NULL COMMENT '同步时间',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_order_account_no` (`account_id`,`order_no`),
  KEY `idx_owner_id` (`owner_id`),
  KEY `idx_order_no` (`order_no`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_order_created_at` (`created_at`),
  KEY `idx_order_placed_status` (`placed_at`,`status`),
  KEY `idx_order_created_status` (`created_at`,`status`),
  KEY `idx_order_owner_placed` (`owner_id`,`placed_at`),
  KEY `idx_order_owner_created` (`owner_id`,`created_at`),
  KEY `idx_order_owner_account_placed` (`owner_id`,`account_id`,`placed_at`),
  KEY `idx_order_owner_account_buyer_created` (`owner_id`,`account_id`,`buyer_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单表';

-- ============================================================
-- 35. xy_personal_blacklist - 个人黑名单表
-- ============================================================
CREATE TABLE `xy_personal_blacklist` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `owner_id` bigint NOT NULL COMMENT '用户ID',
  `account_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '账号ID',
  `buyer_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '买家ID',
  `buyer_nick` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '买家昵称',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商品ID',
  `reason` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '拉黑原因',
  `is_enabled` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否启用',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_pb_owner_id` (`owner_id`),
  KEY `idx_pb_owner_buyer` (`owner_id`,`buyer_id`),
  KEY `idx_pb_owner_account` (`owner_id`,`account_id`),
  KEY `idx_pb_owner_created` (`owner_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='个人黑名单表';

-- ============================================================
-- 36. xy_platform_blacklist - 闲鱼黑名单表
-- ============================================================
CREATE TABLE `xy_platform_blacklist` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `owner_id` bigint NOT NULL COMMENT '拉黑用户(本系统用户ID)',
  `buyer_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '买家ID',
  `buyer_nick` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '买家昵称',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_plb_owner_id` (`owner_id`),
  KEY `idx_plb_owner_buyer` (`owner_id`,`buyer_id`),
  KEY `idx_plb_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='闲鱼黑名单表';

-- ============================================================
-- 37. xy_product_materials - 商品素材库表
-- ============================================================
CREATE TABLE `xy_product_materials` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '所属用户ID',
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品标题',
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品描述',
  `price` decimal(12,2) NOT NULL COMMENT '价格',
  `original_price` decimal(12,2) DEFAULT NULL COMMENT '原价(划线价)',
  `category` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商品分类',
  `images` json DEFAULT NULL COMMENT '图片URL列表(最多9张)',
  `delivery_method` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'express' COMMENT '发货方式',
  `postage` decimal(8,2) DEFAULT '0.00' COMMENT '邮费',
  `address` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '宝贝所在地',
  `brand` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品牌',
  `condition` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT '全新' COMMENT '成色',
  `remark` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_pm_user_created` (`user_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品素材库表';

-- ============================================================
-- 38. xy_publish_addresses - 商品发布随机地址池表
-- ============================================================
CREATE TABLE `xy_publish_addresses` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '地址名称',
  `search_keyword` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '地址搜索关键词',
  `expected_text` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '期望命中的候选文本',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '限定使用的闲鱼账号ID',
  `weight` int NOT NULL DEFAULT '1' COMMENT '随机权重',
  `sort_order` int NOT NULL DEFAULT '100' COMMENT '排序值',
  `is_enabled` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否启用',
  `use_count` int NOT NULL DEFAULT '0' COMMENT '使用次数',
  `last_used_at` datetime DEFAULT NULL COMMENT '最后使用时间',
  `created_by` bigint DEFAULT NULL COMMENT '创建人用户ID',
  `remark` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_pa_enabled_account` (`is_enabled`,`account_id`),
  KEY `idx_pa_sort_created` (`sort_order`,`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=156 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品发布随机地址池表';

-- ============================================================
-- 39. xy_publish_logs - 商品发布日志表
-- ============================================================
CREATE TABLE `xy_publish_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '操作用户ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '闲鱼账号ID',
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品标题',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '商品描述',
  `price` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发布价格',
  `material_id` bigint DEFAULT NULL COMMENT '关联的素材ID',
  `batch_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '批次ID',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending' COMMENT '状态',
  `item_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发布成功后的商品链接',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '发布成功后的商品ID',
  `error_message` varchar(1000) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '失败原因',
  `resolved_address_id` bigint DEFAULT NULL COMMENT '本次发布命中的地址池ID',
  `resolved_address_text` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '本次发布实际使用的地址搜索词',
  `address_source` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '地址来源',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_batch_id` (`batch_id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_publish_user_created` (`user_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品发布日志表';

-- ============================================================
-- 40. xy_recharge_orders - 充值订单表
-- ============================================================
CREATE TABLE `xy_recharge_orders` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `order_no` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '充值订单号',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `amount` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '充值金额',
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending' COMMENT '订单状态',
  `trade_no` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '支付宝交易号',
  `qr_code` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '支付二维码内容',
  `paid_at` datetime DEFAULT NULL COMMENT '支付时间',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_order_no` (`order_no`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='充值订单表';

-- ============================================================
-- 41. xy_risk_control_logs - 风控日志表
-- ============================================================
CREATE TABLE `xy_risk_control_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `owner_id` bigint DEFAULT NULL COMMENT '所属用户ID',
  `account_id` bigint DEFAULT NULL COMMENT '关联账号ID',
  `account_identifier` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '账号标识',
  `event_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT 'slider_captcha' COMMENT '事件类型',
  `event_description` text COLLATE utf8mb4_unicode_ci COMMENT '事件描述',
  `processing_result` text COLLATE utf8mb4_unicode_ci COMMENT '处理结果',
  `processing_status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT 'processing' COMMENT '处理状态',
  `captcha_engine` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '验证引擎',
  `error_message` text COLLATE utf8mb4_unicode_ci COMMENT '错误信息',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_owner_id` (`owner_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_rcl_account_status` (`account_id`,`processing_status`),
  KEY `idx_rcl_identifier_status_created` (`account_identifier`,`processing_status`,`created_at`),
  KEY `idx_rcl_owner_created` (`owner_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='风控日志表';

-- ============================================================
-- 42. xy_scheduled_api_cookie_renew_log - 接口续期Cookies日志表
-- ============================================================
CREATE TABLE `xy_scheduled_api_cookie_renew_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `batch_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '批次ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号ID',
  `status` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态',
  `updated_cookie_count` int NOT NULL DEFAULT '0' COMMENT '更新的Cookie字段数量',
  `updated_cookie_names` text COLLATE utf8mb4_unicode_ci COMMENT '更新的Cookie字段名列表',
  `response_content` text COLLATE utf8mb4_unicode_ci COMMENT '接口返回内容',
  `error_message` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '错误信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_batch_id` (`batch_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='接口续期Cookies日志表';

-- ============================================================
-- 43. xy_scheduled_close_notice_log - 关闭通知日志表
-- ============================================================
CREATE TABLE `xy_scheduled_close_notice_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `batch_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '批次ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号ID',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态',
  `error_message` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '错误信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_batch_id` (`batch_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关闭通知日志表';

-- ============================================================
-- 44. xy_scheduled_cookies_refresh_log - COOKIES刷新日志表
-- ============================================================
CREATE TABLE `xy_scheduled_cookies_refresh_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `batch_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '批次ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号ID',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态',
  `updated_cookie_count` int NOT NULL DEFAULT '0' COMMENT '增量更新的Cookie字段数量',
  `next_expire_at` datetime DEFAULT NULL COMMENT '下次到期时间',
  `error_message` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '错误信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_batch_id` (`batch_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='COOKIES刷新日志表';

-- ============================================================
-- 45. xy_scheduled_login_renew_log - 登录续期日志表
-- ============================================================
CREATE TABLE `xy_scheduled_login_renew_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `batch_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '批次ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号ID',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态',
  `error_message` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '错误信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_batch_id` (`batch_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录续期日志表';

-- ============================================================
-- 46. xy_scheduled_polish_log - 擦亮日志表
-- ============================================================
CREATE TABLE `xy_scheduled_polish_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `batch_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '批次ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号ID',
  `item_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品ID',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态',
  `error_message` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '错误信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_batch_id` (`batch_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_spol_created_batch` (`created_at`,`batch_id`),
  KEY `idx_spol_batch_created_status` (`batch_id`,`created_at`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='擦亮日志表';

-- ============================================================
-- 47. xy_scheduled_rate_log - 补评价日志表
-- ============================================================
CREATE TABLE `xy_scheduled_rate_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `batch_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '批次ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号ID',
  `order_no` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '订单号',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态',
  `error_message` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '错误信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_batch_id` (`batch_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_srate_created_batch` (`created_at`,`batch_id`),
  KEY `idx_srate_batch_created_status` (`batch_id`,`created_at`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='补评价日志表';

-- ============================================================
-- 48. xy_scheduled_red_flower_log - 求小红花日志表
-- ============================================================
CREATE TABLE `xy_scheduled_red_flower_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `batch_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '批次ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号ID',
  `order_no` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '订单号',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态',
  `error_message` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '错误信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_batch_id` (`batch_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_srf_created_batch` (`created_at`,`batch_id`),
  KEY `idx_srf_batch_created_status` (`batch_id`,`created_at`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='求小红花日志表';

-- ============================================================
-- 49. xy_scheduled_redelivery_log - 补发货日志表
-- ============================================================
CREATE TABLE `xy_scheduled_redelivery_log` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `batch_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '批次ID',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号ID',
  `order_no` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '订单号',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态',
  `error_message` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '错误信息',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_batch_id` (`batch_id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_srl_created_batch` (`created_at`,`batch_id`),
  KEY `idx_srl_batch_created_status` (`batch_id`,`created_at`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='补发货日志表';

-- ============================================================
-- 50. xy_scheduled_tasks - 定时任务配置表
-- ============================================================
CREATE TABLE `xy_scheduled_tasks` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务代码',
  `task_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务名称',
  `interval_seconds` int NOT NULL DEFAULT '60' COMMENT '执行间隔(秒)',
  `enabled` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否启用',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '任务描述',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_task_code` (`task_code`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定时任务配置表';

-- ============================================================
-- 51. xy_settlement_records - 结算记录表
-- ============================================================
CREATE TABLE `xy_settlement_records` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `alipay_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '支付宝ID',
  `payment_type` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '收款方式',
  `payment_qrcode` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '收款码图片路径',
  `amount` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '提现金额',
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending_review' COMMENT '状态',
  `remark` text COLLATE utf8mb4_unicode_ci COMMENT '备注',
  `reject_reason` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '拒绝原因',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_sr_user_created_id` (`user_id`,`created_at`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='结算记录表';

-- ============================================================
-- 52. xy_shared_scan_sessions - 共享扫码登录会话表
-- ============================================================
CREATE TABLE `xy_shared_scan_sessions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `session_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '会话唯一ID(UUID)',
  `owner_id` bigint NOT NULL COMMENT '创建者用户ID',
  `owner_username` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '创建者用户名',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT '会话状态',
  `expires_at` datetime NOT NULL COMMENT '过期时间(默认72小时)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `session_id` (`session_id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_owner_id` (`owner_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='共享扫码登录会话表';

-- ============================================================
-- 53. xy_shared_scan_workers - 共享扫码兼职工作者表
-- ============================================================
CREATE TABLE `xy_shared_scan_workers` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `shared_session_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关联的共享会话ID',
  `sub_session_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '兼职子会话唯一ID(UUID)',
  `xianyu_session_id` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联的闲鱼QR登录会话ID',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'qrcode_ready' COMMENT '状态',
  `qr_code_url` longtext COLLATE utf8mb4_unicode_ci COMMENT '二维码图片base64 data URL',
  `account_id` varchar(80) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '扫码成功后的闲鱼账号ID(unb)',
  `cookie_saved` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Cookie是否已保存',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sub_session_id` (`sub_session_id`),
  KEY `idx_shared_session_id` (`shared_session_id`),
  KEY `idx_sub_session_id` (`sub_session_id`),
  KEY `idx_account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='共享扫码兼职工作者表';

-- ============================================================
-- 54. xy_token_cache - Token缓存表
-- ============================================================
CREATE TABLE `xy_token_cache` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户ID(myid)',
  `token` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'IM Token',
  `device_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备ID',
  `expire_at` datetime NOT NULL COMMENT '过期时间',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Token缓存表';

-- ============================================================
-- MIGRATION NOTES (from init_database.py COLUMN_MIGRATIONS):
-- The following columns are auto-migrated on startup via ALTER TABLE ADD COLUMN:
--
-- xy_auto_reply_message_logs:
--   send_status, send_fail_reason
-- xy_risk_control_logs:
--   captcha_engine
-- xy_accounts:
--   proxy_type, proxy_host, proxy_port, proxy_user, proxy_pass,
--   message_expire_time, reply_delay_seconds, disable_reason,
--   scheduled_redelivery, scheduled_rate, auto_polish, confirm_before_send,
--   send_before_confirm, auto_red_flower, delivery_disabled, delivery_disabled_reason,
--   auto_close_order, delivery_only_card_after_close, delivery_disabled_excluded_items,
--   ai_reply_block_ordered_users
-- xy_orders:
--   is_bargain, chat_id, buyer_fish_nick, receiver_name, receiver_phone,
--   receiver_address, is_rated, delivery_method, delivery_content,
--   delivery_fail_reason, source, is_red_flower
-- xy_cards:
--   delivery_count, price, is_dockable, image_urls, fee_payer, min_price, dock_visibility
-- xy_dock_records:
--   delivery_count, disable_reason, level, parent_dock_id, source_user_id,
--   allow_sub_dock, sub_dock_price, sub_dock_visibility
-- xy_users:
--   account_limit, login_fail_count, login_locked_until, dock_code, secret_key
-- xy_default_replies:
--   item_id, reply_image, reply_type, api_url, api_timeout
-- xy_default_reply_records:
--   item_id
-- xy_catalog_items:
--   ai_prompt, is_polished, updated_at
-- xy_announcements:
--   is_deleted
-- xy_card_item_relations:
--   source, dock_record_id
-- xy_agent_orders:
--   card_price, level2_cost, fee_payer, owner_user_id
-- xy_advertisements:
--   months, total_amount
-- xy_settlement_records:
--   payment_type, payment_qrcode, reject_reason
-- xy_publish_logs:
--   resolved_address_id, resolved_address_text, address_source
-- xy_account_login_logs:
--   updated_cookie_names
--
-- Special migrations:
-- - xy_users.account_limit: ALTER to allow NULL with NULL default
-- - xy_advertisements.status: ENUM expanded to include 'unpaid'
-- - xy_token_cache.user_id: VARCHAR expanded from 64 to 128
-- - xy_scheduled_api_cookie_renew_log.status: VARCHAR expanded from 20 to 30
-- - xy_cards.text_content/data_content: TEXT upgraded to LONGTEXT
-- - xy_card_item_relations: uk_card_item -> uk_card_item_dock (added dock_record_id)
-- ============================================================
