package com.xyun.platform.server.rule;

import cn.dev33.satoken.stp.StpUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyDefaultReply;
import com.xyun.platform.common.entity.XyDeliveryBlockRule;
import com.xyun.platform.common.entity.XyKeywordRule;
import com.xyun.platform.common.exception.BusinessException;
import com.xyun.platform.server.mapper.XyDefaultReplyMapper;
import com.xyun.platform.server.mapper.XyDeliveryBlockRuleMapper;
import com.xyun.platform.server.mapper.XyKeywordRuleMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 规则管理业务逻辑（关键词规则、发货拦截规则、默认回复）
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RuleService {

    private final XyKeywordRuleMapper keywordRuleMapper;
    private final XyDeliveryBlockRuleMapper deliveryBlockRuleMapper;
    private final XyDefaultReplyMapper defaultReplyMapper;

    // ==================== 关键词规则 ====================

    /** 查询全部关键词规则 */
    public List<XyKeywordRule> listKeywordRules() {
        return keywordRuleMapper.selectList(
                new LambdaQueryWrapper<XyKeywordRule>().orderByDesc(XyKeywordRule::getPriority)
        );
    }

    /** 创建关键词规则，自动填充当前用户为 owner */
    public XyKeywordRule createKeywordRule(XyKeywordRule rule) {
        rule.setOwnerId(StpUtil.getLoginIdAsLong());
        keywordRuleMapper.insert(rule);
        return rule;
    }

    /** 更新关键词规则 */
    public XyKeywordRule updateKeywordRule(XyKeywordRule rule) {
        findKeywordRule(rule.getId());
        keywordRuleMapper.updateById(rule);
        return rule;
    }

    /** 删除关键词规则 */
    public void deleteKeywordRule(Long id) {
        findKeywordRule(id);
        keywordRuleMapper.deleteById(id);
    }

    /** 查找关键词规则，不存在则抛异常 */
    private XyKeywordRule findKeywordRule(Long id) {
        var rule = keywordRuleMapper.selectById(id);
        if (rule == null) {
            throw new BusinessException(404, "关键词规则不存在");
        }
        return rule;
    }

    // ==================== 发货拦截规则 ====================

    /** 查询全部发货拦截规则 */
    public List<XyDeliveryBlockRule> listDeliveryBlockRules() {
        return deliveryBlockRuleMapper.selectList(
                new LambdaQueryWrapper<XyDeliveryBlockRule>().orderByDesc(XyDeliveryBlockRule::getPriority)
        );
    }

    /** 创建发货拦截规则 */
    public XyDeliveryBlockRule createDeliveryBlockRule(XyDeliveryBlockRule rule) {
        deliveryBlockRuleMapper.insert(rule);
        return rule;
    }

    /** 更新发货拦截规则 */
    public XyDeliveryBlockRule updateDeliveryBlockRule(XyDeliveryBlockRule rule) {
        findDeliveryBlockRule(rule.getId());
        deliveryBlockRuleMapper.updateById(rule);
        return rule;
    }

    /** 删除发货拦截规则 */
    public void deleteDeliveryBlockRule(Long id) {
        findDeliveryBlockRule(id);
        deliveryBlockRuleMapper.deleteById(id);
    }

    /** 查找发货拦截规则，不存在则抛异常 */
    private XyDeliveryBlockRule findDeliveryBlockRule(Long id) {
        var rule = deliveryBlockRuleMapper.selectById(id);
        if (rule == null) {
            throw new BusinessException(404, "发货拦截规则不存在");
        }
        return rule;
    }

    // ==================== 默认回复 ====================

    /** 查询全部默认回复 */
    public List<XyDefaultReply> listDefaultReplies() {
        return defaultReplyMapper.selectList(
                new LambdaQueryWrapper<XyDefaultReply>().orderByDesc(XyDefaultReply::getCreatedAt)
        );
    }

    /** 创建默认回复 */
    public XyDefaultReply createDefaultReply(XyDefaultReply reply) {
        defaultReplyMapper.insert(reply);
        return reply;
    }

    /** 更新默认回复 */
    public XyDefaultReply updateDefaultReply(XyDefaultReply reply) {
        findDefaultReply(reply.getId());
        defaultReplyMapper.updateById(reply);
        return reply;
    }

    /** 删除默认回复 */
    public void deleteDefaultReply(Long id) {
        findDefaultReply(id);
        defaultReplyMapper.deleteById(id);
    }

    /** 查找默认回复，不存在则抛异常 */
    private XyDefaultReply findDefaultReply(Long id) {
        var reply = defaultReplyMapper.selectById(id);
        if (reply == null) {
            throw new BusinessException(404, "默认回复不存在");
        }
        return reply;
    }
}
