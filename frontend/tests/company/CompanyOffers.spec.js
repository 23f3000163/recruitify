import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import CompanyOffers from '../../src/components/company/CompanyOffers.vue'
import { companyApi } from '../../src/api/api'

vi.mock('../../src/api/api', () => ({
  companyApi: {
    getOffers: vi.fn(),
    getApplications: vi.fn(),
    createOffer: vi.fn()
  }
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('CompanyOffers phase 5 flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads and renders offers from API', async () => {
    companyApi.getOffers.mockResolvedValue({
      data: {
        data: {
          items: [
            {
              offer_id: 701,
              student_name: 'Nikhil Roy',
              student_email: 'nikhil@example.com',
              drive_title: 'SRE',
              position: 'Site Reliability Engineer',
              salary: 1450000,
              joining_date: '2030-09-01',
              status: 'offered',
              created_at: '2030-06-01T10:00:00+00:00'
            }
          ],
          drive_options: [{ id: 44, title: 'SRE' }],
          total: 1,
          page: 1,
          pages: 1,
          limit: 10
        }
      }
    })

    const wrapper = mount(CompanyOffers)
    await flushPromises()

    expect(companyApi.getOffers).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Nikhil Roy')
    expect(wrapper.text()).toContain('Site Reliability Engineer')
  })

  it('shows inline error when offers API fails', async () => {
    companyApi.getOffers.mockRejectedValue({
      response: {
        data: {
          error: 'Offers list could not be loaded'
        }
      }
    })

    const wrapper = mount(CompanyOffers)
    await flushPromises()

    expect(companyApi.getOffers).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Offers list could not be loaded')
  })

  it('creates an offer and emits offers-updated', async () => {
    companyApi.getOffers
      .mockResolvedValueOnce({
        data: {
          data: {
            items: [],
            drive_options: [],
            total: 0,
            page: 1,
            pages: 0,
            limit: 10
          }
        }
      })
      .mockResolvedValueOnce({
        data: {
          data: {
            items: [
              {
                offer_id: 702,
                student_name: 'Priya N',
                student_email: 'priya@example.com',
                drive_title: 'Backend Engineer',
                position: 'Backend Engineer',
                salary: 1300000,
                joining_date: null,
                status: 'offered',
                created_at: '2030-06-02T10:00:00+00:00'
              }
            ],
            drive_options: [{ id: 90, title: 'Backend Engineer' }],
            total: 1,
            page: 1,
            pages: 1,
            limit: 10
          }
        }
      })

    companyApi.getApplications.mockResolvedValue({
      data: {
        data: {
          items: [
            {
              application_id: 501,
              student_name: 'Priya N',
              drive_title: 'Backend Engineer',
              status: 'selected',
              has_offer: false
            }
          ]
        }
      }
    })

    companyApi.createOffer.mockResolvedValue({
      data: {
        success: true,
        data: {
          offer_id: 702
        }
      }
    })

    const wrapper = mount(CompanyOffers)
    await flushPromises()

    await wrapper.get('.cq-module-head .cq-btn').trigger('click')
    await flushPromises()

    await wrapper.get('.cq-drive-form select').setValue('501')
    await wrapper.get('.cq-drive-form input[type="number"]').setValue('1300000')
    await wrapper.get('.cq-drive-form input[placeholder="Defaults to drive title if empty"]').setValue('Backend Engineer')

    await wrapper.get('.cq-drive-form').trigger('submit')
    await flushPromises()

    expect(companyApi.createOffer).toHaveBeenCalledWith({
      application_id: 501,
      salary: 1300000,
      position: 'Backend Engineer',
      joining_date: null
    })
    expect(wrapper.emitted('offers-updated')).toBeTruthy()
  })

  it('validates salary before creating an offer', async () => {
    companyApi.getOffers.mockResolvedValue({
      data: {
        data: {
          items: [],
          drive_options: [],
          total: 0,
          page: 1,
          pages: 0,
          limit: 10
        }
      }
    })

    companyApi.getApplications.mockResolvedValue({
      data: {
        data: {
          items: [
            {
              application_id: 502,
              student_name: 'Nitin Raj',
              drive_title: 'Backend Engineer',
              status: 'selected',
              has_offer: false
            }
          ]
        }
      }
    })

    const wrapper = mount(CompanyOffers)
    await flushPromises()

    await wrapper.get('.cq-module-head .cq-btn').trigger('click')
    await flushPromises()

    await wrapper.get('.cq-drive-form select').setValue('502')
    await wrapper.get('.cq-drive-form input[type="number"]').setValue('0')

    await wrapper.get('.cq-drive-form').trigger('submit')
    await flushPromises()

    expect(companyApi.createOffer).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Salary must be greater than zero.')
  })
})
