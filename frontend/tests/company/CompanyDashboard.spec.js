import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import CompanyDashboard from '../../src/views/company/CompanyDashboard.vue'
import { authApi, companyApi } from '../../src/api/api'

vi.mock('../../src/api/api', () => ({
  authApi: {
    getMe: vi.fn()
  },
  companyApi: {
    getDashboard: vi.fn()
  }
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

const STORAGE_KEYS = {
  activeView: 'company.dashboard.activeView',
  sidebarCollapsed: 'company.dashboard.sidebarCollapsed'
}

const buildDashboardResponse = () => ({
  data: {
    message: 'Authenticated',
    data: {
      user: {
        user_id: 41,
        company_name: 'Acme Labs'
      },
      summary: {
        active_drives: 3,
        applications_received: 12,
        interviews_scheduled: 5,
        offers_released: 2,
        offers_accepted: 1,
        offers_rejected: 1,
        unread_notifications: 4
      },
      pipeline: [
        { id: 'applied', label: 'Applied', count: 12 },
        { id: 'shortlisted', label: 'Shortlisted', count: 6 }
      ],
      recent_applicants: [
        {
          application_id: 101,
          student_name: 'Asha Sharma',
          job_title: 'Platform Engineer',
          status: 'shortlisted'
        }
      ]
    }
  }
})

const makeWrapper = (routerPush = vi.fn()) =>
  mount(CompanyDashboard, {
    global: {
      mocks: {
        $router: {
          push: routerPush
        }
      },
      stubs: {
        CompanySidebar: {
          name: 'CompanySidebar',
          template: `
            <div class="sidebar-stub">
              <button class="toggle-sidebar" @click="$emit('toggle-sidebar')">Toggle</button>
              <button class="to-drives" @click="$emit('select-view', 'drives')">Drives</button>
              <button class="to-interviews" @click="$emit('select-view', 'interviews')">Interviews</button>
              <button class="to-notifications" @click="$emit('select-view', 'notifications')">Notifications</button>
              <button class="sidebar-logout" @click="$emit('request-logout')">Logout</button>
            </div>
          `
        },
        CompanyTopbar: {
          name: 'CompanyTopbar',
          props: ['currentPageTitle', 'dashboardMessage', 'syncNote', 'syncTone'],
          template: `
            <div class="topbar-stub">
              <span class="page-title">{{ currentPageTitle }}</span>
              <span class="dashboard-message">{{ dashboardMessage }}</span>
              <span class="sync-note">{{ syncNote }}</span>
              <span class="sync-tone">{{ syncTone }}</span>
              <button class="topbar-logout" @click="$emit('request-logout')">Logout</button>
            </div>
          `
        },
        CompanyOverview: {
          name: 'CompanyOverview',
          template: '<div class="overview-stub">Overview module</div>'
        },
        DriveManagement: {
          name: 'DriveManagement',
          template: '<button class="drive-updated" @click="$emit(\'drive-updated\')">Emit</button>'
        },
        CompanyApplications: {
          name: 'CompanyApplications',
          template: '<button class="applications-updated" @click="$emit(\'applications-updated\')">Emit</button>'
        },
        CompanyInterviews: {
          name: 'CompanyInterviews',
          template: '<button class="interviews-updated" @click="$emit(\'interviews-updated\')">Emit</button>'
        },
        CompanyOffers: {
          name: 'CompanyOffers',
          template: '<button class="offers-updated" @click="$emit(\'offers-updated\')">Emit</button>'
        },
        CompanyNotifications: {
          name: 'CompanyNotifications',
          template: '<button class="notifications-updated" @click="$emit(\'notifications-updated\')">Emit</button>'
        }
      }
    }
  })

describe('CompanyDashboard phase 6 integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('bootstraps identity and renders overview by default', async () => {
    authApi.getMe.mockResolvedValue({
      data: {
        data: {
          user_id: 41,
          username: 'acme_admin',
          email: 'admin@acme.example'
        }
      }
    })
    companyApi.getDashboard.mockResolvedValue(buildDashboardResponse())

    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    expect(authApi.getMe).toHaveBeenCalledTimes(1)
    expect(companyApi.getDashboard).toHaveBeenCalledTimes(1)
    expect(wrapper.find('.overview-stub').exists()).toBe(true)
    expect(wrapper.text()).toContain('Authenticated')
    expect(wrapper.vm.summary).toMatchObject({
      active_drives: 3,
      applications_received: 12,
      interviews_scheduled: 5,
      offers_released: 2,
      offers_accepted: 1,
      offers_rejected: 1,
      unread_notifications: 4
    })
  })

  it('restores persisted view and sidebar state from localStorage', async () => {
    localStorage.setItem(STORAGE_KEYS.activeView, 'interviews')
    localStorage.setItem(STORAGE_KEYS.sidebarCollapsed, '1')

    authApi.getMe.mockResolvedValue({
      data: {
        data: {
          user_id: 41,
          username: 'acme_admin',
          email: 'admin@acme.example'
        }
      }
    })
    companyApi.getDashboard.mockResolvedValue(buildDashboardResponse())

    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    expect(wrapper.vm.activeView).toBe('interviews')
    expect(wrapper.vm.sidebarCollapsed).toBe(true)
    expect(wrapper.find('.interviews-updated').exists()).toBe(true)
  })

  it('falls back to overview when persisted view is invalid', async () => {
    localStorage.setItem(STORAGE_KEYS.activeView, 'invalid-view')

    authApi.getMe.mockResolvedValue({
      data: {
        data: {
          user_id: 41,
          username: 'acme_admin',
          email: 'admin@acme.example'
        }
      }
    })
    companyApi.getDashboard.mockResolvedValue(buildDashboardResponse())

    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    expect(wrapper.vm.activeView).toBe('overview')
    expect(wrapper.find('.overview-stub').exists()).toBe(true)
  })

  it('shows load error and retries bootstrap successfully', async () => {
    authApi.getMe
      .mockRejectedValueOnce({
        response: {
          data: {
            error: 'Session expired. Login again.'
          }
        }
      })
      .mockResolvedValueOnce({
        data: {
          data: {
            user_id: 41,
            username: 'acme_admin',
            email: 'admin@acme.example'
          }
        }
      })

    companyApi.getDashboard.mockResolvedValue(buildDashboardResponse())

    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    expect(wrapper.text()).toContain('Session expired. Login again.')

    await wrapper.get('.cq-state-card.is-error .cq-btn').trigger('click')
    await flushPromises()
    await flushPromises()

    expect(authApi.getMe).toHaveBeenCalledTimes(2)
    expect(companyApi.getDashboard).toHaveBeenCalledTimes(2)
    expect(wrapper.find('.overview-stub').exists()).toBe(true)
  })

  it('persists UI state and refreshes dashboard when module emits update event', async () => {
    authApi.getMe.mockResolvedValue({
      data: {
        data: {
          user_id: 41,
          username: 'acme_admin',
          email: 'admin@acme.example'
        }
      }
    })
    companyApi.getDashboard.mockResolvedValue(buildDashboardResponse())

    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-drives').trigger('click')
    expect(wrapper.vm.activeView).toBe('drives')
    expect(localStorage.getItem(STORAGE_KEYS.activeView)).toBe('drives')

    await wrapper.get('.toggle-sidebar').trigger('click')
    expect(wrapper.vm.sidebarCollapsed).toBe(true)
    expect(localStorage.getItem(STORAGE_KEYS.sidebarCollapsed)).toBe('1')

    await wrapper.get('.drive-updated').trigger('click')
    await flushPromises()
    await flushPromises()

    expect(authApi.getMe).toHaveBeenCalledTimes(2)
    expect(companyApi.getDashboard).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('Drives synced')
    expect(wrapper.vm.syncTone).toBe('success')
  })

  it('shows sync note error without breaking page when silent refresh fails', async () => {
    authApi.getMe.mockResolvedValueOnce({
      data: {
        data: {
          user_id: 41,
          username: 'acme_admin',
          email: 'admin@acme.example'
        }
      }
    })
    companyApi.getDashboard.mockResolvedValueOnce(buildDashboardResponse())

    authApi.getMe.mockRejectedValueOnce({
      response: {
        data: {
          error: 'Background refresh failed'
        }
      }
    })
    companyApi.getDashboard.mockResolvedValueOnce(buildDashboardResponse())

    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-drives').trigger('click')
    await wrapper.get('.drive-updated').trigger('click')
    await flushPromises()
    await flushPromises()

    expect(wrapper.vm.loadError).toBe('')
    expect(wrapper.vm.syncTone).toBe('error')
    expect(wrapper.text()).toContain('Background refresh failed')
  })

  it('switches to notifications view and refreshes on notifications-updated event', async () => {
    authApi.getMe.mockResolvedValue({
      data: {
        data: {
          user_id: 41,
          username: 'acme_admin',
          email: 'admin@acme.example'
        }
      }
    })
    companyApi.getDashboard.mockResolvedValue(buildDashboardResponse())

    const wrapper = makeWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-notifications').trigger('click')
    expect(wrapper.vm.activeView).toBe('notifications')
    expect(wrapper.find('.notifications-updated').exists()).toBe(true)

    await wrapper.get('.notifications-updated').trigger('click')
    await flushPromises()
    await flushPromises()

    expect(authApi.getMe).toHaveBeenCalledTimes(2)
    expect(companyApi.getDashboard).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('Notifications synced')
  })

  it('clears auth storage and routes to login on logout event', async () => {
    const push = vi.fn()

    localStorage.setItem('token', 'sample-token')
    localStorage.setItem('role', 'company')
    localStorage.setItem('user_id', '41')

    authApi.getMe.mockResolvedValue({
      data: {
        data: {
          user_id: 41,
          username: 'acme_admin',
          email: 'admin@acme.example'
        }
      }
    })
    companyApi.getDashboard.mockResolvedValue(buildDashboardResponse())

    const wrapper = makeWrapper(push)
    await flushPromises()
    await flushPromises()

    await wrapper.get('.topbar-logout').trigger('click')

    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('role')).toBeNull()
    expect(localStorage.getItem('user_id')).toBeNull()
    expect(push).toHaveBeenCalledWith('/login')
  })
})
