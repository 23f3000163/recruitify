<template>
  <section class="rq-view">
    <div class="rq-analytics-grid">
      <div class="rq-card rq-col-full rq-analytics-snapshot">
        <div class="rq-card-hd rq-card-hd-center">
          <span class="rq-card-title rq-card-title-strong">Analytics Snapshot</span>
        </div>
        <div class="rq-card-body">
          <div v-if="errorMessage" class="rq-state rq-state-error">
            <span>{{ errorMessage }}</span>
            <button class="rq-ghost" type="button" @click="$emit('retry')">Retry</button>
          </div>
          <div v-else-if="!hasSummaryData" class="rq-empty rq-empty-compact">
            <span class="rq-row-sub">No summary metrics available yet.</span>
          </div>
          <div v-else class="rq-mini-metrics">
            <div class="rq-mini-metric">
              <span class="rq-mini-metric-label">Students</span>
              <span class="rq-mini-metric-value">{{ formatMetric(summary.total_students) }}</span>
            </div>
            <div class="rq-mini-metric">
              <span class="rq-mini-metric-label">Companies</span>
              <span class="rq-mini-metric-value">{{ formatMetric(summary.total_companies) }}</span>
            </div>
            <div class="rq-mini-metric">
              <span class="rq-mini-metric-label">Jobs</span>
              <span class="rq-mini-metric-value">{{ formatMetric(summary.total_jobs) }}</span>
            </div>
            <div class="rq-mini-metric">
              <span class="rq-mini-metric-label">Applications</span>
              <span class="rq-mini-metric-value">{{ formatMetric(summary.total_applications) }}</span>
            </div>
            <div class="rq-mini-metric">
              <span class="rq-mini-metric-label">Offers Released</span>
              <span class="rq-mini-metric-value">{{ formatMetric(summary.offers_released) }}</span>
            </div>
            <div class="rq-mini-metric">
              <span class="rq-mini-metric-label">Offers Accepted</span>
              <span class="rq-mini-metric-value">{{ formatMetric(summary.offers_accepted) }}</span>
            </div>
            <div class="rq-mini-metric">
              <span class="rq-mini-metric-label">Placements</span>
              <span class="rq-mini-metric-value">{{ formatMetric(summary.total_placements) }}</span>
            </div>
            <div class="rq-mini-metric">
              <span class="rq-mini-metric-label">Legacy Placement Rate</span>
              <span class="rq-mini-metric-value">{{ placementRatePct }}%</span>
            </div>
          </div>
        </div>
      </div>

      <div class="rq-col-full rq-analytics-section-head">
        <span class="rq-card-title rq-card-title-strong">Detailed Analytics</span>
      </div>

      <div class="rq-card">
        <div class="rq-card-hd">
          <span class="rq-card-title">Application Funnel</span>
          <span class="rq-pill rq-pill-amber">Total {{ funnelTotal }}</span>
        </div>
        <div class="rq-card-body">
          <div v-if="isLoading" class="rq-empty rq-empty-compact">
            <span class="rq-row-sub">Loading funnel metrics...</span>
          </div>
          <div v-else-if="errorMessage" class="rq-state rq-state-error">
            <span>{{ errorMessage }}</span>
            <button class="rq-ghost" type="button" @click="$emit('retry')">Retry</button>
          </div>
          <div v-else-if="!hasFunnelData" class="rq-empty rq-empty-compact">
            <span class="rq-row-sub">No funnel data available yet.</span>
          </div>
          <div v-else class="rq-chart-wrap rq-chart-md">
            <canvas ref="funnelChart" aria-label="Application funnel chart" role="img"></canvas>
          </div>
        </div>
      </div>

      <div class="rq-card">
        <div class="rq-card-hd">
          <span class="rq-card-title">Top Skill Demand</span>
          <button class="rq-ghost" :disabled="isExportBusy" @click="$emit('export', 'analytics')">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M6 1v7M3 6l3 3 3-3M1 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            {{ exportLabel }}
          </button>
        </div>
        <div class="rq-card-body">
          <div v-if="isLoading" class="rq-empty rq-empty-compact">
            <span class="rq-row-sub">Loading skill demand...</span>
          </div>
          <div v-else-if="errorMessage" class="rq-state rq-state-error">
            <span>{{ errorMessage }}</span>
            <button class="rq-ghost" type="button" @click="$emit('retry')">Retry</button>
          </div>
          <div v-else-if="!hasSkillData" class="rq-empty rq-empty-compact">
            <span class="rq-row-sub">No skill demand data available yet.</span>
          </div>
          <div v-else class="rq-chart-wrap rq-chart-md">
            <canvas ref="skillsChart" aria-label="Skill demand bar chart" role="img"></canvas>
          </div>
        </div>
      </div>

      <div class="rq-card">
        <div class="rq-card-hd">
          <span class="rq-card-title">Placement Growth Trend</span>
          <span class="rq-pill rq-pill-blue">{{ monthLabel }}</span>
        </div>
        <div class="rq-card-body">
          <div v-if="isLoading" class="rq-empty rq-empty-compact">
            <span class="rq-row-sub">Loading placement growth trend...</span>
          </div>
          <div v-else-if="errorMessage" class="rq-state rq-state-error">
            <span>{{ errorMessage }}</span>
            <button class="rq-ghost" type="button" @click="$emit('retry')">Retry</button>
          </div>
          <div v-else-if="!hasTrendData" class="rq-empty rq-empty-compact">
            <span class="rq-row-sub">No placement growth trend data available yet.</span>
          </div>
          <div v-else class="rq-chart-wrap rq-chart-md">
            <canvas ref="trendChart" aria-label="Placement growth trend line chart" role="img"></canvas>
          </div>
        </div>
      </div>

      <div class="rq-card">
        <div class="rq-card-hd">
          <span class="rq-card-title">Conversion Rate Analysis</span>
          <span class="rq-pill rq-pill-blue">Pipeline %</span>
        </div>
        <div class="rq-card-body">
          <div v-if="isLoading" class="rq-empty rq-empty-compact">
            <span class="rq-row-sub">Loading conversion metrics...</span>
          </div>
          <div v-else-if="errorMessage" class="rq-state rq-state-error">
            <span>{{ errorMessage }}</span>
            <button class="rq-ghost" type="button" @click="$emit('retry')">Retry</button>
          </div>
          <div v-else-if="!hasConversionData" class="rq-empty rq-empty-compact">
            <span class="rq-row-sub">No conversion rate data available yet.</span>
          </div>
          <div v-else class="rq-chart-wrap rq-chart-md">
            <canvas ref="conversionChart" aria-label="Conversion rate analysis chart" role="img"></canvas>
          </div>
        </div>
      </div>

    </div>
  </section>
</template>

<script>
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'AnalyticsPanel',
  props: {
    analyticsOverview: {
      type: Object,
      default: () => ({})
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    errorMessage: {
      type: String,
      default: ''
    },
    topCompanies: { type: Array, required: true },
    branchStats: { type: Array, required: true },
    placedCount: { type: Number, required: true },
    inProgressCount: { type: Number, required: true },
    notPlacedCount: { type: Number, required: true },
    placementRatePct: { type: Number, required: true },
    donutCirc: { type: Number, required: true },
    donutPlacedOffset: { type: Number, required: true },
    isExportBusy: { type: Boolean, default: false },
    exportLabel: { type: String, default: 'Export' },
    pct: { type: Function, required: true }
  },
  emits: ['export', 'retry'],
  data() {
    return {
      trendChartInstance: null,
      funnelChartInstance: null,
      skillsChartInstance: null,
      conversionChartInstance: null,
      renderQueued: false
    }
  },
  computed: {
    summary() {
      return this.analyticsOverview?.summary || {}
    },
    monthLabel() {
      const months = Number(this.analyticsOverview?.meta?.months || 0)
      if (!months) return 'Last 6 Months'
      return `Last ${months} Months`
    },
    trendRows() {
      const rows = Array.isArray(this.analyticsOverview?.placement_trends)
        ? this.analyticsOverview.placement_trends
        : []
      if (rows.length) {
        return rows
      }

      return this.branchStats.map((branch, index) => ({
        month_label: `M${index + 1}`,
        applications: Number(branch.total || 0),
        placements: Number(branch.placed || 0),
        offers: Number(branch.placed || 0)
      }))
    },
    funnelCounts() {
      const fallbackTotal = Number(this.placedCount + this.inProgressCount + this.notPlacedCount)
      const raw = this.analyticsOverview?.application_funnel || {}
      return {
        applied: Number(raw.applied || 0),
        shortlisted: Number(raw.shortlisted || 0),
        interview: Number(raw.interview || 0),
        offered: Number(raw.offered || 0),
        placed: Number(raw.placed || 0),
        rejected: Number(raw.rejected || 0),
        total: Number(raw.total || fallbackTotal)
      }
    },
    funnelTotal() {
      return Number(this.funnelCounts.total || 0)
    },
    skillRows() {
      const rows = Array.isArray(this.analyticsOverview?.job_demand_by_skills)
        ? this.analyticsOverview.job_demand_by_skills
        : []
      return rows.slice(0, 10)
    },
    hasTrendData() {
      return this.trendRows.some((row) => (
        Number(row.applications || 0) > 0 ||
        Number(row.offers || 0) > 0 ||
        Number(row.placements || 0) > 0
      ))
    },
    hasFunnelData() {
      const dataset = this.funnelCounts
      return [
        dataset.applied,
        dataset.shortlisted,
        dataset.interview,
        dataset.offered,
        dataset.placed,
        dataset.rejected,
        dataset.total
      ].some((value) => Number(value || 0) > 0)
    },
    hasSkillData() {
      return this.skillRows.some((row) => Number(row.demand_count || 0) > 0)
    },
    conversionRows() {
      const funnel = this.funnelCounts
      return [
        {
          label: 'Applied -> Shortlisted',
          value: this.pct(Number(funnel.shortlisted || 0), Number(funnel.applied || 0)),
          baseline: Number(funnel.applied || 0)
        },
        {
          label: 'Shortlisted -> Interview',
          value: this.pct(Number(funnel.interview || 0), Number(funnel.shortlisted || 0)),
          baseline: Number(funnel.shortlisted || 0)
        },
        {
          label: 'Interview -> Offered',
          value: this.pct(Number(funnel.offered || 0), Number(funnel.interview || 0)),
          baseline: Number(funnel.interview || 0)
        },
        {
          label: 'Offered -> Placed',
          value: this.pct(Number(funnel.placed || 0), Number(funnel.offered || 0)),
          baseline: Number(funnel.offered || 0)
        }
      ]
    },
    hasConversionData() {
      return this.conversionRows.some((row) => Number(row.baseline || 0) > 0)
    },
    hasSummaryData() {
      const keys = [
        'total_students',
        'total_companies',
        'total_jobs',
        'total_applications',
        'offers_released',
        'offers_accepted',
        'total_placements'
      ]

      return keys.some((key) => Number(this.summary?.[key] || 0) > 0)
    }
  },
  watch: {
    analyticsOverview: {
      deep: true,
      handler() {
        this.queueRenderCharts()
      }
    },
    isLoading() {
      this.queueRenderCharts()
    },
    errorMessage() {
      this.queueRenderCharts()
    }
  },
  mounted() {
    this.queueRenderCharts()
  },
  beforeUnmount() {
    this.destroyCharts()
  },
  methods: {
    formatMetric(value) {
      const parsed = Number(value || 0)
      return Number.isFinite(parsed) ? parsed.toLocaleString() : '0'
    },
    queueRenderCharts() {
      if (this.renderQueued) {
        return
      }

      this.renderQueued = true
      this.$nextTick(() => {
        this.renderQueued = false
        this.renderCharts()
      })
    },
    destroyCharts() {
      if (this.trendChartInstance) {
        this.trendChartInstance.destroy()
        this.trendChartInstance = null
      }
      if (this.funnelChartInstance) {
        this.funnelChartInstance.destroy()
        this.funnelChartInstance = null
      }
      if (this.skillsChartInstance) {
        this.skillsChartInstance.destroy()
        this.skillsChartInstance = null
      }
      if (this.conversionChartInstance) {
        this.conversionChartInstance.destroy()
        this.conversionChartInstance = null
      }
    },
    renderCharts() {
      this.destroyCharts()

      if (this.isLoading || this.errorMessage) {
        return
      }

      if (this.hasTrendData) {
        this.renderTrendChart()
      }
      if (this.hasFunnelData) {
        this.renderFunnelChart()
      }
      if (this.hasSkillData) {
        this.renderSkillsChart()
      }
      if (this.hasConversionData) {
        this.renderConversionChart()
      }
    },
    renderTrendChart() {
      const canvas = this.$refs.trendChart
      if (!canvas) return

      const labels = this.trendRows.map((row) => row.month_label || row.month_key || '-')
      const applications = this.trendRows.map((row) => Number(row.applications || 0))
      const offers = this.trendRows.map((row) => Number(row.offers || 0))
      const placements = this.trendRows.map((row) => Number(row.placements || 0))

      this.trendChartInstance = new Chart(canvas, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'Applications',
              data: applications,
              borderColor: '#2563EB',
              backgroundColor: 'rgba(37, 99, 235, 0.12)',
              tension: 0.28,
              fill: true
            },
            {
              label: 'Offers',
              data: offers,
              borderColor: '#D97706',
              backgroundColor: 'rgba(217, 119, 6, 0.1)',
              tension: 0.28,
              fill: false
            },
            {
              label: 'Placements',
              data: placements,
              borderColor: '#059669',
              backgroundColor: 'rgba(5, 150, 105, 0.1)',
              tension: 0.28,
              fill: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom'
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              }
            },
            y: {
              beginAtZero: true
            }
          }
        }
      })
    },
    renderFunnelChart() {
      const canvas = this.$refs.funnelChart
      if (!canvas) return

      const dataset = this.funnelCounts
      this.funnelChartInstance = new Chart(canvas, {
        type: 'bar',
        data: {
          labels: ['Applied', 'Shortlisted', 'Interview', 'Offered', 'Placed', 'Rejected'],
          datasets: [
            {
              label: 'Applications',
              data: [
                dataset.applied,
                dataset.shortlisted,
                dataset.interview,
                dataset.offered,
                dataset.placed,
                dataset.rejected
              ],
              backgroundColor: ['#D97706', '#7C3AED', '#2563EB', '#0891B2', '#059669', '#DC2626'],
              borderRadius: 6,
              borderSkipped: false
            }
          ]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            x: {
              beginAtZero: true
            },
            y: {
              grid: {
                display: false
              }
            }
          }
        }
      })
    },
    renderSkillsChart() {
      const canvas = this.$refs.skillsChart
      if (!canvas) return

      const labels = this.skillRows.map((row) => row.skill || '-')
      const values = this.skillRows.map((row) => Number(row.demand_count || 0))

      // Color palette for skills - cycle through colors
      const skillColors = ['#D97706', '#7C3AED', '#2563EB', '#0891B2']
      const backgroundColor = values.map((_, index) => skillColors[index % skillColors.length])

      this.skillsChartInstance = new Chart(canvas, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'Demand count',
              data: values,
              backgroundColor,
              borderRadius: 6,
              borderSkipped: false
            }
          ]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            x: {
              beginAtZero: true
            },
            y: {
              grid: {
                display: false
              }
            }
          }
        }
      })
    },
    renderConversionChart() {
      const canvas = this.$refs.conversionChart
      if (!canvas) return

      const labels = this.conversionRows.map((row) => row.label)
      const values = this.conversionRows.map((row) => Number(row.value || 0))

      this.conversionChartInstance = new Chart(canvas, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'Conversion %',
              data: values,
              backgroundColor: ['#D97706', '#7C3AED', '#2563EB', '#0891B2'],
              borderRadius: 6,
              borderSkipped: false
            }
          ]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            x: {
              beginAtZero: true,
              max: 100
            },
            y: {
              grid: {
                display: false
              }
            }
          }
        }
      })
    }
  }
}
</script>
