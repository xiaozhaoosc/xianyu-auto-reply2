package com.xyun.platform.scheduler.job;

import lombok.extern.slf4j.Slf4j;
import org.jobrunr.jobs.annotations.Job;
import org.jobrunr.jobs.annotations.Recurring;
import org.springframework.stereotype.Component;

/**
 * 示例定时任务 — 后续替换为实际的 13 个任务
 */
@Slf4j
@Component
public class SampleJob {

    @Recurring(id = "health-check", cron = "0 */5 * * * *")
    @Job(name = "健康检查任务")
    public void healthCheck() {
        log.info("[JobRunr] 健康检查执行成功");
    }

    @Recurring(id = "db-backup", cron = "0 0 2 * * *")
    @Job(name = "数据库备份任务")
    public void dbBackup() {
        log.info("[JobRunr] 数据库备份任务触发");
        // TODO: 实现数据库备份逻辑
    }
}