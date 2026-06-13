package com.xyun.platform.server.card;

import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyCard;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 卡券管理 REST API
 */
@RestController
@RequestMapping("/api/cards")
@RequiredArgsConstructor
public class CardController {

    private final CardService cardService;

    /** 查询卡券列表 */
    @GetMapping
    public ApiResult<List<XyCard>> listCards() {
        return ApiResult.ok(cardService.listCards());
    }

    /** 查询卡券详情 */
    @GetMapping("/{id}")
    public ApiResult<XyCard> getCard(@PathVariable Long id) {
        return ApiResult.ok(cardService.getCard(id));
    }

    /** 创建卡券 */
    @PostMapping
    public ApiResult<XyCard> createCard(@Valid @RequestBody XyCard card) {
        return ApiResult.ok(cardService.createCard(card));
    }

    /** 更新卡券 */
    @PutMapping("/{id}")
    public ApiResult<XyCard> updateCard(@PathVariable Long id,
                                        @Valid @RequestBody XyCard card) {
        card.setId(id);
        return ApiResult.ok(cardService.updateCard(card));
    }

    /** 删除卡券 */
    @DeleteMapping("/{id}")
    public ApiResult<Void> deleteCard(@PathVariable Long id) {
        cardService.deleteCard(id);
        return ApiResult.ok();
    }

    /** 绑定商品 */
    @PostMapping("/{id}/bind-item")
    public ApiResult<Void> bindItem(@PathVariable Long id,
                                    @RequestBody Map<String, String> body) {
        cardService.bindItem(id, body.get("itemId"));
        return ApiResult.ok();
    }

    /** 解绑商品 */
    @DeleteMapping("/{id}/unbind-item")
    public ApiResult<Void> unbindItem(@PathVariable Long id,
                                      @RequestBody Map<String, String> body) {
        cardService.unbindItem(id, body.get("itemId"));
        return ApiResult.ok();
    }
}
