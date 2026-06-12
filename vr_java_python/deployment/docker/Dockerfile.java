FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# 复制 JAR 包
COPY platform-server/target/platform-server-*.jar app.jar

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget -qO- http://localhost:8089/health || exit 1

EXPOSE 8089 9090

ENTRYPOINT ["java", \
    "--enable-preview", \
    "-XX:+UseZGC", \
    "-XX:MaxRAMPercentage=75", \
    "-jar", "app.jar"]