from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.models.schemas import UploadResponse, VerificationResponse
from app.services.email_service import send_verification_email
from app.utils.file_utils import clean_temp_files, deploy_project, save_upload_file, validate_zip_file
from app.utils.token_utils import (
    clean_expired_tokens,
    create_verification_token,
    get_verification_token,
    remove_verification_token,
    save_verification_token,
    update_token_email,
)

# 创建路由器
router = APIRouter(tags=["projects"])


@router.post("/upload/", response_model=UploadResponse)
async def upload_project(
    name: str = Form(...),
    file: UploadFile = File(...),
):
    """
    上传项目ZIP文件
    
    - **name**: 项目名称
    - **file**: ZIP文件
    
    返回上传结果和验证令牌，并自动发送验证邮件
    """
    # 清理过期的验证令牌
    clean_expired_tokens()
    
    # 检查文件大小
    content_length = file.size
    if content_length and content_length > settings.MAX_FILE_SIZE:
        return UploadResponse(
            success=False,
            message=f"文件大小超过限制，最大允许{settings.MAX_FILE_SIZE / 1024 / 1024}MB",
        )
    
    # 检查文件类型
    if not file.filename or not file.filename.endswith(".zip"):
        return UploadResponse(
            success=False,
            message="只接受ZIP文件",
        )
    
    try:
        # 保存上传的文件
        temp_file_path = await save_upload_file(file, name)
        
        # 验证ZIP文件
        is_valid, message, metadata = validate_zip_file(temp_file_path)
        
        if not is_valid:
            # 清理临时文件
            clean_temp_files(temp_file_path)
            return UploadResponse(success=False, message=message)
        
        # 使用meta.json中的project字段作为项目名称
        project_name = metadata.project
        
        # 创建验证令牌
        verification_token = create_verification_token(project_name, temp_file_path)
        
        # 保存验证令牌
        save_verification_token(verification_token)
        
        # 更新令牌关联的邮箱
        update_token_email(verification_token.token, metadata.email)
        
        # 直接发送验证邮件
        success = await send_verification_email(
            metadata.email,
            verification_token.token,
            project_name
        )
        if not success:
            # 清理临时文件
            clean_temp_files(temp_file_path)
            return UploadResponse(
                success=False,
                message="发送验证邮件失败，请稍后重试",
            )
        
        return UploadResponse(
            success=True,
            message=f"项目上传成功，验证链接已发送至 {metadata.email}"
        )
    
    except Exception as e:
        return UploadResponse(
            success=False,
            message=f"上传失败: {str(e)}",
        )


@router.get("/verify/{token}", response_model=VerificationResponse)
async def verify_project(token: str):
    """
    验证并部署项目
    
    - **token**: 验证令牌
    
    返回验证结果和项目访问路径
    """
    # 获取验证令牌
    verification_token = get_verification_token(token)

    if not verification_token:
        return VerificationResponse(
            success=False,
            message="验证令牌不存在或已过期",
            redirect_url=None
        )

    try:
        # 部署项目
        project_dir = deploy_project(
            Path(verification_token.temp_path),
            verification_token.project_name
        )

        # 清理临时文件
        clean_temp_files(Path(verification_token.temp_path))

        # 移除验证令牌
        remove_verification_token(token)

        # 构建项目访问路径
        project_url = f"{settings.DOMAIN}/{verification_token.project_name}/"

        return VerificationResponse(
            success=True,
            message="项目验证成功",
            redirect_url=project_url
        )

    except Exception as e:
        return VerificationResponse(
            success=False,
            message=f"验证失败: {str(e)}",
            redirect_url=None
        )
