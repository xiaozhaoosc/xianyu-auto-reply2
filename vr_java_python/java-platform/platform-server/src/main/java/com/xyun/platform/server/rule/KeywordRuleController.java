package com.xyun.platform.server.rule;

import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyKeywordRule;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 关键词规则管理 REST API
 */
@RestController
@RequestMapping("/api/keyword-rules")
@RequiredArgsConstructor
public class KeywordRuleController {

    private final RuleService ruleService;

    /** 查询关键词规则列表 */
    @GetMapping
    public ApiResult<List<XyKeywordRule>> listKeywordRules() {
        return ApiResult.ok(ruleService.listKeywordRules());
    }

    /** 创建关键词规则 */
    @PostMapping
    public ApiResult<XyKeywordRule> createKeywordRule(@Valid @RequestBody XyKeywordRule rule) {
        return ApiResult.ok(ruleService.createKeywordRule(rule));
    }

    /** 更新关键词规则 */
    @PutMapping("/{id}")
    public ApiResult<XyKeywordRule> updateKeywordRule(@PathVariable Long id,
                                                      @Valid @RequestBody XyKeywordRule rule) {
        rule.setId(id);
        return ApiResult.ok(ruleService.updateKeywordRule(rule));
    }

    /** 删除关键词规则 */
    @DeleteMapping("/{id}")
    public ApiResult<Void> deleteKeywordRule(@PathVariable Long id) {
        ruleService.deleteKeywordRule(id);
        return ApiResult.ok();
    }
}
