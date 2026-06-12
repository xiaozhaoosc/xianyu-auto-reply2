package com.xyun.platform.server.controller;

import com.xyun.platform.common.dto.ApiResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 健康检查
 */
@RestController
public class HealthController {

    @GetMapping("/health")
    public ApiResult<String> health() {
        return ApiResult.ok("OK");
    }
}