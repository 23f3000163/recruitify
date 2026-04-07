import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import StudentApplicationsModal from '../../src/components/admin/StudentApplicationsModal.vue'

const selectedStudent = {
  name: 'Jane Doe',
  roll: 'CS21B1001',
  initials: 'JD',
  color: '#059669',
  appList: [
    {
      id: 7,
      drive: 'SDE Intern',
      company: 'Beta Systems',
      date: 'Mar 31, 2026',
      status: 'pending',
      rawStatus: 'applied'
    }
  ]
}

describe('StudentApplicationsModal action flow', () => {
  it('emits update-app-status with shortlisted value', async () => {
    const wrapper = mount(StudentApplicationsModal, {
      props: {
        selectedStudent,
        pendingApplicationActions: {}
      }
    })

    const select = wrapper.get('select.rq-app-status-select')
    await select.setValue('shortlisted')

    expect(wrapper.emitted('update-app-status')).toBeTruthy()
    expect(wrapper.emitted('update-app-status')[0][0]).toMatchObject({ id: 7 })
    expect(wrapper.emitted('update-app-status')[0][1]).toBe('shortlisted')
  })

  it('does not show interview and selected shortcut options', () => {
    const wrapper = mount(StudentApplicationsModal, {
      props: {
        selectedStudent,
        pendingApplicationActions: {}
      }
    })

    const optionValues = wrapper
      .findAll('select.rq-app-status-select option')
      .map((option) => option.element.value)

    expect(optionValues).not.toContain('interviewed')
    expect(optionValues).not.toContain('selected')
  })

  it('disables status select for in-flight updates', () => {
    const wrapper = mount(StudentApplicationsModal, {
      props: {
        selectedStudent,
        pendingApplicationActions: { 7: true }
      }
    })

    expect(wrapper.get('select.rq-app-status-select').attributes('disabled')).toBeDefined()
  })
})
