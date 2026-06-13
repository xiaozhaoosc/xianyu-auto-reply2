package com.xyun.platform.server.rule;

import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyDefaultReply;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 默认回复管理 REST API
 */
@RestController
@RequestMapping("/api/default-replies")
@RequiredArgsConstructor
public class DefaultReplyController {

    private final RuleService ruleService;

    /** 查询默认回复列表 */
    @GetMapping
    public ApiResult<List<XyDefaultReply>> listDefaultReplies() {
        return ApiResult.ok(ruleService.listDefaultReplies());
    }

    /** 创建默认回复 */
    @PostMapping
    public ApiResult<XyDefaultReply> createDefaultReply(@Valid @RequestBody XyDefaultReply reply) {
        return ApiResult.ok(ruleService.createDefaultReply(reply));
    }

    /** 更新默认回复 */
    @PutMapping("/{id}")
    public ApiResult<XyDefaultReply> updateDefaultReply(@PathVariable Long id,
                                                        @Valid @RequestBody XyDefaultReply reply) {
        reply.setId(id);
        return ApiResult.ok(ruleService.updateDefaultReply(reply));
    }

    /** 删除默认回复 */
    @DeleteMapping("/{id}")
    public ApiResult<Void> deleteDefaultReply(@PathVariable Long id) {
        ruleService.deleteDefaultReply(id);
        return ApiResult.ok();
    }
}
