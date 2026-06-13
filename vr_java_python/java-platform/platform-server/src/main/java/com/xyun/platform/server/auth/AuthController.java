package com.xyun.platform.server.auth;

import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyUser;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 认证管理 REST API
 */
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

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

    /** 获取当前登录用户信息 */
    @GetMapping("/userinfo")
    public ApiResult<XyUser> userinfo() {
        return ApiResult.ok(authService.getCurrentUser());
    }
}
