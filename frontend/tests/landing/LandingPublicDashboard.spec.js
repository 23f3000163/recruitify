import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Landing from '../../src/views/Landing.vue'
import { adminApi } from '../../src/api/api'
import { Chart } from 'chart.js'

vi.mock('../../src/api/api', () => ({
  adminApi: {
    getPublicLandingDashboard: vi.fn()
  }
}))

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

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

const mountLanding = () =>
  mount(Landing, {
    global: {
      mocks: {
        $router: {
          push: vi.fn()
        }
      },
      stubs: {
        Navbar: { template: '<div class="navbar-stub"></div>' },
        HeroSection: { template: '<div class="hero-stub"></div>' },
        Footer: { template: '<div class="footer-stub"></div>' }
      }
    }
  })

describe('Landing public dashboard integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    let timestamp = 0
    globalThis.requestAnimationFrame = vi.fn((callback) => {
      timestamp += 500
      callback(timestamp)
      return timestamp
    })

    globalThis.IntersectionObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
  })

  it('loads public dashboard data and syncs counters/trends', async () => {
    adminApi.getPublicLandingDashboard.mockResolvedValue({
      data: {
        data: {
          highlights: {
            placements_confirmed: 520,
            approved_companies: 88,
            approved_drives: 210,
            latest_month_placements: 42
          },
          placement_trends: [
            {
              month_key: '2026-03',
              month_label: 'Mar 2026',
              applications: 58,
              offers: 12,
              placements: 10
            }
          ],
          application_funnel: {
            applied: 300,
            shortlisted: 170,
            interview: 120,
            offered: 45,
            placed: 33,
            rejected: 140,
            total: 300
          },
          job_demand_by_skills: [
            { skill: 'Python', demand_count: 6 },
            { skill: 'SQL', demand_count: 4 }
          ],
          meta: {
            months: 6
          }
        }
      }
    })

    const wrapper = mountLanding()
    await flushPromises()
    await flushPromises()

    expect(adminApi.getPublicLandingDashboard).toHaveBeenCalledWith({ months: 6 })
    expect(wrapper.vm.publicDashboard.highlights.approved_companies).toBe(88)
    expect(wrapper.vm.counters[0].target).toBe(520)
    expect(wrapper.vm.counters[3].target).toBe(42)
    expect(wrapper.vm.topPublicSkills[0].skill).toBe('Python')
    expect(Chart).toHaveBeenCalled()
  })

  it('shows a public dashboard error when API fetch fails', async () => {
    adminApi.getPublicLandingDashboard.mockRejectedValue({
      response: {
        data: {
          error: 'Public analytics unavailable'
        }
      }
    })

    const wrapper = mountLanding()
    await flushPromises()
    await flushPromises()

    expect(wrapper.vm.publicDashboardError).toBe('Public analytics unavailable')
    expect(wrapper.text()).toContain('Public analytics unavailable')
  })
})
