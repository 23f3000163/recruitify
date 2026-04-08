import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('chart.js', () => {
  const Chart = vi.fn().mockImplementation(() => ({
    destroy: vi.fn()
  }))
  Chart.register = vi.fn()

  return {
    Chart,
    registerables: []
  }
})

import { Chart } from 'chart.js'
import AnalyticsPanel from '../../src/components/admin/AnalyticsPanel.vue'

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

const makeProps = (overrides = {}) => ({
  analyticsOverview: {},
  isLoading: false,
  errorMessage: '',
  topCompanies: [],
  branchStats: [],
  placedCount: 0,
  inProgressCount: 0,
  notPlacedCount: 0,
  placementRatePct: 0,
  donutCirc: 0,
  donutPlacedOffset: 0,
  pct: (a, b) => (b ? Math.round((a / b) * 100) : 0),
  ...overrides
})

describe('AnalyticsPanel chart rendering guards', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows empty states and skips chart rendering when datasets are empty', async () => {
    const wrapper = mount(AnalyticsPanel, {
      props: makeProps()
    })

    await flushPromises()

    expect(wrapper.text()).toContain('No placement growth trend data available yet.')
    expect(wrapper.text()).toContain('No funnel data available yet.')
    expect(wrapper.text()).toContain('No skill demand data available yet.')
    expect(wrapper.text()).toContain('No conversion rate data available yet.')
    expect(Chart).not.toHaveBeenCalled()
  })

  it('renders charts when analytics data is available', async () => {
    const wrapper = mount(AnalyticsPanel, {
      props: makeProps({
        analyticsOverview: {
          summary: {
            total_students: 100,
            total_companies: 15,
            total_jobs: 40,
            total_applications: 300,
            offers_released: 42,
            offers_accepted: 33,
            total_placements: 31
          },
          placement_trends: [
            {
              month_label: 'Mar 2026',
              applications: 52,
              offers: 8,
              placements: 7
            }
          ],
          application_funnel: {
            total: 300,
            applied: 300,
            shortlisted: 180,
            interview: 120,
            offered: 42,
            placed: 31,
            rejected: 138
          },
          job_demand_by_skills: [
            { skill: 'Python', demand_count: 12 },
            { skill: 'SQL', demand_count: 9 }
          ],
          meta: {
            months: 6
          }
        }
      })
    })

    await flushPromises()

    expect(Chart).toHaveBeenCalledTimes(4)

    const conversionCall = Chart.mock.calls.find(([, config]) => (
      config?.data?.datasets?.[0]?.label === 'Conversion %'
    ))
    expect(conversionCall?.[1]?.options?.indexAxis).toBe('y')
  })

  it('derives conversion rate metrics from funnel counts', async () => {
    const wrapper = mount(AnalyticsPanel, {
      props: makeProps({
        analyticsOverview: {
          application_funnel: {
            applied: 300,
            shortlisted: 180,
            interview: 120,
            offered: 42,
            placed: 31
          }
        }
      })
    })

    await flushPromises()

    expect(wrapper.vm.conversionRows.map((row) => row.value)).toEqual([60, 67, 35, 74])
    expect(wrapper.vm.hasConversionData).toBe(true)
  })
})
