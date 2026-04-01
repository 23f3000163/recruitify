import { createRouter, createWebHistory } from 'vue-router'

import Landing from '../views/Landing.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import AdminDashboard from '../views/admin/AdminDashboard.vue'
import StudentDashboardV2 from '../views/student/StudentDashboardV2.vue'
import CompanyDashboard from '../views/company/CompanyDashboard.vue'

const routes = [
  { path: '/', component: Landing },
  { path: '/login', component: Login },
  { path: '/register', redirect: '/register/student' },
  { path: '/register/student', component: Register },
  { path: '/register/company', component: Register },
  { path: '/admin', component: AdminDashboard },
  { path: '/student', component: StudentDashboardV2 },
  { path: '/student-v2', component: StudentDashboardV2 },
  { path: '/company', component: CompanyDashboard }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router