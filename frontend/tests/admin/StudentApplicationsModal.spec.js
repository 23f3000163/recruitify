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

describe('StudentApplicationsModal read-only details', () => {
  it('shows drive, company, applied on, and status columns', () => {
    const wrapper = mount(StudentApplicationsModal, {
      props: {
        selectedStudent
      }
    })

    const headers = wrapper.findAll('thead th').map((header) => header.text())

    expect(headers).toEqual(['Drive', 'Company', 'Applied On', 'Status'])
  })

  it('does not render action controls for status changes', () => {
    const wrapper = mount(StudentApplicationsModal, {
      props: {
        selectedStudent
      }
    })

    expect(wrapper.find('select.rq-app-status-select').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Action')
  })

  it('shows empty state when selected student has no applications', () => {
    const wrapper = mount(StudentApplicationsModal, {
      props: {
        selectedStudent: {
          ...selectedStudent,
          appList: []
        }
      }
    })

    expect(wrapper.text()).toContain('No applications found')
    expect(wrapper.text()).toContain('This student has not applied to any drives yet.')
  })
})
