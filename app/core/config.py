from pathlib import Path
from typing import Optional

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用程序设置，从环境变量加载"""
    
    # 项目基础设置
    PROJECT_NAME: str = "Share Project"
    API_V1_STR: str = "/api/v1"
    
    # 文件存储路径
    DATA_DIR: Path = Path("./data")
    DATA_TMP_DIR: Path = Path("./data-tmp")
    
    # 域名设置
    DOMAIN: str = "http://localhost:8000"
    
    # 文件上传设置
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    # 验证令牌设置
    VERIFICATION_CACHE_FILE: str = "verification_cache.json"
    VERIFICATION_EXPIRY_MINUTES: int = 10
    
    # 邮件设置
    MAIL_USERNAME: Optional[str] = ''
    MAIL_PASSWORD: Optional[str] = ''
    MAIL_FROM: Optional[EmailStr] = ''
    MAIL_PORT: Optional[int] = 465
    MAIL_SERVER: Optional[str] = ''
    MAIL_FROM_NAME: Optional[str] = ''
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)


# 创建全局设置实例
settings = Settings()

# 确保必要的目录存在
def ensure_directories():
    """确保数据目录存在"""
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.DATA_TMP_DIR.mkdir(parents=True, exist_ok=True) 