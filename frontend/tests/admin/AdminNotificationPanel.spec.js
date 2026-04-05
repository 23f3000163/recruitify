import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import AdminNotificationPanel from '../../src/components/admin/AdminNotificationPanel.vue'

const baseNotifications = [
  {
    id: 101,
    title: 'New Company Registration',
    sub: 'Flow Dynamics is awaiting review.',
    time: '5 min ago',
    type: 'warning',
    read: false
  },
  {
    id: 102,
    title: 'Drive Approved',
    sub: 'Backend Engineer drive was approved.',
    time: '1 hr ago',
    type: 'success',
    read: true
  }
]

describe('AdminNotificationPanel', () => {
  it('emits mark-read when unread item is clicked', async () => {
    const wrapper = mount(AdminNotificationPanel, {
      props: {
        notifications: baseNotifications,
        unreadCount: 1,
        isMarking: {}
      }
    })

    await wrapper.get('.rq-admin-notif-item.unread').trigger('click')

    expect(wrapper.emitted('mark-read')).toBeTruthy()
    expect(wrapper.emitted('mark-read')[0]).toEqual([101])
  })

  it('does not emit mark-read for read or pending items', async () => {
    const wrapper = mount(AdminNotificationPanel, {
      props: {
        notifications: baseNotifications,
        unreadCount: 1,
        isMarking: { 101: true }
      }
    })

    await wrapper.get('.rq-admin-notif-item.unread').trigger('click')
    await wrapper.findAll('.rq-admin-notif-item')[1].trigger('click')

    expect(wrapper.emitted('mark-read')).toBeFalsy()
  })

  it('emits mark-all-read and close actions', async () => {
    const wrapper = mount(AdminNotificationPanel, {
      props: {
        notifications: baseNotifications,
        unreadCount: 1,
        isMarkingAll: false
      }
    })

    await wrapper.get('.rq-ghost-xs').trigger('click')
    await wrapper.get('.rq-modal-close').trigger('click')

    expect(wrapper.emitted('mark-all-read')).toBeTruthy()
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
