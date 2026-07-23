# Navi 前端

Navi 前端基于 Vue 3 和 TypeScript 构建，为导航与链接管理系统提供登录、首页导航、收藏、后台管理、系统设置和审计日志等页面。

## 概览

这是一个现代化响应式单页应用，使用 Vue 3、TypeScript、Ant Design Vue、Pinia、Vue Router、Axios 和 Vite 构建。

## 技术栈

- **Vue 3**：使用组合式 API 构建页面和组件。
- **TypeScript**：提供类型安全。
- **Ant Design Vue**：企业级 UI 组件库。
- **Pinia**：状态管理。
- **Vue Router**：前端路由。
- **Axios**：HTTP 请求客户端。
- **Vite**：前端构建工具和开发服务器。

## 项目结构

```text
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts          # Axios 客户端配置
│   │   ├── auth.ts            # 认证接口
│   │   ├── users.ts           # 用户接口
│   │   ├── roles.ts           # 角色接口
│   │   ├── permissions.ts     # 权限接口
│   │   └── navigation.ts      # 导航接口
│   ├── components/
│   │   ├── layout/            # 布局组件
│   │   ├── navigation/        # 导航组件
│   │   └── common/            # 通用组件
│   ├── router/                # 路由定义
│   ├── stores/                # Pinia 状态
│   ├── types/                 # TypeScript 类型
│   ├── views/                 # 页面视图
│   ├── App.vue                # 根组件
│   └── main.ts                # 应用入口
├── public/                    # 静态资源
├── index.html                 # HTML 模板
├── vite.config.ts             # Vite 配置
├── tsconfig.json              # TypeScript 配置
├── package.json               # Node 依赖
├── Dockerfile                 # 生产镜像构建文件
└── nginx.conf                 # Nginx 配置
```

## 安装与启动

### 本地开发

1. 安装依赖：
```bash
npm install
```

2. 配置环境变量：
```bash
cp .env.example .env
# 如有需要，修改 .env 配置
```

3. 启动开发服务器：
```bash
npm run dev
```

4. 打开浏览器访问：
```text
http://localhost:5173
```

### Docker 开发环境

```bash
# 在项目根目录执行
docker-compose -f docker-compose.dev.yml up frontend
```

## 可用脚本

```bash
npm run dev          # 启动开发服务器，支持热更新
npm run build        # 构建生产产物
npm run preview      # 预览生产构建结果
npm run type-check   # 执行 TypeScript 类型检查
```

## 功能模块

### 认证
- 用户登录。
- HttpOnly Cookie 认证。
- 自动刷新 token。
- 路由登录态保护。
- 会话保持。

### 用户管理
- 查看用户列表。
- 创建、编辑和删除用户。
- 分配用户组和权限相关数据。
- 查看用户资料。

### 角色管理
- 创建和管理角色。
- 为角色分配权限。
- 根据权限控制页面入口和操作。

### 导航管理
- 创建导航分组和链接。
- 管理导航层级。
- 编辑和删除导航数据。
- 支持拖拽排序。

### 审计日志
- 查看关键操作日志。
- 支持按操作、资源和时间筛选。
- 展示用户友好的操作详情。

## 状态管理

应用使用 Pinia 管理状态，主要 store 包括：

### 认证状态 `stores/auth.ts`
- 登录状态。
- 登录和退出操作。
- 当前用户信息。
- 认证状态刷新。

### 用户状态 `stores/users.ts`
- 用户列表。
- 用户增删改查。
- 用户锁定、解锁和密码重置。

### 导航状态 `stores/navigation.ts`
- 导航分组。
- 导航层级。
- 导航分组增删改查。

### 链接状态 `stores/links.ts`
- 链接列表。
- 链接增删改查。
- 链接排序和筛选。

## 路由

路由定义位于 `src/router/index.ts`。

常见路由：
- `/`：首页。
- `/login`：登录页。
- `/links`：链接页。
- `/admin/users`：用户管理，仅管理员可访问。
- `/admin/groups`：用户组管理，仅管理员可访问。
- `/admin/roles`：角色管理，仅管理员可访问。
- `/admin/permissions`：权限管理，仅管理员可访问。
- `/admin/audit-logs`：审计日志，仅管理员可访问。

### 路由守卫

- **认证守卫**：未登录用户访问受保护页面时跳转到登录页。
- **权限守卫**：检查用户是否有访问对应页面的权限。
- **访客守卫**：已登录用户访问登录页时跳转到首页。

## API 集成

API 客户端配置位于 `src/api/client.ts`，主要能力：
- 基础地址配置。
- 请求和响应拦截。
- Cookie 认证请求支持。
- CSRF 请求头自动注入。
- 统一错误处理。
- token 自动刷新。

### 调用接口示例

```typescript
import { authApi } from '@/api/auth'

// 登录
const response = await authApi.login({
  username: 'admin',
  password: 'admin123'
})

// 获取当前用户
const user = await authApi.getCurrentUser()
```

## 组件开发规范

### 组合式 API

使用 Vue 3 组合式 API 和 `<script setup>`：

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)
</script>
```

### TypeScript

新增代码应使用 TypeScript，并为关键数据结构定义类型：

```typescript
interface User {
  id: string
  username: string
  email?: string
}

const users = ref<User[]>([])
```

### Props 和 Emits

组件入参和事件应定义类型：

```vue
<script setup lang="ts">
interface Props {
  title: string
  count?: number
}

interface Emits {
  (e: 'update', value: number): void
}

const props = withDefaults(defineProps<Props>(), {
  count: 0
})

const emit = defineEmits<Emits>()
</script>
```

## 样式

### Ant Design Vue

优先使用 Ant Design Vue 组件保持界面一致：

```vue
<template>
  <a-button type="primary" @click="handleClick">
    确认
  </a-button>
</template>
```

### 自定义样式

组件内样式建议使用 `scoped`：

```vue
<style scoped>
.custom-class {
  color: #1890ff;
}
</style>
```

## 错误处理

### API 错误

API 客户端会统一处理常见错误：

```typescript
try {
  await api.someEndpoint()
} catch (error) {
  // 通用错误已在拦截器中处理，这里只处理当前页面的特殊逻辑
}
```

### 表单校验

表单校验使用 Ant Design Vue 表单能力：

```vue
<a-form :model="form" :rules="rules">
  <a-form-item name="username" label="用户名">
    <a-input v-model:value="form.username" />
  </a-form-item>
</a-form>
```

## 性能优化

- **代码拆分**：路由页面按需加载。
- **摇树优化**：构建时移除未使用代码。
- **资源优化**：图片和静态资源按需压缩和缓存。
- **请求缓存**：对合适的数据使用本地状态缓存。
- **懒加载**：非首屏组件按需加载。

## 构建与部署

### 生产构建
```bash
npm run build
```

构建产物输出到 `dist/` 目录。

### Docker 构建
```bash
docker build -t navi-frontend .
```

### 环境变量
通过 `.env` 文件配置：
- `VITE_API_BASE_URL`：后端 API 基础地址。
- `VITE_CSRF_COOKIE_NAME`：CSRF Cookie 名称，必须与后端 `AUTH_CSRF_COOKIE_NAME` 保持一致。
- `VITE_CSRF_HEADER_NAME`：CSRF 请求头名称，必须与后端 `AUTH_CSRF_HEADER_NAME` 保持一致。

## 浏览器支持

- Chrome 最新版。
- Firefox 最新版。
- Safari 最新版。
- Edge 最新版。

## 开发规范

1. 新代码使用 TypeScript。
2. 遵循 Vue 3 组合式 API 写法。
3. 优先使用 Ant Design Vue 组件。
4. 抽取可复用组件。
5. 保持组件职责清晰，避免单个组件过大。
6. 使用 Pinia 管理共享状态。
7. 明确处理错误状态。
8. 异步操作补充加载状态。

## 排错

### 开发服务器无法启动
- 检查端口 `5173` 是否被占用。
- 确认 Node.js 版本满足项目要求。
- 删除 `node_modules` 后重新安装依赖。

### API 连接异常
- 确认后端服务正在运行。
- 检查 `.env` 中的 `VITE_API_BASE_URL`。
- 查看浏览器控制台是否有 CORS 错误。

### 构建异常
- 运行 `npm run type-check` 查看 TypeScript 错误。
- 清理 Vite 缓存：`rm -rf node_modules/.vite`。
- 确认依赖已完整安装。

### 热更新不生效
- 检查 Vite 配置。
- 检查系统文件监听数量是否耗尽。
- 重启开发服务器。

## 相关资源

- [Vue 3 文档](https://vuejs.org/)
- [Ant Design Vue 文档](https://antdv.com/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Vue Router 文档](https://router.vuejs.org/)
- [Vite 文档](https://vitejs.dev/)
- [TypeScript 文档](https://www.typescriptlang.org/)
