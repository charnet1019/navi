# Navi 后端

Navi 后端基于 FastAPI 构建，为导航与链接管理系统提供 RESTful API、JWT 认证、角色权限控制、资源授权和系统管理能力。

## 概览

后端负责用户认证、用户管理、角色权限、用户组、导航分组、链接、收藏、系统设置、文件上传和审计日志等核心功能。

## 技术栈

- **FastAPI**：用于构建 API 的 Python Web 框架。
- **PostgreSQL**：主数据库，通过 asyncpg 提供异步访问能力。
- **Redis**：用于缓存、登录失败次数、token 黑名单等数据。
- **SQLAlchemy 2.0**：异步 ORM。
- **Alembic**：数据库迁移工具。
- **Pydantic**：数据校验和配置管理。
- **JWT**：token 认证机制。
- **Uvicorn**：ASGI 服务运行器。

## 项目结构

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/       # API 接口处理器
│   │       │   ├── auth.py      # 认证接口
│   │       │   ├── users.py     # 用户管理
│   │       │   ├── roles.py     # 角色管理
│   │       │   ├── permissions.py # 权限管理
│   │       │   └── navigation.py # 导航接口
│   │       └── router.py        # API 路由配置
│   ├── core/                    # 核心功能
│   ├── models/                  # 数据库模型
│   ├── schemas/                 # Pydantic 数据结构
│   ├── services/                # 业务服务
│   ├── database.py              # 数据库配置
│   ├── redis.py                 # Redis 配置
│   └── main.py                  # 应用入口
├── alembic/
│   ├── versions/                # 迁移文件
│   └── env.py                   # Alembic 配置
├── tests/                       # 测试文件
├── uploads/                     # 文件上传目录
├── Dockerfile                   # 生产镜像构建文件
├── Dockerfile.dev               # 开发镜像构建文件
├── requirements.txt             # Python 依赖
└── alembic.ini                  # Alembic 配置文件
```

## 安装与启动

### 本地开发

1. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Windows 使用：venv\Scripts\activate
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp ../.env.example ../.env
# 按实际环境修改 .env 配置
```

4. 执行数据库迁移：
```bash
alembic upgrade head
```

5. 启动开发服务器：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker 开发环境

```bash
# 在项目根目录执行
docker-compose -f docker-compose.dev.yml up backend
```

## API 接口

### 认证
- `POST /api/v1/auth/register`：注册新用户。
- `POST /api/v1/auth/login`：登录并写入认证 Cookie。
- `POST /api/v1/auth/refresh`：刷新访问 token。
- `POST /api/v1/auth/logout`：退出登录。
- `GET /api/v1/auth/me`：获取当前登录用户。

### 用户
- `GET /api/v1/users`：查询用户列表，仅管理员可用。
- `GET /api/v1/users/{id}`：根据 ID 查询用户。
- `PUT /api/v1/users/{id}`：更新用户。
- `DELETE /api/v1/users/{id}`：删除用户，仅管理员可用。

### 角色
- `GET /api/v1/roles`：查询角色列表。
- `POST /api/v1/roles`：创建角色，仅管理员可用。
- `GET /api/v1/roles/{id}`：根据 ID 查询角色。
- `PUT /api/v1/roles/{id}`：更新角色，仅管理员可用。
- `DELETE /api/v1/roles/{id}`：删除角色，仅管理员可用。

### 权限
- `GET /api/v1/permissions`：查询权限列表。

### 导航分组与链接
- `GET /api/v1/navigation-groups`：查询导航分组。
- `POST /api/v1/navigation-groups`：创建导航分组。
- `PUT /api/v1/navigation-groups/{id}`：更新导航分组。
- `DELETE /api/v1/navigation-groups/{id}`：删除导航分组。
- `GET /api/v1/links`：查询链接。
- `POST /api/v1/links`：创建链接。
- `PUT /api/v1/links/{id}`：更新链接。
- `DELETE /api/v1/links/{id}`：删除链接。

## 数据库迁移

### 创建新迁移
```bash
alembic revision --autogenerate -m "变更说明"
```

### 应用迁移
```bash
alembic upgrade head
```

### 回滚迁移
```bash
alembic downgrade -1
```

### 查看迁移历史
```bash
alembic history
```

### 查看当前版本
```bash
alembic current
```

## 测试

运行全部测试：
```bash
pytest
```

生成覆盖率报告：
```bash
pytest --cov=app --cov-report=html
```

运行指定测试文件：
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
