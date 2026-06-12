package com.xyun.platform.scheduler;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * JobRunr 定时任务调度服务 — 端口 8091
 */
@SpringBootApplication(scanBasePackages = "com.xyun.platform")
public class PlatformSchedulerApplication {

    public static void main(String[] args) {
        SpringApplication.run(PlatformSchedulerApplication.class, args);
    }
}