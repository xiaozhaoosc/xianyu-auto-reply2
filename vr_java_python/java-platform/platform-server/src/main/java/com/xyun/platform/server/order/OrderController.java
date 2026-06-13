package com.xyun.platform.server.order;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyOrder;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 订单管理 REST API
 */
@RestController
@RequestMapping("/api/orders")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;

    /** 分页查询订单列表 */
    @GetMapping
    public ApiResult<Page<XyOrder>> listOrders(
            @RequestParam(defaultValue = "1") long current,
            @RequestParam(defaultValue = "10") long size,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String accountId) {
        return ApiResult.ok(orderService.listOrders(current, size, status, accountId));
    }

    /** 查询订单详情 */
    @GetMapping("/{id}")
    public ApiResult<XyOrder> getOrder(@PathVariable Long id) {
        return ApiResult.ok(orderService.getOrder(id));
    }

    /** 触发订单同步 */
    @PostMapping("/sync")
    public ApiResult<Void> syncOrders() {
        orderService.triggerSync();
        return ApiResult.ok();
    }

    /** 手动发货 */
    @PutMapping("/{id}/delivery")
    public ApiResult<Void> manualDelivery(@PathVariable Long id,
                                          @RequestBody Map<String, String> body) {
        orderService.manualDelivery(id, body.get("deliveryMethod"), body.get("deliveryContent"));
        return ApiResult.ok();
    }
}
