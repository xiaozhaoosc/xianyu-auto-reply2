package com.xyun.platform.promotion.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.promotion.service.PromotionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 发布/删除规则管理 REST API
 */
@RestController
@RequestMapping("/api/promotion/publish-rules")
@RequiredArgsConstructor
public class PublishRuleController {

    private final PromotionService promotionService;

    /** 发布规则列表（分页） */
    @GetMapping
    public ApiResult<Page<Map<String, Object>>> listRules(
            @RequestParam(defaultValue = "1") int current,
            @RequestParam(defaultValue = "10") int size) {
        return promotionService.listPublishRules(current, size);
    }

    /** 创建发布规则 */
    @PostMapping
    public ApiResult<Map<String, Object>> createRule(@RequestBody Map<String, Object> body) {
        return promotionService.createPublishRule(body);
    }

    /** 更新发布规则 */
    @PutMapping("/{id}")
    public ApiResult<Map<String, Object>> updateRule(
            @PathVariable Long id, @RequestBody Map<String, Object> body) {
        return promotionService.updatePublishRule(id, body);
    }

    /** 删除发布规则 */
    @DeleteMapping("/{id}")
    public ApiResult<Void> deleteRule(@PathVariable Long id) {
        return promotionService.deletePublishRule(id);
    }
}
