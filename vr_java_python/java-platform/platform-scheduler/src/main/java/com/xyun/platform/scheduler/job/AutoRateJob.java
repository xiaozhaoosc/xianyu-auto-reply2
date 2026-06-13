package com.xyun.platform.scheduler.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyAutoRateConfig;
import com.xyun.platform.common.entity.XyOrder;
import com.xyun.platform.common.entity.XyScheduledRateLog;
import com.xyun.platform.server.mapper.XyAccountMapper;
import com.xyun.platform.server.mapper.XyAutoRateConfigMapper;
import com.xyun.platform.server.mapper.XyOrderMapper;
import com.xyun.platform.server.mapper.XyScheduledRateLogMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jobrunr.jobs.annotations.Job;
import org.jobrunr.jobs.annotations.Recurring;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * 自动评价任务 — 每30分钟执行
 * <p>
 * 查询已收货未评价的订单，自动评价。
 * 条件：账号启用 + 定时补评价开启 + 自动评价配置已启用。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AutoRateJob {

    private final XyAccountMapper accountMapper;
    private final XyAutoRateConfigMapper autoRateConfigMapper;
    private final XyOrderMapper orderMapper;
    private final XyScheduledRateLogMapper logMapper;

    @Recurring(id = "auto-rate-job", cron = "0 */30 * * * *")
    @Job(name = "自动评价任务")
    public void execute() {
        log.info("[JobRunr] 自动评价任务 开始执行");
        var batchId = UUID.randomUUID().toString();

        try {
            // 1. 查询符合条件的账号（启用 + 定时补评价开启 + 自动评价配置已启用）
            var accounts = getEligibleAccounts();
            if (accounts.isEmpty()) {
                log.info("[JobRunr] 自动评价任务 没有符合条件的账号");
                return;
            }
            log.info("[JobRunr] 自动评价任务 找到 {} 个符合条件的账号", accounts.size());

            // 2. 处理每个账号
            for (var account : accounts) {
                try {
                    processAccount(batchId, account);
                } catch (Exception e) {
                    log.error("[JobRunr] 自动评价任务 处理账号 {} 异常", account.getAccountId(), e);
                }
            }

            log.info("[JobRunr] 自动评价任务 执行完成，批次ID: {}", batchId);
        } catch (Exception e) {
            log.error("[JobRunr] 自动评价任务 执行失败", e);
            throw e;
        }
    }

    /** 获取符合条件的账号列表 */
    private List<XyAccount> getEligibleAccounts() {
        // 先查询已启用的自动评价配置的accountId
        var enabledConfigs = autoRateConfigMapper.selectList(
            new LambdaQueryWrapper<XyAutoRateConfig>()
                .eq(XyAutoRateConfig::getEnabled, true)
        );
        if (enabledConfigs.isEmpty()) {
            return List.of();
        }

        var accountIds = enabledConfigs.stream()
            .map(XyAutoRateConfig::getAccountId)
            .toList();

        return accountMapper.selectList(
            new LambdaQueryWrapper<XyAccount>()
                .eq(XyAccount::getStatus, "active")
                .eq(XyAccount::getScheduledRate, true)
                .in(XyAccount::getAccountId, accountIds)
        );
    }

    /** 处理单个账号 */
    private void processAccount(String batchId, XyAccount account) {
        var accountId = account.getAccountId();
        log.info("[JobRunr] 自动评价任务 开始处理账号: {}", accountId);

        // 查询当天待评价订单
        var todayStart = LocalDateTime.now().withHour(0).withMinute(0).withSecond(0).withNano(0);
        var orders = orderMapper.selectList(
            new LambdaQueryWrapper<XyOrder>()
                .eq(XyOrder::getAccountId, accountId)
                .isNotNull(XyOrder::getPlacedAt)
                .ge(XyOrder::getPlacedAt, todayStart)
                .in(XyOrder::getStatus, List.of("shipped", "completed"))
                .and(w -> w.eq(XyOrder::getIsRated, false).or().isNull(XyOrder::getIsRated))
                .orderByAsc(XyOrder::getPlacedAt)
        );

        if (orders.isEmpty()) {
            log.info("[JobRunr] 自动评价任务 账号 {} 没有待评价订单", accountId);
            return;
        }
        log.info("[JobRunr] 自动评价任务 账号 {} 找到 {} 个待评价订单", accountId, orders.size());

        for (var order : orders) {
            try {
                // TODO: 调用 check_can_rate 检查是否可以评价
                // TODO: 调用 RateService.rate_buyer() 执行评价
                // TODO: 更新订单 is_rated 状态
                log.info("[JobRunr] 自动评价任务 订单 {} 评价处理", order.getOrderNo());

                writeLog(batchId, accountId, order.getOrderNo(), true, null);
            } catch (Exception e) {
                log.error("[JobRunr] 自动评价任务 处理订单 {} 异常", order.getOrderNo(), e);
                writeLog(batchId, accountId, order.getOrderNo(), false, e.getMessage());
            }
        }
    }

    /** 写入评价日志 */
    private void writeLog(String batchId, String accountId, String orderNo, boolean success, String errorMessage) {
        var logRecord = new XyScheduledRateLog();
        logRecord.setBatchId(batchId);
        logRecord.setAccountId(accountId);
        logRecord.setOrderNo(orderNo);
        logRecord.setStatus(success ? "success" : "failed");
        logRecord.setErrorMessage(errorMessage != null && errorMessage.length() > 500
            ? errorMessage.substring(0, 500) : errorMessage);
        logMapper.insert(logRecord);
    }
}
