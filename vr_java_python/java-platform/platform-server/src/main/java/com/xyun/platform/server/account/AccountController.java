package com.xyun.platform.server.account;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyAccount;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 账号管理 REST API
 */
@RestController
@RequestMapping("/api/accounts")
@RequiredArgsConstructor
public class AccountController {

    private final AccountService accountService;

    /** 分页查询账号列表 */
    @GetMapping
    public ApiResult<Page<XyAccount>> listAccounts(
            @RequestParam(defaultValue = "1") long current,
            @RequestParam(defaultValue = "10") long size) {
        return ApiResult.ok(accountService.listAccounts(current, size));
    }

    /** 查询账号详情 */
    @GetMapping("/{id}")
    public ApiResult<XyAccount> getAccount(@PathVariable Long id) {
        return ApiResult.ok(accountService.getAccount(id));
    }

    /** 添加账号 */
    @PostMapping
    public ApiResult<XyAccount> addAccount(@Valid @RequestBody XyAccount account) {
        return ApiResult.ok(accountService.addAccount(account));
    }

    /** 更新账号 */
    @PutMapping("/{id}")
    public ApiResult<XyAccount> updateAccount(@PathVariable Long id,
                                              @Valid @RequestBody XyAccount account) {
        account.setId(id);
        return ApiResult.ok(accountService.updateAccount(account));
    }

    /** 删除账号 */
    @DeleteMapping("/{id}")
    public ApiResult<Void> deleteAccount(@PathVariable Long id) {
        accountService.deleteAccount(id);
        return ApiResult.ok();
    }

    /** 触发账号登录 */
    @PostMapping("/{id}/login")
    public ApiResult<Void> triggerLogin(@PathVariable Long id) {
        accountService.triggerLogin(id);
        return ApiResult.ok();
    }

    /** 刷新账号 Cookie */
    @PostMapping("/{id}/refresh-cookie")
    public ApiResult<Void> refreshCookie(@PathVariable Long id) {
        accountService.refreshCookie(id);
        return ApiResult.ok();
    }

    /** 更新账号状态 */
    @PutMapping("/{id}/status")
    public ApiResult<Void> updateStatus(@PathVariable Long id,
                                        @RequestBody Map<String, String> body) {
        accountService.updateStatus(id, body.get("status"));
        return ApiResult.ok();
    }
}
