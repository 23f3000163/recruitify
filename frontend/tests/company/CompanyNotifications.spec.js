import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import CompanyNotifications from '../../src/components/company/CompanyNotifications.vue'
import { companyApi } from '../../src/api/api'

vi.mock('../../src/api/api', () => ({
  companyApi: {
    getNotifications: vi.fn(),
    markNotificationRead: vi.fn(),
    markAllNotificationsRead: vi.fn()
  }
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

const pageOnePayload = {
  data: {
    data: {
      items: [
        {
          notification_id: 801,
          title: 'Offer response received',
          message: 'Ria accepted the Backend Engineer offer.',
          is_read: false,
          created_at: '2030-06-03T10:30:00+00:00'
        }
      ],
      unread_count: 1,
      page: 1,
      pages: 1,
      total: 1,
      limit: 10
    }
  }
}

describe('CompanyNotifications step 5 module', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads notifications with default read filter', async () => {
    companyApi.getNotifications.mockResolvedValue(pageOnePayload)

    const wrapper = mount(CompanyNotifications)
    await flushPromises()

    expect(companyApi.getNotifications).toHaveBeenCalledWith({
      page: 1,
      limit: 10,
      is_read: 'all'
    })
    expect(wrapper.text()).toContain('Offer response received')
    expect(wrapper.text()).toContain('Unread')
  })

  it('applies read-status filter from controls', async () => {
    companyApi.getNotifications
      .mockResolvedValueOnce(pageOnePayload)
      .mockResolvedValueOnce({
        data: {
          data: {
            items: [],
            unread_count: 0,
            page: 1,
            pages: 0,
            total: 0,
            limit: 10
          }
        }
      })

    const wrapper = mount(CompanyNotifications)
    await flushPromises()

    await wrapper.get('select').setValue('true')
    await wrapper.get('.cq-module-tools .cq-ghost-btn').trigger('click')
    await flushPromises()

    expect(companyApi.getNotifications).toHaveBeenLastCalledWith({
      page: 1,
      limit: 10,
      is_read: 'true'
    })
  })

  it('marks single notification as read and emits notifications-updated', async () => {
    companyApi.getNotifications
      .mockResolvedValueOnce(pageOnePayload)
      .mockResolvedValueOnce({
        data: {
          data: {
            items: [
              {
                notification_id: 801,
                title: 'Offer response received',
                message: 'Ria accepted the Backend Engineer offer.',
                is_read: true,
                created_at: '2030-06-03T10:30:00+00:00'
              }
            ],
            unread_count: 0,
            page: 1,
            pages: 1,
            total: 1,
            limit: 10
          }
        }
      })
    companyApi.markNotificationRead.mockResolvedValue({ data: { success: true } })

    const wrapper = mount(CompanyNotifications)
    await flushPromises()

    await wrapper.get('.cq-row-actions .cq-ghost-btn').trigger('click')
    await flushPromises()

    expect(companyApi.markNotificationRead).toHaveBeenCalledWith(801)
    expect(wrapper.emitted('notifications-updated')).toBeTruthy()
    expect(wrapper.text()).toContain('Read')
  })

  it('marks all notifications as read and emits notifications-updated', async () => {
    companyApi.getNotifications
      .mockResolvedValueOnce(pageOnePayload)
      .mockResolvedValueOnce({
        data: {
          data: {
            items: [
              {
                notification_id: 801,
                title: 'Offer response received',
                message: 'Ria accepted the Backend Engineer offer.',
                is_read: true,
                created_at: '2030-06-03T10:30:00+00:00'
              }
            ],
            unread_count: 0,
            page: 1,
            pages: 1,
            total: 1,
            limit: 10
          }
        }
      })
    companyApi.markAllNotificationsRead.mockResolvedValue({ data: { success: true } })

    const wrapper = mount(CompanyNotifications)
    await flushPromises()

    await wrapper.get('.cq-module-head .cq-btn').trigger('click')
    await flushPromises()

    expect(companyApi.markAllNotificationsRead).toHaveBeenCalledTimes(1)
    expect(wrapper.emitted('notifications-updated')).toBeTruthy()
  })
})
