import json
import os
import shutil
import traceback
import zipfile
from pathlib import Path
from typing import Optional, Tuple

from fastapi import UploadFile

from app.core.config import settings
from app.models.schemas import ProjectMetadata


async def save_upload_file(upload_file: UploadFile, temp_filename: str) -> Path:
    """
    保存上传的文件到临时目录
    
    Args:
        upload_file: 上传的文件对象
        temp_filename: 临时文件名（不包含扩展名）
    
    Returns:
        保存的文件路径
    """
    temp_file_path = settings.DATA_TMP_DIR / f"{temp_filename}.zip"
    
    # 确保目录存在
    temp_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入文件
    with open(temp_file_path, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)
    
    return temp_file_path


def validate_zip_file(file_path: Path) -> Tuple[bool, str, Optional[ProjectMetadata]]:
    """
    验证ZIP文件是否包含必要的文件结构
    
    Args:
        file_path: ZIP文件路径
    
    Returns:
        验证结果元组 (是否有效, 错误消息, 元数据对象)
    """
    if not zipfile.is_zipfile(file_path):
        return False, "上传的文件不是有效的ZIP文件", None
    
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        
        # 检查是否包含index.html
        if "index.html" not in file_list:
            return False, "ZIP文件必须包含index.html文件", None
        
        # 检查是否包含meta.json
        if "meta.json" not in file_list:
            return False, "ZIP文件必须包含meta.json文件", None
        
        # 读取并解析meta.json
        try:
            with zip_ref.open("meta.json") as meta_file:
                meta_data = json.load(meta_file)
                
                # 验证必要字段
                if "author" not in meta_data:
                    return False, "meta.json必须包含author字段", None
                
                if "email" not in meta_data:
                    return False, "meta.json必须包含email字段", None
                
                # 验证项目名称不存在
                project_dir = settings.DATA_DIR / file_path.name
                if project_dir.exists():
                    old_meta = json.loads(project_dir.joinpath("meta.json").read_text(encoding="utf-8"))
                    if old_meta["author"] != meta_data["author"] and old_meta["email"] != meta_data["email"]:
                        return False, f"项目名称 '{meta_data['project']}' 已存在", None
                
                # 解析为ProjectMetadata对象
                project_metadata = ProjectMetadata(**meta_data)
                return True, "验证成功", project_metadata
        except Exception as e:
            print(e, traceback.format_exc())
            return False, f"meta.json格式无效: {str(e)}", None


def deploy_project(temp_path: Path, project_name: str) -> Path:
    """
    将验证通过的项目部署到正式目录
    
    Args:
        temp_path: 临时文件路径
        project_name: 项目名称
    
    Returns:
        部署后的项目路径
    """
    # 创建项目目录
    project_dir = settings.DATA_DIR / project_name
    
    # 如果目录已存在，先删除
    if project_dir.exists():
        shutil.rmtree(project_dir)
    
    # 创建项目目录
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # 解压文件到项目目录
    with zipfile.ZipFile(temp_path, 'r') as zip_ref:
        zip_ref.extractall(project_dir)
    
    return project_dir


def clean_temp_files(temp_path: Path) -> None:
    """
    清理临时文件
    
    Args:
        temp_path: 临时文件路径
    """
    if temp_path.exists():
        os.remove(temp_path) 