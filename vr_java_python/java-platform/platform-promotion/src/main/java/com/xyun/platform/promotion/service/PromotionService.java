package com.xyun.platform.promotion.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyAgentOrder;
import com.xyun.platform.common.entity.XyDockRecord;
import com.xyun.platform.common.entity.XyFundFlow;
import com.xyun.platform.common.entity.XySettlementRecord;
import com.xyun.platform.common.exception.BusinessException;
import com.xyun.platform.server.mapper.XyAgentOrderMapper;
import com.xyun.platform.server.mapper.XyDockRecordMapper;
import com.xyun.platform.server.mapper.XyFundFlowMapper;
import com.xyun.platform.server.mapper.XySettlementRecordMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;

/**
 * 返佣系统核心业务服务
 *
 * <p>职责：返佣账号、选品规则、素材库、发布规则、结算的 CRUD 操作</p>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PromotionService {

    private final XyDockRecordMapper dockRecordMapper;
    private final XyAgentOrderMapper agentOrderMapper;
    private final XySettlementRecordMapper settlementRecordMapper;
    private final XyFundFlowMapper fundFlowMapper;

    // ==================== 返佣账号（对接记录） ====================

    /**
     * 分页查询返佣账号
     *
     * @param current 页码
     * @param size    每页条数
     * @param userId  用户ID（可选，管理员查看所有）
     */
    public ApiResult<Page<XyDockRecord>> listDockRecords(int current, int size, Long userId) {
        var page = new Page<XyDockRecord>(current, size);
        var wrapper = new LambdaQueryWrapper<XyDockRecord>()
                .eq(userId != null, XyDockRecord::getUserId, userId)
                .orderByDesc(XyDockRecord::getCreatedAt);
        return ApiResult.ok(dockRecordMapper.selectPage(page, wrapper));
    }

    /**
     * 创建返佣账号
     */
    public ApiResult<XyDockRecord> createDockRecord(XyDockRecord record) {
        validateDockRecord(record);
        dockRecordMapper.insert(record);
        log.info("创建返佣账号: id={}, userId={}", record.getId(), record.getUserId());
        return ApiResult.ok(record);
    }

    /**
     * 更新返佣账号
     */
    public ApiResult<XyDockRecord> updateDockRecord(Long id, XyDockRecord record) {
        if (dockRecordMapper.selectById(id) == null) {
            throw new BusinessException("返佣账号不存在: " + id);
        }
        record.setId(id);
        dockRecordMapper.updateById(record);
        log.info("更新返佣账号: id={}", id);
        return ApiResult.ok(record);
    }

    /**
     * 删除返佣账号
     */
    public ApiResult<Void> deleteDockRecord(Long id) {
        if (dockRecordMapper.deleteById(id) <= 0) {
            throw new BusinessException("返佣账号不存在: " + id);
        }
        log.info("删除返佣账号: id={}", id);
        return ApiResult.ok();
    }

    // ==================== 选品规则（代理订单视角） ====================

    /**
     * 分页查询选品规则
     *
     * <p>基于代理订单数据模拟选品规则列表</p>
     */
    public ApiResult<Page<Map<String, Object>>> listSelectionRules(int current, int size) {
        var page = new Page<XyAgentOrder>(current, size);
        var wrapper = new LambdaQueryWrapper<XyAgentOrder>()
                .orderByDesc(XyAgentOrder::getCreatedAt);
        var orderPage = agentOrderMapper.selectPage(page, wrapper);

        // 转换为选品规则视图
        var result = new Page<Map<String, Object>>(current, size, orderPage.getTotal());
        result.setRecords(orderPage.getRecords().stream().map(this::orderToSelectionRule).toList());
        return ApiResult.ok(result);
    }

    /**
     * 创建选品规则
     */
    public ApiResult<Map<String, Object>> createSelectionRule(Map<String, Object> body) {
        var order = new XyAgentOrder();
        fillAgentOrderFromBody(order, body);
        agentOrderMapper.insert(order);
        log.info("创建选品规则: id={}", order.getId());
        return ApiResult.ok(orderToSelectionRule(order));
    }

    /**
     * 更新选品规则
     */
    public ApiResult<Map<String, Object>> updateSelectionRule(Long id, Map<String, Object> body) {
        var order = agentOrderMapper.selectById(id);
        if (order == null) {
            throw new BusinessException("选品规则不存在: " + id);
        }
        fillAgentOrderFromBody(order, body);
        order.setId(id);
        agentOrderMapper.updateById(order);
        log.info("更新选品规则: id={}", id);
        return ApiResult.ok(orderToSelectionRule(order));
    }

    /**
     * 删除选品规则
     */
    public ApiResult<Void> deleteSelectionRule(Long id) {
        if (agentOrderMapper.deleteById(id) <= 0) {
            throw new BusinessException("选品规则不存在: " + id);
        }
        log.info("删除选品规则: id={}", id);
        return ApiResult.ok();
    }

    // ==================== 素材库（代理订单 + 对接记录关联） ====================

    /**
     * 分页查询素材库
     *
     * @param current       页码
     * @param size          每页条数
     * @param keyword       关键词搜索
     * @param accountId     闲鱼账号筛选
     * @param publishStatus 发布状态筛选
     */
    public ApiResult<Page<Map<String, Object>>> listMaterials(
            int current, int size, String keyword, String accountId, String publishStatus) {
        var page = new Page<XyAgentOrder>(current, size);
        var wrapper = new LambdaQueryWrapper<XyAgentOrder>()
                // 关键词匹配订单号或商品ID
                .and(StringUtils.hasText(keyword), w -> w
                        .like(XyAgentOrder::getOrderNo, keyword)
                        .or().like(XyAgentOrder::getItemId, keyword))
                // 按状态筛选
                .eq(StringUtils.hasText(publishStatus), XyAgentOrder::getStatus, publishStatus)
                .orderByDesc(XyAgentOrder::getCreatedAt);
        var orderPage = agentOrderMapper.selectPage(page, wrapper);

        // 转换为素材视图
        var result = new Page<Map<String, Object>>(current, size, orderPage.getTotal());
        result.setRecords(orderPage.getRecords().stream().map(this::orderToMaterial).toList());
        return ApiResult.ok(result);
    }

    /**
     * 创建素材
     */
    public ApiResult<Map<String, Object>> createMaterial(Map<String, Object> body) {
        var order = new XyAgentOrder();
        fillAgentOrderFromBody(order, body);
        agentOrderMapper.insert(order);
        log.info("创建素材: id={}", order.getId());
        return ApiResult.ok(orderToMaterial(order));
    }

    /**
     * 更新素材
     */
    public ApiResult<Map<String, Object>> updateMaterial(Long id, Map<String, Object> body) {
        var order = agentOrderMapper.selectById(id);
        if (order == null) {
            throw new BusinessException("素材不存在: " + id);
        }
        fillAgentOrderFromBody(order, body);
        order.setId(id);
        agentOrderMapper.updateById(order);
        log.info("更新素材: id={}", id);
        return ApiResult.ok(orderToMaterial(order));
    }

    /**
     * 删除素材
     */
    public ApiResult<Void> deleteMaterial(Long id) {
        if (agentOrderMapper.deleteById(id) <= 0) {
            throw new BusinessException("素材不存在: " + id);
        }
        log.info("删除素材: id={}", id);
        return ApiResult.ok();
    }

    // ==================== 发布规则 ====================

    /**
     * 分页查询发布规则
     *
     * <p>基于对接记录数据模拟发布规则列表</p>
     */
    public ApiResult<Page<Map<String, Object>>> listPublishRules(int current, int size) {
        var page = new Page<XyDockRecord>(current, size);
        var wrapper = new LambdaQueryWrapper<XyDockRecord>()
                .orderByDesc(XyDockRecord::getCreatedAt);
        var dockPage = dockRecordMapper.selectPage(page, wrapper);

        // 转换为发布规则视图
        var result = new Page<Map<String, Object>>(current, size, dockPage.getTotal());
        result.setRecords(dockPage.getRecords().stream().map(this::dockToPublishRule).toList());
        return ApiResult.ok(result);
    }

    /**
     * 创建发布规则
     */
    public ApiResult<Map<String, Object>> createPublishRule(Map<String, Object> body) {
        var record = new XyDockRecord();
        fillDockRecordFromBody(record, body);
        dockRecordMapper.insert(record);
        log.info("创建发布规则: id={}", record.getId());
        return ApiResult.ok(dockToPublishRule(record));
    }

    /**
     * 更新发布规则
     */
    public ApiResult<Map<String, Object>> updatePublishRule(Long id, Map<String, Object> body) {
        var record = dockRecordMapper.selectById(id);
        if (record == null) {
            throw new BusinessException("发布规则不存在: " + id);
        }
        fillDockRecordFromBody(record, body);
        record.setId(id);
        dockRecordMapper.updateById(record);
        log.info("更新发布规则: id={}", id);
        return ApiResult.ok(dockToPublishRule(record));
    }

    /**
     * 删除发布规则
     */
    public ApiResult<Void> deletePublishRule(Long id) {
        if (dockRecordMapper.deleteById(id) <= 0) {
            throw new BusinessException("发布规则不存在: " + id);
        }
        log.info("删除发布规则: id={}", id);
        return ApiResult.ok();
    }

    // ==================== 结算管理 ====================

    /**
     * 分页查询结算记录
     *
     * @param current 页码
     * @param size    每页条数
     * @param userId  用户ID（可选）
     * @param status  结算状态（可选）
     */
    public ApiResult<Page<XySettlementRecord>> listSettlements(
            int current, int size, Long userId, String status) {
        var page = new Page<XySettlementRecord>(current, size);
        var wrapper = new LambdaQueryWrapper<XySettlementRecord>()
                .eq(userId != null, XySettlementRecord::getUserId, userId)
                .eq(StringUtils.hasText(status), XySettlementRecord::getStatus, status)
                .orderByDesc(XySettlementRecord::getCreatedAt);
        return ApiResult.ok(settlementRecordMapper.selectPage(page, wrapper));
    }

    /**
     * 申请结算
     *
     * <p>创建结算记录，同时扣减用户余额（写入资金流水）</p>
     */
    @Transactional
    public ApiResult<XySettlementRecord> applySettlement(Map<String, Object> body) {
        var userId = toLong(body.get("userId"));
        var amount = toStr(body.get("amount"));
        var paymentType = toStr(body.getOrDefault("paymentType", "alipay"));
        var alipayId = toStr(body.getOrDefault("alipayId", ""));
        var remark = toStr(body.getOrDefault("remark", ""));

        if (userId == null) {
            throw new BusinessException("用户ID不能为空");
        }
        if (!StringUtils.hasText(amount)) {
            throw new BusinessException("结算金额不能为空");
        }

        // 创建结算记录
        var record = new XySettlementRecord();
        record.setUserId(userId);
        record.setAmount(amount);
        record.setPaymentType(paymentType);
        record.setAlipayId(alipayId);
        record.setStatus("PENDING");
        record.setRemark(remark);
        settlementRecordMapper.insert(record);

        // 写入资金流水
        var flow = new XyFundFlow();
        flow.setUserId(userId);
        flow.setType("SETTLEMENT_APPLY");
        flow.setAmount("-" + amount);
        flow.setDescription("申请结算，金额：" + amount);
        fundFlowMapper.insert(flow);

        log.info("申请结算: id={}, userId={}, amount={}", record.getId(), userId, amount);
        return ApiResult.ok(record);
    }

    /**
     * 审批结算
     *
     * <p>将结算状态更新为 APPROVED，并写入审批资金流水</p>
     */
    @Transactional
    public ApiResult<XySettlementRecord> approveSettlement(Long id, String remark) {
        var record = settlementRecordMapper.selectById(id);
        if (record == null) {
            throw new BusinessException("结算记录不存在: " + id);
        }
        if (!"PENDING".equals(record.getStatus())) {
            throw new BusinessException("只能审批待审核的结算记录");
        }

        record.setStatus("APPROVED");
        record.setRemark(StringUtils.hasText(remark) ? remark : record.getRemark());
        settlementRecordMapper.updateById(record);

        // 写入审批通过资金流水
        var flow = new XyFundFlow();
        flow.setUserId(record.getUserId());
        flow.setType("SETTLEMENT_APPROVE");
        flow.setAmount(record.getAmount());
        flow.setDescription("结算审批通过，金额：" + record.getAmount());
        fundFlowMapper.insert(flow);

        log.info("审批结算: id={}, status=APPROVED", id);
        return ApiResult.ok(record);
    }

    /**
     * 拒绝结算
     *
     * <p>将结算状态更新为 REJECTED，并退还金额</p>
     */
    @Transactional
    public ApiResult<XySettlementRecord> rejectSettlement(Long id, String rejectReason) {
        var record = settlementRecordMapper.selectById(id);
        if (record == null) {
            throw new BusinessException("结算记录不存在: " + id);
        }
        if (!"PENDING".equals(record.getStatus())) {
            throw new BusinessException("只能拒绝待审核的结算记录");
        }

        record.setStatus("REJECTED");
        record.setRejectReason(rejectReason);
        settlementRecordMapper.updateById(record);

        // 拒绝结算，退还金额
        var flow = new XyFundFlow();
        flow.setUserId(record.getUserId());
        flow.setType("SETTLEMENT_REJECT");
        flow.setAmount(record.getAmount());
        flow.setDescription("结算被拒绝，退还金额：" + record.getAmount() + "，原因：" + rejectReason);
        fundFlowMapper.insert(flow);

        log.info("拒绝结算: id={}, reason={}", id, rejectReason);
        return ApiResult.ok(record);
    }

    // ==================== 私有辅助方法 ====================

    /** 校验对接记录必填字段 */
    private void validateDockRecord(XyDockRecord record) {
        if (record.getUserId() == null) {
            throw new BusinessException("用户ID不能为空");
        }
        if (!StringUtils.hasText(record.getDockName())) {
            throw new BusinessException("对接名称不能为空");
        }
    }

    /** 代理订单转选品规则视图 */
    private Map<String, Object> orderToSelectionRule(XyAgentOrder order) {
        var map = new HashMap<String, Object>();
        map.put("id", order.getId());
        map.put("userId", order.getUserId());
        map.put("orderNo", order.getOrderNo());
        map.put("itemId", order.getItemId());
        map.put("salePrice", order.getSalePrice());
        map.put("dockPrice", order.getDockPrice());
        map.put("profit", order.getProfit());
        map.put("status", order.getStatus());
        map.put("createdAt", order.getCreatedAt());
        map.put("updatedAt", order.getUpdatedAt());
        return map;
    }

    /** 代理订单转素材视图 */
    private Map<String, Object> orderToMaterial(XyAgentOrder order) {
        var map = new HashMap<String, Object>();
        map.put("id", order.getId());
        map.put("userId", order.getUserId());
        map.put("itemId", order.getItemId());
        map.put("title", order.getOrderNo());
        map.put("price", order.getSalePrice());
        map.put("description", order.getDeliveryContent());
        map.put("clickUrl", order.getItemId());
        map.put("publishStatus", order.getStatus());
        map.put("createdAt", order.getCreatedAt());
        map.put("updatedAt", order.getUpdatedAt());
        return map;
    }

    /** 对接记录转发布规则视图 */
    private Map<String, Object> dockToPublishRule(XyDockRecord record) {
        var map = new HashMap<String, Object>();
        map.put("id", record.getId());
        map.put("userId", record.getUserId());
        map.put("ruleName", record.getDockName());
        map.put("accountId", record.getCardId());
        map.put("dailyCount", record.getDeliveryCount());
        map.put("enabled", record.getStatus());
        map.put("remark", record.getRemark());
        map.put("createdAt", record.getCreatedAt());
        map.put("updatedAt", record.getUpdatedAt());
        return map;
    }

    /** 从请求体填充代理订单字段 */
    private void fillAgentOrderFromBody(XyAgentOrder order, Map<String, Object> body) {
        if (body.containsKey("userId")) order.setUserId(toLong(body.get("userId")));
        if (body.containsKey("orderNo")) order.setOrderNo(toStr(body.get("orderNo")));
        if (body.containsKey("itemId")) order.setItemId(toStr(body.get("itemId")));
        if (body.containsKey("cardId")) order.setCardId(toLong(body.get("cardId")));
        if (body.containsKey("dockRecordId")) order.setDockRecordId(toLong(body.get("dockRecordId")));
        if (body.containsKey("salePrice")) order.setSalePrice(toStr(body.get("salePrice")));
        if (body.containsKey("dockPrice")) order.setDockPrice(toStr(body.get("dockPrice")));
        if (body.containsKey("profit")) order.setProfit(toStr(body.get("profit")));
        if (body.containsKey("status")) order.setStatus(toStr(body.get("status")));
        if (body.containsKey("remark")) order.setSettleRemark(toStr(body.get("remark")));
    }

    /** 从请求体填充对接记录字段 */
    private void fillDockRecordFromBody(XyDockRecord record, Map<String, Object> body) {
        if (body.containsKey("userId")) record.setUserId(toLong(body.get("userId")));
        if (body.containsKey("dockName")) record.setDockName(toStr(body.get("dockName")));
        if (body.containsKey("markupAmount")) record.setMarkupAmount(toStr(body.get("markupAmount")));
        if (body.containsKey("remark")) record.setRemark(toStr(body.get("remark")));
        if (body.containsKey("deliveryCount")) record.setDeliveryCount(toInteger(body.get("deliveryCount")));
        if (body.containsKey("status")) record.setStatus(toBoolean(body.get("status")));
    }

    /** 安全转换为 Long */
    private Long toLong(Object value) {
        if (value == null) return null;
        if (value instanceof Number n) return n.longValue();
        try { return Long.parseLong(value.toString()); } catch (NumberFormatException e) { return null; }
    }

    /** 安全转换为 String */
    private String toStr(Object value) {
        return value != null ? value.toString() : "";
    }

    /** 安全转换为 Integer */
    private Integer toInteger(Object value) {
        if (value == null) return null;
        if (value instanceof Number n) return n.intValue();
        try { return Integer.parseInt(value.toString()); } catch (NumberFormatException e) { return null; }
    }

    /** 安全转换为 Boolean */
    private Boolean toBoolean(Object value) {
        if (value == null) return null;
        if (value instanceof Boolean b) return b;
        return "true".equalsIgnoreCase(value.toString());
    }
}
