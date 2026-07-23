import { createRouter, createWebHistory } from 'vue-router'
import { authGuard, adminGuard, guestGuard } from './guards'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      beforeEnter: guestGuard
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      beforeEnter: authGuard
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      beforeEnter: authGuard
    },
    {
      path: '/admin',
      name: 'admin',
      redirect: '/admin/users',
      beforeEnter: adminGuard,
      children: [
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('@/views/admin/UsersView.vue')
        },
        {
          path: 'user-groups',
          name: 'admin-user-groups',
          component: () => import('@/views/admin/GroupsView.vue')
        },
        {
          path: 'nav-groups',
          name: 'admin-nav-groups',
          component: () => import('@/views/admin/NavigationGroupsView.vue')
        },
        {
          path: 'authorization',
          name: 'admin-authorization',
          component: () => import('@/views/admin/AuthorizationView.vue')
        },
        {
          path: 'settings',
          name: 'admin-settings',
          component: () => import('@/views/admin/SettingsView.vue')
        },
        {
          path: 'audit-logs',
          name: 'admin-audit-logs',
          component: () => import('@/views/admin/AuditLogsView.vue')
        }
      ]
    }
  ]
})

export default router
