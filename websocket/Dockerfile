# WebSocket 服务 Dockerfile
# 单阶段构建，直接使用Python源码

FROM python:3.11-slim

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple

WORKDIR /app

RUN apt-get update && apt-get install -y curl ca-certificates gcc \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 仅复制 pyproject.toml 优先安装依赖，利用 Docker 构建缓存
COPY websocket/pyproject.toml /app/websocket/
RUN python -c "\
import tomllib; \
deps = tomllib.load(open('/app/websocket/pyproject.toml','rb')).get('project',{}).get('dependencies',[]); \
open('/tmp/requirements.txt','w').write('\n'.join(deps))" && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# 复制项目源码
COPY common /app/common
COPY websocket /app/websocket
COPY launcher /app/launcher

# 安装Playwright浏览器（--with-deps 自动安装系统依赖）
RUN python -m playwright install --with-deps chromium

# 创建日志目录
RUN mkdir -p /app/websocket/logs /app/static /app/browser_data

# 暴露端口
EXPOSE 8090

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TZ=Asia/Shanghai

# 启动服务
CMD ["python", "websocket/main.py"]
