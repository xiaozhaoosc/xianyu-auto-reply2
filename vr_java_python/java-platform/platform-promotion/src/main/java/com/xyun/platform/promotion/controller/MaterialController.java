package com.xyun.platform.promotion.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.promotion.service.PromotionService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 素材库管理 REST API
 */
@RestController
@RequestMapping("/api/promotion/materials")
@RequiredArgsConstructor
public class MaterialController {

    private final PromotionService promotionService;

    /** 素材列表（分页 + 关键词搜索） */
    @GetMapping
    public ApiResult<Page<Map<String, Object>>> listMaterials(
            @RequestParam(defaultValue = "1") int current,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false, defaultValue = "") String keyword,
            @RequestParam(required = false, defaultValue = "") String accountId,
            @RequestParam(required = false, defaultValue = "") String publishStatus) {
        return promotionService.listMaterials(current, size, keyword, accountId, publishStatus);
    }

    /** 创建素材 */
    @PostMapping
    public ApiResult<Map<String, Object>> createMaterial(@RequestBody Map<String, Object> body) {
        return promotionService.createMaterial(body);
    }

    /** 更新素材 */
    @PutMapping("/{id}")
    public ApiResult<Map<String, Object>> updateMaterial(
            @PathVariable Long id, @RequestBody Map<String, Object> body) {
        return promotionService.updateMaterial(id, body);
    }

    /** 删除素材 */
    @DeleteMapping("/{id}")
    public ApiResult<Void> deleteMaterial(@PathVariable Long id) {
        return promotionService.deleteMaterial(id);
    }
}
