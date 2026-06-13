package com.xyun.platform.promotion.config;

import cn.dev33.satoken.interceptor.SaInterceptor;
import cn.dev33.satoken.stp.StpUtil;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 返佣系统 Sa-Token 安全配置
 *
 * <p>排除 /api/promotion/auth/** 路径，其余接口需登录后访问</p>
 */
@Configuration
public class SecurityConfig implements WebMvcConfigurer {

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new SaInterceptor(handle -> StpUtil.checkLogin()))
                .addPathPatterns("/api/promotion/**")
                .excludePathPatterns(
                        "/api/promotion/auth/**",
                        "/health"
                );
    }
}
