from string import Template

email_template = Template("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>项目验证邮件</title>
  <style>
    body { background: #fff; color: #111; font-family: "Helvetica Neue", Helvetica, Arial, "PingFang SC", "Microsoft YaHei", sans-serif; margin: 0; padding: 0; }
    .container { max-width: 500px; margin: 40px auto; background: #fff; border: 1px solid #ddd; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); padding: 36px 32px 28px 32px; }
    h2 { border-left: 4px solid #111; padding-left: 10px; margin-bottom: 28px; font-size: 1.6em; color: #111; letter-spacing: 1px; }
    p { line-height: 1.8; margin: 14px 0; font-size: 1em; color: #222; }
    .project-name { font-weight: bold; color: #111; background: #f5f5f5; padding: 2px 8px; border-radius: 4px; display: inline-block; }
    .token-box { font-size: 1.3em; font-family: "Fira Mono", "Consolas", monospace; background: #111; color: #fff; padding: 8px 18px; border-radius: 8px; letter-spacing: 2px; margin: 18px 0 12px 0; display: inline-block; }
    .footer { margin-top: 36px; color: #888; font-size: 0.95em; text-align: right; border-top: 1px solid #eee; padding-top: 16px; }
  </style>
</head>
<body>
  <div class="container">
    <h2>项目验证</h2>
    <p>您好，</p>
    <p>感谢您上传项目 <span class="project-name">$project_name</span>。</p>
    <p>请确保你的网页符合法律法规。</p>
    <p>验证密钥为：</p>
    <div class="token-box">$token</div>
    <p>此密钥将在 <strong>$expiry_minutes</strong> 分钟后过期。</p>
    <p>谢谢！</p>
    <div class="footer">
      — $mail_from_name 团队
    </div>
  </div>
</body>
</html>
""")