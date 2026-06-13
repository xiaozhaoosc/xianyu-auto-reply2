package com.xyun.platform.grpc.server;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xyun.platform.common.entity.XyAccount;
import com.xyun.platform.common.entity.XyAccountLoginLog;
import com.xyun.platform.grpc.*;
import com.xyun.platform.server.mapper.XyAccountLoginLogMapper;
import com.xyun.platform.server.mapper.XyAccountMapper;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.service.GrpcService;

/**
 * 账号 gRPC 服务实现 — Python 运行时通过此服务获取账号信息
 */
@Slf4j
@GrpcService
@RequiredArgsConstructor
public class AccountServiceImpl extends AccountServiceGrpc.AccountServiceImplBase {

    private final XyAccountMapper accountMapper;
    private final XyAccountLoginLogMapper accountLoginLogMapper;

    @Override
    public void getAccount(AccountRequest request, StreamObserver<AccountResponse> responseObserver) {
        try {
            var account = accountMapper.selectOne(
                new LambdaQueryWrapper<XyAccount>()
                    .eq(XyAccount::getAccountId, request.getAccountId())
                    .eq(XyAccount::getOwnerId, request.getOwnerId())
            );
            if (account == null) {
                responseObserver.onError(new RuntimeException("账号不存在"));
                return;
            }
            var response = AccountResponse.newBuilder()
                .setId(account.getId())
                .setAccountId(account.getAccountId())
                .setNickname(account.getDisplayName() != null ? account.getDisplayName() : "")
                .setStatus(account.getStatus())
                .setCookies(account.getCookie())
                .build();
            responseObserver.onNext(response);
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("获取账号信息失败", e);
            responseObserver.onError(e);
        }
    }

    @Override
    public void updateStatus(StatusRequest request, StreamObserver<StatusResponse> responseObserver) {
        try {
            var account = accountMapper.selectOne(
                new LambdaQueryWrapper<XyAccount>()
                    .eq(XyAccount::getAccountId, request.getAccountId())
            );
            if (account == null) {
                responseObserver.onNext(StatusResponse.newBuilder().setSuccess(false).build());
                responseObserver.onCompleted();
                return;
            }
            account.setStatus(request.getStatus());
            accountMapper.updateById(account);
            responseObserver.onNext(StatusResponse.newBuilder().setSuccess(true).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("更新账号状态失败", e);
            responseObserver.onError(e);
        }
    }

    @Override
    public void writeLoginLog(LoginLogRequest request, StreamObserver<Empty> responseObserver) {
        try {
            var loginLog = new XyAccountLoginLog();
            loginLog.setAccountIdentifier(request.getAccountId());
            loginLog.setLoginStatus(request.getSuccess() ? "success" : "failed");
            loginLog.setErrorMessage(request.getMessage());
            loginLog.setTriggerReason(request.getLoginType());
            accountLoginLogMapper.insert(loginLog);
            responseObserver.onNext(Empty.newBuilder().build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            log.error("写入登录日志失败", e);
            responseObserver.onError(e);
        }
    }
}
