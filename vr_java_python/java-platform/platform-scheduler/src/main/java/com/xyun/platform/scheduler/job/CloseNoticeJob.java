package com.xyun.platform.scheduler.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyScheduledCloseNoticeLog;
import com.xyun.platform.server.mapper.XyAccountMapper;
import com.xyun.platform.server.mapper.XyScheduledCloseNoticeLogMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jobrunr.jobs.annotations.Job;
import org.jobrunr.jobs.annotations.Recurring;
import org.springframework.stereotype.Component;

import java.util.Set;
import java.util.UUID;

/**
 * 关闭通知任务 — 每小时执行
 * <p>
 * 检查即将关闭的订单，发送通知。
 * 逐个账号调用公共关闭账号通知方法。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class CloseNoticeJob {

    /** 非活跃状态集合 */
    private static final Set<String> INACTIVE_STATUSES = Set.of("inactive", "disabled", "suspended", "deleted");

    private final XyAccountMapper accountMapper;
    private final XyScheduledCloseNoticeLogMapper logMapper;

    @Recurring(id = "close-notice-job", cron = "0 0 * * * *")
    @Job(name = "关闭通知任务")
    public void execute() {
        log.info("[JobRunr] 关闭通知任务 开始执行");
        var batchId = UUID.randomUUID().toString();
        var startTime = System.currentTimeMillis();

        try {
            // 1. 查询所有启用状态的账号
            var accounts = accountMapper.selectList(
                new LambdaQueryWrapper<XyAccount>()
                    .notIn(XyAccount::getStatus, INACTIVE_STATUSES)
            );

            if (accounts.isEmpty()) {
                log.info("[JobRunr] 关闭通知任务 没有启用状态的账号，任务结束");
                return;
            }
            log.info("[JobRunr] 关闭通知任务 查询到 {} 个启用状态的账号", accounts.size());

            // 2. 逐个账号关闭消息通知
            int successCount = 0, failedCount = 0;

            for (var account : accounts) {
                try {
                    // TODO: 调用 close_account_notice() 关闭账号消息通知
                    log.info("[JobRunr] 关闭通知任务 账号 {} 关闭通知处理", account.getAccountId());

                    writeLog(batchId, account.getAccountId(), "success", null);
                    successCount++;
                } catch (Exception e) {
                    failedCount++;
                    log.error("[JobRunr] 关闭通知任务 账号 {} 处理异常", account.getAccountId(), e);
                    writeLog(batchId, account.getAccountId(), "failed", e.getMessage());
                }
            }

            var elapsed = (System.currentTimeMillis() - startTime) / 1000.0;
            log.info("[JobRunr] 关闭通知任务 执行完成，成功: {}, 失败: {}, 耗时: {:.2f}秒",
                successCount, failedCount, elapsed);
        } catch (Exception e) {
            log.error("[JobRunr] 关闭通知任务 执行失败", e);
            throw e;
        }
    }

    /** 写入关闭通知日志 */
    private void writeLog(String batchId, String accountId, String status, String errorMessage) {
        try {
            var logRecord = new XyScheduledCloseNoticeLog();
            logRecord.setBatchId(batchId);
            logRecord.setAccountId(accountId);
            logRecord.setStatus(status);
            logRecord.setErrorMessage(errorMessage != null && errorMessage.length() > 500
                ? errorMessage.substring(0, 500) : errorMessage);
            logMapper.insert(logRecord);
        } catch (Exception e) {
            log.error("[JobRunr] 关闭通知任务 记录日志失败", e);
        }
    }
}
