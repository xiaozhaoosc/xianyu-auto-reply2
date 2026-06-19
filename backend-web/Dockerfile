# Backend-Web 服务 Dockerfile
# 单阶段构建，直接使用Python源码

FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple

WORKDIR /app

RUN apt-get update && apt-get install -y curl ca-certificates gcc \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 仅复制 pyproject.toml 优先安装依赖，利用 Docker 构建缓存
COPY backend-web/pyproject.toml /app/backend-web/
RUN python -c "\
import tomllib; \
deps = tomllib.load(open('/app/backend-web/pyproject.toml','rb')).get('project',{}).get('dependencies',[]); \
open('/tmp/requirements.txt','w').write('\n'.join(deps))" && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# 安装Playwright浏览器（--with-deps 自动安装系统依赖）
RUN python -m playwright install --with-deps chromium

# 复制项目源码
COPY common /app/common
COPY backend-web /app/backend-web
COPY launcher /app/launcher

# 创建日志目录
RUN mkdir -p /app/backend-web/logs /app/static/uploads

# 安装 xvfb-run 必需的 xauth 工具
RUN apt-get update && apt-get install -y xauth && rm -rf /var/lib/apt/lists/*


# 暴露端口
EXPOSE 8089

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TZ=Asia/Shanghai

# 启动服务
CMD ["sh", "-c", "rm -f /tmp/.X*-lock; xvfb-run python backend-web/main.py"]
