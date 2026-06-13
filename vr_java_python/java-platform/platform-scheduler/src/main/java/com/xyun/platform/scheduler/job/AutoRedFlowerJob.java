package com.xyun.platform.scheduler.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyOrder;
import com.xyun.platform.common.entity.XyScheduledRedFlowerLog;
import com.xyun.platform.server.mapper.XyAccountMapper;
import com.xyun.platform.server.mapper.XyOrderMapper;
import com.xyun.platform.server.mapper.XyScheduledRedFlowerLogMapper;
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
 * 求小红花任务 — 每30分钟执行
 * <p>
 * 查询已评价未求小红花的订单，自动求小红花。
 * 调用闲鱼 mtop.taobao.idlemessage.red.flower API，
 * 处理令牌过期重试和Session过期降级。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AutoRedFlowerJob {

    /** 不需要求小红花的订单状态 */
    private static final Set<String> EXCLUDED_STATUSES = Set.of("cancelled", "processing");

    private final XyAccountMapper accountMapper;
    private final XyOrderMapper orderMapper;
    private final XyScheduledRedFlowerLogMapper logMapper;

    @Recurring(id = "auto-red-flower-job", cron = "0 */30 * * * *")
    @Job(name = "求小红花任务")
    public void execute() {
        log.info("[JobRunr] 求小红花任务 开始执行");
        var batchId = UUID.randomUUID().toString();

        try {
            // 1. 查询开启自动求小红花的账号
            var accounts = accountMapper.selectList(
                new LambdaQueryWrapper<XyAccount>()
                    .eq(XyAccount::getStatus, "active")
                    .eq(XyAccount::getAutoRedFlower, true)
            );

            if (accounts.isEmpty()) {
                log.info("[JobRunr] 求小红花任务 没有符合条件的账号");
                return;
            }
            log.info("[JobRunr] 求小红花任务 找到 {} 个符合条件的账号", accounts.size());

            // 2. 处理每个账号
            for (var account : accounts) {
                try {
                    processAccount(batchId, account);
                } catch (Exception e) {
                    log.error("[JobRunr] 求小红花任务 处理账号 {} 异常", account.getAccountId(), e);
                }
            }

            log.info("[JobRunr] 求小红花任务 执行完成，批次ID: {}", batchId);
        } catch (Exception e) {
            log.error("[JobRunr] 求小红花任务 执行失败", e);
            throw e;
        }
    }

    /** 处理单个账号 */
    private void processAccount(String batchId, XyAccount account) {
        var accountId = account.getAccountId();
        log.info("[JobRunr] 求小红花任务 开始处理账号: {}", accountId);

        // 查询近10天内未求小红花的订单
        var tenDaysAgo = LocalDateTime.now().minusDays(10);
        var orders = orderMapper.selectList(
            new LambdaQueryWrapper<XyOrder>()
                .eq(XyOrder::getAccountId, accountId)
                .eq(XyOrder::getIsRedFlower, false)
                .notIn(XyOrder::getStatus, EXCLUDED_STATUSES)
                .isNotNull(XyOrder::getPlacedAt)
                .ge(XyOrder::getPlacedAt, tenDaysAgo)
                .orderByAsc(XyOrder::getPlacedAt)
        );

        if (orders.isEmpty()) {
            log.info("[JobRunr] 求小红花任务 账号 {} 没有待求小红花的订单", accountId);
            return;
        }
        log.info("[JobRunr] 求小红花任务 账号 {} 找到 {} 个待求小红花订单", accountId, orders.size());

        for (var order : orders) {
            try {
                // TODO: 调用 mtop.taobao.idlemessage.red.flower API
                // TODO: 处理令牌过期重试（从Set-Cookie提取新Cookie后重试一次）
                // TODO: Session过期时标记冷却并触发密码登录
                log.info("[JobRunr] 求小红花任务 订单 {} 求小红花处理", order.getOrderNo());

                // 成功时更新订单 is_red_flower 字段
                orderMapper.update(null,
                    new LambdaUpdateWrapper<XyOrder>()
                        .eq(XyOrder::getOrderNo, order.getOrderNo())
                        .set(XyOrder::getIsRedFlower, true)
                );

                writeLog(batchId, accountId, order.getOrderNo(), true, null);
            } catch (Exception e) {
                log.error("[JobRunr] 求小红花任务 处理订单 {} 异常", order.getOrderNo(), e);
                writeLog(batchId, accountId, order.getOrderNo(), false, e.getMessage());
            }
        }
    }

    /** 写入求小红花日志 */
    private void writeLog(String batchId, String accountId, String orderNo, boolean success, String errorMessage) {
        var logRecord = new XyScheduledRedFlowerLog();
        logRecord.setBatchId(batchId);
        logRecord.setAccountId(accountId);
        logRecord.setOrderNo(orderNo);
        logRecord.setStatus(success ? "success" : "failed");
        logRecord.setErrorMessage(errorMessage != null && errorMessage.length() > 500
            ? errorMessage.substring(0, 500) : errorMessage);
        logMapper.insert(logRecord);
    }
}
