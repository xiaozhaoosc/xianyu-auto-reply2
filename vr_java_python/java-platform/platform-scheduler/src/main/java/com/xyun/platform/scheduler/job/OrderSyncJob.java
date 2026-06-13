package com.xyun.platform.scheduler.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.server.mapper.XyAccountMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jobrunr.jobs.annotations.Job;
import org.jobrunr.jobs.annotations.Recurring;
import org.springframework.stereotype.Component;

import java.util.Set;

/**
 * 订单拉取任务 — 每5分钟执行
 * <p>
 * 从闲鱼 API 拉取最新订单，写入 xy_orders 表。
 * 逐个账号调用闲鱼订单列表API获取订单并同步到数据库，
 * 单个账号失败不影响其他账号。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class OrderSyncJob {

    /** 非活跃状态集合 */
    private static final Set<String> INACTIVE_STATUSES = Set.of("inactive", "disabled", "suspended", "deleted");

    private final XyAccountMapper accountMapper;

    @Recurring(id = "order-sync-job", cron = "0 */5 * * * *")
    @Job(name = "订单拉取任务")
    public void execute() {
        log.info("[JobRunr] 订单拉取任务 开始执行");
        var startTime = System.currentTimeMillis();

        try {
            // 1. 查询所有启用状态的账号
            var accounts = accountMapper.selectList(
                new LambdaQueryWrapper<XyAccount>()
                    .notIn(XyAccount::getStatus, INACTIVE_STATUSES)
            );

            if (accounts.isEmpty()) {
                log.info("[JobRunr] 订单拉取任务 没有启用状态的账号，任务结束");
                return;
            }
            log.info("[JobRunr] 订单拉取任务 查询到 {} 个启用状态的账号", accounts.size());

            // 2. 逐个账号获取订单
            int successCount = 0, failedCount = 0, totalFetched = 0, totalNew = 0;

            for (var account : accounts) {
                try {
                    // TODO: 调用 OrderService.fetchXianyuOrders() 拉取订单
                    // query_code=ALL, 翻页拉取全部订单
                    log.info("[JobRunr] 订单拉取任务 账号 {} 获取完成", account.getAccountId());
                    successCount++;
                } catch (Exception e) {
                    failedCount++;
                    log.error("[JobRunr] 订单拉取任务 账号 {} 获取订单失败", account.getAccountId(), e);
                }
            }

            var elapsed = (System.currentTimeMillis() - startTime) / 1000.0;
            log.info("[JobRunr] 订单拉取任务 执行完成，账号: 成功{}/失败{}/共{}，耗时: {:.2f}秒",
                successCount, failedCount, accounts.size(), elapsed);
        } catch (Exception e) {
            log.error("[JobRunr] 订单拉取任务 执行异常", e);
            throw e;
        }
    }
}
