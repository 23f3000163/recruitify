import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import CompanyDashboard from '../../src/views/company/CompanyDashboard.vue'
import { companyApi, parseApiError } from '../../src/api/api'

vi.mock('../../src/api/api', () => ({
  parseApiError: vi.fn((error, fallback = 'Something went wrong') => (
    error?.response?.data?.error ||
    error?.response?.data?.message ||
    error?.message ||
    fallback
  )),
  companyApi: {
    getDashboardData: vi.fn(),
    mapDashboardSummary: vi.fn(),
    getProfile: vi.fn(),
    getDrives: vi.fn(),
    getApplications: vi.fn(),
    getNotifications: vi.fn(),
    createDrive: vi.fn(),
    updateDrive: vi.fn(),
    updateApplicationStatus: vi.fn(),
    updateProfile: vi.fn(),
    markNotificationRead: vi.fn(),
    markAllNotificationsRead: vi.fn()
  }
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

const SUMMARY = Object.freeze({
  active_drives: 2,
  applications_received: 3,
  interviews_scheduled: 1,
  offers_released: 1,
  offers_accepted: 0,
  offers_rejected: 0,
  unread_notifications: 1
})

const buildDrivesResponse = (items = []) => ({
  data: {
    data: {
      items
    }
  }
})

const buildApplicationsResponse = (items = []) => ({
  data: {
    data: {
      items
    }
  }
})

const buildNotificationsResponse = (items = []) => ({
  data: {
    data: {
      items
    }
  }
})

const configureBootstrapMocks = ({ approvalStatus = 'approved' } = {}) => {
  companyApi.getDashboardData.mockResolvedValue({ summary: SUMMARY })
  companyApi.mapDashboardSummary.mockImplementation((summary) => ({ ...summary }))

  companyApi.getProfile.mockResolvedValue({
    data: {
      data: {
        company_name: 'Acme Labs',
        website: 'acme.example',
        hr_contact_name: 'Ari HR',
        hr_contact_email: 'ari@acme.example',
        industry: 'Software',
        location: 'Pune',
        company_description: 'Hiring backend and data roles.',
        approval_status: approvalStatus,
        created_at: '2024-06-01T00:00:00+00:00'
      }
    }
  })

  companyApi.getDrives.mockResolvedValue(
    buildDrivesResponse([
      {
        id: 11,
        job_title: 'Backend Engineer',
        status: 'approved',
        salary_lpa: 12,
        min_cgpa: 7.0,
        eligible_branches: ['CSE'],
        interview_mode: 'online',
        application_deadline: '2026-12-31T23:59:59+00:00',
        applications_count: 1
      }
    ])
  )

  companyApi.getApplications.mockResolvedValue(
    buildApplicationsResponse([
      {
        application_id: 501,
        drive_id: 11,
        drive_title: 'Backend Engineer',
        student_name: 'Asha Sharma',
        student_email: 'asha@example.com',
        student_branch: 'CSE',
        student_year: 4,
        student_cgpa: 8.6,
        status: 'applied',
        applied_at: '2026-04-01T10:00:00+00:00'
      }
    ])
  )

  companyApi.getNotifications.mockResolvedValue(
    buildNotificationsResponse([
      {
        notification_id: 801,
        title: 'New application received',
        message: 'A new student applied for Backend Engineer.',
        is_read: false,
        created_at: '2026-04-01T11:00:00+00:00'
      }
    ])
  )

  companyApi.updateApplicationStatus.mockResolvedValue({
    data: {
      data: {
        status: 'shortlisted'
      }
    }
  })

  companyApi.createDrive.mockResolvedValue({ data: { success: true } })
  companyApi.updateDrive.mockResolvedValue({ data: { success: true } })
  companyApi.updateProfile.mockResolvedValue({ data: { data: {} } })
  companyApi.markNotificationRead.mockResolvedValue({ data: { success: true } })
  companyApi.markAllNotificationsRead.mockResolvedValue({ data: { success: true } })
}

const makeWrapper = (routerPush = vi.fn()) =>
  mount(CompanyDashboard, {
    global: {
      mocks: {
        $router: {
          push: routerPush
        }
      },
      stubs: {
        Sidebar: {
          name: 'Sidebar',
          template: `
            <div class="sidebar-stub">
              <button class="toggle-sidebar" @click="$emit('toggle-sidebar')">Toggle</button>
              <button class="to-dashboard" @click="$emit('select-view', { id: 'dashboard', locked: false })">Dashboard</button>
              <button class="to-drives" @click="$emit('select-view', { id: 'drives', locked: false })">Drives</button>
              <button class="to-applications" @click="$emit('select-view', { id: 'applications', locked: false })">Applications</button>
              <button class="to-profile" @click="$emit('select-view', { id: 'profile', locked: false })">Profile</button>
              <button class="to-locked" @click="$emit('select-view', { id: 'drives', locked: true })">Locked</button>
            </div>
          `
        },
        Topbar: {
          name: 'Topbar',
          template: `
            <div class="topbar-stub" @click.stop>
              <button class="topbar-toggle-notifications" @click="$emit('toggle-notifications')">Toggle Notifications</button>
              <button class="topbar-open-profile" @click="$emit('open-profile')">Open Profile</button>
            </div>
          `
        },
        NotificationPanel: {
          name: 'NotificationPanel',
          template: `
            <div class="notification-panel-stub" @click.stop>
              <button class="mark-all-read" @click="$emit('mark-all-read')">Mark all read</button>
              <button class="close-notifications" @click="$emit('close')">Close</button>
            </div>
          `
        },
        DashboardOverview: {
          name: 'DashboardOverview',
          template: '<div class="dashboard-overview-stub">Dashboard overview</div>'
        },
        DrivesView: {
          name: 'DrivesView',
          template: `
            <div class="drives-view-stub">
              <button class="open-new-drive" @click="$emit('request-new-drive')">New drive</button>
              <button class="open-applications" @click="$emit('open-applications', 11)">Open applications</button>
            </div>
          `
        },
        ApplicationsView: {
          name: 'ApplicationsView',
          props: ['filteredApplications'],
          template: `
            <div class="applications-view-stub">
              <button
                class="shortlist-first"
                @click="$emit('shortlist', filteredApplications[0])"
              >Shortlist first</button>
            </div>
          `
        },
        ProfileView: {
          name: 'ProfileView',
          template: '<div class="profile-view-stub">Profile view</div>'
        },
        AnalyticsView: {
          name: 'AnalyticsView',
          template: '<div class="analytics-view-stub">Analytics view</div>'
        },
        NewDriveModal: {
          name: 'NewDriveModal',
          template: `
            <div class="new-drive-modal-stub">
              <button class="set-title" @click="$emit('update-field', 'title', 'Platform Engineer Intern')">Title</button>
              <button class="set-salary" @click="$emit('update-field', 'salary', '18')">Salary</button>
              <button class="set-deadline" @click="$emit('update-field', 'deadline', '2026-12-30')">Deadline</button>
              <button class="submit-drive" @click="$emit('submit')">Submit</button>
              <button class="close-drive-modal" @click="$emit('close')">Close</button>
            </div>
          `
        },
        Toast: {
          name: 'Toast',
          props: ['toast'],
          template: '<div class="toast-stub">{{ toast.message }}</div>'
        }
      }
    }
  })

describe('CompanyDashboard phase 6 integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    configureBootstrapMocks()
  })

  it('bootstraps API data and renders dashboard by default', async () => {
    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    expect(companyApi.getDashboardData).toHaveBeenCalledTimes(1)
    expect(companyApi.getProfile).toHaveBeenCalledTimes(1)
    expect(companyApi.getDrives).toHaveBeenCalledTimes(1)
    expect(companyApi.getApplications).toHaveBeenCalledTimes(1)
    expect(companyApi.getNotifications).toHaveBeenCalledTimes(1)
    expect(companyApi.mapDashboardSummary).toHaveBeenCalledTimes(1)

    expect(wrapper.vm.activeView).toBe('dashboard')
    expect(wrapper.find('.dashboard-overview-stub').exists()).toBe(true)
    expect(wrapper.vm.companyProfile.name).toBe('Acme Labs')
    expect(wrapper.vm.myDrives).toHaveLength(1)
    expect(wrapper.vm.allApplications).toHaveLength(1)
  })

  it('shows load error and retries bootstrap successfully when profile call fails', async () => {
    companyApi.getProfile
      .mockRejectedValueOnce({
        response: {
          data: {
            error: 'Profile temporarily unavailable'
          }
        }
      })

    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    expect(wrapper.text()).toContain('Profile temporarily unavailable')
    expect(parseApiError).toHaveBeenCalled()

    await wrapper.get('.rq-btn-primary').trigger('click')
    await flushPromises()
    await flushPromises()

    expect(companyApi.getProfile).toHaveBeenCalledTimes(2)
    expect(wrapper.vm.loadError).toBe('')
    expect(wrapper.find('.dashboard-overview-stub').exists()).toBe(true)
  })

  it('keeps dashboard visible when a non-critical API call fails', async () => {
    companyApi.getNotifications.mockRejectedValueOnce({ message: 'Network Error' })

    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    expect(wrapper.vm.loadError).toBe('')
    expect(wrapper.find('.dashboard-overview-stub').exists()).toBe(true)
    expect(wrapper.vm.toast.show).toBe(true)
    expect(wrapper.vm.toast.type).toBe('warning')
    expect(wrapper.vm.toast.message).toContain('temporarily unavailable')
  })

  it('toggles sidebar and blocks locked section while pending approval', async () => {
    configureBootstrapMocks({ approvalStatus: 'pending' })

    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.toggle-sidebar').trigger('click')
    expect(wrapper.vm.sidebarCollapsed).toBe(true)

    await wrapper.get('.to-locked').trigger('click')
    expect(wrapper.vm.activeView).toBe('dashboard')
    expect(wrapper.vm.toast.show).toBe(true)
    expect(wrapper.vm.toast.type).toBe('warning')
    expect(wrapper.vm.toast.message).toContain('available after admin approval')
  })

  it('creates a new drive from modal and refreshes drive list', async () => {
    companyApi.getDrives
      .mockResolvedValueOnce(
        buildDrivesResponse([
          {
            id: 11,
            job_title: 'Backend Engineer',
            status: 'approved',
            salary_lpa: 12,
            min_cgpa: 7.0,
            eligible_branches: ['CSE'],
            interview_mode: 'online',
            application_deadline: '2026-12-31T23:59:59+00:00',
            applications_count: 1
          }
        ])
      )
      .mockResolvedValueOnce(
        buildDrivesResponse([
          {
            id: 11,
            job_title: 'Backend Engineer',
            status: 'approved',
            salary_lpa: 12,
            min_cgpa: 7.0,
            eligible_branches: ['CSE'],
            interview_mode: 'online',
            application_deadline: '2026-12-31T23:59:59+00:00',
            applications_count: 1
          },
          {
            id: 12,
            job_title: 'Platform Engineer Intern',
            status: 'pending',
            salary_lpa: 18,
            min_cgpa: 7.5,
            eligible_branches: ['CSE', 'ECE'],
            interview_mode: 'both',
            application_deadline: '2026-12-30T23:59:59+00:00',
            applications_count: 0
          }
        ])
      )

    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-drives').trigger('click')
    expect(wrapper.vm.activeView).toBe('drives')

    await wrapper.get('.open-new-drive').trigger('click')
    expect(wrapper.vm.showNewDriveModal).toBe(true)

    await wrapper.get('.set-title').trigger('click')
    await wrapper.get('.set-salary').trigger('click')
    await wrapper.get('.set-deadline').trigger('click')
    await wrapper.get('.submit-drive').trigger('click')
    await flushPromises()
    await flushPromises()

    expect(companyApi.createDrive).toHaveBeenCalledWith(
      expect.objectContaining({
        job_title: 'Platform Engineer Intern',
        salary_lpa: 18,
        application_deadline: '2026-12-30T23:59:59+00:00'
      })
    )
    expect(companyApi.getDrives).toHaveBeenCalledTimes(2)
    expect(wrapper.vm.showNewDriveModal).toBe(false)
    expect(wrapper.vm.myDrives).toHaveLength(2)
    expect(wrapper.vm.toast.message).toContain('submitted for admin approval')
  })

  it('updates application status from applications actions', async () => {
    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-applications').trigger('click')
    expect(wrapper.vm.activeView).toBe('applications')

    await wrapper.get('.shortlist-first').trigger('click')
    await flushPromises()
    await flushPromises()

    expect(companyApi.updateApplicationStatus).toHaveBeenCalledWith(501, { status: 'shortlisted' })
    expect(wrapper.vm.allApplications[0].status).toBe('shortlisted')
    expect(wrapper.vm.toast.message).toContain('shortlisted')
  })

  it('routes to login when an API call returns 401', async () => {
    const push = vi.fn()

    companyApi.getProfile.mockRejectedValue({
      response: {
        status: 401,
        data: {
          error: 'Session expired. Login again.'
        }
      }
    })

    const wrapper = makeWrapper(push)
    await flushPromises()
    await flushPromises()

    expect(push).toHaveBeenCalledWith('/login')
    expect(wrapper.vm.loadError).toBe('Session expired. Login again.')
  })

  it('opens and closes notification panel and marks all as read', async () => {
    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    expect(wrapper.vm.showNotifPanel).toBe(false)

    await wrapper.get('.topbar-toggle-notifications').trigger('click')
    expect(wrapper.vm.showNotifPanel).toBe(true)

    await wrapper.get('.mark-all-read').trigger('click')
    await flushPromises()

    expect(companyApi.markAllNotificationsRead).toHaveBeenCalledTimes(1)
    expect(wrapper.vm.notifications.every((entry) => entry.read)).toBe(true)

    await wrapper.get('.close-notifications').trigger('click')
    expect(wrapper.vm.showNotifPanel).toBe(false)
  })

  it('keeps actions blocked for pending companies', async () => {
    configureBootstrapMocks({ approvalStatus: 'pending' })

    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-applications').trigger('click')
    expect(wrapper.vm.activeView).toBe('applications')

    await wrapper.get('.shortlist-first').trigger('click')
    expect(companyApi.updateApplicationStatus).not.toHaveBeenCalled()
    expect(wrapper.vm.toast.message).toContain('enabled only after admin approval')
    expect(wrapper.vm.toast.type).toBe('warning')
  })
})
