package com.xyun.platform.scheduler.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyScheduledLoginRenewLog;
import com.xyun.platform.server.mapper.XyAccountMapper;
import com.xyun.platform.server.mapper.XyScheduledLoginRenewLogMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jobrunr.jobs.annotations.Job;
import org.jobrunr.jobs.annotations.Recurring;
import org.springframework.stereotype.Component;

import java.util.Set;
import java.util.UUID;

/**
 * 登录续期任务 — 每6小时执行
 * <p>
 * 查询长时间未登录的账号，通过 gRPC 调用 Python 执行重新登录。
 * 检查 mtop.taobao.idlemessage.pc.loginuser.get 接口判断登录状态，
 * Session过期时触发后台密码登录。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class LoginRenewJob {

    /** 非活跃状态集合 */
    private static final Set<String> INACTIVE_STATUSES = Set.of("inactive", "disabled", "suspended", "deleted");

    private final XyAccountMapper accountMapper;
    private final XyScheduledLoginRenewLogMapper logMapper;

    @Recurring(id = "login-renew-job", cron = "0 0 */6 * * *")
    @Job(name = "登录续期任务")
    public void execute() {
        log.info("[JobRunr] 登录续期任务 开始执行");
        var batchId = UUID.randomUUID().toString();
        int successCount = 0, tokenRefreshedCount = 0, sessionExpiredCount = 0, failedCount = 0;

        try {
            // 1. 查询所有启用状态的账号
            var accounts = accountMapper.selectList(
                new LambdaQueryWrapper<XyAccount>()
                    .notIn(XyAccount::getStatus, INACTIVE_STATUSES)
            );

            if (accounts.isEmpty()) {
                log.info("[JobRunr] 登录续期任务 没有启用状态的账号");
                return;
            }
            log.info("[JobRunr] 登录续期任务 找到 {} 个启用状态的账号", accounts.size());

            // 2. 遍历账号，执行续期检查
            for (var account : accounts) {
                try {
                    var result = renewAccount(account);

                    // 记录日志
                    writeLog(batchId, account.getAccountId(), result.status(), result.message());

                    switch (result.status()) {
                        case "success" -> successCount++;
                        case "token_refreshed" -> tokenRefreshedCount++;
                        case "session_expired" -> sessionExpiredCount++;
                        default -> failedCount++;
                    }
                } catch (Exception e) {
                    failedCount++;
                    log.error("[JobRunr] 登录续期任务 账号 {} 处理异常", account.getAccountId(), e);
                    writeLog(batchId, account.getAccountId(), "failed", e.getMessage());
                }
            }

            log.info("[JobRunr] 登录续期任务 执行完成，成功: {}, 令牌刷新: {}, Session过期: {}, 失败: {}",
                successCount, tokenRefreshedCount, sessionExpiredCount, failedCount);
        } catch (Exception e) {
            log.error("[JobRunr] 登录续期任务 执行失败", e);
            throw e;
        }
    }

    /** 对单个账号执行续期检查 */
    private RenewResult renewAccount(XyAccount account) {
        var accountId = account.getAccountId();
        log.info("[JobRunr] 登录续期任务 开始检查账号: {}", accountId);

        // TODO: 调用 mtop.taobao.idlemessage.pc.loginuser.get 接口检查登录状态
        // TODO: 令牌过期时从 Set-Cookie 提取新Cookie，更新数据库
        // TODO: Session过期时通过 gRPC 触发后台密码登录
        // 当前为框架搭建阶段，后续接入 gRPC 客户端

        return new RenewResult("success", "登录状态正常");
    }

    /** 续期结果记录 */
    private record RenewResult(String status, String message) {}

    /** 写入登录续期日志 */
    private void writeLog(String batchId, String accountId, String status, String errorMessage) {
        var logRecord = new XyScheduledLoginRenewLog();
        logRecord.setBatchId(batchId);
        logRecord.setAccountId(accountId);
        logRecord.setStatus(status);
        logRecord.setErrorMessage(errorMessage != null && errorMessage.length() > 500
            ? errorMessage.substring(0, 500) : errorMessage);
        logMapper.insert(logRecord);
    }
}
