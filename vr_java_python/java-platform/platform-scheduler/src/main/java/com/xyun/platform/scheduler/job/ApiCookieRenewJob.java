package com.xyun.platform.scheduler.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyScheduledApiCookieRenewLog;
import com.xyun.platform.server.mapper.XyAccountMapper;
import com.xyun.platform.server.mapper.XyScheduledApiCookieRenewLogMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jobrunr.jobs.annotations.Job;
import org.jobrunr.jobs.annotations.Recurring;
import org.springframework.stereotype.Component;

import java.util.UUID;

/**
 * 接口续期Cookie任务 — 每小时执行
 * <p>
 * 通过 API 接口续期 Cookie（不需要浏览器）。
 * 调用 cookie_renew_api_service 执行接口续期，
 * 如有差异则覆盖更新数据库中的 cookie 字符串。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ApiCookieRenewJob {

    private final XyAccountMapper accountMapper;
    private final XyScheduledApiCookieRenewLogMapper logMapper;

    @Recurring(id = "api-cookie-renew-job", cron = "0 0 * * * *")
    @Job(name = "接口续期Cookie任务")
    public void execute() {
        log.info("[JobRunr] 接口续期Cookie任务 开始执行");
        var batchId = UUID.randomUUID().toString();
        int successCount = 0, cookieUpdatedCount = 0, failedCount = 0, needPasswordLoginCount = 0;

        try {
            // 1. 查询所有启用状态的账号
            var accounts = accountMapper.selectList(
                new LambdaQueryWrapper<XyAccount>()
                    .eq(XyAccount::getStatus, "active")
                    .orderByAsc(XyAccount::getId)
            );

            if (accounts.isEmpty()) {
                log.info("[JobRunr] 接口续期Cookie任务 未找到可处理的账号");
                return;
            }
            log.info("[JobRunr] 接口续期Cookie任务 共找到 {} 个启用账号", accounts.size());

            // 2. 逐个账号执行接口续期
            for (var account : accounts) {
                try {
                    var result = renewAccount(account);
                    switch (result) {
                        case "success" -> successCount++;
                        case "cookie_updated" -> cookieUpdatedCount++;
                        case "need_password_login" -> needPasswordLoginCount++;
                        default -> failedCount++;
                    }

                    writeLog(batchId, account.getAccountId(), result, null);
                } catch (Exception e) {
                    failedCount++;
                    log.error("[JobRunr] 接口续期Cookie任务 账号 {} 执行异常", account.getAccountId(), e);
                    writeLog(batchId, account.getAccountId(), "failed", e.getMessage());
                }
            }

            log.info("[JobRunr] 接口续期Cookie任务 执行完成，接口续期成功 {} 个，Cookie更新 {} 个，需要密码登录 {} 个，失败 {} 个",
                successCount, cookieUpdatedCount, needPasswordLoginCount, failedCount);
        } catch (Exception e) {
            log.error("[JobRunr] 接口续期Cookie任务 执行失败", e);
            throw e;
        }
    }

    /** 对单个账号执行接口续期 */
    private String renewAccount(XyAccount account) {
        var accountId = account.getAccountId();
        var cookieStr = account.getCookie();

        if (cookieStr == null || cookieStr.isBlank()) {
            return "failed";
        }

        log.info("[JobRunr] 接口续期Cookie任务 开始处理账号: {}", accountId);

        // TODO: 调用 cookie_renew_api_service.renew() 执行接口续期
        // TODO: 接口续期失败时降级为浏览器续期（通过 gRPC 调用 Python）
        // TODO: 两者都失败时触发后台密码登录
        // 当前为框架搭建阶段，后续接入 gRPC 客户端

        return "success";
    }

    /** 写入接口续期日志 */
    private void writeLog(String batchId, String accountId, String status, String errorMessage) {
        var logRecord = new XyScheduledApiCookieRenewLog();
        logRecord.setBatchId(batchId);
        logRecord.setAccountId(accountId);
        logRecord.setStatus(status);
        logRecord.setErrorMessage(errorMessage != null && errorMessage.length() > 500
            ? errorMessage.substring(0, 500) : errorMessage);
        logMapper.insert(logRecord);
    }
}
