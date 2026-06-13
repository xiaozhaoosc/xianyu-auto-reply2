package com.xyun.platform.server.order;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.entity.XyOrder;
import com.xyun.platform.common.exception.BusinessException;
import com.xyun.platform.server.mapper.XyOrderMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

/**
 * 订单管理业务逻辑
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class OrderService {

    private final XyOrderMapper orderMapper;

    /** 分页查询订单，支持按状态和账号ID筛选 */
    public Page<XyOrder> listOrders(long current, long size, String status, String accountId) {
        var wrapper = new LambdaQueryWrapper<XyOrder>().orderByDesc(XyOrder::getCreatedAt);
        if (status != null && !status.isBlank()) {
            wrapper.eq(XyOrder::getStatus, status);
        }
        if (accountId != null && !accountId.isBlank()) {
            wrapper.eq(XyOrder::getAccountId, accountId);
        }
        return orderMapper.selectPage(new Page<>(current, size), wrapper);
    }

    /** 查询订单详情，不存在则抛出业务异常 */
    public XyOrder getOrder(Long id) {
        var order = orderMapper.selectById(id);
        if (order == null) {
            throw new BusinessException(404, "订单不存在");
        }
        return order;
    }

    /** 触发订单同步（标记同步时间，实际同步由调度任务执行） */
    public void triggerSync() {
        log.info("触发订单同步");
        // 同步逻辑由调度模块负责，此处仅做触发标记
    }

    /** 手动发货 */
    public void manualDelivery(Long id, String deliveryMethod, String deliveryContent) {
        var order = getOrder(id);
        if (deliveryMethod == null || deliveryMethod.isBlank()) {
            throw new BusinessException("发货方式不能为空");
        }
        order.setDeliveryMethod(deliveryMethod);
        order.setDeliveryContent(deliveryContent);
        order.setStatus("DELIVERED");
        orderMapper.updateById(order);
        log.info("手动发货: orderId={}, method={}", id, deliveryMethod);
    }
}
