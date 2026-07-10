import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'

const Landing = () => import('../views/Landing.vue')
const Login = () => import('../views/Login.vue')
const Register = () => import('../views/Register.vue')
const AdminDashboard = () => import('../views/admin/AdminDashboard.vue')
const StudentDashboard = () => import('../views/student/StudentDashboard.vue')
const CompanyDashboard = () => import('../views/company/CompanyDashboard.vue')

const routes = [
  { path: '/', component: Landing },
  { path: '/login', component: Login },
  { path: '/register', redirect: '/register/student' },
  { path: '/register/student', component: Register },
  { path: '/register/company', component: Register },
  { path: '/admin', component: AdminDashboard },
  { path: '/student', component: StudentDashboard },
  { path: '/company', component: CompanyDashboard }
]

const PUBLIC_PATHS = new Set(['/', '/login', '/register', '/register/student', '/register/company'])

function roleHome(role) {
  if (role === 'admin') return '/admin'
  if (role === 'student') return '/student'
  if (role === 'company') return '/company'
  return '/login'
}

function routeRequiredRole(path) {
  if (path.startsWith('/admin')) return 'admin'
  if (path.startsWith('/student')) return 'student'
  if (path.startsWith('/company')) return 'company'
  return null
}

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  const token = authStore.token
  const role = String(authStore.role || '').trim().toLowerCase()
  const requiresRole = routeRequiredRole(to.path)

  if (!token) {
    if (PUBLIC_PATHS.has(to.path)) {
      return true
    }
    return '/login'
  }

  if (to.path === '/login' || to.path.startsWith('/register')) {
    return roleHome(role)
  }

  if (!requiresRole) {
    return true
  }

  if (requiresRole !== role) {
    return roleHome(role)
  }

  return true
})

export default router