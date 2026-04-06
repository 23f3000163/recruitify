import { createRouter, createWebHistory } from 'vue-router'

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
  { path: '/student-v2', component: StudentDashboard },
  { path: '/company', component: CompanyDashboard }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router