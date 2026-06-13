package com.xyun.platform.server.auth;

import cn.dev33.satoken.stp.StpUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyUser;
import com.xyun.platform.common.exception.BusinessException;
import com.xyun.platform.server.mapper.XyUserMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 认证业务逻辑（基于 Sa-Token）
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final XyUserMapper userMapper;

    /** 用户登录，校验用户名密码后通过 Sa-Token 建立会话 */
    public Map<String, Object> login(String username, String password) {
        if (username == null || username.isBlank()) {
            throw new BusinessException("用户名不能为空");
        }
        if (password == null || password.isBlank()) {
            throw new BusinessException("密码不能为空");
        }

        var user = userMapper.selectOne(
                new LambdaQueryWrapper<XyUser>().eq(XyUser::getUsername, username)
        );
        if (user == null) {
            throw new BusinessException(401, "用户名或密码错误");
        }

        // 检查账号状态
        if ("SUSPENDED".equals(user.getStatus())) {
            throw new BusinessException(403, "账号已被封禁");
        }
        if ("DELETED".equals(user.getStatus())) {
            throw new BusinessException(403, "账号已被删除");
        }

        // 校验密码（简单比对，生产环境应使用 BCrypt）
        if (!password.equals(user.getPasswordHash())) {
            throw new BusinessException(401, "用户名或密码错误");
        }

        // Sa-Token 登录
        StpUtil.login(user.getId());

        // 更新最后登录时间
        user.setLastLoginAt(LocalDateTime.now());
        user.setLoginFailCount(0);
        userMapper.updateById(user);

        log.info("用户登录成功: username={}, id={}", username, user.getId());

        return Map.of(
                "token", StpUtil.getTokenValue(),
                "userId", user.getId(),
                "username", user.getUsername(),
                "role", user.getRole() != null ? user.getRole() : ""
        );
    }

    /** 用户登出 */
    public void logout() {
        StpUtil.logout();
        log.info("用户登出");
    }

    /** 获取当前登录用户信息 */
    public XyUser getCurrentUser() {
        var loginId = StpUtil.getLoginIdAsLong();
        var user = userMapper.selectById(loginId);
        if (user == null) {
            throw new BusinessException(404, "用户不存在");
        }
        // 清除敏感字段
        user.setPasswordHash(null);
        user.setSecretKey(null);
        return user;
    }
}
