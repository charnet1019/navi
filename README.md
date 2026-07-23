# Navi 导航与链接管理系统

Navi 是一个用于管理导航链接的全栈 Web 应用，支持基于角色的访问控制、导航分组、链接管理、用户管理和系统设置。

## 功能特性

- **用户认证**：基于 JWT 与 HttpOnly Cookie 的登录认证，支持访问 token 和刷新 token。
- **角色权限控制**：支持角色、权限、用户组和细粒度资源授权。
- **导航管理**：支持创建、组织和管理导航分组与链接。
- **后台管理**：提供用户、用户组、角色、链接、导航分组、权限、系统设置和审计日志管理。
- **现代前端**：基于 Vue 3、Ant Design Vue 和 TypeScript 构建。
- **RESTful API**：后端基于 FastAPI，提供自动接口文档。
- **缓存支持**：使用 Redis 缓存权限、登录失败次数和 token 黑名单等数据。
- **容器化部署**：支持 Docker Compose 和 Kubernetes 部署。

## 技术栈

### 后端
- **FastAPI**：Python Web 框架。
- **PostgreSQL**：关系型数据库。
- **Redis**：缓存和会话辅助存储。
- **SQLAlchemy**：异步 ORM。
- **Alembic**：数据库迁移工具。
- **JWT**：token 认证机制。

### 前端
- **Vue 3**：前端框架。
- **TypeScript**：类型安全的前端开发语言。
- **Ant Design Vue**：UI 组件库。
- **Pinia**：状态管理。
- **Vue Router**：前端路由。
- **Axios**：HTTP 请求客户端。
- **Vite**：构建工具和开发服务器。

## 快速开始

### 环境要求

- Docker 和 Docker Compose
- Git

### 开发环境启动

1. 克隆代码仓库：
```bash
git clone <repository-url>
cd navi
```

2. 创建环境变量文件：
```bash
cp .env.example .env
# 按实际环境修改 .env 配置
```

3. 启动开发环境：
```bash
./scripts/start-dev.sh
```

4. 访问应用：
- 前端地址：http://localhost:5173
- 后端接口：http://localhost:8000
- 接口文档：http://localhost:8000/docs

### 默认登录账号

初始数据库迁移会创建默认管理员账号：

- 用户名：`admin`
- 密码：`admin123`

首次登录后请立即修改默认密码，生产环境尤其必须修改。

### 生产环境部署

1. 在 `.env` 中配置生产环境变量。

2. 启动生产环境：
```bash
./scripts/start-prod.sh
```

3. 访问应用：
- 前端地址：http://localhost:80
- 后端接口：http://localhost:8000

## 项目结构

```text
navi/
├── backend/              # FastAPI 后端
│   ├── app/              # 后端应用代码
│   │   ├── api/          # API 路由
│   │   ├── core/         # 核心功能
│   │   ├── models/       # 数据库模型
│   │   ├── schemas/      # Pydantic 数据结构
│   │   └── services/     # 业务服务
│   ├── alembic/          # 数据库迁移
│   ├── tests/            # 后端测试
│   ├── Dockerfile        # 生产镜像构建文件
│   └── requirements.txt  # Python 依赖
├── frontend/             # Vue 前端
│   ├── src/              # 前端应用代码
│   │   ├── api/          # API 客户端
│   │   ├── components/   # Vue 组件
│   │   ├── router/       # 路由定义
│   │   ├── stores/       # Pinia 状态
│   │   ├── types/        # TypeScript 类型
│   │   └── views/        # 页面视图
│   ├── Dockerfile        # 生产镜像构建文件
│   └── package.json      # Node 依赖
├── scripts/              # 脚本工具
├── docker-compose.yml    # 生产 Compose 文件
├── docker-compose.dev.yml # 开发 Compose 文件
└── README.md             # 项目说明
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

## API 文档

交互式 API 文档地址：
- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

## 开发

### 后端开发

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 执行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产产物
npm run build
```

## 测试

### 后端测试
```bash
cd backend
pytest
```

### 前端测试
```bash
cd frontend
npm run test
```

## 数据库迁移

创建新迁移：
```bash
cd backend
alembic revision --autogenerate -m "变更说明"
```

应用迁移：
```bash
alembic upgrade head
```

回滚迁移：
```bash
alembic downgrade -1
```

## Docker 命令

### 开发环境
```bash
# 启动所有服务
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 停止所有服务
docker-compose -f docker-compose.dev.yml down

# 重新构建镜像
docker-compose -f docker-compose.dev.yml build
```

### 生产环境
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止所有服务
docker-compose down

# 重新构建镜像
docker-compose build --no-cache
```

## 安全建议

1. **修改默认凭据**：生产环境必须修改默认管理员密码、`SECRET_KEY` 和 `POSTGRES_PASSWORD`。
2. **启用 HTTPS**：生产环境应配置 SSL/TLS 证书。
3. **保护环境变量**：不要将 `.env` 文件提交到版本控制系统。
4. **收紧 CORS 配置**：生产环境将 `CORS_ORIGINS` 设置为明确的前端域名，并在使用 Cookie 登录时保持 `CORS_ALLOW_CREDENTIALS=true`。
5. **启用安全 Cookie**：HTTPS 生产环境设置 `AUTH_COOKIE_SECURE=true`；完全跨站点部署时设置 `AUTH_COOKIE_SAMESITE=none`。
6. **限流与依赖更新**：生产环境建议增加接口限流，并定期更新依赖。

## 排错

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

## 许可证

待补充。

## 贡献指南

待补充。

## 支持

待补充。
