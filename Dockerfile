# DataAgent Dockerfile
# 支持多种构建目标：dev, test, prod

# 基础镜像
FROM python:3.11-slim-bookworm AS base

LABEL maintainer="DataAgent Team"
LABEL description="DataAgent - OpenClaw-powered AI Assistant"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=100

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    ca-certificates \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*


# 开发环境
FROM base AS dev
LABEL stage="development"

# 复制 requirements
COPY dataagent/requirements.txt /app/requirements.txt
COPY dataagent/requirements-minimal.txt /app/requirements-minimal.txt

# 安装 Python 依赖
RUN pip install -r /app/requirements.txt

# 复制代码
COPY dataagent /app

# 创建必要的目录
RUN mkdir -p /app/data \
    && mkdir -p /app/logs \
    && mkdir -p /app/config \
    && mkdir -p /app/workspace \
    && mkdir -p /root/.dataagent

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 开发命令
CMD ["python", "-m", "uvicorn", "web_app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# 生产环境
FROM base AS prod
LABEL stage="production"

# 创建非 root 用户
RUN groupadd -r dataagent && useradd -r -g dataagent dataagent

# 复制 requirements
COPY dataagent/requirements-minimal.txt /app/requirements.txt

# 安装 Python 依赖
RUN pip install -r /app/requirements.txt

# 复制代码
COPY dataagent /app

# 创建必要的目录并设置权限
RUN mkdir -p /app/data \
    && mkdir -p /app/logs \
    && mkdir -p /app/config \
    && mkdir -p /app/workspace \
    && mkdir -p /root/.dataagent \
    && chown -R dataagent:dataagent /app

# 切换用户
USER dataagent

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 生产命令
CMD ["python", "-m", "uvicorn", "web_app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]


# 测试环境
FROM base AS test
LABEL stage="test"

# 复制 requirements
COPY dataagent/requirements.txt /app/requirements.txt

# 安装 Python 依赖
RUN pip install -r /app/requirements.txt

# 复制代码
COPY dataagent /app

# 创建必要的目录
RUN mkdir -p /app/data \
    && mkdir -p /app/logs

# 运行测试
CMD ["pytest", "-v", "tests/"]
