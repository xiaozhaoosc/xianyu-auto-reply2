package com.xyun.platform.promotion.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.promotion.service.PromotionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 选品规则管理 REST API
 */
@RestController
@RequestMapping("/api/promotion/selection-rules")
@RequiredArgsConstructor
public class SelectionRuleController {

    private final PromotionService promotionService;

    /** 选品规则列表（分页） */
    @GetMapping
    public ApiResult<Page<Map<String, Object>>> listRules(
            @RequestParam(defaultValue = "1") int current,
            @RequestParam(defaultValue = "10") int size) {
        return promotionService.listSelectionRules(current, size);
    }

    /** 创建选品规则 */
    @PostMapping
    public ApiResult<Map<String, Object>> createRule(@RequestBody Map<String, Object> body) {
        return promotionService.createSelectionRule(body);
    }

    /** 更新选品规则 */
    @PutMapping("/{id}")
    public ApiResult<Map<String, Object>> updateRule(
            @PathVariable Long id, @RequestBody Map<String, Object> body) {
        return promotionService.updateSelectionRule(id, body);
    }

    /** 删除选品规则 */
    @DeleteMapping("/{id}")
    public ApiResult<Void> deleteRule(@PathVariable Long id) {
        return promotionService.deleteSelectionRule(id);
    }
}
