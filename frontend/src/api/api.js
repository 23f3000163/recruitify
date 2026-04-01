import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:5000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

let isRedirectingToLogin = false

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const statusCode = error.response?.status
    const requestUrl = String(error.config?.url || '')
    const hasToken = Boolean(localStorage.getItem('token'))
    const isLoginRequest = requestUrl.includes('/auth/login')

    if (statusCode === 401 && hasToken && !isLoginRequest && !isRedirectingToLogin) {
      isRedirectingToLogin = true

      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('user_id')

      if (window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    }

    return Promise.reject(error)
  }
)

export const authApi = {
  login(payload) {
    return api.post('/auth/login', payload)
  },
  getMe() {
    return api.get('/auth/me')
  },
  registerStudent(payload) {
    return api.post('/auth/register/student', payload)
  },
  registerCompany(payload) {
    return api.post('/auth/register/company', payload)
  }
}

export const companyApi = {
  getDashboard() {
    return api.get('/auth/company/dashboard')
  },
  getDrives(params = {}) {
    return api.get('/company/drives', { params })
  },
  createDrive(payload) {
    return api.post('/company/drives', payload)
  },
  closeDrive(driveId) {
    return api.put(`/company/drives/${driveId}/close`)
  },
  getApplications(params = {}) {
    return api.get('/company/applications', { params })
  },
  updateApplicationStatus(applicationId, payload) {
    return api.put(`/company/applications/${applicationId}/status`, payload)
  },
  getInterviews(params = {}) {
    return api.get('/company/interviews', { params })
  },
  scheduleInterview(payload) {
    return api.post('/company/interviews', payload)
  },
  updateInterviewResult(interviewId, payload) {
    return api.put(`/company/interviews/${interviewId}/result`, payload)
  },
  getOffers(params = {}) {
    return api.get('/company/offers', { params })
  },
  createOffer(payload) {
    return api.post('/company/offers', payload)
  },
  getNotifications(params = {}) {
    return api.get('/company/notifications', { params })
  },
  markNotificationRead(notificationId) {
    return api.put(`/company/notifications/${notificationId}/read`)
  },
  markAllNotificationsRead() {
    return api.put('/company/notifications/read-all')
  }
}

export const adminApi = {
  getDashboard(params = {}) {
    return api.get('/admin/dashboard', { params })
  },
  getActivityLogs(params = {}) {
    return api.get('/admin/activity-logs', { params })
  },
  getCompanies(params = {}) {
    return api.get('/admin/companies', { params })
  },
  approveCompany(companyId) {
    return api.put(`/admin/company/${companyId}/approve`)
  },
  rejectCompany(companyId) {
    return api.put(`/admin/company/${companyId}/reject`)
  },
  deleteCompany(companyId) {
    return api.delete(`/admin/company/${companyId}`)
  },
  deactivateCompany(companyId) {
    return api.put(`/admin/company/${companyId}/deactivate`)
  },
  activateCompany(companyId) {
    return api.put(`/admin/company/${companyId}/activate`)
  },
  getStudents(params = {}) {
    return api.get('/admin/students', { params })
  },
  deactivateStudent(studentId) {
    return api.put(`/admin/student/${studentId}/deactivate`)
  },
  activateStudent(studentId) {
    return api.put(`/admin/student/${studentId}/activate`)
  },
  getJobs(params = {}) {
    return api.get('/admin/jobs', { params })
  },
  approveJob(jobId) {
    return api.put(`/admin/job/${jobId}/approve`)
  },
  rejectJob(jobId) {
    return api.put(`/admin/job/${jobId}/reject`)
  },
  deleteJob(jobId) {
    return api.delete(`/admin/job/${jobId}`)
  },
  getApplications(params = {}) {
    return api.get('/admin/applications', { params })
  },
  updateApplicationStatus(applicationId, payload) {
    return api.put(`/admin/application/${applicationId}/status`, payload)
  },
  searchCompanies(query, params = {}) {
    return api.get('/admin/search/companies', { params: { q: query, ...params } })
  },
  searchStudents(query, params = {}) {
    return api.get('/admin/search/students', { params: { q: query, ...params } })
  }
}

export const studentApi = {
  getDashboard() {
    return api.get('/student/dashboard')
  },
  getApplications(params = {}) {
    return api.get('/student/applications', { params })
  },
  getNotifications(params = {}) {
    return api.get('/student/notifications', { params })
  },
  markNotificationRead(notificationId) {
    return api.put(`/student/notifications/${notificationId}/read`)
  },
  markAllNotificationsRead() {
    return api.put('/student/notifications/read-all')
  },
  respondToOffer(offerId, payload) {
    return api.put(`/student/offers/${offerId}/respond`, payload)
  },
  updateProfile(payload) {
    return api.put('/student/profile', payload)
  }
}

export default api
