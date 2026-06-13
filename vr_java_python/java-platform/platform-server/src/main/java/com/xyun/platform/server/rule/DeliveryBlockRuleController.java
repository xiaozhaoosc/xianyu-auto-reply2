package com.xyun.platform.server.rule;

import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyDeliveryBlockRule;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 发货拦截规则管理 REST API
 */
@RestController
@RequestMapping("/api/delivery-block-rules")
@RequiredArgsConstructor
public class DeliveryBlockRuleController {

    private final RuleService ruleService;

    /** 查询发货拦截规则列表 */
    @GetMapping
    public ApiResult<List<XyDeliveryBlockRule>> listDeliveryBlockRules() {
        return ApiResult.ok(ruleService.listDeliveryBlockRules());
    }

    /** 创建发货拦截规则 */
    @PostMapping
    public ApiResult<XyDeliveryBlockRule> createDeliveryBlockRule(
            @Valid @RequestBody XyDeliveryBlockRule rule) {
        return ApiResult.ok(ruleService.createDeliveryBlockRule(rule));
    }

    /** 更新发货拦截规则 */
    @PutMapping("/{id}")
    public ApiResult<XyDeliveryBlockRule> updateDeliveryBlockRule(
            @PathVariable Long id, @Valid @RequestBody XyDeliveryBlockRule rule) {
        rule.setId(id);
        return ApiResult.ok(ruleService.updateDeliveryBlockRule(rule));
    }

    /** 删除发货拦截规则 */
    @DeleteMapping("/{id}")
    public ApiResult<Void> deleteDeliveryBlockRule(@PathVariable Long id) {
        ruleService.deleteDeliveryBlockRule(id);
        return ApiResult.ok();
    }
}
