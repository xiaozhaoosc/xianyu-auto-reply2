package com.xyun.platform.server.dock;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyAgentOrder;
import com.xyun.platform.common.entity.XyDockRecord;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 分销对接 API — 对接记录、代理订单
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class DockController {

    private final DockService dockService;

    // ==================== 对接记录 ====================

    /** 对接记录列表 */
    @GetMapping("/dock-records")
    public ApiResult<Page<XyDockRecord>> listDockRecords(
            @RequestParam(defaultValue = "1") int current,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) Long userId) {
        return dockService.listDockRecords(current, size, userId);
    }

    /** 创建对接 */
    @PostMapping("/dock-records")
    public ApiResult<XyDockRecord> createDockRecord(@RequestBody XyDockRecord record) {
        return dockService.createDockRecord(record);
    }

    /** 更新对接 */
    @PutMapping("/dock-records/{id}")
    public ApiResult<XyDockRecord> updateDockRecord(
            @PathVariable Long id, @RequestBody XyDockRecord record) {
        return dockService.updateDockRecord(id, record);
    }

    /** 删除对接 */
    @DeleteMapping("/dock-records/{id}")
    public ApiResult<Void> deleteDockRecord(@PathVariable Long id) {
        return dockService.deleteDockRecord(id);
    }

    // ==================== 代理订单 ====================

    /** 代理订单列表 */
    @GetMapping("/agent-orders")
    public ApiResult<Page<XyAgentOrder>> listAgentOrders(
            @RequestParam(defaultValue = "1") int current,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) Long userId,
            @RequestParam(required = false) String status) {
        return dockService.listAgentOrders(current, size, userId, status);
    }
}
