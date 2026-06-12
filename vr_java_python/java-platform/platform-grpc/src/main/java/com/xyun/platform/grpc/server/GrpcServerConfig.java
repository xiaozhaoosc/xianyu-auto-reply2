package com.xyun.platform.grpc.server;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;

/**
 * gRPC Server 配置 — 端口 9090
 */
@Slf4j
@Component
public class GrpcServerConfig {

    @Value("${grpc.server.port:9090}")
    private int port;

    private Server server;

    @PostConstruct
    public void start() throws IOException {
        server = ServerBuilder.forPort(port)
                .build()
                .start();
        log.info("gRPC Server 已启动，端口: {}", port);
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            log.info("gRPC Server 正在关闭...");
            GrpcServerConfig.this.stop();
        }));
    }

    @PreDestroy
    public void stop() {
        if (server != null) {
            server.shutdown();
            log.info("gRPC Server 已关闭");
        }
    }
}