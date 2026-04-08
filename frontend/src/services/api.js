import axios from 'axios'

const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) ||
  'http://127.0.0.1:5000'

const AUTH_STORAGE_KEYS = Object.freeze(['token', 'role', 'user_id'])
let isRedirectingToLogin = false

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

function clearAuthStorage() {
  AUTH_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key))
}

function maybeRedirectToLogin() {
  if (isRedirectingToLogin) {
    return
  }

  isRedirectingToLogin = true
  clearAuthStorage()

  if (window.location.pathname !== '/login') {
    window.location.assign('/login')
    return
  }

  isRedirectingToLogin = false
}

export function parseApiError(error, fallbackMessage = 'Something went wrong. Please try again.') {
  return (
    error?.response?.data?.error ||
    error?.response?.data?.message ||
    error?.message ||
    fallbackMessage
  )
}

function isEndpointMissing(error) {
  const status = error?.response?.status
  return status === 404 || status === 405
}

async function requestWithFallback(requestFns) {
  let lastError = null

  for (let index = 0; index < requestFns.length; index += 1) {
    const requestFn = requestFns[index]

    try {
      return await requestFn()
    } catch (error) {
      lastError = error

      const hasAnotherOption = index < requestFns.length - 1
      if (!hasAnotherOption || !isEndpointMissing(error)) {
        throw error
      }
    }
  }

  throw lastError || new Error('Request failed')
}

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const statusCode = error?.response?.status
    const requestUrl = String(error?.config?.url || '')
    const hasToken = Boolean(localStorage.getItem('token'))
    const isLoginRequest = requestUrl.includes('/auth/login')

    if (statusCode === 401 && hasToken && !isLoginRequest) {
      maybeRedirectToLogin()
    }

    return Promise.reject(error)
  }
)

function mapDashboardSummary(summary = {}) {
  return {
    active_drives: Number(summary.active_drives || summary.total_drives || 0),
    applications_received: Number(summary.applications_received || summary.total_applications || 0),
    interviews_scheduled: Number(summary.interviews_scheduled || 0),
    offers_released: Number(summary.offers_released || 0),
    offers_accepted: Number(summary.offers_accepted || 0),
    offers_rejected: Number(summary.offers_rejected || 0),
    unread_notifications: Number(summary.unread_notifications || 0)
  }
}

async function fetchDashboardRaw() {
  return requestWithFallback([
    () => apiClient.get('/company/dashboard'),
    () => apiClient.get('/auth/company/dashboard')
  ])
}

async function deriveDashboardData() {
  const [drivesRes, appsRes, notificationsRes, meRes] = await Promise.all([
    companyApi.getDrives({ page: 1, limit: 100 }),
    companyApi.getApplications({ page: 1, limit: 100 }),
    companyApi.getNotifications({ page: 1, limit: 100, is_read: 'all' }),
    authApi.getMe()
  ])

  const drivesData = drivesRes?.data?.data || {}
  const appsData = appsRes?.data?.data || {}
  const notificationsData = notificationsRes?.data?.data || {}
  const meData = meRes?.data?.data || {}

  const driveItems = Array.isArray(drivesData.items) ? drivesData.items : []
  const appItems = Array.isArray(appsData.items) ? appsData.items : []

  const summary = {
    active_drives: driveItems.filter((drive) => ['pending', 'approved', 'active'].includes(String(drive.status || '').toLowerCase())).length,
    applications_received: Number(appsData.total || appItems.length || 0),
    interviews_scheduled: appItems.filter((item) => String(item.status || '').toLowerCase() === 'interview').length,
    offers_released: appItems.filter((item) => String(item.status || '').toLowerCase() === 'offered').length,
    offers_accepted: appItems.filter((item) => String(item.status || '').toLowerCase() === 'placed').length,
    offers_rejected: appItems.filter((item) => String(item.status || '').toLowerCase() === 'rejected').length,
    unread_notifications: Number(notificationsData.unread_count || 0)
  }

  const pipeline = [
    {
      id: 'applied',
      label: 'Applied',
      count: appItems.filter((item) => String(item.status || '').toLowerCase() === 'applied').length
    },
    {
      id: 'shortlisted',
      label: 'Shortlisted',
      count: appItems.filter((item) => String(item.status || '').toLowerCase() === 'shortlisted').length
    },
    {
      id: 'interview',
      label: 'Interview',
      count: appItems.filter((item) => String(item.status || '').toLowerCase() === 'interview').length
    },
    {
      id: 'offered',
      label: 'Offered',
      count: appItems.filter((item) => String(item.status || '').toLowerCase() === 'offered').length
    }
  ]

  return {
    user: {
      user_id: meData.user_id,
      username: meData.username,
      email: meData.email,
      company_name: meData.username
    },
    summary,
    pipeline,
    recent_applicants: appItems.slice(0, 8).map((item) => ({
      application_id: item.application_id || item.id,
      student_name: item.student_name || item?.student?.name || 'Candidate',
      job_title: item.drive_title || item?.drive?.title || 'Drive',
      status: item.status,
      updated_at: item.updated_at || item.applied_at || null
    }))
  }
}

export const authApi = {
  login(payload) {
    return apiClient.post('/auth/login', payload)
  },
  getMe() {
    return apiClient.get('/auth/me')
  },
  registerStudent(payload) {
    return apiClient.post('/auth/register/student', payload)
  },
  registerCompany(payload) {
    return apiClient.post('/auth/register/company', payload)
  }
}

export const applicationsApi = {
  applyToJob(payload) {
    return apiClient.post('/applications', payload)
  },
  getStudentApplications(params = {}) {
    return apiClient.get('/applications/student', { params })
  },
  getApplicationsForJob(jobId, params = {}) {
    return apiClient.get(`/applications/job/${jobId}`, { params })
  },
  updateStatus(applicationId, payload) {
    return apiClient.patch(`/applications/${applicationId}`, payload)
  },
  scoreResumeKeywords(payload) {
    return apiClient.post('/applications/screener', payload)
  }
}

export const companyApi = {
  getDashboard() {
    return requestWithFallback([
      () => apiClient.get('/company/dashboard'),
      () => apiClient.get('/auth/company/dashboard')
    ])
  },

  async getDashboardData() {
    try {
      const response = await fetchDashboardRaw()
      return response?.data?.data || {}
    } catch (error) {
      const statusCode = error?.response?.status
      if (statusCode === 401 || statusCode === 403) {
        throw error
      }

      return deriveDashboardData()
    }
  },

  async getProfile() {
    try {
      const response = await requestWithFallback([
        () => apiClient.get('/company/profile'),
        () => apiClient.get('/company/company-profile')
      ])
      return response
    } catch (error) {
      if (!isEndpointMissing(error)) {
        throw error
      }

      const [meResponse, dashboardResponse] = await Promise.all([
        authApi.getMe(),
        fetchDashboardRaw().catch(() => ({ data: { data: {} } }))
      ])

      const me = meResponse?.data?.data || {}
      const dashUser = dashboardResponse?.data?.data?.user || {}

      return {
        data: {
          success: true,
          data: {
            user_id: me.user_id || dashUser.user_id || null,
            username: me.username || 'Company User',
            email: me.email || '',
            company_id: dashUser.company_id || null,
            company_name: dashUser.company_name || me.username || 'Company User',
            industry: '',
            website: '',
            company_description: '',
            hr_contact_name: me.username || '',
            hr_contact_email: me.email || '',
            hr_contact_phone: '',
            approval_status: 'approved'
          }
        }
      }
    }
  },

  updateProfile(payload) {
    return requestWithFallback([
      () => apiClient.patch('/company/profile', payload),
      () => apiClient.put('/company/profile', payload)
    ])
  },

  getDrives(params = {}) {
    return apiClient.get('/company/drives', { params })
  },

  createDrive(payload) {
    return requestWithFallback([
      () => apiClient.post('/drives', payload),
      () => apiClient.post('/company/drives', payload)
    ])
  },

  updateDrive(driveId, payload) {
    const normalizedPayload = payload || {}

    if (String(normalizedPayload.status || '').toLowerCase() === 'closed') {
      return requestWithFallback([
        () => apiClient.patch(`/drives/${driveId}`, normalizedPayload),
        () => apiClient.put(`/company/drives/${driveId}/close`)
      ])
    }

    return requestWithFallback([
      () => apiClient.patch(`/drives/${driveId}`, normalizedPayload),
      () => apiClient.patch(`/company/drives/${driveId}`, normalizedPayload)
    ])
  },

  closeDrive(driveId) {
    return requestWithFallback([
      () => apiClient.patch(`/drives/${driveId}`, { status: 'closed' }),
      () => apiClient.put(`/company/drives/${driveId}/close`)
    ])
  },

  getApplications(params = {}) {
    return requestWithFallback([
      () => apiClient.get('/applications/company', { params }),
      () => apiClient.get('/company/applications', { params })
    ])
  },

  getApplicationsForJob(jobId, params = {}) {
    return apiClient.get(`/applications/job/${jobId}`, { params })
  },

  updateApplicationStatus(applicationId, payload) {
    const legacyStatusMap = {
      interview: 'interviewed',
      offered: 'selected',
      placed: 'selected'
    }

    const fallbackPayload = {
      ...payload,
      status: legacyStatusMap[String(payload?.status || '').toLowerCase()] || payload?.status
    }

    return requestWithFallback([
      () => apiClient.patch(`/applications/${applicationId}`, payload),
      () => apiClient.put(`/company/applications/${applicationId}/status`, fallbackPayload)
    ])
  },

  scoreApplicationResume(applicationId, keywords = null) {
    const payload = {
      application_id: applicationId
    }
    if (keywords) {
      payload.keywords = keywords
    }
    return applicationsApi.scoreResumeKeywords(payload)
  },

  getInterviews(params = {}) {
    return apiClient.get('/company/interviews', { params })
  },

  scheduleInterview(payload) {
    return apiClient.post('/company/interviews', payload)
  },

  updateInterviewResult(interviewId, payload) {
    return apiClient.put(`/company/interviews/${interviewId}/result`, payload)
  },

  getOffers(params = {}) {
    return apiClient.get('/company/offers', { params })
  },

  createOffer(payload) {
    return apiClient.post('/company/offers', payload)
  },

  getNotifications(params = {}) {
    return apiClient.get('/company/notifications', { params })
  },

  markNotificationRead(notificationId) {
    return apiClient.put(`/company/notifications/${notificationId}/read`)
  },

  markAllNotificationsRead() {
    return apiClient.put('/company/notifications/read-all')
  },

  triggerApplicationsExportJob() {
    return apiClient.post('/jobs/exports/company/applications')
  },

  triggerDrivesExportJob() {
    return apiClient.post('/jobs/exports/company/drives')
  },

  triggerPlacementsExportJob() {
    return apiClient.post('/jobs/exports/company/placements')
  },

  getExportStatus(jobId) {
    return apiClient.get(`/jobs/exports/company/${jobId}`)
  },

  downloadExport(jobId) {
    return apiClient.get(`/jobs/exports/company/${jobId}/download`, {
      responseType: 'blob'
    })
  },

  mapDashboardSummary
}

export const adminApi = {
  getDashboard(params = {}) {
    return apiClient.get('/admin/dashboard', { params })
  },
  getAnalyticsOverview(params = {}) {
    return apiClient.get('/admin/analytics/overview', { params })
  },
  getPublicLandingDashboard(params = {}) {
    return apiClient.get('/admin/public/landing-dashboard', { params })
  },
  getActivityLogs(params = {}) {
    return apiClient.get('/admin/activity-logs', { params })
  },
  getCompanies(params = {}) {
    return apiClient.get('/admin/companies', { params })
  },
  approveCompany(companyId) {
    return apiClient.put(`/admin/company/${companyId}/approve`)
  },
  rejectCompany(companyId) {
    return apiClient.put(`/admin/company/${companyId}/reject`)
  },
  deleteCompany(companyId) {
    return apiClient.delete(`/admin/company/${companyId}`)
  },
  deactivateCompany(companyId) {
    return apiClient.put(`/admin/company/${companyId}/deactivate`)
  },
  activateCompany(companyId) {
    return apiClient.put(`/admin/company/${companyId}/activate`)
  },
  getStudents(params = {}) {
    return apiClient.get('/admin/students', { params })
  },
  deactivateStudent(studentId) {
    return apiClient.put(`/admin/student/${studentId}/deactivate`)
  },
  activateStudent(studentId) {
    return apiClient.put(`/admin/student/${studentId}/activate`)
  },
  getJobs(params = {}) {
    return apiClient.get('/admin/jobs', { params })
  },
  approveJob(jobId) {
    return apiClient.put(`/admin/job/${jobId}/approve`)
  },
  rejectJob(jobId) {
    return apiClient.put(`/admin/job/${jobId}/reject`)
  },
  deleteJob(jobId) {
    return apiClient.delete(`/admin/job/${jobId}`)
  },
  getApplications(params = {}) {
    return apiClient.get('/admin/applications', { params })
  },
  updateApplicationStatus(applicationId, payload) {
    return apiClient.put(`/admin/application/${applicationId}/status`, payload)
  },
  searchCompanies(query, params = {}) {
    return apiClient.get('/admin/search/companies', { params: { q: query, ...params } })
  },
  searchStudents(query, params = {}) {
    return apiClient.get('/admin/search/students', { params: { q: query, ...params } })
  },
  getNotifications(params = {}) {
    return apiClient.get('/admin/notifications', { params })
  },
  markNotificationRead(notificationId) {
    return apiClient.put(`/admin/notifications/${notificationId}/read`)
  },
  markAllNotificationsRead() {
    return apiClient.put('/admin/notifications/read-all')
  },
  triggerExport(scope) {
    return apiClient.post(`/jobs/exports/admin/${scope}`)
  },
  getExportStatus(jobId) {
    return apiClient.get(`/jobs/exports/admin/jobs/${jobId}`)
  },
  downloadExport(jobId) {
    return apiClient.get(`/jobs/exports/admin/jobs/${jobId}/download`, {
      responseType: 'blob'
    })
  }
}

export const studentApi = {
  getDashboard() {
    return requestWithFallback([
      () => apiClient.get('/student/dashboard')
    ])
  },
  getProfile() {
    return requestWithFallback([
      () => apiClient.get('/student/profile')
    ])
  },
  getDrives(params = {}) {
    return requestWithFallback([
      () => apiClient.get('/student/drives', { params }),
      () => apiClient.get('/drives', { params })
    ])
  },
  applyToDrive(driveId) {
    return requestWithFallback([
      () => apiClient.post(`/student/drives/${driveId}/apply`),
      () => applicationsApi.applyToJob({ job_id: driveId })
    ])
  },
  getApplications(params = {}) {
    return applicationsApi.getStudentApplications(params)
  },
  scoreResumeForJob(jobId, keywords = null) {
    const payload = {
      job_id: jobId
    }
    if (keywords) {
      payload.keywords = keywords
    }
    return applicationsApi.scoreResumeKeywords(payload)
  },
  applyToJob(jobId) {
    return applicationsApi.applyToJob({ job_id: jobId })
  },
  getHistory(params = {}) {
    return apiClient.get('/student/history', { params })
  },
  triggerApplicationsExportJob() {
    return apiClient.post('/jobs/exports/applications')
  },
  triggerHistoryExportJob() {
    return apiClient.post('/jobs/exports/history')
  },
  getExportStatus(jobId) {
    return apiClient.get(`/jobs/exports/${jobId}`)
  },
  downloadExport(jobId) {
    return apiClient.get(`/jobs/exports/${jobId}/download`, {
      responseType: 'blob'
    })
  },
  getNotifications(params = {}) {
    return apiClient.get('/student/notifications', { params })
  },
  markNotificationRead(notificationId) {
    return requestWithFallback([
      () => apiClient.patch(`/student/notifications/${notificationId}`),
      () => apiClient.put(`/student/notifications/${notificationId}/read`)
    ])
  },
  markAllNotificationsRead() {
    return requestWithFallback([
      () => apiClient.patch('/student/notifications/read-all'),
      () => apiClient.put('/student/notifications/read-all')
    ])
  },
  respondToOffer(offerId, payload) {
    return apiClient.put(`/student/offers/${offerId}/respond`, payload)
  },
  downloadOfferDocument(offerId) {
    return apiClient.get(`/student/offers/${offerId}/document`, {
      responseType: 'blob'
    })
  },
  downloadPlacementDocument(placementId) {
    return apiClient.get(`/student/placements/${placementId}/document`, {
      responseType: 'blob'
    })
  },
  updateProfile(payload) {
    return requestWithFallback([
      () => apiClient.patch('/student/profile', payload),
      () => apiClient.put('/student/profile', payload)
    ])
  },
  uploadResume(file) {
    const formData = new FormData()
    formData.append('resume', file)

    return apiClient.post('/student/profile/resume', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

export default apiClient
