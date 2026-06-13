package com.xyun.platform.scheduler.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyGoofishCrawlJob;
import com.xyun.platform.server.mapper.XyAccountMapper;
import com.xyun.platform.server.mapper.XyGoofishCrawlJobMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jobrunr.jobs.annotations.Job;
import org.jobrunr.jobs.annotations.Recurring;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.Set;

/**
 * Goofish 采集任务 — 每15分钟执行
 * <p>
 * 执行 Goofish 商品采集任务。
 * 查询已启用的采集任务，通过 gRPC 调用 Python 运行时执行采集。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class GoofishCrawlJob {

    /** 非活跃状态集合 */
    private static final Set<String> INACTIVE_STATUSES = Set.of("inactive", "disabled", "suspended", "deleted");

    private final XyGoofishCrawlJobMapper crawlJobMapper;
    private final XyAccountMapper accountMapper;

    @Recurring(id = "goofish-crawl-job", cron = "0 */15 * * * *")
    @Job(name = "Goofish采集任务")
    public void execute() {
        log.info("[JobRunr] Goofish采集任务 开始执行");
        var startTime = System.currentTimeMillis();

        try {
            // 1. 查询已启用的采集任务
            var crawlJobs = crawlJobMapper.selectList(
                new LambdaQueryWrapper<XyGoofishCrawlJob>()
                    .eq(XyGoofishCrawlJob::getEnabled, true)
            );

            if (crawlJobs.isEmpty()) {
                log.info("[JobRunr] Goofish采集任务 没有已启用的采集任务");
                return;
            }
            log.info("[JobRunr] Goofish采集任务 找到 {} 个已启用的采集任务", crawlJobs.size());

            int successCount = 0, failedCount = 0;

            for (var crawlJob : crawlJobs) {
                try {
                    // 检查采集间隔是否满足
                    if (crawlJob.getLastRunAt() != null && crawlJob.getIntervalSeconds() != null) {
                        var nextRunTime = crawlJob.getLastRunAt().plusSeconds(crawlJob.getIntervalSeconds());
                        if (nextRunTime.isAfter(LocalDateTime.now())) {
                            log.info("[JobRunr] Goofish采集任务 采集任务 {} 未到执行时间，跳过", crawlJob.getId());
                            continue;
                        }
                    }

                    // 检查关联账号是否启用
                    if (crawlJob.getCookieId() != null) {
                        var account = accountMapper.selectOne(
                            new LambdaQueryWrapper<XyAccount>()
                                .eq(XyAccount::getAccountId, crawlJob.getCookieId())
                        );
                        if (account == null || INACTIVE_STATUSES.contains(account.getStatus())) {
                            log.info("[JobRunr] Goofish采集任务 采集任务 {} 关联账号不可用，跳过", crawlJob.getId());
                            continue;
                        }
                    }

                    // TODO: 通过 gRPC 调用 Python 运行时执行采集
                    log.info("[JobRunr] Goofish采集任务 执行采集任务 {}，关键词: {}",
                        crawlJob.getId(), crawlJob.getKeyword());

                    // 更新最后执行时间
                    crawlJob.setLastRunAt(LocalDateTime.now());
                    crawlJobMapper.updateById(crawlJob);
                    successCount++;
                } catch (Exception e) {
                    failedCount++;
                    log.error("[JobRunr] Goofish采集任务 采集任务 {} 执行异常", crawlJob.getId(), e);
                    // 记录错误信息
                    crawlJob.setLastError(e.getMessage() != null && e.getMessage().length() > 500
                        ? e.getMessage().substring(0, 500) : e.getMessage());
                    crawlJobMapper.updateById(crawlJob);
                }
            }

            var elapsed = (System.currentTimeMillis() - startTime) / 1000.0;
            log.info("[JobRunr] Goofish采集任务 执行完成，成功: {}, 失败: {}, 耗时: {:.2f}秒",
                successCount, failedCount, elapsed);
        } catch (Exception e) {
            log.error("[JobRunr] Goofish采集任务 执行失败", e);
            throw e;
        }
    }
}
