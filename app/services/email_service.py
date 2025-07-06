import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path
from typing import Optional

from pydantic import EmailStr

from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)


async def send_verification_email(
    email_to: EmailStr,
    token: str,
    project_name: str
) -> bool:
    """
    发送验证邮件
    
    Args:
        email_to: 收件人邮箱
        token: 验证令牌
        project_name: 项目名称
    
    Returns:
        发送是否成功
    """
    # 邮件主题
    subject = f"验证您的项目: {project_name}"
    
    # 邮件内容
    html_content = f"""
    <html>
    <body>
        <h2>项目验证</h2>
        <p>您好，</p>
        <p>感谢您上传项目 <strong>{project_name}</strong>。</p>
        <p>请确保你的网页符合法律法规</p>
        <p>验证密钥为：</p>
        <p>{token}</p>
        <p>此链接将在 {settings.VERIFICATION_EXPIRY_MINUTES} 分钟后过期。</p>
        <p>谢谢！</p>
        <p>{settings.MAIL_FROM_NAME} 团队</p>
    </body>
    </html>
    """
    
    # 创建邮件消息
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    
    # 设置发件人，格式为"名称 <邮箱>"
    mail_from = settings.MAIL_FROM or "noreply@example.com"
    mail_from_name = settings.MAIL_FROM_NAME or "Share Project"
    message["From"] = formataddr((mail_from_name, mail_from))
    
    message["To"] = email_to
    
    # 添加HTML内容
    html_part = MIMEText(html_content, "html")
    message.attach(html_part)
    
    try:
        # 连接SMTP服务器
        mail_server = settings.MAIL_SERVER or "localhost"
        mail_port = settings.MAIL_PORT or 587
        mail_username = settings.MAIL_USERNAME or ""
        mail_password = settings.MAIL_PASSWORD or ""
        
        # 创建SMTP连接
        if settings.MAIL_TLS:
            # 使用STARTTLS
            smtp = smtplib.SMTP(mail_server, mail_port)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
        else:
            # 使用SSL/TLS
            context = ssl.create_default_context()
            smtp = smtplib.SMTP_SSL(mail_server, mail_port, context=context)
        
        # 登录
        if mail_username and mail_password:
            smtp.login(mail_username, mail_password)
        
        # 发送邮件
        smtp.sendmail(
            mail_from,
            email_to,
            message.as_string()
        )
        
        # 关闭连接
        smtp.quit()
        
        logger.info(f"验证邮件已发送至 {email_to}")
        return True
    except Exception as e:
        logger.error(f"发送邮件失败: {str(e)}")
        return False 