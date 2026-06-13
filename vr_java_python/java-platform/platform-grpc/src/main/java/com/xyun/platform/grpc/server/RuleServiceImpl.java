package com.xyun.platform.grpc.server;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyDefaultReply;
import com.xyun.platform.common.entity.XyDeliveryBlockRule;
import com.xyun.platform.common.entity.XyKeywordRule;
import com.xyun.platform.grpc.*;
import com.xyun.platform.server.mapper.XyAccountMapper;
import com.xyun.platform.server.mapper.XyDefaultReplyMapper;
import com.xyun.platform.server.mapper.XyDeliveryBlockRuleMapper;
import com.xyun.platform.server.mapper.XyKeywordRuleMapper;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.service.GrpcService;

import java.util.Optional;

/**
 * 规则 gRPC 服务实现 — 提供关键词规则、发货规则、AI 设置、默认回复
 */
@Slf4j
@GrpcService
@RequiredArgsConstructor
public class RuleServiceImpl extends RuleServiceGrpc.RuleServiceImplBase {

    private final XyKeywordRuleMapper keywordRuleMapper;
    private final XyDeliveryBlockRuleMapper deliveryBlockRuleMapper;
    private final XyAccountMapper accountMapper;
    private final XyDefaultReplyMapper defaultReplyMapper;
    private final ObjectMapper objectMapper;

    @Override
    public void getKeywordRules(RuleRequest request, StreamObserver<KeywordRuleListResponse> responseObserver) {
        try {
            var rules = keywordRuleMapper.selectList(
                new LambdaQueryWrapper<XyKeywordRule>()
                    .eq(XyKeywordRule::getAccountId, request.getAccountId())
                    .eq(XyKeywordRule::getIsActive, true)
                    .orderByDesc(XyKeywordRule::getPriority)
            );
            var builder = KeywordRuleListResponse.newBuilder();
            for (var rule : rules) {
                builder.addRules(KeywordRule.newBuilder()
                    .setId(rule.getId())
                    .setAccountId(String.valueOf(rule.getAccountId()))
                    .setKeyword(Optional.ofNullable(rule.getKeyword()).orElse(""))
                    .setMatchType(mapMatchType(rule.getReplyType()))
                    .setReplyContent(Optional.ofNullable(rule.getReplyContent()).orElse(""))
                    .setPriority(Optional.ofNullable(rule.getPriority()).orElse(0))
                    .setEnabled(Boolean.TRUE.equals(rule.getIsActive()))
                    .build());
            }
            responseObserver.onNext(builder.build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("获取关键词规则失败", e);
            responseObserver.onError(e);
        }
    }

    @Override
    public void getDeliveryRules(RuleRequest request, StreamObserver<DeliveryRuleListResponse> responseObserver) {
        try {
            var rules = deliveryBlockRuleMapper.selectList(
                new LambdaQueryWrapper<XyDeliveryBlockRule>()
                    .eq(XyDeliveryBlockRule::getAccountId, request.getAccountId())
                    .eq(XyDeliveryBlockRule::getEnabled, true)
                    .orderByDesc(XyDeliveryBlockRule::getPriority)
            );
            var builder = DeliveryRuleListResponse.newBuilder();
            for (var rule : rules) {
                builder.addRules(DeliveryRule.newBuilder()
                    .setId(rule.getId())
                    .setAccountId(Optional.ofNullable(rule.getAccountId()).orElse(""))
                    .setRuleCode(Optional.ofNullable(rule.getRuleCode()).orElse(""))
                    .setEnabled(Boolean.TRUE.equals(rule.getEnabled()))
                    .setPriority(Optional.ofNullable(rule.getPriority()).orElse(0))
                    .setBlockReason(Optional.ofNullable(rule.getBlockReason()).orElse(""))
                    .setAutoCloseOrder(Boolean.TRUE.equals(rule.getAutoCloseOrder()))
                    .setConfig(Optional.ofNullable(rule.getConfig()).orElse(""))
                    .build());
            }
            responseObserver.onNext(builder.build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("获取发货规则失败", e);
            responseObserver.onError(e);
        }
    }

    @Override
    public void getAISettings(AISettingRequest request, StreamObserver<AISettingResponse> responseObserver) {
        try {
            var account = accountMapper.selectOne(
                new LambdaQueryWrapper<XyAccount>()
                    .eq(XyAccount::getAccountId, request.getAccountId())
            );
            var builder = AISettingResponse.newBuilder();
            if (account != null && account.getMetadata() != null) {
                parseMetadataToAISetting(account.getMetadata(), builder);
            }
            responseObserver.onNext(builder.build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("获取AI设置失败", e);
            responseObserver.onError(e);
        }
    }

    @Override
    public void getDefaultReply(DefaultReplyRequest request, StreamObserver<DefaultReplyResponse> responseObserver) {
        try {
            var reply = defaultReplyMapper.selectOne(
                new LambdaQueryWrapper<XyDefaultReply>()
                    .eq(XyDefaultReply::getAccountId, request.getAccountId())
                    .eq(XyDefaultReply::getItemId, request.getItemId())
                    .eq(XyDefaultReply::getEnabled, true)
                    .last("LIMIT 1")
            );
            var builder = DefaultReplyResponse.newBuilder();
            if (reply != null) {
                builder.setContent(Optional.ofNullable(reply.getReplyContent()).orElse(""))
                    .setReplyOnce(Boolean.TRUE.equals(reply.getReplyOnce()));
            }
            responseObserver.onNext(builder.build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("获取默认回复失败", e);
            responseObserver.onError(e);
        }
    }

    /** 回复类型映射为 matchType 数值 */
    private int mapMatchType(String replyType) {
        if (replyType == null) return 0;
        return switch (replyType.toLowerCase()) {
            case "exact" -> 1;
            case "fuzzy" -> 2;
            case "regex" -> 3;
            default -> 0;
        };
    }

    /** 从 metadata JSON 中解析 AI 设置字段 */
    private void parseMetadataToAISetting(String metadata, AISettingResponse.Builder builder) {
        try {
            var node = objectMapper.readTree(metadata);
            var aiNode = node.has("ai") ? node.get("ai") : node;
            if (aiNode.has("enabled")) builder.setEnabled(aiNode.get("enabled").asBoolean());
            if (aiNode.has("provider")) builder.setProvider(aiNode.get("provider").asText());
            if (aiNode.has("model")) builder.setModel(aiNode.get("model").asText());
            if (aiNode.has("apiKey")) builder.setApiKey(aiNode.get("apiKey").asText());
            if (aiNode.has("baseUrl")) builder.setBaseUrl(aiNode.get("baseUrl").asText());
            if (aiNode.has("systemPrompt")) builder.setSystemPrompt(aiNode.get("systemPrompt").asText());
        } catch (JsonProcessingException e) {
            log.warn("解析AI设置metadata失败: {}", e.getMessage());
        }
    }
}
