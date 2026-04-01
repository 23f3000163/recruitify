import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import CompanyApplications from '../../src/components/company/CompanyApplications.vue'
import { companyApi } from '../../src/api/api'

vi.mock('../../src/api/api', () => ({
  companyApi: {
    getApplications: vi.fn(),
    updateApplicationStatus: vi.fn()
  }
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('CompanyApplications phase 5 flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads and renders applications from API', async () => {
    companyApi.getApplications.mockResolvedValue({
      data: {
        data: {
          items: [
            {
              application_id: 91,
              student_name: 'Asha Sharma',
              student_email: 'asha@example.com',
              drive_title: 'Platform Engineer',
              status: 'applied',
              application_date: '2026-06-10T10:00:00+00:00',
              updated_at: '2026-06-11T10:00:00+00:00'
            }
          ],
          drive_options: [{ id: 12, title: 'Platform Engineer' }],
          total: 1,
          page: 1,
          pages: 1,
          limit: 10
        }
      }
    })

    const wrapper = mount(CompanyApplications)
    await flushPromises()

    expect(companyApi.getApplications).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Asha Sharma')
    expect(wrapper.text()).toContain('Platform Engineer')
  })

  it('shows inline error when applications API fails', async () => {
    companyApi.getApplications.mockRejectedValue({
      response: {
        data: {
          error: 'Applications service unavailable'
        }
      }
    })

    const wrapper = mount(CompanyApplications)
    await flushPromises()

    expect(companyApi.getApplications).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Applications service unavailable')
  })

  it('updates status and emits applications-updated', async () => {
    const initialResponse = {
      data: {
        data: {
          items: [
            {
              application_id: 91,
              student_name: 'Asha Sharma',
              student_email: 'asha@example.com',
              drive_title: 'Platform Engineer',
              status: 'applied',
              application_date: '2026-06-10T10:00:00+00:00',
              updated_at: '2026-06-11T10:00:00+00:00'
            }
          ],
          drive_options: [{ id: 12, title: 'Platform Engineer' }],
          total: 1,
          page: 1,
          pages: 1,
          limit: 10
        }
      }
    }

    const updatedResponse = {
      data: {
        data: {
          items: [
            {
              application_id: 91,
              student_name: 'Asha Sharma',
              student_email: 'asha@example.com',
              drive_title: 'Platform Engineer',
              status: 'shortlisted',
              application_date: '2026-06-10T10:00:00+00:00',
              updated_at: '2026-06-12T10:00:00+00:00'
            }
          ],
          drive_options: [{ id: 12, title: 'Platform Engineer' }],
          total: 1,
          page: 1,
          pages: 1,
          limit: 10
        }
      }
    }

    companyApi.getApplications.mockResolvedValueOnce(initialResponse).mockResolvedValueOnce(updatedResponse)
    companyApi.updateApplicationStatus.mockResolvedValue({
      data: {
        success: true,
        data: {
          application_id: 91,
          status: 'shortlisted'
        }
      }
    })

    const wrapper = mount(CompanyApplications)
    await flushPromises()

    await wrapper.get('.cq-inline-controls select').setValue('selected')
    await wrapper.get('.cq-inline-controls .cq-ghost-btn').trigger('click')
    await flushPromises()

    expect(companyApi.updateApplicationStatus).toHaveBeenCalledWith(
      91,
      expect.objectContaining({ status: 'selected' })
    )
    expect(wrapper.emitted('applications-updated')).toBeTruthy()
  })

  it('shows inline error when status update fails', async () => {
    companyApi.getApplications.mockResolvedValueOnce({
      data: {
        data: {
          items: [
            {
              application_id: 93,
              student_name: 'Kriti Sharma',
              student_email: 'kriti@example.com',
              drive_title: 'Security Analyst',
              status: 'applied',
              application_date: '2026-06-12T10:00:00+00:00',
              updated_at: '2026-06-13T10:00:00+00:00'
            }
          ],
          drive_options: [{ id: 18, title: 'Security Analyst' }],
          total: 1,
          page: 1,
          pages: 1,
          limit: 10
        }
      }
    })

    companyApi.updateApplicationStatus.mockRejectedValue({
      response: {
        data: {
          error: 'Status update rejected by server'
        }
      }
    })

    const wrapper = mount(CompanyApplications)
    await flushPromises()

    await wrapper.get('.cq-inline-controls select').setValue('selected')
    await wrapper.get('.cq-inline-controls .cq-ghost-btn').trigger('click')
    await flushPromises()

    expect(companyApi.updateApplicationStatus).toHaveBeenCalledWith(
      93,
      expect.objectContaining({ status: 'selected' })
    )
    expect(wrapper.text()).toContain('Status update rejected by server')
    expect(wrapper.emitted('applications-updated')).toBeFalsy()
  })

  it('collects shortlist feedback through modal before updating', async () => {
    const initialResponse = {
      data: {
        data: {
          items: [
            {
              application_id: 96,
              student_name: 'Riya Kapoor',
              student_email: 'riya@example.com',
              drive_title: 'Frontend Engineer',
              status: 'applied',
              application_date: '2026-06-10T10:00:00+00:00',
              updated_at: '2026-06-11T10:00:00+00:00'
            }
          ],
          drive_options: [{ id: 12, title: 'Frontend Engineer' }],
          total: 1,
          page: 1,
          pages: 1,
          limit: 10
        }
      }
    }

    const updatedResponse = {
      data: {
        data: {
          items: [
            {
              application_id: 96,
              student_name: 'Riya Kapoor',
              student_email: 'riya@example.com',
              drive_title: 'Frontend Engineer',
              status: 'shortlisted',
              notes: 'Strong portfolio and project depth.',
              rejection_reason: null,
              application_date: '2026-06-10T10:00:00+00:00',
              updated_at: '2026-06-12T10:00:00+00:00'
            }
          ],
          drive_options: [{ id: 12, title: 'Frontend Engineer' }],
          total: 1,
          page: 1,
          pages: 1,
          limit: 10
        }
      }
    }

    companyApi.getApplications.mockResolvedValueOnce(initialResponse).mockResolvedValueOnce(updatedResponse)
    companyApi.updateApplicationStatus.mockResolvedValue({
      data: {
        success: true,
        data: {
          application_id: 96,
          status: 'shortlisted',
          notes: 'Strong portfolio and project depth.'
        }
      }
    })

    const wrapper = mount(CompanyApplications)
    await flushPromises()

    await wrapper.get('.cq-inline-controls select').setValue('shortlisted')
    await wrapper.get('.cq-inline-controls .cq-ghost-btn').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Add Shortlist Feedback')

    await wrapper.get('#company-application-feedback-modal textarea').setValue('Strong portfolio and project depth.')
    await wrapper.get('#company-application-feedback-modal form').trigger('submit')
    await flushPromises()

    expect(companyApi.updateApplicationStatus).toHaveBeenCalledWith(
      96,
      expect.objectContaining({
        status: 'shortlisted',
        notes: 'Strong portfolio and project depth.',
        rejection_reason: null
      })
    )
    expect(wrapper.emitted('applications-updated')).toBeTruthy()
  })

  it('requires rejection reason before submitting rejected status', async () => {
    const initialResponse = {
      data: {
        data: {
          items: [
            {
              application_id: 97,
              student_name: 'Ankit Jain',
              student_email: 'ankit@example.com',
              drive_title: 'QA Engineer',
              status: 'applied',
              application_date: '2026-06-10T10:00:00+00:00',
              updated_at: '2026-06-11T10:00:00+00:00'
            }
          ],
          drive_options: [{ id: 42, title: 'QA Engineer' }],
          total: 1,
          page: 1,
          pages: 1,
          limit: 10
        }
      }
    }

    const updatedResponse = {
      data: {
        data: {
          items: [
            {
              application_id: 97,
              student_name: 'Ankit Jain',
              student_email: 'ankit@example.com',
              drive_title: 'QA Engineer',
              status: 'rejected',
              notes: 'Coding fundamentals need improvement.',
              rejection_reason: 'Did not meet coding assessment threshold.',
              application_date: '2026-06-10T10:00:00+00:00',
              updated_at: '2026-06-12T10:00:00+00:00'
            }
          ],
          drive_options: [{ id: 42, title: 'QA Engineer' }],
          total: 1,
          page: 1,
          pages: 1,
          limit: 10
        }
      }
    }

    companyApi.getApplications.mockResolvedValueOnce(initialResponse).mockResolvedValueOnce(updatedResponse)
    companyApi.updateApplicationStatus.mockResolvedValue({
      data: {
        success: true,
        data: {
          application_id: 97,
          status: 'rejected',
          rejection_reason: 'Did not meet coding assessment threshold.'
        }
      }
    })

    const wrapper = mount(CompanyApplications)
    await flushPromises()

    await wrapper.get('.cq-inline-controls select').setValue('rejected')
    await wrapper.get('.cq-inline-controls .cq-ghost-btn').trigger('click')
    await flushPromises()

    await wrapper.get('#company-application-feedback-modal form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Rejection reason is required for rejected status.')
    expect(companyApi.updateApplicationStatus).not.toHaveBeenCalled()

    const rejectionReasonField = wrapper.get('#company-application-feedback-modal textarea[required]')
    const allTextAreas = wrapper.findAll('#company-application-feedback-modal textarea')
    await rejectionReasonField.setValue('Did not meet coding assessment threshold.')
    await allTextAreas[1].setValue('Coding fundamentals need improvement.')
    await wrapper.get('#company-application-feedback-modal form').trigger('submit')
    await flushPromises()

    expect(companyApi.updateApplicationStatus).toHaveBeenCalledWith(
      97,
      expect.objectContaining({
        status: 'rejected',
        rejection_reason: 'Did not meet coding assessment threshold.',
        notes: 'Coding fundamentals need improvement.'
      })
    )
  })
})
