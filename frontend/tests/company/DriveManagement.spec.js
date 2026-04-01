import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import DriveManagement from '../../src/components/company/DriveManagement.vue'
import { companyApi } from '../../src/api/api'

vi.mock('../../src/api/api', () => ({
  companyApi: {
    getDrives: vi.fn(),
    createDrive: vi.fn(),
    closeDrive: vi.fn()
  }
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('DriveManagement phase 3 flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads and renders drives from API', async () => {
    companyApi.getDrives.mockResolvedValue({
      data: {
        data: {
          items: [
            {
              id: 11,
              title: 'Platform Engineer',
              status: 'approved',
              application_deadline: '2026-05-20T10:00:00+00:00',
              job_location: 'Remote',
              salary_lpa: 18,
              applications_count: 4,
              required_skills: 'Python, SQL',
              experience_required: '1-3 years',
              benefits: 'Insurance, hybrid work'
            }
          ],
          total: 1,
          page: 1,
          pages: 1,
          limit: 8
        }
      }
    })

    const wrapper = mount(DriveManagement)
    await flushPromises()

    expect(companyApi.getDrives).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Platform Engineer')
    expect(wrapper.text()).toContain('Remote')
  })

  it('creates a drive and emits drive-updated', async () => {
    companyApi.getDrives.mockResolvedValue({
      data: {
        data: {
          items: [],
          total: 0,
          page: 1,
          pages: 0,
          limit: 8
        }
      }
    })
    companyApi.createDrive.mockResolvedValue({
      data: {
        data: {
          id: 21,
          title: 'Backend Engineer'
        }
      }
    })

    const wrapper = mount(DriveManagement)
    await flushPromises()

    await wrapper.get('.cq-drives-head .cq-btn').trigger('click')

    const textInputs = wrapper.findAll('.cq-drive-form input[type="text"]')
    await textInputs[0].setValue('Backend Engineer')
    await wrapper.get('.cq-drive-form textarea').setValue('Build APIs and services')
    await textInputs[2].setValue('0-2 years')
    await textInputs[3].setValue('Insurance and flexible hours')
    await wrapper.get('.cq-drive-form input[type="number"]').setValue('7.2')
    await wrapper.get('.cq-drive-form input[type="date"]').setValue('2030-12-20')

    await wrapper.get('.cq-drive-form').trigger('submit')
    await flushPromises()

    expect(companyApi.createDrive).toHaveBeenCalledTimes(1)
    expect(companyApi.createDrive).toHaveBeenCalledWith(
      expect.objectContaining({
        experience_required: '0-2 years',
        benefits: 'Insurance and flexible hours'
      })
    )
    expect(wrapper.emitted('drive-updated')).toBeTruthy()
  })

  it('closes a drive and emits drive-updated', async () => {
    const initialResponse = {
      data: {
        data: {
          items: [
            {
              id: 31,
              title: 'QA Engineer',
              status: 'approved',
              application_deadline: '2026-08-10T10:00:00+00:00',
              job_location: 'Noida',
              salary_lpa: 12,
              applications_count: 2,
              required_skills: 'Selenium',
              experience_required: '1+ years',
              benefits: 'Health insurance'
            }
          ],
          total: 1,
          page: 1,
          pages: 1,
          limit: 8
        }
      }
    }
    const closedResponse = {
      data: {
        data: {
          items: [
            {
              id: 31,
              title: 'QA Engineer',
              status: 'closed',
              application_deadline: '2026-08-10T10:00:00+00:00',
              job_location: 'Noida',
              salary_lpa: 12,
              applications_count: 2,
              required_skills: 'Selenium',
              experience_required: '1+ years',
              benefits: 'Health insurance'
            }
          ],
          total: 1,
          page: 1,
          pages: 1,
          limit: 8
        }
      }
    }

    companyApi.getDrives
      .mockResolvedValueOnce(initialResponse)
      .mockResolvedValueOnce(closedResponse)
    companyApi.closeDrive.mockResolvedValue({ data: { success: true } })

    const wrapper = mount(DriveManagement)
    await flushPromises()

    await wrapper.get('.cq-row-actions .cq-ghost-btn').trigger('click')
    await flushPromises()

    expect(companyApi.closeDrive).toHaveBeenCalledWith(31)
    expect(wrapper.emitted('drive-updated')).toBeTruthy()
  })
})