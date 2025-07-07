import json
import shutil
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Request, Query
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.models.schemas import (
    DeleteProjectResponse,
    ProjectListResponse,
    ProjectResponse,
    UploadResponse,
    VerificationResponse,
)
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
project_meta_path = settings.DATA_DIR / "projects.json"

@router.post("/upload/", response_model=UploadResponse)
async def upload_project(
    file: UploadFile = File(...),
):
    """
    上传项目ZIP文件
    
    - **file**: ZIP文件，必须包含meta.json文件，其中的project属性将作为项目名称
    
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
        # 生成临时文件名
        temp_filename = f"temp_{int(datetime.now().timestamp())}"
        
        # 保存上传的文件
        temp_file_path = await save_upload_file(file, temp_filename)
        
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
            message=f"项目上传成功，验证链接已发送至 {metadata.email}",
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


        if project_meta_path.exists():
            project_meta_data = json.loads(project_meta_path.read_text(encoding="utf-8"))
        else:
            project_meta_data = {}
        project_meta_data[verification_token.email] = verification_token.project_name
        project_meta_path.write_text(json.dumps(project_meta_data, ensure_ascii=False, indent=4), encoding="utf-8")

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

@router.get("/project/", response_model=ProjectListResponse, summary="获取用户项目列表", description="根据邮箱地址获取用户已部署的所有项目列表")
async def get_projects(
    email: str = Query(..., description="用户邮箱地址", example="user@example.com")
):
    """
    获取用户已部署的项目列表
    
    ## 参数说明
    - **email**: 用户邮箱地址
    
    ## 返回说明
    - **projects**: 项目列表，包含项目名称、访问URL和关联邮箱
    
    ## 错误码
    - **400**: 缺少email参数
    - **500**: 项目元数据格式错误
    """
    if not email:
        raise HTTPException(status_code=400, detail="缺少email参数")

    if not project_meta_path.exists():
        return {"projects": []}
    
    try:
        project_meta_data = json.loads(project_meta_path.read_text(encoding="utf-8"))
        projects = [
            {"name": name, "url": f"{settings.DOMAIN}/{name}/", "email": email_key}
            for email_key, name in project_meta_data.items()
            if email_key == email
        ]
        return {"projects": projects}
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="项目元数据格式错误")

@router.delete("/project/", response_model=DeleteProjectResponse, summary="删除项目", description="删除用户已部署的项目，需要提供邮箱和项目名称")
async def delete_project(
    email: str = Query(..., description="用户邮箱地址", example="user@example.com"),
    name: str = Query(..., description="项目名称", example="my-project")
):
    """
    删除用户已部署的项目
    
    ## 参数说明
    - **email**: 用户邮箱地址
    - **name**: 项目名称
    
    ## 返回说明
    - **message**: 操作结果消息
    
    ## 错误码
    - **400**: 缺少email或name参数
    - **404**: 未找到项目元数据或指定的项目
    - **500**: 项目元数据格式错误或删除项目失败
    """
    if not email or not name:
        raise HTTPException(status_code=400, detail="缺少email或name参数")
    
    if not project_meta_path.exists():
        raise HTTPException(status_code=404, detail="没有找到项目元数据")
    
    try:
        project_meta_data = json.loads(project_meta_path.read_text(encoding="utf-8"))
        
        if email in project_meta_data and project_meta_data[email] == name:
            # 删除项目目录
            project_dir = settings.DATA_DIR / name
            if project_dir.exists():
                shutil.rmtree(project_dir)
            
            # 从元数据中删除项目记录
            del project_meta_data[email]
            project_meta_path.write_text(json.dumps(project_meta_data, ensure_ascii=False, indent=4), encoding="utf-8")
            
            return {"message": "项目删除成功"}
        else:
            raise HTTPException(status_code=404, detail="未找到指定的项目")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="项目元数据格式错误")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")
