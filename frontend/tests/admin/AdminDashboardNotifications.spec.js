import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import AdminDashboard from '../../src/views/admin/AdminDashboard.vue'
import { adminApi } from '../../src/api/api'

vi.mock('../../src/api/api', () => ({
  adminApi: {
    getDashboard: vi.fn(),
    getActivityLogs: vi.fn(),
    getCompanies: vi.fn(),
    getStudents: vi.fn(),
    getJobs: vi.fn(),
    getApplications: vi.fn(),
    searchCompanies: vi.fn(),
    searchStudents: vi.fn(),
    getNotifications: vi.fn(),
    markNotificationRead: vi.fn(),
    markAllNotificationsRead: vi.fn()
  }
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

const notificationItems = [
  {
    notification_id: 401,
    title: 'New Company Registration',
    message: 'Flow Dynamics is awaiting approval.',
    is_read: false,
    created_at: '2026-04-10T10:00:00+00:00'
  },
  {
    notification_id: 402,
    title: 'Drive Approved',
    message: 'Data Engineer drive was approved.',
    is_read: true,
    created_at: '2026-04-10T09:00:00+00:00'
  }
]

const buildCollection = (items = []) => ({
  data: {
    data: {
      items,
      total: items.length,
      page: 1,
      pages: 1
    }
  }
})

const mountDashboard = () =>
  mount(AdminDashboard, {
    global: {
      mocks: {
        $router: {
          push: vi.fn()
        }
      },
      stubs: {
        Sidebar: {
          template: '<div class="sidebar-stub"></div>'
        },
        Topbar: {
          props: ['pendingCount'],
          template: `
            <div class="topbar-stub">
              <span class="pending-count">{{ pendingCount }}</span>
              <button class="toggle-notifications" @click="$emit('toggle-notifications')">toggle</button>
            </div>
          `
        },
        AdminNotificationPanel: {
          template: `
            <div class="notif-panel-stub">
              <button class="panel-mark-read" @click="$emit('mark-read', 401)">mark</button>
              <button class="panel-mark-all" @click="$emit('mark-all-read')">mark all</button>
              <button class="panel-close" @click="$emit('close')">close</button>
            </div>
          `
        },
        DashboardOverview: { template: '<div class="dashboard-overview-stub"></div>' },
        CompaniesTable: { template: '<div class="companies-table-stub"></div>' },
        StudentsTable: { template: '<div class="students-table-stub"></div>' },
        DrivesPanel: { template: '<div class="drives-panel-stub"></div>' },
        AnalyticsPanel: { template: '<div class="analytics-panel-stub"></div>' },
        StudentApplicationsModal: { template: '<div class="applications-modal-stub"></div>' }
      }
    }
  })

describe('AdminDashboard notifications integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    adminApi.getDashboard.mockResolvedValue({
      data: {
        data: {
          total_students: 0,
          total_companies: 0,
          total_jobs: 0,
          total_applications: 0
        }
      }
    })
    adminApi.getCompanies.mockResolvedValue(buildCollection([]))
    adminApi.getStudents.mockResolvedValue(buildCollection([]))
    adminApi.getJobs.mockResolvedValue(buildCollection([]))
    adminApi.getApplications.mockResolvedValue(buildCollection([]))
    adminApi.getActivityLogs.mockResolvedValue(buildCollection([]))
    adminApi.getNotifications.mockResolvedValue({
      data: {
        data: {
          items: notificationItems,
          total: notificationItems.length,
          page: 1,
          pages: 1,
          limit: 25,
          unread_count: 1
        }
      }
    })
    adminApi.markNotificationRead.mockResolvedValue({
      data: {
        data: {
          unread_count: 0
        }
      }
    })
    adminApi.markAllNotificationsRead.mockResolvedValue({
      data: {
        data: {
          unread_count: 0
        }
      }
    })
  })

  it('loads notifications, toggles panel, and marks one notification as read', async () => {
    const wrapper = mountDashboard()
    await flushPromises()
    await flushPromises()

    expect(adminApi.getNotifications).toHaveBeenCalledTimes(1)
    expect(wrapper.vm.unreadNotificationsCount).toBe(1)
    expect(wrapper.get('.pending-count').text()).toBe('1')

    await wrapper.get('.toggle-notifications').trigger('click')
    await flushPromises()

    expect(wrapper.vm.showNotifications).toBe(true)
    expect(adminApi.getNotifications).toHaveBeenCalledTimes(2)
    expect(wrapper.find('.notif-panel-stub').exists()).toBe(true)

    await wrapper.get('.panel-mark-read').trigger('click')
    await flushPromises()

    expect(adminApi.markNotificationRead).toHaveBeenCalledWith(401)
    expect(wrapper.vm.unreadNotificationsCount).toBe(0)
    expect(wrapper.vm.notifications.find((item) => item.id === 401)?.read).toBe(true)

    await wrapper.get('.panel-close').trigger('click')
    expect(wrapper.vm.showNotifications).toBe(false)
  })

  it('marks all notifications as read from the panel action', async () => {
    const wrapper = mountDashboard()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.toggle-notifications').trigger('click')
    await flushPromises()

    await wrapper.get('.panel-mark-all').trigger('click')
    await flushPromises()

    expect(adminApi.markAllNotificationsRead).toHaveBeenCalledTimes(1)
    expect(wrapper.vm.unreadNotificationsCount).toBe(0)
    expect(wrapper.vm.notifications.every((item) => item.read)).toBe(true)
  })
})
