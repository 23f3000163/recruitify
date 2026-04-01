import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import CompanyInterviews from '../../src/components/company/CompanyInterviews.vue'
import { companyApi } from '../../src/api/api'

vi.mock('../../src/api/api', () => ({
  companyApi: {
    getInterviews: vi.fn(),
    getApplications: vi.fn(),
    scheduleInterview: vi.fn(),
    updateInterviewResult: vi.fn()
  }
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('CompanyInterviews phase 5 flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads and renders interviews from API', async () => {
    companyApi.getInterviews.mockResolvedValue({
      data: {
        data: {
          items: [
            {
              interview_id: 301,
              student_name: 'Rahul Verma',
              student_email: 'rahul@example.com',
              drive_title: 'Data Engineer',
              interview_date: '2030-06-10T10:00:00+00:00',
              interview_mode: 'online',
              interviewer_name: 'Panel A',
              result: 'pending'
            }
          ],
          drive_options: [{ id: 55, title: 'Data Engineer' }],
          total: 1,
          page: 1,
          pages: 1,
          limit: 10
        }
      }
    })

    const wrapper = mount(CompanyInterviews)
    await flushPromises()

    expect(companyApi.getInterviews).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Rahul Verma')
    expect(wrapper.text()).toContain('Panel A')
  })

  it('shows inline error when interviews API fails', async () => {
    companyApi.getInterviews.mockRejectedValue({
      response: {
        data: {
          error: 'Interview feed is temporarily unavailable'
        }
      }
    })

    const wrapper = mount(CompanyInterviews)
    await flushPromises()

    expect(companyApi.getInterviews).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Interview feed is temporarily unavailable')
  })

  it('schedules an interview and emits interviews-updated', async () => {
    companyApi.getInterviews
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
                interview_id: 302,
                student_name: 'Mira Das',
                student_email: 'mira@example.com',
                drive_title: 'Frontend Engineer',
                interview_date: '2030-06-01T10:30:00+00:00',
                interview_mode: 'online',
                interviewer_name: 'Panel One',
                result: 'pending'
              }
            ],
            drive_options: [{ id: 77, title: 'Frontend Engineer' }],
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
              application_id: 88,
              student_name: 'Mira Das',
              drive_title: 'Frontend Engineer',
              status: 'shortlisted'
            }
          ]
        }
      }
    })

    companyApi.scheduleInterview.mockResolvedValue({
      data: {
        success: true,
        data: {
          interview_id: 302
        }
      }
    })

    const wrapper = mount(CompanyInterviews)
    await flushPromises()

    await wrapper.get('.cq-module-head .cq-btn').trigger('click')
    await flushPromises()

    const formSelects = wrapper.findAll('.cq-drive-form select')
    await formSelects[0].setValue('88')
    await wrapper.get('input[type="datetime-local"]').setValue('2030-06-01T10:30')
    await wrapper.get('input[placeholder="Panel member"]').setValue('Panel One')

    await wrapper.get('.cq-drive-form').trigger('submit')
    await flushPromises()

    expect(companyApi.scheduleInterview).toHaveBeenCalledTimes(1)
    expect(companyApi.scheduleInterview).toHaveBeenCalledWith(
      expect.objectContaining({
        application_id: 88,
        interview_mode: 'online',
        interviewer_name: 'Panel One'
      })
    )
    expect(wrapper.emitted('interviews-updated')).toBeTruthy()
  })

  it('shows scheduling error when candidate options fail to load', async () => {
    companyApi.getInterviews.mockResolvedValue({
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

    companyApi.getApplications.mockRejectedValue({
      response: {
        data: {
          error: 'Candidate shortlist API failed'
        }
      }
    })

    const wrapper = mount(CompanyInterviews)
    await flushPromises()

    await wrapper.get('.cq-module-head .cq-btn').trigger('click')
    await flushPromises()

    expect(companyApi.getApplications).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Candidate shortlist API failed')
  })

  it('updates interview result and emits interviews-updated', async () => {
    const initialResponse = {
      data: {
        data: {
          items: [
            {
              interview_id: 401,
              student_name: 'Riya Sen',
              student_email: 'riya@example.com',
              drive_title: 'ML Engineer',
              interview_date: '2030-07-10T10:00:00+00:00',
              interview_mode: 'online',
              interviewer_name: 'Panel B',
              result: 'pending'
            }
          ],
          drive_options: [{ id: 12, title: 'ML Engineer' }],
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
              interview_id: 401,
              student_name: 'Riya Sen',
              student_email: 'riya@example.com',
              drive_title: 'ML Engineer',
              interview_date: '2030-07-10T10:00:00+00:00',
              interview_mode: 'online',
              interviewer_name: 'Panel B',
              result: 'pass'
            }
          ],
          drive_options: [{ id: 12, title: 'ML Engineer' }],
          total: 1,
          page: 1,
          pages: 1,
          limit: 10
        }
      }
    }

    companyApi.getInterviews.mockResolvedValueOnce(initialResponse).mockResolvedValueOnce(updatedResponse)
    companyApi.updateInterviewResult.mockResolvedValue({
      data: {
        success: true,
        data: {
          interview_id: 401,
          result: 'pass'
        }
      }
    })

    const wrapper = mount(CompanyInterviews)
    await flushPromises()

    await wrapper.get('.cq-inline-controls select').setValue('pass')
    await wrapper.get('.cq-inline-controls .cq-ghost-btn').trigger('click')
    await flushPromises()

    expect(companyApi.updateInterviewResult).toHaveBeenCalledWith(401, { result: 'pass' })
    expect(wrapper.emitted('interviews-updated')).toBeTruthy()
  })
})
