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

    await wrapper.get('.cq-inline-controls select').setValue('shortlisted')
    await wrapper.get('.cq-inline-controls .cq-ghost-btn').trigger('click')
    await flushPromises()

    expect(companyApi.updateApplicationStatus).toHaveBeenCalledWith(
      91,
      expect.objectContaining({ status: 'shortlisted' })
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

    await wrapper.get('.cq-inline-controls select').setValue('shortlisted')
    await wrapper.get('.cq-inline-controls .cq-ghost-btn').trigger('click')
    await flushPromises()

    expect(companyApi.updateApplicationStatus).toHaveBeenCalledWith(
      93,
      expect.objectContaining({ status: 'shortlisted' })
    )
    expect(wrapper.text()).toContain('Status update rejected by server')
    expect(wrapper.emitted('applications-updated')).toBeFalsy()
  })
})
