package com.xyun.platform.scheduler.controller;

import com.xyun.platform.common.dto.ApiResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController("schedulerHealthController")
public class SchedulerHealthController {

    @GetMapping("/scheduler/health")
    public ApiResult<String> health() {
        return ApiResult.ok("SCHEDULER_OK");
    }
}