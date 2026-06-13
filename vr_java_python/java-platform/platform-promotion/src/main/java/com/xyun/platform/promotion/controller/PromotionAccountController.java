package com.xyun.platform.promotion.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyDockRecord;
import com.xyun.platform.promotion.service.PromotionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 返佣账号管理 REST API
 */
@RestController
@RequestMapping("/api/promotion/accounts")
@RequiredArgsConstructor
public class PromotionAccountController {

    private final PromotionService promotionService;

    /** 返佣账号列表（分页） */
    @GetMapping
    public ApiResult<Page<XyDockRecord>> listAccounts(
            @RequestParam(defaultValue = "1") int current,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) Long userId) {
        return promotionService.listDockRecords(current, size, userId);
    }

    /** 创建返佣账号 */
    @PostMapping
    public ApiResult<XyDockRecord> createAccount(@RequestBody XyDockRecord record) {
        return promotionService.createDockRecord(record);
    }

    /** 更新返佣账号 */
    @PutMapping("/{id}")
    public ApiResult<XyDockRecord> updateAccount(
            @PathVariable Long id, @RequestBody XyDockRecord record) {
        return promotionService.updateDockRecord(id, record);
    }

    /** 删除返佣账号 */
    @DeleteMapping("/{id}")
    public ApiResult<Void> deleteAccount(@PathVariable Long id) {
        return promotionService.deleteDockRecord(id);
    }
}
