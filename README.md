# Share Project

A FastAPI application for sharing static web projects through a verification process.

## Features

- Upload ZIP files containing static web projects
- Validate project structure (must contain meta.json and index.html)
- Generate verification links for project deployment
- Send verification emails to users
- Deploy verified projects to a specified directory
- Redirect to deployed projects

## Requirements

- Python 3.13+
- FastAPI
- Uvicorn
- Docker (for production deployment)

## Setup

1. Install dependencies:
```bash
uv add fastapi uvicorn python-multipart python-dotenv pydantic pydantic-settings aiofiles fastapi-mail
```

2. Configure environment variables in `.env` file:
```
DATA_DIR=./data
DATA_TMP_DIR=./data-tmp
DOMAIN=http://localhost:8000
MAX_FILE_SIZE=5242880
VERIFICATION_CACHE_FILE=verification_cache.json
VERIFICATION_EXPIRY_MINUTES=10

# Email settings
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_password
MAIL_FROM=your_email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.example.com
MAIL_FROM_NAME=Share Project
MAIL_TLS=True
MAIL_SSL=False
```

## Running the Application

### Development

```bash
uvicorn main:app --reload
```

### Production with Docker

#### Using Docker directly

```bash
docker build -t share-project .
docker run -p 8000:8000 -v ./data:/app/data -v ./data-tmp:/app/data-tmp share-project
```

#### Using Docker Compose (Recommended)

```bash
# Start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the services
docker-compose down
```

## API Endpoints

- `GET /`: Welcome page
- `POST /upload/`: Upload a ZIP file with a name parameter
- `POST /send-verification/{token}`: Send verification email
- `GET /verify/{token}`: Verify and deploy a project
- `GET /projects/{project_name}/{file_path}`: Access project files

## API Documentation

API documentation is available at:

- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Project Structure

```
share-project/
├── app/
│   ├── api/
│   │   └── routes.py         # API路由定义
│   ├── core/
│   │   └── config.py         # 配置管理
│   ├── models/
│   │   └── schemas.py        # 数据模型
│   ├── services/
│   │   └── email_service.py  # 邮件服务
│   └── utils/
│       ├── file_utils.py     # 文件处理工具
│       └── token_utils.py    # 令牌处理工具
├── data/                     # 项目存储目录
├── data-tmp/                 # 临时文件目录
├── main.py                   # 应用入口
├── Dockerfile                # Docker配置
├── docker-compose.yml        # Docker Compose配置
├── nginx.conf                # Nginx配置
└── pyproject.toml            # 项目依赖
```

## Notes

- In production, you should configure actual email sending functionality
- The verification links expire after the time specified in VERIFICATION_EXPIRY_MINUTES
- Nginx is configured to serve the static files from the `/app/data` directory
- Make sure to properly secure your application in production
