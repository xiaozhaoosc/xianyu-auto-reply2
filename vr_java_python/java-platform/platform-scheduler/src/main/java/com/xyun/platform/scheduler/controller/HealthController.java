package com.xyun.platform.scheduler.controller;

import com.xyun.platform.common.dto.ApiResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {

    @GetMapping("/health")
    public ApiResult<String> health() {
        return ApiResult.ok("OK");
    }
}