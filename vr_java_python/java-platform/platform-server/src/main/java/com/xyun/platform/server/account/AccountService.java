package com.xyun.platform.server.account;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyAccountLoginLog;
import com.xyun.platform.common.exception.BusinessException;
import com.xyun.platform.server.mapper.XyAccountLoginLogMapper;
import com.xyun.platform.server.mapper.XyAccountMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

/**
 * 账号管理业务逻辑
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AccountService {

    private final XyAccountMapper accountMapper;
    private final XyAccountLoginLogMapper loginLogMapper;

    /** 分页查询账号列表 */
    public Page<XyAccount> listAccounts(long current, long size) {
        return accountMapper.selectPage(
                new Page<>(current, size),
                new LambdaQueryWrapper<XyAccount>().orderByDesc(XyAccount::getCreatedAt)
        );
    }

    /** 查询账号详情，不存在则抛出业务异常 */
    public XyAccount getAccount(Long id) {
        var account = accountMapper.selectById(id);
        if (account == null) {
            throw new BusinessException(404, "账号不存在");
        }
        return account;
    }

    /** 添加账号 */
    public XyAccount addAccount(XyAccount account) {
        accountMapper.insert(account);
        return account;
    }

    /** 更新账号信息 */
    public XyAccount updateAccount(XyAccount account) {
        getAccount(account.getId());
        accountMapper.updateById(account);
        return account;
    }

    /** 删除账号 */
    public void deleteAccount(Long id) {
        getAccount(id);
        accountMapper.deleteById(id);
    }

    /** 触发账号登录，记录登录日志 */
    public void triggerLogin(Long id) {
        var account = getAccount(id);
        var loginLog = new XyAccountLoginLog();
        loginLog.setOwnerId(account.getOwnerId());
        loginLog.setAccountId(account.getId());
        loginLog.setAccountIdentifier(account.getAccountId());
        loginLog.setUsername(account.getUsername());
        loginLog.setTriggerReason("MANUAL");
        loginLog.setLoginStatus("TRIGGERED");
        loginLogMapper.insert(loginLog);

        // 更新账号最后登录时间
        account.setLastLoginAt(LocalDateTime.now());
        accountMapper.updateById(account);
        log.info("触发账号登录: id={}, accountId={}", id, account.getAccountId());
    }

    /** 刷新账号 Cookie，记录登录日志 */
    public void refreshCookie(Long id) {
        var account = getAccount(id);
        var loginLog = new XyAccountLoginLog();
        loginLog.setOwnerId(account.getOwnerId());
        loginLog.setAccountId(account.getId());
        loginLog.setAccountIdentifier(account.getAccountId());
        loginLog.setUsername(account.getUsername());
        loginLog.setTriggerReason("COOKIE_REFRESH");
        loginLog.setLoginStatus("TRIGGERED");
        loginLogMapper.insert(loginLog);

        // 更新账号最后刷新时间
        account.setLastRefreshAt(LocalDateTime.now());
        accountMapper.updateById(account);
        log.info("触发Cookie刷新: id={}, accountId={}", id, account.getAccountId());
    }

    /** 更新账号状态 */
    public void updateStatus(Long id, String status) {
        if (status == null || status.isBlank()) {
            throw new BusinessException("状态不能为空");
        }
        var account = getAccount(id);
        account.setStatus(status);
        accountMapper.updateById(account);
        log.info("更新账号状态: id={}, status={}", id, status);
    }
}
