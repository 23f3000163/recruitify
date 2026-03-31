import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import DashboardOverview from '../../src/components/admin/DashboardOverview.vue'

const baseProps = {
  kpiCards: [],
  pendingApprovals: [
    {
      id: 'company-11',
      entityType: 'company',
      entityId: 11,
      name: 'Acme Labs',
      sub: 'New registration',
      type: 'Company',
      date: '2026-03-31',
      initials: 'AL',
      color: '#2563EB'
    }
  ],
  branchStats: [],
  auditLog: [],
  recentApplications: [],
  pct: (a, b) => {
    if (!b) return 0
    return Math.round((a / b) * 100)
  }
}

describe('DashboardOverview action flow', () => {
  it('emits approve-item when approve is clicked', async () => {
    const wrapper = mount(DashboardOverview, {
      props: {
        ...baseProps,
        pendingCompanyActions: {},
        pendingDriveActions: {}
      }
    })

    await wrapper.get('.rq-btn-ok').trigger('click')

    expect(wrapper.emitted('approve-item')).toBeTruthy()
    expect(wrapper.emitted('approve-item')[0][0]).toMatchObject({
      id: 'company-11',
      entityType: 'company',
      entityId: 11
    })
  })

  it('keeps approve disabled while company action is pending', () => {
    const wrapper = mount(DashboardOverview, {
      props: {
        ...baseProps,
        pendingCompanyActions: { 11: true },
        pendingDriveActions: {}
      }
    })

    expect(wrapper.get('.rq-btn-ok').attributes('disabled')).toBeDefined()
    expect(wrapper.get('.rq-btn-no').attributes('disabled')).toBeDefined()
  })

  it('emits retry when retry button is clicked', async () => {
    const wrapper = mount(DashboardOverview, {
      props: {
        ...baseProps,
        errorMessage: 'Network issue',
        pendingCompanyActions: {},
        pendingDriveActions: {}
      }
    })

    await wrapper.get('.rq-state-error .rq-ghost-xs').trigger('click')

    expect(wrapper.emitted('retry')).toBeTruthy()
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })
})
