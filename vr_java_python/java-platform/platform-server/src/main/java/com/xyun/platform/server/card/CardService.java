package com.xyun.platform.server.card;

import cn.dev33.satoken.stp.StpUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyCard;
import com.xyun.platform.common.entity.XyCardItemRelation;
import com.xyun.platform.common.exception.BusinessException;
import com.xyun.platform.server.mapper.XyCardItemRelationMapper;
import com.xyun.platform.server.mapper.XyCardMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 卡券管理业务逻辑
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CardService {

    private final XyCardMapper cardMapper;
    private final XyCardItemRelationMapper relationMapper;

    /** 查询全部卡券列表 */
    public List<XyCard> listCards() {
        return cardMapper.selectList(
                new LambdaQueryWrapper<XyCard>().orderByDesc(XyCard::getCreatedAt)
        );
    }

    /** 查询卡券详情，不存在则抛出业务异常 */
    public XyCard getCard(Long id) {
        var card = cardMapper.selectById(id);
        if (card == null) {
            throw new BusinessException(404, "卡券不存在");
        }
        return card;
    }

    /** 创建卡券，自动填充当前用户ID */
    public XyCard createCard(XyCard card) {
        card.setUserId(StpUtil.getLoginIdAsLong());
        cardMapper.insert(card);
        return card;
    }

    /** 更新卡券信息 */
    public XyCard updateCard(XyCard card) {
        getCard(card.getId());
        cardMapper.updateById(card);
        return card;
    }

    /** 删除卡券及其商品关联 */
    @Transactional
    public void deleteCard(Long id) {
        getCard(id);
        // 先删除关联关系
        relationMapper.delete(
                new LambdaQueryWrapper<XyCardItemRelation>().eq(XyCardItemRelation::getCardId, id)
        );
        cardMapper.deleteById(id);
        log.info("删除卡券及关联: id={}", id);
    }

    /** 绑定商品到卡券 */
    @Transactional
    public void bindItem(Long cardId, String itemId) {
        getCard(cardId);
        if (itemId == null || itemId.isBlank()) {
            throw new BusinessException("商品ID不能为空");
        }
        // 检查是否已绑定
        var exists = relationMapper.selectOne(
                new LambdaQueryWrapper<XyCardItemRelation>()
                        .eq(XyCardItemRelation::getCardId, cardId)
                        .eq(XyCardItemRelation::getItemId, itemId)
        );
        if (exists != null) {
            throw new BusinessException("该商品已绑定到此卡券");
        }
        var relation = new XyCardItemRelation();
        relation.setCardId(cardId);
        relation.setItemId(itemId);
        relationMapper.insert(relation);
        log.info("绑定商品: cardId={}, itemId={}", cardId, itemId);
    }

    /** 解绑商品 */
    @Transactional
    public void unbindItem(Long cardId, String itemId) {
        getCard(cardId);
        if (itemId == null || itemId.isBlank()) {
            throw new BusinessException("商品ID不能为空");
        }
        int deleted = relationMapper.delete(
                new LambdaQueryWrapper<XyCardItemRelation>()
                        .eq(XyCardItemRelation::getCardId, cardId)
                        .eq(XyCardItemRelation::getItemId, itemId)
        );
        if (deleted == 0) {
            throw new BusinessException("未找到该绑定关系");
        }
        log.info("解绑商品: cardId={}, itemId={}", cardId, itemId);
    }
}
