FROM python:3.13-slim

WORKDIR /app

# 复制项目文件
COPY pyproject.toml .
COPY main.py .
COPY app/ ./app/

# 创建数据目录
RUN mkdir -p /app/data /app/data-tmp

# 安装依赖
RUN pip install --no-cache-dir uv && \
    uv sync

# 设置环境变量
ENV DATA_DIR=/app/data
ENV DATA_TMP_DIR=/app/data-tmp
ENV DOMAIN=http://localhost:8000
ENV MAX_FILE_SIZE=5242880
ENV VERIFICATION_CACHE_FILE=verification_cache.json
ENV VERIFICATION_EXPIRY_MINUTES=10

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]