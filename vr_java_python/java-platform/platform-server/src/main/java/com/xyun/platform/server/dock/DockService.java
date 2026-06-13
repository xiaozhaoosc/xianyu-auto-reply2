package com.xyun.platform.server.dock;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xyun.platform.common.dto.ApiResult;
import com.xyun.platform.common.entity.XyAgentOrder;
import com.xyun.platform.common.entity.XyDockCodeBinding;
import com.xyun.platform.common.entity.XyDockRecord;
import com.xyun.platform.common.exception.BusinessException;
import com.xyun.platform.server.mapper.XyAgentOrderMapper;
import com.xyun.platform.server.mapper.XyDockCodeBindingMapper;
import com.xyun.platform.server.mapper.XyDockRecordMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

/**
 * 分销对接 Service — 对接记录、代理订单 CRUD
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DockService {

    private final XyDockRecordMapper dockRecordMapper;
    private final XyDockCodeBindingMapper dockCodeBindingMapper;
    private final XyAgentOrderMapper agentOrderMapper;

    // ==================== 对接记录 ====================

    /**
     * 分页查询对接记录
     */
    public ApiResult<Page<XyDockRecord>> listDockRecords(int current, int size, Long userId) {
        var page = new Page<XyDockRecord>(current, size);
        var wrapper = new LambdaQueryWrapper<XyDockRecord>()
                .eq(userId != null, XyDockRecord::getUserId, userId)
                .orderByDesc(XyDockRecord::getCreatedAt);
        return ApiResult.ok(dockRecordMapper.selectPage(page, wrapper));
    }

    /**
     * 创建对接记录
     */
    public ApiResult<XyDockRecord> createDockRecord(XyDockRecord record) {
        validateDockRecord(record);
        dockRecordMapper.insert(record);
        return ApiResult.ok(record);
    }

    /**
     * 更新对接记录
     */
    public ApiResult<XyDockRecord> updateDockRecord(Long id, XyDockRecord record) {
        if (dockRecordMapper.selectById(id) == null) {
            throw new BusinessException("对接记录不存在: " + id);
        }
        record.setId(id);
        dockRecordMapper.updateById(record);
        return ApiResult.ok(record);
    }

    /**
     * 删除对接记录
     */
    public ApiResult<Void> deleteDockRecord(Long id) {
        if (dockRecordMapper.deleteById(id) <= 0) {
            throw new BusinessException("对接记录不存在: " + id);
        }
        return ApiResult.ok();
    }

    // ==================== 代理订单 ====================

    /**
     * 分页查询代理订单
     */
    public ApiResult<Page<XyAgentOrder>> listAgentOrders(int current, int size, Long userId, String status) {
        var page = new Page<XyAgentOrder>(current, size);
        var wrapper = new LambdaQueryWrapper<XyAgentOrder>()
                .eq(userId != null, XyAgentOrder::getUserId, userId)
                .eq(StringUtils.hasText(status), XyAgentOrder::getStatus, status)
                .orderByDesc(XyAgentOrder::getCreatedAt);
        return ApiResult.ok(agentOrderMapper.selectPage(page, wrapper));
    }

    // ==================== 参数校验 ====================

    /** 校验对接记录 */
    private void validateDockRecord(XyDockRecord record) {
        if (record.getUserId() == null) {
            throw new BusinessException("用户ID不能为空");
        }
        if (!StringUtils.hasText(record.getDockName())) {
            throw new BusinessException("对接名称不能为空");
        }
    }
}
