# 第一阶段：uv 工具镜像
FROM ghcr.io/astral-sh/uv:0.7.19 AS uv

# 第二阶段：构建依赖
FROM python:3.13.5-slim-bookworm AS builder

WORKDIR /build

# 设置环境变量提升构建性能和一致性
ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_INSTALLER_METADATA=1 \
    UV_LINK_MODE=copy \
    PIP_NO_CACHE_DIR=1

# 复制项目依赖文件
COPY pyproject.toml uv.lock ./

# 安装依赖到指定目录
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv export --frozen --no-dev -o requirements.txt && \
    mkdir -p deps && \
    uv pip install -r requirements.txt --target deps

# 第三阶段：最终镜像
FROM python:3.13.5-slim-bookworm

WORKDIR /app

# 环境变量配置
ENV PYTHONPATH=/app/deps \
    DATA_DIR=/app/data \
    DATA_TMP_DIR=/app/data-tmp \
    DOMAIN=http://localhost:8000 \
    MAX_FILE_SIZE=5242880 \
    VERIFICATION_CACHE_FILE=verification_cache.json \
    VERIFICATION_EXPIRY_MINUTES=10 \
    DEBUG=false

# 复制依赖和项目文件
COPY --from=builder /build/deps ./deps
COPY main.py ./
COPY app/ ./app/

# 创建运行所需目录
RUN mkdir -p "$DATA_DIR" "$DATA_TMP_DIR"

EXPOSE 8000

# 启动应用
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]