import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import ensure_directories, settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 确保必要的目录存在
ensure_directories()

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="一个用于共享静态Web项目的服务",
    version="0.1.0",
    # 只在DEBUG模式下启用API文档
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(router)


@app.get("/")
async def root():
    """
    API根路径
    """
    return {
        "message": "欢迎使用Share Project API",
        "docs": "/docs" if settings.DEBUG else "API文档在生产环境中已禁用"
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 