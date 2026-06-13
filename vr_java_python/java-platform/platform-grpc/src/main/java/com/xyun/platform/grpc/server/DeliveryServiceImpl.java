package com.xyun.platform.grpc.server;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyCard;
import com.xyun.platform.common.entity.XyCardItemRelation;
import com.xyun.platform.common.entity.XyOrder;
import com.xyun.platform.grpc.*;
import com.xyun.platform.server.mapper.XyCardItemRelationMapper;
import com.xyun.platform.server.mapper.XyCardMapper;
import com.xyun.platform.server.mapper.XyOrderMapper;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.service.GrpcService;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Optional;

/**
 * 发货 gRPC 服务实现 — 卡券匹配、发货日志、订单查询
 */
@Slf4j
@GrpcService
@RequiredArgsConstructor
public class DeliveryServiceImpl extends DeliveryServiceGrpc.DeliveryServiceImplBase {

    private final XyCardMapper cardMapper;
    private final XyCardItemRelationMapper cardItemRelationMapper;
    private final XyOrderMapper orderMapper;

    @Override
    public void matchCard(MatchCardRequest request, StreamObserver<MatchCardResponse> responseObserver) {
        try {
            // 先通过关联表找到卡券ID
            var relation = cardItemRelationMapper.selectOne(
                new LambdaQueryWrapper<XyCardItemRelation>()
                    .eq(XyCardItemRelation::getItemId, request.getItemId())
                    .last("LIMIT 1")
            );
            if (relation == null) {
                responseObserver.onNext(MatchCardResponse.newBuilder().setMatched(false).build());
                responseObserver.onCompleted();
                return;
            }
            // 查询卡券详情
            var card = cardMapper.selectById(relation.getCardId());
            if (card == null || !Boolean.TRUE.equals(card.getEnabled())) {
                responseObserver.onNext(MatchCardResponse.newBuilder().setMatched(false).build());
                responseObserver.onCompleted();
                return;
            }
            var response = MatchCardResponse.newBuilder()
                .setMatched(true)
                .setCardId(card.getId())
                .setCardContent(Optional.ofNullable(card.getTextContent()).orElse(""))
                .setCardType(Optional.ofNullable(card.getType()).orElse(""))
                .setCardSource(Optional.ofNullable(relation.getSource()).orElse(""))
                .build();
            responseObserver.onNext(response);
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("匹配卡券失败", e);
            responseObserver.onError(e);
        }
    }

    @Override
    public void writeDeliveryLog(DeliveryLogRequest request, StreamObserver<Empty> responseObserver) {
        try {
            var order = orderMapper.selectOne(
                new LambdaQueryWrapper<XyOrder>()
                    .eq(XyOrder::getOrderNo, request.getOrderId())
            );
            if (order == null) {
                // 订单不存在时创建新记录
                order = new XyOrder();
                order.setOrderNo(request.getOrderId());
                order.setItemId(request.getItemId());
                order.setBuyerId(request.getBuyerId());
                order.setAccountId(request.getAccountId());
            }
            // 更新发货信息
            order.setDeliveryMethod("card");
            order.setDeliveryContent(request.getContent());
            order.setDeliveryFailReason(request.getFailReason());
            order.setStatus(request.getSuccess() ? "delivered" : "delivery_failed");
            if (order.getId() == null) {
                orderMapper.insert(order);
            } else {
                orderMapper.updateById(order);
            }
            responseObserver.onNext(Empty.newBuilder().build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("写入发货日志失败", e);
            responseObserver.onError(e);
        }
    }

    @Override
    public void getOrderInfo(OrderRequest request, StreamObserver<OrderResponse> responseObserver) {
        try {
            var order = orderMapper.selectOne(
                new LambdaQueryWrapper<XyOrder>()
                    .eq(XyOrder::getOrderNo, request.getOrderId())
            );
            if (order == null) {
                responseObserver.onError(new RuntimeException("订单不存在"));
                return;
            }
            var response = OrderResponse.newBuilder()
                .setOrderId(order.getOrderNo())
                .setItemId(Optional.ofNullable(order.getItemId()).orElse(""))
                .setBuyerId(Optional.ofNullable(order.getBuyerId()).orElse(""))
                .setStatus(Optional.ofNullable(order.getStatus()).orElse(""))
                .setAmount(order.getAmount() != null ? order.getAmount().doubleValue() : 0.0)
                .setCreatedAt(toEpochMilli(order.getCreatedAt()))
                .build();
            responseObserver.onNext(response);
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("获取订单信息失败", e);
            responseObserver.onError(e);
        }
    }

    /** LocalDateTime 转毫秒时间戳 */
    private long toEpochMilli(LocalDateTime ldt) {
        return ldt != null
            ? ldt.atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
            : 0L;
    }
}
