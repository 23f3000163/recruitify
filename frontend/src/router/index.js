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
  { path: '/admin', component: AdminDashboard, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/student', component: StudentDashboard, meta: { requiresAuth: true, role: 'student' } },
  { path: '/company', component: CompanyDashboard, meta: { requiresAuth: true, role: 'company' } },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue')
  }
]

function roleHome(role) {
  if (role === 'admin') return '/admin'
  if (role === 'company') return '/company'
  return '/student'
}

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return '/login'
  }
  if (to.meta.role && auth.role !== to.meta.role) {
    if (!auth.isAuthenticated) return '/login'
    return roleHome(auth.role)
  }
})

export default router