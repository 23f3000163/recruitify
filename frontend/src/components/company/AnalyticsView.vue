<template>
  <section class="rq-view rq-analytics-view">
    <article class="rq-card rq-analytics-toolbar-card">
      <header class="rq-card-hd rq-analytics-toolbar-head">
        <div>
          <span class="rq-card-title">Analytics Command Center</span>
          <p class="rq-analytics-subtitle">{{ filterSummary }}</p>
        </div>
        <span class="rq-pill rq-pill-green">{{ effectiveOfferRate }}% offer conversion</span>
      </header>
      <div class="rq-card-body rq-analytics-toolbar-body">
        <label class="rq-analytics-control" for="analytics-drive-status">
          <span>Drive Status</span>
          <select id="analytics-drive-status" v-model="selectedDriveStatus" class="rq-select">
            <option v-for="option in driveStatusOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>

        <label class="rq-analytics-control" for="analytics-branch-filter">
          <span>Branch</span>
          <select id="analytics-branch-filter" v-model="selectedBranch" class="rq-select">
            <option v-for="option in branchOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>

        <label class="rq-analytics-control" for="analytics-date-window">
          <span>Date Window</span>
          <select id="analytics-date-window" v-model="selectedDateWindow" class="rq-select">
            <option v-for="option in dateWindowOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
      </div>
    </article>

    <article class="rq-card rq-analytics-snapshot-card">
      <header class="rq-card-hd rq-analytics-snapshot-head">
        <span class="rq-card-title">Analytics Snapshot</span>
        <span class="rq-pill rq-pill-blue">Scoped summary</span>
      </header>

      <div class="rq-card-body">
        <div class="rq-analytics-snapshot-grid" role="list" aria-label="Company analytics snapshot">
          <article
            v-for="item in analyticsSnapshotCards"
            :key="item.id"
            class="rq-analytics-snapshot-item"
            role="listitem"
          >
            <span class="rq-analytics-snapshot-label">{{ item.label }}</span>
            <strong class="rq-analytics-snapshot-value">{{ item.value }}</strong>
            <span class="rq-analytics-snapshot-meta">{{ item.meta }}</span>
          </article>
        </div>
      </div>
    </article>

    <article v-if="!hasAnyData" class="rq-card">
      <div class="rq-card-body">
        <div class="rq-empty rq-analytics-empty">
          <div class="rq-empty-ico">No analytics yet</div>
          <b>No records match your current filters.</b>
          <span>Try broadening the date window or removing branch and status filters.</span>
        </div>
      </div>
    </article>

    <div v-else class="rq-analytics-grid">
      <div class="rq-card">
        <div class="rq-card-hd">
          <span class="rq-card-title">Application Pipeline</span>
          <span class="rq-pill rq-pill-blue">{{ effectiveOfferRate }}% offer rate</span>
        </div>
        <div class="rq-card-body">
          <div v-if="hasPipelineData" class="rq-chart-block">
            <div class="rq-chart-wrap rq-chart-md">
              <canvas ref="pipelineChart" aria-label="Application funnel chart" role="img"></canvas>
            </div>

            <div class="rq-stage-strip" role="list" aria-label="Pipeline stage summary">
              <div v-for="stage in stageOverview" :key="stage.key" class="rq-stage-chip" role="listitem">
                <span class="rq-stage-name">{{ stage.label }}</span>
                <strong class="rq-stage-value">{{ stage.count }}</strong>
                <span class="rq-stage-meta">{{ stage.meta }}</span>
              </div>
            </div>
          </div>
          <p v-else class="rq-empty-text">No pipeline records match the selected filters.</p>
        </div>
      </div>

      <div class="rq-card rq-col-2">
        <div class="rq-card-hd">
          <span class="rq-card-title">Drive Performance</span>
          <button class="rq-ghost" :disabled="isExportBusy" @click="$emit('export-analytics')">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M6 1v7M3 6l3 3 3-3M1 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            {{ exportLabel }}
          </button>
        </div>
        <div class="rq-card-body">
          <div v-if="hasDriveData" class="rq-chart-block">
            <div class="rq-chart-wrap rq-chart-lg">
              <canvas ref="driveChart" aria-label="Drive performance chart" role="img"></canvas>
            </div>

            <div class="rq-drive-insights" role="list" aria-label="Top drive conversion rows">
              <div v-for="drive in topDriveRows.slice(0, 5)" :key="drive.id" class="rq-drive-insight-row" role="listitem">
                <div class="rq-drive-insight-main">
                  <span class="rq-drive-insight-title">{{ drive.title || 'Drive' }}</span>
                  <span class="rq-drive-insight-sub">{{ drive.applicants }} applicants - {{ drive.offered }} offers</span>
                </div>
                <span class="rq-conv-rate" :class="convClass(drive.offered, drive.applicants)">
                  {{ conversionLabel(drive.offered, drive.applicants) }}
                </span>
              </div>
            </div>
          </div>
          <p v-else class="rq-empty-text">Drive performance data is unavailable for the selected filters.</p>
        </div>
      </div>

      <div class="rq-card rq-col-full">
        <div class="rq-card-hd">
          <span class="rq-card-title">Branch-wise Applicants</span>
          <span class="rq-pill rq-pill-blue">{{ branchApplicantsFiltered.length }} branch segments</span>
        </div>
        <div class="rq-card-body">
          <div v-if="hasBranchData" class="rq-chart-block">
            <div class="rq-chart-wrap rq-chart-md">
              <canvas ref="branchChart" aria-label="Branch applicant chart" role="img"></canvas>
            </div>

            <div class="rq-branch-list" role="list" aria-label="Branch applicant totals">
              <span
                v-for="branch in branchApplicantsFiltered"
                :key="branch.name"
                class="rq-branch-chip"
                :style="{ '--rq-branch-chip-color': branch.color || '#2563EB' }"
                role="listitem"
              >
                {{ branch.name }} - {{ branch.count }}
              </span>
            </div>
          </div>
          <p v-else class="rq-empty-text">No branch-level applicant records are available right now.</p>
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
    },
    applications: {
      type: Array,
      default: () => []
    },
    isExportBusy: {
      type: Boolean,
      default: false
    },
    exportLabel: {
      type: String,
      default: 'Export'
    }
  },
  emits: ['export-analytics'],
  data() {
    return {
      pipelineChartInstance: null,
      driveChartInstance: null,
      branchChartInstance: null,
      renderQueued: false,
      selectedDriveStatus: 'all',
      selectedBranch: 'all',
      selectedDateWindow: 'all'
    }
  },
  computed: {
    driveStatusOptions() {
      return [
        { value: 'all', label: 'All Drives' },
        { value: 'active', label: 'Active Drives' },
        { value: 'pending', label: 'Pending Drives' },
        { value: 'closed', label: 'Closed Drives' }
      ]
    },
    dateWindowOptions() {
      return [
        { value: 'all', label: 'All Time' },
        { value: '30d', label: 'Last 30 Days' },
        { value: '90d', label: 'Last 90 Days' },
        { value: 'ytd', label: 'Year to Date' }
      ]
    },
    branchOptions() {
      const branchSet = new Set()

      this.branchApplicants.forEach((branch) => {
        const normalized = String(branch?.name || '').trim().toUpperCase()
        if (normalized) {
          branchSet.add(normalized)
        }
      })

      this.applications.forEach((application) => {
        const normalized = String(application?.branch || '').trim().toUpperCase()
        if (normalized) {
          branchSet.add(normalized)
        }
      })

      return [
        { value: 'all', label: 'All Branches' },
        ...Array.from(branchSet)
          .sort((left, right) => left.localeCompare(right))
          .map((branchName) => ({
            value: branchName,
            label: branchName
          }))
      ]
    },
    normalizedDrives() {
      return this.myDrives.map((drive, index) => ({
        ...drive,
        id: Number(drive.id || index + 1),
        status: this.normalizeDriveStatus(drive.status),
        deadlineDate: this.parseDateValue(drive.deadlineRaw || drive.deadline || null)
      }))
    },
    normalizedApplications() {
      return this.applications.map((application, index) => ({
        ...application,
        id: Number(application.id || index + 1),
        driveId: Number(application.driveId || application.drive_id || application.job_id || 0),
        branch: String(application.branch || 'OTHER').trim().toUpperCase(),
        status: this.normalizeApplicationStatus(application.status),
        appliedDate: this.parseDateValue(application.date || application.applied_at || application.created_at || null)
      }))
    },
    statusAndWindowDrives() {
      return this.normalizedDrives.filter((drive) => {
        const statusMatches = this.selectedDriveStatus === 'all' || drive.status === this.selectedDriveStatus
        const dateMatches = this.selectedDateWindow === 'all' || this.driveInDateWindow(drive)
        return statusMatches && dateMatches
      })
    },
    statusAndWindowDriveIds() {
      return new Set(this.statusAndWindowDrives.map((drive) => Number(drive.id || 0)))
    },
    filteredApplications() {
      return this.normalizedApplications.filter((application) => {
        const belongsToDrive = application.driveId > 0
          ? this.statusAndWindowDriveIds.has(application.driveId)
          : this.selectedDriveStatus === 'all'

        const branchMatches = this.selectedBranch === 'all' || application.branch === this.selectedBranch
        const dateMatches = this.selectedDateWindow === 'all' || this.isWithinDateWindow(application.appliedDate)

        return belongsToDrive && branchMatches && dateMatches
      })
    },
    filteredApplicationDriveIds() {
      return new Set(this.filteredApplications.map((application) => Number(application.driveId || 0)))
    },
    drivesForCharts() {
      if (this.selectedBranch === 'all') {
        return this.statusAndWindowDrives
      }

      return this.statusAndWindowDrives.filter((drive) => (
        this.filteredApplicationDriveIds.has(Number(drive.id || 0)) ||
        this.driveSupportsBranch(drive, this.selectedBranch)
      ))
    },
    perDriveMetrics() {
      const metrics = new Map()

      this.filteredApplications.forEach((application) => {
        const driveId = Number(application.driveId || 0)
        if (!driveId) {
          return
        }

        if (!metrics.has(driveId)) {
          metrics.set(driveId, {
            applicants: 0,
            offered: 0
          })
        }

        const target = metrics.get(driveId)
        target.applicants += 1
        if (application.status === 'offered') {
          target.offered += 1
        }
      })

      return metrics
    },
    topDriveRows() {
      return this.drivesForCharts
        .map((drive) => {
          const metrics = this.perDriveMetrics.get(Number(drive.id || 0))
          const applicants = metrics ? metrics.applicants : Number(drive.applicants || 0)
          const offered = metrics ? metrics.offered : Number(this.stageCount(drive, 3) || 0)

          return {
            ...drive,
            applicants,
            offered
          }
        })
        .sort((left, right) => Number(right.applicants || 0) - Number(left.applicants || 0))
        .slice(0, 8)
    },
    pipelineMetrics() {
      const metrics = {
        applied: 0,
        shortlisted: 0,
        interview: 0,
        offered: 0,
        rejected: 0
      }

      this.filteredApplications.forEach((application) => {
        if (Object.prototype.hasOwnProperty.call(metrics, application.status)) {
          metrics[application.status] += 1
        }
      })

      if (
        this.filteredApplications.length === 0 &&
        this.selectedDriveStatus === 'all' &&
        this.selectedBranch === 'all' &&
        this.selectedDateWindow === 'all'
      ) {
        return {
          applied: Number(this.analytics.applied || 0),
          shortlisted: Number(this.analytics.shortlisted || 0),
          interview: Number(this.analytics.interview || 0),
          offered: Number(this.analytics.offered || 0),
          rejected: Number(this.analytics.rejected || 0)
        }
      }

      return metrics
    },
    pipelineTotal() {
      const metrics = this.pipelineMetrics
      return Number(metrics.applied || 0) +
        Number(metrics.shortlisted || 0) +
        Number(metrics.interview || 0) +
        Number(metrics.offered || 0) +
        Number(metrics.rejected || 0)
    },
    effectiveOfferRate() {
      const denominator = this.filteredApplications.length || this.pipelineTotal
      if (denominator <= 0) {
        return Number(this.offerRatePct || 0)
      }

      return this.pct(Number(this.pipelineMetrics.offered || 0), denominator)
    },
    branchApplicantsFiltered() {
      if (this.filteredApplications.length > 0) {
        const counts = {}

        this.filteredApplications.forEach((application) => {
          const branch = String(application.branch || 'OTHER').toUpperCase()
          counts[branch] = (counts[branch] || 0) + 1
        })

        return Object.entries(counts)
          .sort((left, right) => right[1] - left[1])
          .map(([name, count], index) => ({
            name,
            count,
            color: this.branchColor(name, index)
          }))
      }

      const fallbackRows = this.branchApplicants
        .map((branch, index) => ({
          name: String(branch.name || 'OTHER').toUpperCase(),
          count: Number(branch.count || 0),
          color: branch.color || this.branchColor(branch.name, index)
        }))
        .filter((branch) => branch.count > 0)

      if (this.selectedBranch === 'all') {
        return fallbackRows
      }

      return fallbackRows.filter((branch) => branch.name === this.selectedBranch)
    },
    stageOverview() {
      const ordered = [
        { key: 'applied', label: 'Applied', count: Number(this.pipelineMetrics.applied || 0) },
        { key: 'shortlisted', label: 'Shortlisted', count: Number(this.pipelineMetrics.shortlisted || 0) },
        { key: 'interview', label: 'Interview', count: Number(this.pipelineMetrics.interview || 0) },
        { key: 'offered', label: 'Offered', count: Number(this.pipelineMetrics.offered || 0) },
        { key: 'rejected', label: 'Rejected', count: Number(this.pipelineMetrics.rejected || 0) }
      ]

      return ordered.map((stage, index) => {
        if (index === 0) {
          return {
            ...stage,
            meta: `${stage.count} candidates`
          }
        }

        const previous = ordered[index - 1].count
        if (previous <= 0) {
          return {
            ...stage,
            meta: 'No baseline yet'
          }
        }

        if (stage.key === 'rejected') {
          return {
            ...stage,
            meta: `${this.pct(stage.count, Math.max(this.pipelineTotal, 1))}% of total`
          }
        }

        return {
          ...stage,
          meta: `${this.pct(stage.count, previous)}% retained`
        }
      })
    },
    analyticsSnapshotCards() {
      const applicationsTotal = this.filteredApplications.length || this.pipelineTotal
      const shortlisted = Number(this.pipelineMetrics.shortlisted || 0)
      const interview = Number(this.pipelineMetrics.interview || 0)
      const offered = Number(this.pipelineMetrics.offered || 0)
      const rejected = Number(this.pipelineMetrics.rejected || 0)

      const topBranch = this.branchApplicantsFiltered[0]
      const topBranchLabel = topBranch ? topBranch.name : '-'
      const topBranchCount = topBranch ? Number(topBranch.count || 0) : 0

      return [
        {
          id: 'drives-scope',
          label: 'Drives In Scope',
          value: String(this.drivesForCharts.length),
          meta: `${this.selectedDriveStatus === 'all' ? 'all statuses' : this.selectedDriveStatus} filter`
        },
        {
          id: 'applications',
          label: 'Applications',
          value: String(applicationsTotal),
          meta: `${this.selectedBranch === 'all' ? 'all branches' : this.selectedBranch} scoped`
        },
        {
          id: 'shortlisted',
          label: 'Shortlisted',
          value: String(shortlisted),
          meta: `${this.pct(shortlisted, Math.max(applicationsTotal, 1))}% of applications`
        },
        {
          id: 'interviewed',
          label: 'Interviews',
          value: String(interview),
          meta: `${this.pct(interview, Math.max(shortlisted, 1))}% from shortlist`
        },
        {
          id: 'offers',
          label: 'Offers Released',
          value: String(offered),
          meta: `${this.effectiveOfferRate}% conversion`
        },
        {
          id: 'rejected',
          label: 'Rejected',
          value: String(rejected),
          meta: `${this.pct(rejected, Math.max(applicationsTotal, 1))}% rejection share`
        },
        {
          id: 'top-branch',
          label: 'Top Branch',
          value: topBranchLabel,
          meta: `${topBranchCount} applicants`
        },
        {
          id: 'window',
          label: 'Date Window',
          value: this.dateWindowOptions.find((option) => option.value === this.selectedDateWindow)?.label || 'All Time',
          meta: 'Current filter range'
        }
      ]
    },
    filterSummary() {
      const branchLabel = this.selectedBranch === 'all' ? 'all branches' : this.selectedBranch
      const statusLabel = this.driveStatusOptions.find((option) => option.value === this.selectedDriveStatus)?.label || 'All Drives'
      const dateLabel = this.dateWindowOptions.find((option) => option.value === this.selectedDateWindow)?.label || 'All Time'
      const scopedApplications = this.filteredApplications.length || this.pipelineTotal

      return `${scopedApplications} applications across ${statusLabel.toLowerCase()} (${branchLabel}, ${dateLabel.toLowerCase()}).`
    },
    chartRenderKey() {
      const pipelineKey = [
        Number(this.pipelineMetrics.applied || 0),
        Number(this.pipelineMetrics.shortlisted || 0),
        Number(this.pipelineMetrics.interview || 0),
        Number(this.pipelineMetrics.offered || 0),
        Number(this.pipelineMetrics.rejected || 0)
      ].join('|')

      const driveKey = this.topDriveRows
        .map((drive) => `${drive.id || drive.title || 'drive'}:${Number(drive.applicants || 0)}:${Number(drive.offered || 0)}`)
        .join(';')

      const branchKey = this.branchApplicantsFiltered
        .map((branch) => `${branch.name || 'OTHER'}:${Number(branch.count || 0)}`)
        .join(';')

      return [
        pipelineKey,
        driveKey,
        branchKey,
        this.selectedDriveStatus,
        this.selectedBranch,
        this.selectedDateWindow
      ].join('__')
    },
    hasPipelineData() {
      return [
        this.pipelineMetrics.applied,
        this.pipelineMetrics.shortlisted,
        this.pipelineMetrics.interview,
        this.pipelineMetrics.offered,
        this.pipelineMetrics.rejected
      ].some((value) => Number(value || 0) > 0)
    },
    hasDriveData() {
      return this.topDriveRows.some((drive) => (
        Number(drive.applicants || 0) > 0 ||
        Number(drive.offered || 0) > 0
      ))
    },
    hasBranchData() {
      return this.branchApplicantsFiltered.some((branch) => Number(branch.count || 0) > 0)
    },
    hasAnyData() {
      return this.hasPipelineData || this.hasDriveData || this.hasBranchData
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
    normalizeDriveStatus(rawStatus) {
      const normalized = String(rawStatus || '').trim().toLowerCase()
      if (['active', 'pending', 'closed'].includes(normalized)) {
        return normalized
      }
      if (normalized === 'approved') {
        return 'active'
      }
      return 'pending'
    },
    normalizeApplicationStatus(rawStatus) {
      const normalized = String(rawStatus || '').trim().toLowerCase()
      const aliases = {
        interviewed: 'interview',
        interview: 'interview',
        shortlisted: 'shortlisted',
        waitlisted: 'shortlisted',
        selected: 'offered',
        offered: 'offered',
        placed: 'offered',
        rejected: 'rejected',
        fail: 'rejected'
      }

      return aliases[normalized] || 'applied'
    },
    parseDateValue(rawValue) {
      if (!rawValue) {
        return null
      }

      const parsed = new Date(rawValue)
      if (Number.isNaN(parsed.getTime())) {
        return null
      }

      return parsed
    },
    isWithinDateWindow(dateValue) {
      if (!dateValue || this.selectedDateWindow === 'all') {
        return true
      }

      const now = new Date()
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const startOfToday = new Date(dateValue.getFullYear(), dateValue.getMonth(), dateValue.getDate())
      const deltaMs = today.getTime() - startOfToday.getTime()
      const dayDiff = Math.floor(deltaMs / 86400000)

      if (this.selectedDateWindow === '30d') {
        return dayDiff >= 0 && dayDiff <= 30
      }
      if (this.selectedDateWindow === '90d') {
        return dayDiff >= 0 && dayDiff <= 90
      }
      if (this.selectedDateWindow === 'ytd') {
        return dateValue.getFullYear() === now.getFullYear() && dateValue <= now
      }

      return true
    },
    driveInDateWindow(drive) {
      if (this.selectedDateWindow === 'all') {
        return true
      }

      const hasApplicationInWindow = this.normalizedApplications.some((application) => (
        Number(application.driveId || 0) === Number(drive.id || 0) && this.isWithinDateWindow(application.appliedDate)
      ))

      if (hasApplicationInWindow) {
        return true
      }

      return this.isWithinDateWindow(drive.deadlineDate)
    },
    driveSupportsBranch(drive, branchName) {
      const branches = String(drive.branches || '')
        .split(',')
        .map((branch) => String(branch || '').trim().toUpperCase())
        .filter(Boolean)

      return branches.includes(branchName)
    },
    branchColor(branchName, index) {
      const fallbackPalette = ['#2563EB', '#059669', '#D97706', '#7C3AED', '#DC2626', '#0EA5E9']
      const normalized = String(branchName || '').toUpperCase()
      const existing = this.branchApplicants.find(
        (branch) => String(branch.name || '').toUpperCase() === normalized
      )

      return existing?.color || fallbackPalette[index % fallbackPalette.length]
    },
    conversionLabel(offered, total) {
      return `${this.pct(Number(offered || 0), Math.max(Number(total || 0), 1))}%`
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
                Number(this.pipelineMetrics.applied || 0),
                Number(this.pipelineMetrics.shortlisted || 0),
                Number(this.pipelineMetrics.interview || 0),
                Number(this.pipelineMetrics.offered || 0),
                Number(this.pipelineMetrics.rejected || 0)
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
      const offered = this.topDriveRows.map((drive) => Number(drive.offered || 0))

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

      const labels = this.branchApplicantsFiltered.map((branch) => branch.name || 'OTHER')
      const counts = this.branchApplicantsFiltered.map((branch) => Number(branch.count || 0))
      const colors = this.branchApplicantsFiltered.map((branch) => branch.color || '#2563EB')

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

<style scoped>
.rq-analytics-view {
  gap: 14px;
}

.rq-analytics-toolbar-card {
  overflow: visible;
}

.rq-analytics-toolbar-head {
  align-items: flex-start;
  gap: 14px;
}

.rq-analytics-subtitle {
  margin: 4px 0 0;
  font-size: 0.74rem;
  color: var(--rq-t3);
}

.rq-analytics-toolbar-body {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.rq-analytics-control {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rq-analytics-control span {
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--rq-t4);
}

.rq-analytics-snapshot-card {
  overflow: visible;
}

.rq-analytics-snapshot-head {
  align-items: center;
}

.rq-analytics-snapshot-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.rq-analytics-snapshot-item {
  border: 1px solid var(--rq-border2);
  border-radius: 10px;
  background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
  padding: 10px;
  display: grid;
  gap: 2px;
}

.rq-analytics-snapshot-label {
  font-size: 0.64rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--rq-t4);
  font-weight: 700;
}

.rq-analytics-snapshot-value {
  font-family: var(--rq-mono);
  font-size: 1rem;
  color: var(--rq-ink);
  letter-spacing: -0.02em;
}

.rq-analytics-snapshot-meta {
  font-size: 0.68rem;
  color: var(--rq-t3);
}

.rq-chart-block {
  display: grid;
  gap: 12px;
}

.rq-stage-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.rq-stage-chip {
  border: 1px solid var(--rq-border2);
  border-radius: 8px;
  padding: 8px;
  display: grid;
  gap: 2px;
}

.rq-stage-name {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--rq-t4);
  font-weight: 700;
}

.rq-stage-value {
  font-family: var(--rq-mono);
  font-size: 0.95rem;
}

.rq-stage-meta {
  font-size: 0.66rem;
  color: var(--rq-t3);
}

.rq-drive-insights {
  display: grid;
  gap: 8px;
}

.rq-drive-insight-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid var(--rq-border2);
  border-radius: 8px;
  padding: 8px 10px;
}

.rq-drive-insight-main {
  display: grid;
  gap: 1px;
}

.rq-drive-insight-title {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--rq-ink);
}

.rq-drive-insight-sub {
  font-size: 0.68rem;
  color: var(--rq-t3);
}

.rq-branch-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rq-branch-chip {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: var(--rq-r-full);
  border: 1px solid color-mix(in srgb, var(--rq-branch-chip-color) 40%, white);
  color: color-mix(in srgb, var(--rq-branch-chip-color) 70%, black);
  background: color-mix(in srgb, var(--rq-branch-chip-color) 12%, white);
}

.rq-analytics-empty {
  min-height: 190px;
}

@media (max-width: 1100px) {
  .rq-analytics-snapshot-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .rq-stage-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 840px) {
  .rq-analytics-toolbar-body {
    grid-template-columns: 1fr;
  }

  .rq-stage-strip {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 560px) {
  .rq-analytics-snapshot-grid,
  .rq-stage-strip {
    grid-template-columns: 1fr;
  }

  .rq-drive-insight-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
