package com.xyun.platform.grpc.server;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyAiChatMessage;
import com.xyun.platform.common.entity.XyAutoReplyMessageLog;
import com.xyun.platform.common.entity.XyPersonalBlacklist;
import com.xyun.platform.common.entity.XyPlatformBlacklist;
import com.xyun.platform.grpc.*;
import com.xyun.platform.server.mapper.XyAiChatMessageMapper;
import com.xyun.platform.server.mapper.XyAutoReplyMessageLogMapper;
import com.xyun.platform.server.mapper.XyPersonalBlacklistMapper;
import com.xyun.platform.server.mapper.XyPlatformBlacklistMapper;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.service.GrpcService;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;

/**
 * 消息 gRPC 服务实现 — 写入回复日志、AI 聊天消息、黑名单校验
 */
@Slf4j
@GrpcService
@RequiredArgsConstructor
public class MessageServiceImpl extends MessageServiceGrpc.MessageServiceImplBase {

    private final XyAutoReplyMessageLogMapper autoReplyMessageLogMapper;
    private final XyAiChatMessageMapper aiChatMessageMapper;
    private final XyPersonalBlacklistMapper personalBlacklistMapper;
    private final XyPlatformBlacklistMapper platformBlacklistMapper;

    @Override
    public void writeReplyLog(ReplyLogRequest request, StreamObserver<Empty> responseObserver) {
        try {
            var logEntry = new XyAutoReplyMessageLog();
            logEntry.setAccountId(request.getAccountId());
            logEntry.setSenderUserId(request.getBuyerId());
            logEntry.setSourceMessage(request.getBuyerMessage());
            logEntry.setReplyText(request.getReplyContent());
            logEntry.setReplyStrategy(request.getReplyType());
            logEntry.setItemId(request.getItemId());
            logEntry.setSourceMessageTime(toLocalDateTime(request.getTimestamp()));
            autoReplyMessageLogMapper.insert(logEntry);
            responseObserver.onNext(Empty.newBuilder().build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("写入回复日志失败", e);
            responseObserver.onError(e);
        }
    }

    @Override
    public void writeAIChatMessage(AIChatRequest request, StreamObserver<Empty> responseObserver) {
        try {
            var message = new XyAiChatMessage();
            message.setCookieId(request.getAccountId());
            message.setUserId(request.getBuyerId());
            message.setRole(request.getRole());
            message.setContent(request.getContent());
            aiChatMessageMapper.insert(message);
            responseObserver.onNext(Empty.newBuilder().build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("写入AI聊天消息失败", e);
            responseObserver.onError(e);
        }
    }

    @Override
    public void checkBlacklist(BlacklistRequest request, StreamObserver<BlacklistResponse> responseObserver) {
        try {
            // 先查个人黑名单
            var personal = personalBlacklistMapper.selectOne(
                new LambdaQueryWrapper<XyPersonalBlacklist>()
                    .eq(XyPersonalBlacklist::getAccountId, request.getAccountId())
                    .eq(XyPersonalBlacklist::getBuyerId, request.getBuyerId())
                    .eq(XyPersonalBlacklist::getIsEnabled, true)
                    .last("LIMIT 1")
            );
            if (personal != null) {
                responseObserver.onNext(BlacklistResponse.newBuilder()
                    .setIsBlacklisted(true)
                    .setReason(personal.getReason() != null ? personal.getReason() : "个人黑名单")
                    .build());
                responseObserver.onCompleted();
                return;
            }
            // 再查平台黑名单
            var platform = platformBlacklistMapper.selectOne(
                new LambdaQueryWrapper<XyPlatformBlacklist>()
                    .eq(XyPlatformBlacklist::getBuyerId, request.getBuyerId())
                    .last("LIMIT 1")
            );
            if (platform != null) {
                responseObserver.onNext(BlacklistResponse.newBuilder()
                    .setIsBlacklisted(true)
                    .setReason("平台黑名单")
                    .build());
                responseObserver.onCompleted();
                return;
            }
            // 不在黑名单中
            responseObserver.onNext(BlacklistResponse.newBuilder()
                .setIsBlacklisted(false)
                .setReason("")
                .build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("检查黑名单失败", e);
            responseObserver.onError(e);
        }
    }

    /** 毫秒时间戳转 LocalDateTime */
    private LocalDateTime toLocalDateTime(long timestampMs) {
        return timestampMs > 0
            ? LocalDateTime.ofInstant(Instant.ofEpochMilli(timestampMs), ZoneId.systemDefault())
            : null;
    }
}
