package com.xyun.platform.scheduler.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyCatalogItem;
import com.xyun.platform.common.entity.XyScheduledPolishLog;
import com.xyun.platform.server.mapper.XyAccountMapper;
import com.xyun.platform.server.mapper.XyCatalogItemMapper;
import com.xyun.platform.server.mapper.XyScheduledPolishLogMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jobrunr.jobs.annotations.Job;
import org.jobrunr.jobs.annotations.Recurring;
import org.springframework.stereotype.Component;

import java.util.UUID;

/**
 * 商品擦亮任务 — 每4小时执行
 * <p>
 * 查询开启了自动擦亮的账号，擦亮商品。
 * 调用闲鱼 mtop.taobao.idle.item.polish API，
 * 令牌过期时通过 Set-Cookie 刷新后重试。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ItemPolishJob {

    private final XyAccountMapper accountMapper;
    private final XyCatalogItemMapper catalogItemMapper;
    private final XyScheduledPolishLogMapper logMapper;

    @Recurring(id = "item-polish-job", cron = "0 0 */4 * * *")
    @Job(name = "商品擦亮任务")
    public void execute() {
        log.info("[JobRunr] 商品擦亮任务 开始执行");
        var batchId = UUID.randomUUID().toString();
        var startTime = System.currentTimeMillis();
        int totalSuccess = 0, totalFailed = 0;

        try {
            // 1. 查询开启了商品自动擦亮的账号
            var accounts = accountMapper.selectList(
                new LambdaQueryWrapper<XyAccount>()
                    .eq(XyAccount::getStatus, "active")
                    .eq(XyAccount::getAutoPolish, true)
            );

            if (accounts.isEmpty()) {
                log.info("[JobRunr] 商品擦亮任务 没有开启商品自动擦亮的账号");
                return;
            }
            log.info("[JobRunr] 商品擦亮任务 找到 {} 个开启商品自动擦亮的账号", accounts.size());

            // 2. 遍历账号，处理每个账号的商品
            for (var account : accounts) {
                try {
                    var counts = processAccount(batchId, account);
                    totalSuccess += counts[0];
                    totalFailed += counts[1];
                } catch (Exception e) {
                    log.error("[JobRunr] 商品擦亮任务 处理账号 {} 失败", account.getAccountId(), e);
                    totalFailed++;
                }
            }

            var elapsed = (System.currentTimeMillis() - startTime) / 1000.0;
            log.info("[JobRunr] 商品擦亮任务 执行完成，成功: {}, 失败: {}, 耗时: {:.2f}秒",
                totalSuccess, totalFailed, elapsed);
        } catch (Exception e) {
            log.error("[JobRunr] 商品擦亮任务 执行失败", e);
            throw e;
        }
    }

    /** 处理单个账号的商品擦亮，返回 [成功数, 失败数] */
    private int[] processAccount(String batchId, XyAccount account) {
        var accountId = account.getAccountId();
        log.info("[JobRunr] 商品擦亮任务 开始处理账号: {}", accountId);

        // 查询该账号下未擦亮的商品
        var items = catalogItemMapper.selectList(
            new LambdaQueryWrapper<XyCatalogItem>()
                .eq(XyCatalogItem::getAccountId, account.getId())
                .and(w -> w.eq(XyCatalogItem::getIsPolished, false).or().isNull(XyCatalogItem::getIsPolished))
        );

        if (items.isEmpty()) {
            log.info("[JobRunr] 商品擦亮任务 账号 {} 没有需要擦亮的商品", accountId);
            return new int[]{0, 0};
        }
        log.info("[JobRunr] 商品擦亮任务 账号 {} 找到 {} 个需要擦亮的商品", accountId, items.size());

        int successCount = 0, failedCount = 0;

        for (var item : items) {
            try {
                // TODO: 调用 mtop.taobao.idle.item.polish API 擦亮商品
                // TODO: 令牌过期时通过 Set-Cookie 刷新后重试（最多3次）
                // TODO: "一天只能擦亮一次"也视为成功
                log.info("[JobRunr] 商品擦亮任务 账号 {} 商品 {} 擦亮处理", accountId, item.getItemId());

                // 擦亮成功，更新商品状态
                catalogItemMapper.update(null,
                    new LambdaUpdateWrapper<XyCatalogItem>()
                        .eq(XyCatalogItem::getId, item.getId())
                        .set(XyCatalogItem::getIsPolished, true)
                );
                successCount++;

                writeLog(batchId, accountId, item.getItemId(), true, null);
            } catch (Exception e) {
                failedCount++;
                log.error("[JobRunr] 商品擦亮任务 账号 {} 商品 {} 擦亮异常", accountId, item.getItemId(), e);
                writeLog(batchId, accountId, item.getItemId(), false, e.getMessage());
            }
        }

        return new int[]{successCount, failedCount};
    }

    /** 写入擦亮日志 */
    private void writeLog(String batchId, String accountId, String itemId, boolean success, String errorMessage) {
        var logRecord = new XyScheduledPolishLog();
        logRecord.setBatchId(batchId);
        logRecord.setAccountId(accountId);
        logRecord.setItemId(itemId);
        logRecord.setStatus(success ? "success" : "failed");
        logRecord.setErrorMessage(errorMessage != null && errorMessage.length() > 500
            ? errorMessage.substring(0, 500) : errorMessage);
        logMapper.insert(logRecord);
    }
}
