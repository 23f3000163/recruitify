import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import StudentDashboard from '../../src/views/student/StudentDashboard.vue'
import { studentApi } from '../../src/api/api'

vi.mock('../../src/api/api', () => ({
  studentApi: {
    getDashboard: vi.fn(),
    getApplications: vi.fn(),
    getNotifications: vi.fn(),
    markNotificationRead: vi.fn()
  }
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('StudentDashboard step 3 flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads summary, applications, and notifications', async () => {
    studentApi.getDashboard.mockResolvedValue({
      data: {
        data: {
          summary: {
            applications_total: 3,
            shortlisted: 1,
            interviewed: 1,
            offers_released: 1
          },
          unread_notifications: 1
        }
      }
    })

    studentApi.getApplications.mockResolvedValue({
      data: {
        data: {
          items: [
            {
              application_id: 1001,
              status: 'shortlisted',
              status_label: 'Shortlisted',
              notes: 'Strong project profile.',
              updated_at: '2026-06-12T10:00:00+00:00',
              drive: {
                title: 'Platform Engineer',
                location: 'Bengaluru'
              },
              company: {
                name: 'Step3 Labs'
              },
              timeline: [
                {
                  id: '1001-shortlisted',
                  label: 'Shortlisted',
                  message: 'Application moved to shortlist.',
                  tone: 'success'
                }
              ]
            }
          ],
          total: 1,
          page: 1,
          pages: 1,
          limit: 10
        }
      }
    })

    studentApi.getNotifications.mockResolvedValue({
      data: {
        data: {
          items: [
            {
              notification_id: 701,
              title: 'Application Update',
              message: 'Your application is now shortlisted.',
              is_read: false,
              created_at: '2026-06-12T10:00:00+00:00'
            }
          ],
          unread_count: 1,
          total: 1,
          page: 1,
          pages: 1,
          limit: 8
        }
      }
    })

    const wrapper = mount(StudentDashboard)
    await flushPromises()

    expect(studentApi.getDashboard).toHaveBeenCalled()
    expect(studentApi.getApplications).toHaveBeenCalled()
    expect(studentApi.getNotifications).toHaveBeenCalled()

    expect(wrapper.text()).toContain('Platform Engineer')
    expect(wrapper.text()).toContain('Step3 Labs')
    expect(wrapper.text()).toContain('Shortlisted')
    expect(wrapper.text()).toContain('Application Update')
    expect(wrapper.text()).toContain('1 unread')
  })

  it('marks unread notification as read', async () => {
    studentApi.getDashboard.mockResolvedValue({
      data: {
        data: {
          summary: {
            applications_total: 1,
            shortlisted: 1,
            interviewed: 0,
            offers_released: 0
          },
          unread_notifications: 1
        }
      }
    })

    studentApi.getApplications.mockResolvedValue({
      data: {
        data: {
          items: [],
          total: 0,
          page: 1,
          pages: 0,
          limit: 10
        }
      }
    })

    studentApi.getNotifications.mockResolvedValue({
      data: {
        data: {
          items: [
            {
              notification_id: 701,
              title: 'Interview Scheduled',
              message: 'Interview is scheduled for tomorrow.',
              is_read: false,
              created_at: '2026-06-12T10:00:00+00:00'
            }
          ],
          unread_count: 1,
          total: 1,
          page: 1,
          pages: 1,
          limit: 8
        }
      }
    })

    studentApi.markNotificationRead.mockResolvedValue({
      data: {
        data: {
          notification: {
            notification_id: 701,
            is_read: true,
            read_at: '2026-06-12T11:00:00+00:00'
          },
          unread_count: 0
        }
      }
    })

    const wrapper = mount(StudentDashboard)
    await flushPromises()

    await wrapper.get('.std-notify-btn').trigger('click')
    await flushPromises()

    expect(studentApi.markNotificationRead).toHaveBeenCalledWith(701)
    expect(wrapper.vm.unreadCount).toBe(0)
    expect(wrapper.text()).toContain('0 unread')
  })
})
