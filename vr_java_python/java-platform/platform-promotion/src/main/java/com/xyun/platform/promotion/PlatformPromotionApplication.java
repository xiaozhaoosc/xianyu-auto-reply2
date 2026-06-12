package com.xyun.platform.promotion;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 返佣系统服务 — 端口 8092
 */
@SpringBootApplication(scanBasePackages = "com.xyun.platform")
public class PlatformPromotionApplication {

    public static void main(String[] args) {
        SpringApplication.run(PlatformPromotionApplication.class, args);
    }
}