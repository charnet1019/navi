# Navi - Navigation & Link Management System

A modern, full-stack web application for managing navigation links with role-based access control (RBAC).

## Features

- **User Authentication**: Secure JWT-based authentication with access and refresh tokens
- **Role-Based Access Control**: Fine-grained permissions system with roles and permissions
- **Navigation Management**: Create, organize, and manage navigation links
- **Admin Dashboard**: Comprehensive admin interface for user and system management
- **Modern UI**: Built with Vue 3, Ant Design Vue, and TypeScript
- **RESTful API**: FastAPI backend with automatic OpenAPI documentation
- **Caching**: Redis-based caching for improved performance
- **Docker Support**: Full containerization with Docker and Docker Compose

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Relational database
- **Redis**: Caching and session management
- **SQLAlchemy**: ORM with async support
- **Alembic**: Database migrations
- **JWT**: Token-based authentication

### Frontend
- **Vue 3**: Progressive JavaScript framework
- **TypeScript**: Type-safe development
- **Ant Design Vue**: UI component library
- **Pinia**: State management
- **Vue Router**: Client-side routing
- **Axios**: HTTP client
- **Vite**: Build tool and dev server

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd navi
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start development environment:
```bash
./scripts/start-dev.sh
```

4. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Default Login

The initial database migration creates a default administrator account:

- Username: `admin`
- Password: `admin123`

Change this password immediately after first login, especially outside local development.

### Production Deployment

1. Configure environment variables in `.env`

2. Start production environment:
```bash
./scripts/start-prod.sh
```

3. Access the application:
- Frontend: http://localhost:80
- Backend API: http://localhost:8000

## Project Structure

```
navi/
├── backend/              # FastAPI backend
│   ├── app/             # Application code
│   │   ├── api/         # API routes
│   │   ├── core/        # Core functionality
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── alembic/         # Database migrations
│   ├── tests/           # Backend tests
│   ├── Dockerfile       # Production Docker image
│   └── requirements.txt # Python dependencies
├── frontend/            # Vue.js frontend
│   ├── src/            # Application code
│   │   ├── api/        # API client
│   │   ├── components/ # Vue components
│   │   ├── router/     # Route definitions
│   │   ├── stores/     # Pinia stores
│   │   ├── types/      # TypeScript types
│   │   └── views/      # Page components
│   ├── Dockerfile      # Production Docker image
│   └── package.json    # Node dependencies
├── scripts/            # Utility scripts
├── docker-compose.yml  # Production compose file
├── docker-compose.dev.yml # Development compose file
└── README.md          # This file
```

## 环境变量

完整配置项请参考 `.env.example`。

关键配置：
- `POSTGRES_PASSWORD`：数据库密码。
- `DATABASE_URL`：PostgreSQL 数据库连接地址。
- `REDIS_URL`：Redis 连接地址。
- `SECRET_KEY`：JWT 签名密钥，生产环境必须修改。
- `DEBUG`：是否启用调试模式，生产环境应设置为 `false`。
- `CORS_ORIGINS`：允许跨域访问的前端域名，默认 `*`。生产环境建议指定明确域名，例如 `https://navi.example.com`。
- `CORS_ALLOW_CREDENTIALS`：是否允许跨域请求携带 Cookie。使用固定前端域名和 HttpOnly Cookie 登录时应设置为 `true`。
- `AUTH_COOKIE_SECURE`：是否仅通过 HTTPS 发送认证 Cookie。生产环境建议设置为 `true`。
- `AUTH_COOKIE_SAMESITE`：认证 Cookie 的 SameSite 策略，默认 `lax`。前后端完全跨站点域名时需设置为 `none`，并同时启用 `AUTH_COOKIE_SECURE=true`。
- `AUTH_COOKIE_DOMAIN`：可选的 Cookie 域名，用于同一主域下多个子域共享登录态。
- `AUTH_CSRF_COOKIE_NAME` / `AUTH_CSRF_HEADER_NAME`：CSRF 双重提交校验使用的 Cookie 名称和请求头名称。

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

### HttpOnly Cookie 认证

JWT 保存在 HttpOnly Cookie 中，前端 JavaScript 无法读取认证 token。非 GET/HEAD 等安全请求使用 CSRF 双重提交校验：后端写入 `AUTH_CSRF_COOKIE_NAME` 指定的 Cookie，前端读取该 CSRF Cookie 后通过 `AUTH_CSRF_HEADER_NAME` 指定的请求头回传。

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## Database Migrations

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Docker Commands

### Development
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Rebuild images
docker-compose -f docker-compose.dev.yml build
```

### Production
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild images
docker-compose build --no-cache
```

## 安全建议

1. **修改默认凭据**：生产环境必须修改默认管理员密码、`SECRET_KEY` 和 `POSTGRES_PASSWORD`。
2. **启用 HTTPS**：生产环境应配置 SSL/TLS 证书。
3. **保护环境变量**：不要将 `.env` 文件提交到版本控制系统。
4. **收紧 CORS 配置**：生产环境将 `CORS_ORIGINS` 设置为明确的前端域名，并在使用 Cookie 登录时保持 `CORS_ALLOW_CREDENTIALS=true`。
5. **启用安全 Cookie**：HTTPS 生产环境设置 `AUTH_COOKIE_SECURE=true`；完全跨站点部署时设置 `AUTH_COOKIE_SAMESITE=none`。
6. **限流与依赖更新**：生产环境建议增加接口限流，并定期更新依赖。

## Troubleshooting

### 数据库连接异常
- 确认 PostgreSQL 容器正在运行：`docker-compose ps`
- 查看数据库日志：`docker-compose logs postgres`
- 检查 `.env` 中的 `DATABASE_URL` 是否正确

### Redis 连接异常
- 确认 Redis 容器正在运行：`docker-compose ps`
- 查看 Redis 日志：`docker-compose logs redis`
- 检查 `.env` 中的 `REDIS_URL` 是否正确

### 前端页面无法加载
- 检查后端是否正常运行：`curl http://localhost:8000/health`
- 确认 `CORS_ORIGINS` 包含前端地址，且 `CORS_ALLOW_CREDENTIALS` 配置符合 Cookie 登录要求
- 查看浏览器控制台错误信息

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

## Support

[Your Support Information Here]
