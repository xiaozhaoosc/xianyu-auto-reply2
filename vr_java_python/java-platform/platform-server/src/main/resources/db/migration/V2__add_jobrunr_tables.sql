-- JobRunr 数据库表（由 JobRunr 自动创建，此处为手动建表脚本）
-- 参考：https://www.jobrunr.io/en/documentation/configuration/storage/
-- 注意：JobRunr 7.x 支持自动建表，此脚本为备用

CREATE TABLE IF NOT EXISTS `jobrunr_jobs` (
    `id` varchar(36) NOT NULL,
    `version` int NOT NULL,
    `job_signature` varchar(512) DEFAULT NULL,
    `job_name` varchar(512) DEFAULT NULL,
    `state` varchar(36) NOT NULL,
    `created_at` datetime NOT NULL,
    `updated_at` datetime NOT NULL,
    `scheduled_at` datetime DEFAULT NULL,
    `recurring_job_id` varchar(120) DEFAULT NULL,
    `job_as_json` mediumtext NOT NULL,
    `job_history_as_json` mediumtext NOT NULL,
    `metadata_as_json` mediumtext DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_jobrunr_jobs_state` (`state`),
    KEY `idx_jobrunr_jobs_scheduled_at` (`scheduled_at`),
    KEY `idx_jobrunr_jobs_recurring_job_id` (`recurring_job_id`),
    KEY `idx_jobrunr_jobs_created_at` (`created_at`),
    KEY `idx_jobrunr_jobs_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `jobrunr_recurring_jobs` (
    `id` varchar(120) NOT NULL,
    `version` int NOT NULL,
    `job_as_json` mediumtext NOT NULL,
    `created_at` datetime NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `jobrunr_backgroundjobservers` (
    `id` varchar(36) NOT NULL,
    `worker_pool_size` int NOT NULL,
    `poll_interval_in_seconds` int NOT NULL,
    `first_heartbeat` datetime NOT NULL,
    `last_heartbeat` datetime NOT NULL,
    `is_running` boolean NOT NULL,
    `system_total_memory` bigint DEFAULT NULL,
    `system_free_memory` bigint DEFAULT NULL,
    `system_cpu_load` double DEFAULT NULL,
    `process_max_memory` bigint DEFAULT NULL,
    `process_free_memory` bigint DEFAULT NULL,
    `process_allocated_memory` bigint DEFAULT NULL,
    `process_cpu_load` double DEFAULT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `jobrunr_metadata` (
    `id` varchar(36) NOT NULL,
    `name` varchar(512) NOT NULL,
    `owner` varchar(512) NOT NULL,
    `value` mediumtext DEFAULT NULL,
    `created_at` datetime NOT NULL,
    `updated_at` datetime NOT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_jobrunr_metadata_name` (`name`),
    KEY `idx_jobrunr_metadata_owner` (`owner`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
