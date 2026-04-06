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
import AnalyticsView from '../../src/components/company/AnalyticsView.vue'

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

const makeProps = (overrides = {}) => ({
  analytics: {
    applied: 0,
    shortlisted: 0,
    interview: 0,
    offered: 0,
    rejected: 0
  },
  offerRatePct: 0,
  donutCirc: 0,
  offerRateOffset: 0,
  myDrives: [],
  branchApplicants: [],
  maxBranchCount: 0,
  ...overrides
})

describe('AnalyticsView chart rendering guards', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('skips chart rendering when all analytics inputs are empty', async () => {
    mount(AnalyticsView, {
      props: makeProps()
    })

    await flushPromises()

    expect(Chart).not.toHaveBeenCalled()
  })

  it('renders charts when pipeline, drive, and branch datasets are available', async () => {
    mount(AnalyticsView, {
      props: makeProps({
        analytics: {
          applied: 22,
          shortlisted: 13,
          interview: 8,
          offered: 4,
          rejected: 6
        },
        myDrives: [
          {
            id: 11,
            title: 'Backend Engineer',
            applicants: 18,
            stages: [
              { count: 18 },
              { count: 10 },
              { count: 6 },
              { count: 3 }
            ]
          }
        ],
        branchApplicants: [
          { name: 'CSE', count: 14, color: '#2563EB' },
          { name: 'ECE', count: 8, color: '#059669' }
        ],
        maxBranchCount: 14
      })
    })

    await flushPromises()

    expect(Chart).toHaveBeenCalledTimes(3)
  })
})
