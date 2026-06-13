package com.xyun.platform.promotion.controller;

import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.promotion.service.PromotionAuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 返佣系统认证 REST API
 */
@RestController
@RequestMapping("/api/promotion/auth")
@RequiredArgsConstructor
public class AuthController {

    private final PromotionAuthService authService;

    /** 用户登录 */
    @PostMapping("/login")
    public ApiResult<Map<String, Object>> login(@RequestBody Map<String, String> body) {
        var username = body.get("username");
        var password = body.get("password");
        return ApiResult.ok(authService.login(username, password));
    }

    /** 用户登出 */
    @PostMapping("/logout")
    public ApiResult<Void> logout() {
        authService.logout();
        return ApiResult.ok();
    }
}
