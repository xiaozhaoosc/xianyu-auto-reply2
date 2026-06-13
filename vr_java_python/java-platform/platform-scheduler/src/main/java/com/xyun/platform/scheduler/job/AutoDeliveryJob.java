package com.xyun.platform.scheduler.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyCard;
import com.xyun.platform.common.entity.XyCardItemRelation;
import com.xyun.platform.common.entity.XyOrder;
import com.xyun.platform.server.mapper.XyAccountMapper;
import com.xyun.platform.server.mapper.XyCardItemRelationMapper;
import com.xyun.platform.server.mapper.XyCardMapper;
import com.xyun.platform.server.mapper.XyOrderMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jobrunr.jobs.annotations.Job;
import org.jobrunr.jobs.annotations.Recurring;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Set;

/**
 * 自动发货任务 — 每3分钟执行
 * <p>
 * 查询待发货订单，匹配卡券，通过 gRPC 调用 Python 发货。
 * 条件：账号启用 + 自动确认发货开启 + 订单状态为待发货。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AutoDeliveryJob {

    /** 待发货的订单状态 */
    private static final Set<String> PENDING_SHIP_STATUSES = Set.of("pending_payment", "processing", "pending_ship");
    /** 非活跃状态集合 */
    private static final Set<String> INACTIVE_STATUSES = Set.of("inactive", "disabled", "suspended", "deleted");

    private final XyAccountMapper accountMapper;
    private final XyOrderMapper orderMapper;
    private final XyCardMapper cardMapper;
    private final XyCardItemRelationMapper cardItemRelationMapper;

    @Recurring(id = "auto-delivery-job", cron = "0 */3 * * * *")
    @Job(name = "自动发货任务")
    public void execute() {
        log.info("[JobRunr] 自动发货任务 开始执行");
        var startTime = System.currentTimeMillis();

        try {
            // 1. 查询启用且开启自动确认发货的账号
            var accounts = accountMapper.selectList(
                new LambdaQueryWrapper<XyAccount>()
                    .eq(XyAccount::getStatus, "active")
                    .eq(XyAccount::getAutoConfirm, true)
            );

            if (accounts.isEmpty()) {
                log.info("[JobRunr] 自动发货任务 没有符合条件的账号");
                return;
            }
            log.info("[JobRunr] 自动发货任务 找到 {} 个符合条件的账号", accounts.size());

            int totalSuccess = 0, totalFailed = 0;

            for (var account : accounts) {
                try {
                    var counts = processAccount(account);
                    totalSuccess += counts[0];
                    totalFailed += counts[1];
                } catch (Exception e) {
                    log.error("[JobRunr] 自动发货任务 处理账号 {} 失败", account.getAccountId(), e);
                    totalFailed++;
                }
            }

            var elapsed = (System.currentTimeMillis() - startTime) / 1000.0;
            log.info("[JobRunr] 自动发货任务 执行完成，成功: {}, 失败: {}, 耗时: {:.2f}秒",
                totalSuccess, totalFailed, elapsed);
        } catch (Exception e) {
            log.error("[JobRunr] 自动发货任务 执行失败", e);
            throw e;
        }
    }

    /** 处理单个账号的待发货订单，返回 [成功数, 失败数] */
    private int[] processAccount(XyAccount account) {
        var accountId = account.getAccountId();
        log.info("[JobRunr] 自动发货任务 开始处理账号: {}", accountId);

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
            log.info("[JobRunr] 自动发货任务 账号 {} 没有待发货订单", accountId);
            return new int[]{0, 0};
        }
        log.info("[JobRunr] 自动发货任务 账号 {} 找到 {} 个待发货订单", accountId, orders.size());

        int successCount = 0, failedCount = 0;

        for (var order : orders) {
            try {
                // 匹配卡券
                var card = matchCard(order.getItemId(), order.getSpecName(), order.getSpecValue());
                if (card == null) {
                    log.info("[JobRunr] 自动发货任务 订单 {} 未找到匹配的卡券", order.getOrderNo());
                    failedCount++;
                    continue;
                }

                // TODO: 通过 gRPC 调用 Python WebSocket 服务执行发货
                // deliver_url = websocket_service_url + "/internal/orders/deliver"
                log.info("[JobRunr] 自动发货任务 订单 {} 匹配卡券 {}，触发发货",
                    order.getOrderNo(), card.getId());
                successCount++;
            } catch (Exception e) {
                failedCount++;
                log.error("[JobRunr] 自动发货任务 处理订单 {} 异常", order.getOrderNo(), e);
            }
        }

        return new int[]{successCount, failedCount};
    }

    /** 匹配卡券：通过关联表查询 */
    private XyCard matchCard(String itemId, String specName, String specValue) {
        var relation = cardItemRelationMapper.selectOne(
            new LambdaQueryWrapper<XyCardItemRelation>()
                .eq(XyCardItemRelation::getItemId, itemId)
                .last("LIMIT 1")
        );
        if (relation == null) {
            return null;
        }
        var card = cardMapper.selectById(relation.getCardId());
        if (card == null || !Boolean.TRUE.equals(card.getEnabled())) {
            return null;
        }
        return card;
    }
}
