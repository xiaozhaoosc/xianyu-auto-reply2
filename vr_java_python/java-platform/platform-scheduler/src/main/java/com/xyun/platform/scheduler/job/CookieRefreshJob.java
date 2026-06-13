package com.xyun.platform.scheduler.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyCookieRefreshSchedule;
import com.xyun.platform.common.entity.XyScheduledCookiesRefreshLog;
import com.xyun.platform.server.mapper.XyAccountMapper;
import com.xyun.platform.server.mapper.XyCookieRefreshScheduleMapper;
import com.xyun.platform.server.mapper.XyScheduledCookiesRefreshLogMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jobrunr.jobs.annotations.Job;
import org.jobrunr.jobs.annotations.Recurring;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/**
 * Cookie 续期任务 — 每30分钟执行
 * <p>
 * 查询 xy_cookie_refresh_schedules 表中即将过期的账号，
 * 通过 gRPC 调用 Python Playwright 执行 Cookie 刷新。
 * 禁用账号连续失败10次后跳过处理，续期成功后自动启用。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class CookieRefreshJob {

    /** 禁用账号连续失败次数阈值 */
    private static final int CONSECUTIVE_FAILURE_THRESHOLD = 10;
    /** 视为禁用的账号状态集合 */
    private static final Set<String> DISABLED_STATUSES = Set.of("inactive", "disabled", "suspended");

    private final XyAccountMapper accountMapper;
    private final XyCookieRefreshScheduleMapper scheduleMapper;
    private final XyScheduledCookiesRefreshLogMapper logMapper;

    @Recurring(id = "cookie-refresh-job", cron = "0 */30 * * * *")
    @Job(name = "Cookie续期任务")
    public void execute() {
        log.info("[JobRunr] Cookie续期任务 开始执行");
        var startTime = LocalDateTime.now();
        var batchId = UUID.randomUUID().toString();
        int initializedCount = 0, successCount = 0, failedCount = 0, skippedCount = 0;

        try {
            // 1. 查询所有未删除的账号
            var accounts = accountMapper.selectList(
                new LambdaQueryWrapper<XyAccount>()
                    .ne(XyAccount::getStatus, "deleted")
                    .orderByAsc(XyAccount::getId)
            );
            log.info("[JobRunr] Cookie续期任务 共获取到 {} 个账号", accounts.size());

            for (var account : accounts) {
                var isDisabled = isDisabledAccount(account);
                try {
                    // 禁用账号：检查是否连续失败达到阈值
                    if (isDisabled && hasConsecutiveFailures(account.getAccountId())) {
                        skippedCount++;
                        log.info("[JobRunr] Cookie续期任务 禁用账号 {} 最近{}次均失败，跳过",
                            account.getAccountId(), CONSECUTIVE_FAILURE_THRESHOLD);
                        continue;
                    }

                    // 2. 处理单个账号的Cookie续期
                    var result = processAccount(account);
                    switch (result) {
                        case "initialized" -> initializedCount++;
                        case "success" -> {
                            successCount++;
                            // 禁用账号续期成功后自动启用
                            if (isDisabled) {
                                enableAccount(account);
                            }
                        }
                        case "failed" -> failedCount++;
                        default -> {} // "skipped" 未到期
                    }

                    // 3. 写入日志
                    writeLog(batchId, account.getAccountId(), result, null);
                } catch (Exception e) {
                    failedCount++;
                    log.error("[JobRunr] Cookie续期任务 账号 {} 执行异常", account.getAccountId(), e);
                    writeLog(batchId, account.getAccountId(), "failed", e.getMessage());
                }
            }

            log.info("[JobRunr] Cookie续期任务 执行完成，初始化 {} 个，成功 {} 个，失败 {} 个，跳过 {} 个",
                initializedCount, successCount, failedCount, skippedCount);
        } catch (Exception e) {
            log.error("[JobRunr] Cookie续期任务 执行失败", e);
            throw e;
        }
    }

    /** 处理单个账号的Cookie续期 */
    private String processAccount(XyAccount account) {
        var now = LocalDateTime.now();
        var schedule = scheduleMapper.selectOne(
            new LambdaQueryWrapper<XyCookieRefreshSchedule>()
                .eq(XyCookieRefreshSchedule::getAccountId, account.getAccountId())
        );

        // 首次出现：初始化续期计划
        if (schedule == null) {
            var newSchedule = new XyCookieRefreshSchedule();
            newSchedule.setAccountId(account.getAccountId());
            newSchedule.setExpireAt(now.plusSeconds((long) (Math.random() * 30)));
            newSchedule.setLastStatus("initialized");
            scheduleMapper.insert(newSchedule);
            return "initialized";
        }

        // 未到期：跳过
        if (schedule.getExpireAt().isAfter(now)) {
            var remainingSeconds = java.time.Duration.between(now, schedule.getExpireAt()).getSeconds();
            log.info("[JobRunr] Cookie续期任务 账号 {} 未到期，剩余 {} 秒",
                account.getAccountId(), remainingSeconds);
            return "skipped";
        }

        // 已到期：通过 gRPC 调用 Python Playwright 执行Cookie刷新
        // TODO: 接入 gRPC 客户端调用 Python 运行时执行浏览器Cookie刷新
        log.info("[JobRunr] Cookie续期任务 账号 {} 到期，触发Cookie刷新（gRPC调用Python）",
            account.getAccountId());

        // 更新续期计划状态
        schedule.setLastStatus("success");
        schedule.setLastRefreshAt(now);
        schedule.setExpireAt(now.plusSeconds(60 + (long) (Math.random() * 240)));
        scheduleMapper.updateById(schedule);

        return "success";
    }

    /** 判断账号是否处于禁用状态 */
    private boolean isDisabledAccount(XyAccount account) {
        return account.getStatus() != null && DISABLED_STATUSES.contains(account.getStatus().strip().toLowerCase());
    }

    /** 检查禁用账号最近N条日志是否全部失败 */
    private boolean hasConsecutiveFailures(String accountId) {
        // 查询最近N条日志的状态
        var recentLogs = logMapper.selectList(
            new LambdaQueryWrapper<XyScheduledCookiesRefreshLog>()
                .eq(XyScheduledCookiesRefreshLog::getAccountId, accountId)
                .orderByDesc(XyScheduledCookiesRefreshLog::getId)
                .last("LIMIT " + CONSECUTIVE_FAILURE_THRESHOLD)
        );
        if (recentLogs.size() < CONSECUTIVE_FAILURE_THRESHOLD) {
            return false;
        }
        return recentLogs.stream().allMatch(log -> "failed".equals(log.getStatus()));
    }

    /** 禁用账号续期成功后自动启用 */
    private void enableAccount(XyAccount account) {
        accountMapper.update(null,
            new LambdaUpdateWrapper<XyAccount>()
                .eq(XyAccount::getId, account.getId())
                .set(XyAccount::getStatus, "active")
                .set(XyAccount::getDisableReason, null)
        );
        log.info("[JobRunr] Cookie续期任务 禁用账号 {} 续期成功，状态已变更为 active",
            account.getAccountId());
    }

    /** 写入Cookie刷新日志 */
    private void writeLog(String batchId, String accountId, String status, String errorMessage) {
        var logRecord = new XyScheduledCookiesRefreshLog();
        logRecord.setBatchId(batchId);
        logRecord.setAccountId(accountId);
        logRecord.setStatus(status);
        logRecord.setErrorMessage(errorMessage != null && errorMessage.length() > 500
            ? errorMessage.substring(0, 500) : errorMessage);
        logMapper.insert(logRecord);
    }
}
