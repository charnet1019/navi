# Navi Frontend

Vue 3 + TypeScript frontend for the Navi navigation and link management system.

## Overview

Modern, responsive single-page application built with Vue 3, TypeScript, and Ant Design Vue.

## Technology Stack

- **Vue 3**: Progressive JavaScript framework with Composition API
- **TypeScript**: Type-safe development
- **Ant Design Vue**: Enterprise-class UI component library
- **Pinia**: Intuitive state management
- **Vue Router**: Official routing library
- **Axios**: Promise-based HTTP client
- **Vite**: Next-generation frontend build tool

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts         # Axios configuration
│   │   ├── auth.ts           # Authentication API
│   │   ├── users.ts          # User API
│   │   ├── roles.ts          # Role API
│   │   ├── permissions.ts    # Permission API
│   │   └── navigation.ts     # Navigation API
│   ├── components/
│   │   ├── layout/           # Layout components
│   │   │   ├── AppHeader.vue
│   │   │   ├── AppSidebar.vue
│   │   │   └── AppLayout.vue
│   │   ├── navigation/       # Navigation components
│   │   └── common/           # Shared components
│   ├── router/
│   │   └── index.ts          # Route definitions
│   ├── stores/
│   │   ├── auth.ts           # Authentication store
│   │   ├── user.ts           # User store
│   │   └── navigation.ts     # Navigation store
│   ├── types/
│   │   ├── auth.ts           # Auth types
│   │   ├── user.ts           # User types
│   │   ├── role.ts           # Role types
│   │   └── navigation.ts     # Navigation types
│   ├── views/
│   │   ├── auth/             # Auth pages
│   │   │   ├── LoginView.vue
│   │   │   └── RegisterView.vue
│   │   ├── admin/            # Admin pages
│   │   │   ├── UsersView.vue
│   │   │   ├── RolesView.vue
│   │   │   └── PermissionsView.vue
│   │   ├── navigation/       # Navigation pages
│   │   │   └── NavigationView.vue
│   │   └── HomeView.vue      # Home page
│   ├── App.vue               # Root component
│   └── main.ts               # Application entry point
├── public/                   # Static assets
├── index.html               # HTML template
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
├── package.json             # Dependencies
├── Dockerfile               # Production Docker image
└── nginx.conf               # Nginx configuration
```

## Setup

### Local Development

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env if needed
```

3. Start development server:
```bash
npm run dev
```

4. Open browser:
```
http://localhost:5173
```

### Docker Development

```bash
# From project root
docker-compose -f docker-compose.dev.yml up frontend
```

## Available Scripts

### Development
```bash
npm run dev          # Start dev server with hot reload
npm run build        # Build for production
npm run preview      # Preview production build
npm run type-check   # Run TypeScript type checking
```

## Features

### Authentication
- User registration and login
- JWT token management
- Automatic token refresh
- Protected routes
- Session persistence

### User Management
- View user list (admin)
- Create/edit/delete users
- Assign roles to users
- User profile management

### Role Management
- Create and manage roles
- Assign permissions to roles
- Role-based UI rendering

### Navigation Management
- Create navigation items
- Organize navigation hierarchy
- Edit and delete items
- Drag-and-drop ordering

## State Management

The application uses Pinia for state management with the following stores:

### Auth Store (`stores/auth.ts`)
- User authentication state
- Login/logout actions
- Token management
- Current user information

### User Store (`stores/user.ts`)
- User list management
- User CRUD operations
- Role assignments

### Navigation Store (`stores/navigation.ts`)
- Navigation items
- CRUD operations
- Hierarchy management

## Routing

Routes are defined in `src/router/index.ts`:

- `/` - Home page
- `/login` - Login page
- `/register` - Registration page
- `/navigation` - Navigation management
- `/admin/users` - User management (admin only)
- `/admin/roles` - Role management (admin only)
- `/admin/permissions` - Permission management (admin only)

### Route Guards

- **Authentication Guard**: Redirects to login if not authenticated
- **Permission Guard**: Checks user permissions for protected routes
- **Guest Guard**: Redirects authenticated users away from auth pages

## API Integration

API client is configured in `src/api/client.ts` with:
- Base URL configuration
- Request/response interceptors
- Automatic token injection
- Error handling
- Token refresh logic

### Making API Calls

```typescript
import { authApi } from '@/api/auth'

// Login
const response = await authApi.login({
  username: 'user',
  password: 'pass'
})

// Get current user
const user = await authApi.getCurrentUser()
```

## Component Guidelines

### Composition API
Use Vue 3 Composition API with `<script setup>`:

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)
</script>
```

### TypeScript
Always use TypeScript with proper typing:

```typescript
interface User {
  id: number
  username: string
  email: string
}

const users = ref<User[]>([])
```

### Props and Emits
Define props and emits with types:

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

## Styling

### Ant Design Vue
Use Ant Design components for consistent UI:

```vue
<template>
  <a-button type="primary" @click="handleClick">
    Click Me
  </a-button>
</template>
```

### Custom Styles
Use scoped styles when needed:

```vue
<style scoped>
.custom-class {
  color: #1890ff;
}
</style>
```

## Error Handling

### API Errors
Errors are handled globally in the API client:

```typescript
try {
  await api.someEndpoint()
} catch (error) {
  // Error is already logged and displayed
  // Handle specific error cases if needed
}
```

### Form Validation
Use Ant Design form validation:

```vue
<a-form :model="form" :rules="rules">
  <a-form-item name="username" label="Username">
    <a-input v-model:value="form.username" />
  </a-form-item>
</a-form>
```

## Performance Optimization

- **Code Splitting**: Routes are lazy-loaded
- **Tree Shaking**: Unused code is removed
- **Asset Optimization**: Images and assets are optimized
- **Caching**: API responses are cached where appropriate
- **Lazy Loading**: Components loaded on demand

## Build and Deployment

### Production Build
```bash
npm run build
```

Output is generated in the `dist/` directory.

### Docker Build
```bash
docker build -t navi-frontend .
```

### Environment Variables
Configure via `.env` file:
- `VITE_API_BASE_URL`: Backend API base URL

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development Guidelines

1. Use TypeScript for all new code
2. Follow Vue 3 Composition API patterns
3. Use Ant Design components
4. Write reusable components
5. Keep components small and focused
6. Use Pinia for state management
7. Handle errors appropriately
8. Add loading states for async operations

## Troubleshooting

### Development server not starting
- Check if port 5173 is available
- Verify Node.js version (16+)
- Delete `node_modules` and reinstall

### API connection errors
- Verify backend is running
- Check `VITE_API_BASE_URL` in `.env`
- Check browser console for CORS errors

### Build errors
- Run `npm run type-check` to find TypeScript errors
- Clear Vite cache: `rm -rf node_modules/.vite`
- Verify all dependencies are installed

### Hot reload not working
- Check Vite configuration
- Verify file watchers are not exhausted
- Restart development server

## Additional Resources

- [Vue 3 Documentation](https://vuejs.org/)
- [Ant Design Vue](https://antdv.com/)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Vue Router Documentation](https://router.vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
