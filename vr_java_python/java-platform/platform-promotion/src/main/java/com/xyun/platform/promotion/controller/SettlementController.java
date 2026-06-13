package com.xyun.platform.promotion.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XySettlementRecord;
import com.xyun.platform.promotion.service.PromotionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 结算管理 REST API
 */
@RestController
@RequestMapping("/api/promotion/settlements")
@RequiredArgsConstructor
public class SettlementController {

    private final PromotionService promotionService;

    /** 结算记录列表（分页） */
    @GetMapping
    public ApiResult<Page<XySettlementRecord>> listSettlements(
            @RequestParam(defaultValue = "1") int current,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) Long userId,
            @RequestParam(required = false, defaultValue = "") String status) {
        return promotionService.listSettlements(current, size, userId, status);
    }

    /** 申请结算 */
    @PostMapping("/apply")
    public ApiResult<XySettlementRecord> applySettlement(@RequestBody Map<String, Object> body) {
        return promotionService.applySettlement(body);
    }

    /** 审批结算 */
    @PutMapping("/{id}/approve")
    public ApiResult<XySettlementRecord> approveSettlement(
            @PathVariable Long id, @RequestBody(required = false) Map<String, Object> body) {
        var remark = body != null ? (String) body.getOrDefault("remark", "") : "";
        return promotionService.approveSettlement(id, remark);
    }

    /** 拒绝结算 */
    @PutMapping("/{id}/reject")
    public ApiResult<XySettlementRecord> rejectSettlement(
            @PathVariable Long id, @RequestBody Map<String, Object> body) {
        var rejectReason = (String) body.getOrDefault("rejectReason", "");
        return promotionService.rejectSettlement(id, rejectReason);
    }
}
