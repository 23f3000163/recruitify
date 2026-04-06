<template>
  <section class="rq-view">
    <div class="rq-analytics-grid">
      <div class="rq-card">
        <div class="rq-card-hd">
          <span class="rq-card-title">Application Pipeline</span>
          <span class="rq-pill rq-pill-blue">Offer Rate {{ offerRatePct }}%</span>
        </div>
        <div class="rq-card-body">
          <div class="rq-chart-wrap rq-chart-md">
            <canvas ref="pipelineChart" aria-label="Application funnel chart" role="img"></canvas>
          </div>
        </div>
      </div>

      <div class="rq-card rq-col-2">
        <div class="rq-card-hd">
          <span class="rq-card-title">Drive Performance</span>
          <button class="rq-ghost" @click="$emit('export-analytics')">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M6 1v7M3 6l3 3 3-3M1 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            Export
          </button>
        </div>
        <div class="rq-card-body">
          <div class="rq-chart-wrap rq-chart-lg">
            <canvas ref="driveChart" aria-label="Drive performance chart" role="img"></canvas>
          </div>
        </div>
      </div>

      <div class="rq-card rq-col-full">
        <div class="rq-card-hd">
          <span class="rq-card-title">Branch-wise Applicants</span>
        </div>
        <div class="rq-card-body">
          <div class="rq-chart-wrap rq-chart-md">
            <canvas ref="branchChart" aria-label="Branch applicant chart" role="img"></canvas>
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
  name: 'AnalyticsView',
  props: {
    analytics: {
      type: Object,
      required: true
    },
    offerRatePct: {
      type: Number,
      required: true
    },
    donutCirc: {
      type: Number,
      required: true
    },
    offerRateOffset: {
      type: Number,
      required: true
    },
    myDrives: {
      type: Array,
      required: true
    },
    branchApplicants: {
      type: Array,
      required: true
    },
    maxBranchCount: {
      type: Number,
      required: true
    }
  },
  emits: ['export-analytics'],
  data() {
    return {
      pipelineChartInstance: null,
      driveChartInstance: null,
      branchChartInstance: null,
      renderQueued: false
    }
  },
  computed: {
    topDriveRows() {
      return [...this.myDrives]
        .sort((left, right) => Number(right.applicants || 0) - Number(left.applicants || 0))
        .slice(0, 8)
    },
    chartRenderKey() {
      const analytics = this.analytics || {}
      const pipelineKey = [
        Number(analytics.applied || 0),
        Number(analytics.shortlisted || 0),
        Number(analytics.interview || 0),
        Number(analytics.offered || 0),
        Number(analytics.rejected || 0)
      ].join('|')

      const driveKey = this.topDriveRows
        .map((drive) => `${drive.id || drive.title || 'drive'}:${Number(drive.applicants || 0)}:${Number(this.stageCount(drive, 3) || 0)}`)
        .join(';')

      const branchKey = this.branchApplicants
        .map((branch) => `${branch.name || 'OTHER'}:${Number(branch.count || 0)}`)
        .join(';')

      return `${pipelineKey}__${driveKey}__${branchKey}`
    },
    hasPipelineData() {
      const analytics = this.analytics || {}
      return [
        analytics.applied,
        analytics.shortlisted,
        analytics.interview,
        analytics.offered,
        analytics.rejected
      ].some((value) => Number(value || 0) > 0)
    },
    hasDriveData() {
      return this.topDriveRows.some((drive) => (
        Number(drive.applicants || 0) > 0 ||
        Number(this.stageCount(drive, 3) || 0) > 0
      ))
    },
    hasBranchData() {
      return this.branchApplicants.some((branch) => Number(branch.count || 0) > 0)
    }
  },
  watch: {
    chartRenderKey() {
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
    pct(value, maxValue) {
      return maxValue > 0 ? Math.round((value / maxValue) * 100) : 0
    },
    convClass(offered, total) {
      const ratio = total > 0 ? offered / total : 0
      return ratio >= 0.15 ? 'conv-hi' : ratio >= 0.08 ? 'conv-md' : 'conv-lo'
    },
    stageCount(drive, index) {
      if (!drive || !Array.isArray(drive.stages) || !drive.stages[index]) {
        return 0
      }

      return Number(drive.stages[index].count || 0)
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
      if (this.pipelineChartInstance) {
        this.pipelineChartInstance.destroy()
        this.pipelineChartInstance = null
      }
      if (this.driveChartInstance) {
        this.driveChartInstance.destroy()
        this.driveChartInstance = null
      }
      if (this.branchChartInstance) {
        this.branchChartInstance.destroy()
        this.branchChartInstance = null
      }
    },
    renderCharts() {
      this.destroyCharts()
      if (this.hasPipelineData) {
        this.renderPipelineChart()
      }
      if (this.hasDriveData) {
        this.renderDriveChart()
      }
      if (this.hasBranchData) {
        this.renderBranchChart()
      }
    },
    renderPipelineChart() {
      const canvas = this.$refs.pipelineChart
      if (!canvas) return

      this.pipelineChartInstance = new Chart(canvas, {
        type: 'bar',
        data: {
          labels: ['Applied', 'Shortlisted', 'Interview', 'Offered', 'Rejected'],
          datasets: [
            {
              label: 'Candidates',
              data: [
                Number(this.analytics.applied || 0),
                Number(this.analytics.shortlisted || 0),
                Number(this.analytics.interview || 0),
                Number(this.analytics.offered || 0),
                Number(this.analytics.rejected || 0)
              ],
              backgroundColor: ['#D97706', '#7C3AED', '#2563EB', '#059669', '#DC2626'],
              borderRadius: 8,
              borderSkipped: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              beginAtZero: true
            },
            x: {
              grid: {
                display: false
              }
            }
          }
        }
      })
    },
    renderDriveChart() {
      const canvas = this.$refs.driveChart
      if (!canvas) return

      const labels = this.topDriveRows.map((drive) => drive.title || 'Drive')
      const applied = this.topDriveRows.map((drive) => Number(drive.applicants || 0))
      const offered = this.topDriveRows.map((drive) => Number(this.stageCount(drive, 3) || 0))

      this.driveChartInstance = new Chart(canvas, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'Applied',
              data: applied,
              backgroundColor: 'rgba(37, 99, 235, 0.35)',
              borderColor: '#2563EB',
              borderWidth: 1,
              borderRadius: 6,
              borderSkipped: false
            },
            {
              label: 'Offered',
              data: offered,
              backgroundColor: 'rgba(5, 150, 105, 0.85)',
              borderColor: '#059669',
              borderWidth: 1,
              borderRadius: 6,
              borderSkipped: false
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
            y: {
              beginAtZero: true
            },
            x: {
              grid: {
                display: false
              }
            }
          }
        }
      })
    },
    renderBranchChart() {
      const canvas = this.$refs.branchChart
      if (!canvas) return

      const labels = this.branchApplicants.map((branch) => branch.name || 'OTHER')
      const counts = this.branchApplicants.map((branch) => Number(branch.count || 0))
      const colors = this.branchApplicants.map((branch) => branch.color || '#2563EB')

      this.branchChartInstance = new Chart(canvas, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'Applicants',
              data: counts,
              backgroundColor: colors,
              borderRadius: 8,
              borderSkipped: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              beginAtZero: true
            },
            x: {
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
