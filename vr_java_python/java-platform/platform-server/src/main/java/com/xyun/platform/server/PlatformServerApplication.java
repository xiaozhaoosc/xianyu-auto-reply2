package com.xyun.platform.server;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 管理后台 REST API 服务 — 端口 8089
 */
@SpringBootApplication(scanBasePackages = "com.xyun.platform")
public class PlatformServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(PlatformServerApplication.class, args);
    }
}