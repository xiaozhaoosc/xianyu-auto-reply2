package com.xyun.platform.rules;

import com.xyun.platform.rules.fact.DeliveryCheckFact;
import com.xyun.platform.rules.fact.ReplyCheckFact;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;
import org.springframework.stereotype.Service;

/**
 * Drools 规则引擎服务 — 替代 Python 硬编码 if-else 规则
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RuleEngineService {

    private final KieContainer kieContainer;

    /**
     * 执行发货检查规则
     */
    public DeliveryCheckFact checkDelivery(DeliveryCheckFact fact) {
        KieSession session = kieContainer.newKieSession();
        try {
            session.insert(fact);
            session.fireAllRules();
            return fact;
        } catch (Exception e) {
            log.error("发货规则执行失败", e);
            return fact;
        } finally {
            session.dispose();
        }
    }

    /**
     * 执行回复优先级规则
     */
    public ReplyCheckFact checkReply(ReplyCheckFact fact) {
        KieSession session = kieContainer.newKieSession();
        try {
            session.insert(fact);
            session.fireAllRules();
            return fact;
        } catch (Exception e) {
            log.error("回复规则执行失败", e);
            return fact;
        } finally {
            session.dispose();
        }
    }
}
