import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from pydantic import EmailStr

from app.core.config import settings
from app.models.schemas import VerificationToken


def generate_token() -> str:
    """
    生成随机验证令牌
    
    Returns:
        随机令牌字符串
    """
    return secrets.token_urlsafe(32)


def create_verification_token(project_name: str, temp_path: Path) -> VerificationToken:
    """
    创建验证令牌
    
    Args:
        project_name: 项目名称
        temp_path: 临时文件路径
    
    Returns:
        验证令牌对象
    """
    token = generate_token()
    expires_at = datetime.now() + timedelta(minutes=settings.VERIFICATION_EXPIRY_MINUTES)
    
    verification_token = VerificationToken(
        token=token,
        project_name=project_name,
        temp_path=str(temp_path),
        expires_at=expires_at,
        email=None
    )
    
    return verification_token


def save_verification_token(token: VerificationToken) -> None:
    """
    保存验证令牌到缓存文件
    
    Args:
        token: 验证令牌对象
    """
    cache_file = settings.DATA_TMP_DIR / settings.VERIFICATION_CACHE_FILE
    
    # 读取现有缓存
    tokens = load_verification_tokens()
    
    # 添加新令牌
    tokens[token.token] = token.model_dump()
    
    # 写入缓存文件
    with open(cache_file, "w") as f:
        json.dump(tokens, f, default=str)


def load_verification_tokens() -> Dict[str, dict]:
    """
    从缓存文件加载验证令牌
    
    Returns:
        令牌字典，键为令牌值，值为令牌数据
    """
    cache_file = settings.DATA_TMP_DIR / settings.VERIFICATION_CACHE_FILE
    
    if not cache_file.exists():
        return {}
    
    try:
        with open(cache_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def get_verification_token(token: str) -> Optional[VerificationToken]:
    """
    获取验证令牌
    
    Args:
        token: 令牌字符串
    
    Returns:
        验证令牌对象，如果不存在或已过期则返回None
    """
    tokens = load_verification_tokens()
    
    if token not in tokens:
        return None
    
    token_data = tokens[token]
    verification_token = VerificationToken(**token_data)
    
    # 检查是否过期
    if datetime.fromisoformat(str(verification_token.expires_at)) < datetime.now():
        remove_verification_token(token)
        return None
    
    return verification_token


def remove_verification_token(token: str) -> None:
    """
    从缓存中移除验证令牌
    
    Args:
        token: 令牌字符串
    """
    tokens = load_verification_tokens()
    
    if token in tokens:
        del tokens[token]
        
        cache_file = settings.DATA_TMP_DIR / settings.VERIFICATION_CACHE_FILE
        with open(cache_file, "w") as f:
            json.dump(tokens, f, default=str)


def clean_expired_tokens() -> None:
    """
    清理过期的验证令牌
    """
    tokens = load_verification_tokens()
    current_time = datetime.now()
    
    # 过滤出未过期的令牌
    valid_tokens = {}
    for token, token_data in tokens.items():
        expires_at = datetime.fromisoformat(str(token_data["expires_at"]))
        if expires_at > current_time:
            valid_tokens[token] = token_data
    
    # 更新缓存文件
    cache_file = settings.DATA_TMP_DIR / settings.VERIFICATION_CACHE_FILE
    with open(cache_file, "w") as f:
        json.dump(valid_tokens, f, default=str)


def update_token_email(token: str, email: EmailStr) -> bool:
    """
    更新令牌关联的邮箱地址
    
    Args:
        token: 令牌字符串
        email: 邮箱地址
    
    Returns:
        更新是否成功
    """
    verification_token = get_verification_token(token)
    
    if not verification_token:
        return False
    
    # 更新邮箱
    verification_token.email = email
    
    # 保存更新后的令牌
    tokens = load_verification_tokens()
    tokens[token] = verification_token.model_dump()
    
    cache_file = settings.DATA_TMP_DIR / settings.VERIFICATION_CACHE_FILE
    with open(cache_file, "w") as f:
        json.dump(tokens, f, default=str)
    
    return True 