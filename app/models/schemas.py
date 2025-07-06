from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ProjectMetadata(BaseModel):
    """项目元数据模型，对应meta.json文件内容"""
    
    project: str = Field(..., description="项目名称，用于部署路径")
    description: str = Field(..., description="项目描述")
    author: str = Field(..., description="项目作者")
    email: EmailStr = Field(..., description="作者邮箱")


class UploadResponse(BaseModel):
    """上传响应模型"""
    
    success: bool = Field(..., description="上传是否成功")
    message: str = Field(..., description="响应消息")


class VerificationRequest(BaseModel):
    """验证请求模型"""
    
    token: str = Field(..., description="验证令牌")
    email: EmailStr = Field(..., description="接收验证链接的邮箱")


class VerificationResponse(BaseModel):
    """验证响应模型"""
    
    success: bool = Field(..., description="验证是否成功")
    message: str = Field(..., description="响应消息")
    redirect_url: Optional[str] = Field(None, description="重定向URL，仅在成功时返回")


class VerificationToken(BaseModel):
    """验证令牌模型，用于缓存"""
    
    token: str = Field(..., description="验证令牌")
    project_name: str = Field(..., description="项目名称")
    temp_path: str = Field(..., description="临时文件路径")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    expires_at: datetime = Field(..., description="过期时间")
    email: Optional[EmailStr] = Field(None, description="接收验证链接的邮箱") 