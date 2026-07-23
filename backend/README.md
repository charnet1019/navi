# Navi Backend

FastAPI-based backend for the Navi navigation and link management system.

## Overview

The backend provides a RESTful API with JWT authentication, role-based access control, and comprehensive data management capabilities.

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Primary database with async support via asyncpg
- **Redis**: Caching and session management
- **SQLAlchemy 2.0**: Async ORM for database operations
- **Alembic**: Database migration tool
- **Pydantic**: Data validation and settings management
- **JWT**: Token-based authentication
- **Uvicorn**: ASGI server

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # API endpoint handlers
│   │       │   ├── auth.py     # Authentication endpoints
│   │       │   ├── users.py    # User management
│   │       │   ├── roles.py    # Role management
│   │       │   ├── permissions.py # Permission management
│   │       │   └── navigation.py  # Navigation endpoints
│   │       └── router.py       # API router configuration
│   ├── core/
│   │   ├── config.py          # Application configuration
│   │   ├── security.py        # Security utilities
│   │   └── dependencies.py    # FastAPI dependencies
│   ├── models/
│   │   ├── user.py           # User model
│   │   ├── role.py           # Role model
│   │   ├── permission.py     # Permission model
│   │   └── navigation.py     # Navigation model
│   ├── schemas/
│   │   ├── user.py           # User schemas
│   │   ├── role.py           # Role schemas
│   │   ├── permission.py     # Permission schemas
│   │   ├── navigation.py     # Navigation schemas
│   │   └── token.py          # Token schemas
│   ├── services/
│   │   ├── auth.py           # Authentication service
│   │   ├── user.py           # User service
│   │   ├── role.py           # Role service
│   │   └── navigation.py     # Navigation service
│   ├── database.py           # Database configuration
│   ├── redis.py              # Redis configuration
│   └── main.py               # Application entry point
├── alembic/
│   ├── versions/             # Migration files
│   └── env.py               # Alembic configuration
├── tests/
│   ├── conftest.py          # Test configuration
│   └── test_*.py            # Test files
├── uploads/                 # File upload directory
├── Dockerfile              # Production Docker image
├── Dockerfile.dev          # Development Docker image
├── requirements.txt        # Python dependencies
└── alembic.ini            # Alembic configuration
```

## Setup

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp ../.env.example ../.env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Development

```bash
# From project root
docker-compose -f docker-compose.dev.yml up backend
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user
- `GET /api/v1/auth/me` - Get current user

### Users
- `GET /api/v1/users` - List users (admin only)
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user (admin only)

### Roles
- `GET /api/v1/roles` - List roles
- `POST /api/v1/roles` - Create role (admin only)
- `GET /api/v1/roles/{id}` - Get role by ID
- `PUT /api/v1/roles/{id}` - Update role (admin only)
- `DELETE /api/v1/roles/{id}` - Delete role (admin only)

### Permissions
- `GET /api/v1/permissions` - List permissions
- `POST /api/v1/permissions` - Create permission (admin only)

### Navigation
- `GET /api/v1/navigation` - List navigation items
- `POST /api/v1/navigation` - Create navigation item
- `GET /api/v1/navigation/{id}` - Get navigation item
- `PUT /api/v1/navigation/{id}` - Update navigation item
- `DELETE /api/v1/navigation/{id}` - Delete navigation item

## Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

### View current version
```bash
alembic current
```

## Testing

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_auth.py
```

## 配置说明

后端配置通过环境变量和 `app/config.py` 管理。完整配置项请参考项目根目录 `.env.example`。

### 关键配置项

- `DATABASE_URL`：PostgreSQL 数据库连接地址。
- `REDIS_URL`：Redis 连接地址。
- `SECRET_KEY`：JWT 签名密钥，生产环境必须修改。
- `ALGORITHM`：JWT 签名算法，默认 `HS256`。
- `ACCESS_TOKEN_EXPIRE_MINUTES`：访问 token 有效期。
- `REFRESH_TOKEN_EXPIRE_DAYS`：刷新 token 有效期。
- `DEBUG`：是否启用调试模式，生产环境应设置为 `false`。
- `CORS_ORIGINS`：允许跨域访问的前端域名，默认 `*`。生产环境建议指定明确域名，例如 `https://navi.example.com`。
- `CORS_ALLOW_CREDENTIALS`：是否允许跨域请求携带 Cookie。使用固定前端域名和 HttpOnly Cookie 登录时应设置为 `true`。
- `AUTH_COOKIE_SECURE`：是否仅通过 HTTPS 发送认证 Cookie。生产环境建议设置为 `true`。
- `AUTH_COOKIE_SAMESITE`：认证 Cookie 的 SameSite 策略，默认 `lax`。前后端完全跨站点域名时需设置为 `none`，并同时启用 `AUTH_COOKIE_SECURE=true`。
- `AUTH_COOKIE_DOMAIN`：可选的 Cookie 域名，用于同一主域下多个子域共享登录态。
- `AUTH_CSRF_COOKIE_NAME` / `AUTH_CSRF_HEADER_NAME`：CSRF 双重提交校验使用的 Cookie 名称和请求头名称。
- `LOG_LEVEL`：日志级别。

### 生产环境 Cookie 与 CORS 推荐配置

前后端在同站点或同一主域下部署时，建议：

```env
AUTH_COOKIE_SECURE=true
AUTH_COOKIE_SAMESITE=lax
CORS_ORIGINS=https://你的前端域名
CORS_ALLOW_CREDENTIALS=true
```

如果前后端是完全跨站点域名，则使用：

```env
AUTH_COOKIE_SECURE=true
AUTH_COOKIE_SAMESITE=none
CORS_ORIGINS=https://你的前端域名
CORS_ALLOW_CREDENTIALS=true
```

## 安全说明

### 认证流程

1. 用户提交用户名和密码登录。
2. 后端校验凭据并签发访问 token 和刷新 token。
3. token 写入 HttpOnly Cookie，前端 JavaScript 无法读取认证 token。
4. 浏览器后续请求会自动携带认证 Cookie，后端在每次请求中校验登录状态。
5. 非 GET/HEAD 等安全请求需要携带 CSRF 请求头，刷新 token 过期前可自动续期登录状态。

### 密码安全

- 密码使用 bcrypt 哈希保存。
- 系统会按当前密码规则校验最小长度和复杂度。
- 管理员可重置用户密码，用户也可修改自己的密码。

### RBAC 权限体系

- 用户通过角色获得基础权限。
- 角色可以绑定多个权限。
- 接口会按所需权限进行访问校验。
- 导航分组和链接支持细粒度授权。

## 缓存

Redis 用于：
- 登录会话辅助管理。
- token 黑名单。
- 登录失败次数和锁定状态。
- 用户权限缓存。

## 错误处理

API 使用标准 HTTP 状态码：
- `200`：请求成功。
- `201`：创建成功。
- `400`：请求参数错误。
- `401`：未登录或认证失败。
- `403`：无权限访问。
- `404`：资源不存在。
- `422`：请求数据校验失败。
- `500`：服务器内部错误。

错误响应格式：
```json
{
  "detail": "错误信息"
}
```

## 日志

日志级别通过 `LOG_LEVEL` 环境变量配置。

可用级别：`DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`。

## 性能优化

- 使用异步数据库访问。
- 配置数据库连接池。
- 使用 Redis 缓存权限等高频数据。
- 通过 SQLAlchemy 优化查询。
- 避免不必要的关系数据加载。

## 开发规范

1. 遵循 PEP 8 代码风格。
2. 函数尽量补充类型标注。
3. 公共函数保留必要的 docstring。
4. 新功能应补充对应测试。
5. I/O 操作优先使用 async/await。
6. 使用 Pydantic schema 校验输入。
7. 明确处理异常和错误响应。
8. 复用 FastAPI 依赖注入。

## 排错

### 数据库连接异常
- 检查 `DATABASE_URL` 是否正确。
- 确认 PostgreSQL 正在运行。
- 检查网络连通性。

### Redis 连接异常
- 检查 `REDIS_URL` 是否正确。
- 确认 Redis 正在运行。
- 如果 Redis 设置了密码，确认连接地址中已包含密码。

### 数据库迁移异常
- 检查 `alembic.ini` 配置。
- 确认数据库账号有足够权限。
- 检查迁移文件是否存在冲突。

### Python 导入异常
- 确认虚拟环境已激活。
- 确认依赖已完整安装。
- 检查 Python 版本是否兼容。

## 相关资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Alembic 文档](https://alembic.sqlalchemy.org/)
- [Pydantic 文档](https://docs.pydantic.dev/)
