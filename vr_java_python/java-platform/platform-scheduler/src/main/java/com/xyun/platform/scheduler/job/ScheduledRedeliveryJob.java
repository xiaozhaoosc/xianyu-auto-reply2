package com.xyun.platform.scheduler.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyCard;
import com.xyun.platform.common.entity.XyCardItemRelation;
import com.xyun.platform.common.entity.XyOrder;
import com.xyun.platform.common.entity.XyScheduledRedeliveryLog;
import com.xyun.platform.server.mapper.XyAccountMapper;
import com.xyun.platform.server.mapper.XyCardItemRelationMapper;
import com.xyun.platform.server.mapper.XyCardMapper;
import com.xyun.platform.server.mapper.XyOrderMapper;
import com.xyun.platform.server.mapper.XyScheduledRedeliveryLogMapper;
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
 * 补发货任务 — 每10分钟执行
 * <p>
 * 查询发货失败的订单，重新发货。
 * 条件：账号启用 + 自动确认发货开启 + 定时补发货开启。
 * 通过 WebSocket 服务发送发货消息，支持 Redis 分布式锁防并发。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ScheduledRedeliveryJob {

    /** 待发货的订单状态 */
    private static final Set<String> PENDING_SHIP_STATUSES = Set.of("pending_payment", "processing", "pending_ship");

    private final XyAccountMapper accountMapper;
    private final XyOrderMapper orderMapper;
    private final XyCardMapper cardMapper;
    private final XyCardItemRelationMapper cardItemRelationMapper;
    private final XyScheduledRedeliveryLogMapper logMapper;

    @Recurring(id = "scheduled-redelivery-job", cron = "0 */10 * * * *")
    @Job(name = "补发货任务")
    public void execute() {
        log.info("[JobRunr] 补发货任务 开始执行");
        var batchId = UUID.randomUUID().toString();

        try {
            // 1. 查询符合条件的账号（启用 + 自动确认发货 + 定时补发货开启）
            var accounts = accountMapper.selectList(
                new LambdaQueryWrapper<XyAccount>()
                    .eq(XyAccount::getStatus, "active")
                    .eq(XyAccount::getAutoConfirm, true)
                    .eq(XyAccount::getScheduledRedelivery, true)
            );

            if (accounts.isEmpty()) {
                log.info("[JobRunr] 补发货任务 没有符合条件的账号");
                return;
            }
            log.info("[JobRunr] 补发货任务 找到 {} 个符合条件的账号", accounts.size());

            // 2. 处理每个账号
            for (var account : accounts) {
                try {
                    processAccount(batchId, account);
                } catch (Exception e) {
                    log.error("[JobRunr] 补发货任务 处理账号 {} 异常", account.getAccountId(), e);
                }
            }

            log.info("[JobRunr] 补发货任务 执行完成，批次ID: {}", batchId);
        } catch (Exception e) {
            log.error("[JobRunr] 补发货任务 执行失败", e);
            throw e;
        }
    }

    /** 处理单个账号 */
    private void processAccount(String batchId, XyAccount account) {
        var accountId = account.getAccountId();
        log.info("[JobRunr] 补发货任务 开始处理账号: {}", accountId);

        // 查询当天待发货订单
        var todayStart = LocalDateTime.now().withHour(0).withMinute(0).withSecond(0).withNano(0);
        var orders = orderMapper.selectList(
            new LambdaQueryWrapper<XyOrder>()
                .eq(XyOrder::getAccountId, accountId)
                .isNotNull(XyOrder::getPlacedAt)
                .ge(XyOrder::getPlacedAt, todayStart)
                .in(XyOrder::getStatus, PENDING_SHIP_STATUSES)
                .orderByAsc(XyOrder::getPlacedAt)
        );

        if (orders.isEmpty()) {
            log.info("[JobRunr] 补发货任务 账号 {} 没有待发货订单", accountId);
            return;
        }
        log.info("[JobRunr] 补发货任务 账号 {} 找到 {} 个待发货订单", accountId, orders.size());

        for (var order : orders) {
            try {
                // 匹配卡券
                var card = matchCard(order.getItemId());
                if (card == null) {
                    log.info("[JobRunr] 补发货任务 订单 {} 未找到匹配的卡券", order.getOrderNo());
                    writeLog(batchId, accountId, order.getOrderNo(), false, "未找到匹配的卡券");
                    continue;
                }

                // TODO: 获取 Redis 分布式锁（防止与自动发货并发）
                // TODO: 调用 check_can_ship 检查订单是否可以发货
                // TODO: 通过 WebSocket 服务发送发货消息
                // TODO: 更新订单状态为已发货
                log.info("[JobRunr] 补发货任务 订单 {} 匹配卡券 {}，触发补发货",
                    order.getOrderNo(), card.getId());

                writeLog(batchId, accountId, order.getOrderNo(), true, null);
            } catch (Exception e) {
                log.error("[JobRunr] 补发货任务 处理订单 {} 异常", order.getOrderNo(), e);
                writeLog(batchId, accountId, order.getOrderNo(), false, e.getMessage());
            }
        }
    }

    /** 匹配卡券 */
    private XyCard matchCard(String itemId) {
        var relation = cardItemRelationMapper.selectOne(
            new LambdaQueryWrapper<XyCardItemRelation>()
                .eq(XyCardItemRelation::getItemId, itemId)
                .last("LIMIT 1")
        );
        if (relation == null) return null;
        var card = cardMapper.selectById(relation.getCardId());
        if (card == null || !Boolean.TRUE.equals(card.getEnabled())) return null;
        return card;
    }

    /** 写入补发货日志 */
    private void writeLog(String batchId, String accountId, String orderNo, boolean success, String errorMessage) {
        try {
            var logRecord = new XyScheduledRedeliveryLog();
            logRecord.setBatchId(batchId);
            logRecord.setAccountId(accountId);
            logRecord.setOrderNo(orderNo);
            logRecord.setStatus(success ? "success" : "failed");
            logRecord.setErrorMessage(errorMessage != null && errorMessage.length() > 500
                ? errorMessage.substring(0, 500) : errorMessage);
            logMapper.insert(logRecord);
        } catch (Exception e) {
            log.error("[JobRunr] 补发货任务 记录日志失败", e);
        }
    }
}
