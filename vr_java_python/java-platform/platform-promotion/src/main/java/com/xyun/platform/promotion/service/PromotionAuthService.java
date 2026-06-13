package com.xyun.platform.promotion.service;

import cn.dev33.satoken.stp.StpUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.xyun.platform.common.entity.XyUser;
import com.xyun.platform.common.exception.BusinessException;
import com.xyun.platform.server.mapper.XyUserMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 返佣系统认证服务（基于 Sa-Token）
 *
 * <p>职责：用户登录校验、登录失败锁定、会话管理</p>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PromotionAuthService {

    /** 最大登录失败次数 */
    private static final int MAX_LOGIN_FAIL_COUNT = 3;
    /** 登录锁定时长（小时） */
    private static final int LOGIN_LOCK_HOURS = 2;

    private final XyUserMapper userMapper;

    /**
     * 用户登录
     *
     * @param username 用户名
     * @param password 密码
     * @return 登录结果信息
     */
    public Map<String, Object> login(String username, String password) {
        if (username == null || username.isBlank()) {
            throw new BusinessException("请输入用户名");
        }
        if (password == null || password.isBlank()) {
            throw new BusinessException("请输入密码");
        }

        // 按用户名查找用户（忽略大小写）
        var user = userMapper.selectOne(
                new LambdaQueryWrapper<XyUser>()
                        .eq(XyUser::getUsername, username)
        );
        if (user == null) {
            throw new BusinessException(401, "用户名或密码错误");
        }

        // 检查账号锁定状态
        checkLoginLocked(user);

        // 校验密码
        if (!verifyPassword(user, password)) {
            handleLoginFail(user);
            throw new BusinessException(401, buildFailMessage(user));
        }

        // 检查账号状态
        if ("SUSPENDED".equals(user.getStatus())) {
            throw new BusinessException(403, "账号已被封禁");
        }

        // 登录成功：重置失败计数，建立 Sa-Token 会话
        resetLoginFail(user);
        StpUtil.login(user.getId());

        log.info("返佣系统用户登录成功: username={}, id={}", username, user.getId());

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
        log.info("返佣系统用户登出");
    }

    // ==================== 私有方法 ====================

    /** 检查用户是否处于登录锁定状态 */
    private void checkLoginLocked(XyUser user) {
        var lockedUntil = user.getLoginLockedUntil();
        if (lockedUntil != null && lockedUntil.isAfter(LocalDateTime.now())) {
            var remainingMinutes = java.time.Duration.between(LocalDateTime.now(), lockedUntil).toMinutes();
            var timeStr = remainingMinutes > 60
                    ? (remainingMinutes / 60) + "小时" + (remainingMinutes % 60) + "分钟"
                    : remainingMinutes + "分钟";
            throw new BusinessException(403, "账号已被锁定，请" + timeStr + "后再试");
        }
    }

    /** 验证密码 */
    private boolean verifyPassword(XyUser user, String password) {
        var storedHash = user.getPasswordHash();
        if (storedHash == null || storedHash.isBlank()) {
            return false;
        }
        // 简单比对（生产环境应使用 BCrypt）
        return password.equals(storedHash);
    }

    /** 处理登录失败：增加失败计数，超过阈值则锁定 */
    private void handleLoginFail(XyUser user) {
        var failCount = (user.getLoginFailCount() != null ? user.getLoginFailCount() : 0) + 1;
        user.setLoginFailCount(failCount);

        if (failCount >= MAX_LOGIN_FAIL_COUNT) {
            user.setLoginLockedUntil(LocalDateTime.now().plusHours(LOGIN_LOCK_HOURS));
            log.warn("用户登录失败次数过多，已锁定: userId={}", user.getId());
        }

        userMapper.updateById(user);
    }

    /** 登录成功后重置失败计数 */
    private void resetLoginFail(XyUser user) {
        if (user.getLoginFailCount() != null && user.getLoginFailCount() > 0) {
            user.setLoginFailCount(0);
            user.setLoginLockedUntil(null);
            userMapper.updateById(user);
        }
        user.setLastLoginAt(LocalDateTime.now());
        userMapper.updateById(user);
    }

    /** 构建登录失败提示信息 */
    private String buildFailMessage(XyUser user) {
        var remaining = MAX_LOGIN_FAIL_COUNT - (user.getLoginFailCount() != null ? user.getLoginFailCount() : 0);
        if (remaining <= 0) {
            return "密码错误次数过多，账号已被锁定" + LOGIN_LOCK_HOURS + "小时";
        }
        return "用户名或密码错误，还剩" + remaining + "次尝试机会";
    }
}
