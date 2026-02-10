import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/LoginView.vue')
    },
    {
      path: '/',
      component: () => import('@/components/layout/AppLayout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
          meta: { title: '仪表盘' }
        },
        {
          path: 'users',
          name: 'Users',
          component: () => import('@/views/user/UserList.vue'),
          meta: { title: '用户管理' }
        },
        {
          path: 'roles',
          name: 'Roles',
          component: () => import('@/views/role/RoleList.vue'),
          meta: { title: '角色管理' }
        },
        {
          path: 'permissions',
          name: 'Permissions',
          component: () => import('@/views/permission/PermissionList.vue'),
          meta: { title: '权限管理' }
        }
      ]
    }
  ]
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
