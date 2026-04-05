<template>
  <section class="rq-view">
    <div class="rq-greeting-bar">
      <div>
        <span class="rq-greeting-hi">Good {{ timeOfDay }}, {{ studentFirstName }}</span>
        <span class="rq-greeting-sub">{{ greetingSubline }} · {{ todayDate }}</span>
      </div>
      <div class="rq-live-pill">
        <span class="rq-live-dot" aria-hidden="true"></span>
        Live · {{ liveOpenCount }} drives open
      </div>
    </div>

    <div class="rq-kpi-grid">
      <article v-for="card in statCards" :key="card.id" class="rq-kpi">
        <div class="rq-kpi-val">{{ card.value }}</div>
        <div class="rq-kpi-label">{{ card.label }}</div>
        <div class="rq-kpi-sub">{{ card.sub }}</div>
      </article>
    </div>

    <article v-if="errorMessage" class="rq-card">
      <div class="rq-card-body">
        <p class="rq-error-text">{{ errorMessage }}</p>
      </div>
    </article>

    <div class="rq-dash-grid">
      <div class="rq-dash-main">
        <article class="rq-card">
          <header class="rq-card-hd rq-card-hd-split">
            <div class="rq-card-hd-l">
              <span class="rq-card-title">Eligible Drives</span>
              <span class="rq-pill rq-pill-blue">{{ liveOpenCount }} live</span>
            </div>
            <button class="rq-ghost" type="button" @click="$emit('switch-view', 'drives')">
              View all
            </button>
          </header>
          <div class="rq-card-body">
            <div v-if="isLoading" class="rq-list">
              <p class="rq-empty-text">Loading dashboard highlights...</p>
            </div>
            <div v-else-if="drives.length" class="rq-drive-list">
              <div v-for="drive in drives.slice(0, 4)" :key="drive.id" class="rq-drive-row">
                <div class="rq-drive-main">
                  <p class="rq-list-title">{{ drive.role }}</p>
                  <p class="rq-list-sub">{{ drive.company }}</p>
                  <div class="rq-drive-meta">
                    <span class="rq-drive-chip">{{ drive.salary || '-' }}</span>
                    <span class="rq-drive-chip">{{ drive.deadline || '-' }}</span>
                  </div>
                </div>
                <span class="rq-status-pill" :class="driveStateClass(drive)">{{ driveStateLabel(drive) }}</span>
              </div>
            </div>
            <p v-else class="rq-empty-text">No eligible drives yet.</p>
          </div>
        </article>

        <article class="rq-card">
          <header class="rq-card-hd rq-card-hd-split">
            <div class="rq-card-hd-l">
              <span class="rq-card-title">My Applications</span>
              <span v-if="shortlistedCount > 0" class="rq-pill rq-pill-amber">{{ shortlistedCount }} shortlisted</span>
            </div>
            <button class="rq-ghost" type="button" @click="$emit('switch-view', 'applications')">
              View all
            </button>
          </header>
          <div class="rq-table-wrap">
            <table class="rq-table rq-dashboard-table" aria-label="Recent applications">
              <thead>
                <tr>
                  <th scope="col">Company / Role</th>
                  <th scope="col">Applied</th>
                  <th scope="col">Package</th>
                  <th scope="col">Status</th>
                  <th scope="col">Next Step</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="isLoading">
                  <td colspan="5" class="rq-empty-row">Loading recent applications...</td>
                </tr>
                <tr v-else-if="!applications.length">
                  <td colspan="5" class="rq-empty-row">No applications yet.</td>
                </tr>
                <tr v-for="row in applications.slice(0, 5)" :key="row.id">
                  <td>
                    <p class="rq-row-title">{{ row.role }}</p>
                    <p class="rq-row-sub">{{ row.company }}</p>
                  </td>
                  <td class="rq-row-sub">{{ row.appliedOn || '-' }}</td>
                  <td class="rq-row-sub">{{ row.package || '-' }}</td>
                  <td>
                    <span class="rq-status-pill" :class="statusClass(row.status)">{{ row.statusLabel }}</span>
                  </td>
                  <td class="rq-row-sub">{{ row.nextStep || 'Awaiting update' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </div>

      <div class="rq-dash-side">
        <article v-if="hasApplications" class="rq-card rq-progress-card">
          <header class="rq-card-hd">
            <span class="rq-card-title">Placement Progress</span>
          </header>
          <div class="rq-card-body">
            <div class="rq-progress-wrap">
              <div class="rq-progress-ring" :style="progressRingStyle">
                <div class="rq-progress-ring-center">
                  <strong>{{ placedPercent }}%</strong>
                  <span>Placed</span>
                </div>
              </div>
            </div>
            <div class="rq-progress-legend">
              <div class="rq-progress-legend-row">
                <span class="rq-progress-dot dot-placed" aria-hidden="true"></span>
                <span class="rq-progress-label">Placed</span>
                <span class="rq-progress-value">{{ placedPercent }}%</span>
              </div>
              <div class="rq-progress-legend-row">
                <span class="rq-progress-dot dot-progress" aria-hidden="true"></span>
                <span class="rq-progress-label">In progress</span>
                <span class="rq-progress-value">{{ inProgressPercent }}%</span>
              </div>
              <div class="rq-progress-legend-row">
                <span class="rq-progress-dot dot-pending" aria-hidden="true"></span>
                <span class="rq-progress-label">Pending</span>
                <span class="rq-progress-value">{{ pendingPercent }}%</span>
              </div>
            </div>
          </div>
        </article>

        <article v-if="hasApplications" class="rq-card">
          <header class="rq-card-hd">
            <span class="rq-card-title">{{ currentStatusTitle }}</span>
          </header>
          <div class="rq-card-body">
            <div class="rq-status-steps">
              <div v-for="(step, index) in statusSteps" :key="step.id" class="rq-status-step">
                <div class="rq-status-step-track">
                  <span class="rq-status-step-dot" :class="step.dotClass" aria-hidden="true"></span>
                  <span
                    v-if="index < statusSteps.length - 1"
                    class="rq-status-step-line"
                    :class="{ 'is-done': step.done }"
                    aria-hidden="true"
                  ></span>
                </div>
                <div class="rq-status-step-body">
                  <p class="rq-status-step-title" :class="{ 'is-active': step.active }">{{ step.label }}</p>
                  <p class="rq-status-step-meta">{{ step.meta }}</p>
                </div>
              </div>
            </div>
          </div>
        </article>

        <article class="rq-card">
          <header class="rq-card-hd">
            <span class="rq-card-title">Upcoming Deadlines</span>
            <span v-if="urgentDeadlineCount > 0" class="rq-pill rq-pill-amber">{{ urgentDeadlineCount }} urgent</span>
          </header>
          <div class="rq-card-body">
            <div v-if="upcomingDeadlines.length" class="rq-deadline-list">
              <div v-for="deadline in upcomingDeadlines" :key="deadline.id" class="rq-deadline-row">
                <div>
                  <p class="rq-list-title">{{ deadline.role }}</p>
                  <p class="rq-list-sub">{{ deadline.company }}</p>
                </div>
                <div class="rq-deadline-meta">
                  <span class="rq-deadline-days" :class="{ 'is-urgent': deadline.daysLeft <= 3 }">{{ deadline.daysLeft }}d</span>
                  <span class="rq-list-sub">{{ deadline.deadline }}</span>
                </div>
              </div>
            </div>
            <div v-else class="rq-deadline-empty" role="status" aria-live="polite">
              <div class="rq-deadline-empty-icon" aria-hidden="true">
                <CircleCheck :size="16" class="rq-deadline-empty-check" />
              </div>
              <p class="rq-deadline-empty-title">All caught up!</p>
              <p class="rq-deadline-empty-sub">No upcoming deadlines.</p>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script>
import { CircleCheck } from 'lucide-vue-next'

const STATUS_RANK = Object.freeze({
  rejected: 0,
  applied: 1,
  shortlisted: 2,
  interview: 3,
  offer: 4,
  placed: 5
})

export default {
  name: 'StudentDashboardOverview',
  components: {
    CircleCheck
  },
  props: {
    studentFirstName: {
      type: String,
      default: 'Student'
    },
    timeOfDay: {
      type: String,
      default: 'day'
    },
    todayDate: {
      type: String,
      default: ''
    },
    liveOpenCount: {
      type: Number,
      default: 0
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    errorMessage: {
      type: String,
      default: ''
    },
    statCards: {
      type: Array,
      default: () => []
    },
    drives: {
      type: Array,
      default: () => []
    },
    applications: {
      type: Array,
      default: () => []
    },
    summary: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['switch-view'],
  computed: {
    greetingSubline() {
      const count = this.newDrivesCount
      if (count <= 0) {
        return 'No new eligible drives in the latest update'
      }

      return `${count} new eligible drive${count === 1 ? '' : 's'} in the latest update`
    },
    shortlistedCount() {
      return this.applications.filter((row) => this.normalizeStatus(row.status) === 'shortlisted').length
    },
    newDrivesCount() {
      if (!this.drives.length) {
        return 0
      }

      return this.drives.filter((row) => {
        const days = this.daysUntilDeadline(row.deadline)
        return days >= 0 && days <= 7
      }).length
    },
    applicationTotal() {
      const summaryTotal = Number(this.summary?.applications_total || 0)
      if (summaryTotal > 0) {
        return summaryTotal
      }
      return this.applications.length
    },
    hasApplications() {
      return this.applicationTotal > 0
    },
    placedCount() {
      return Number(this.summary?.offers_accepted || 0)
    },
    inProgressCount() {
      return (
        Number(this.summary?.shortlisted || 0) +
        Number(this.summary?.interviewed || 0) +
        Number(this.summary?.offers_released || 0)
      )
    },
    placedPercent() {
      return this.percent(this.placedCount, this.applicationTotal)
    },
    inProgressPercent() {
      const raw = this.percent(this.inProgressCount, this.applicationTotal)
      return Math.max(0, Math.min(100 - this.placedPercent, raw))
    },
    pendingPercent() {
      return Math.max(0, 100 - this.placedPercent - this.inProgressPercent)
    },
    progressRingStyle() {
      const progressStop = Math.min(100, this.placedPercent + this.inProgressPercent)
      return {
        '--rq-placed-pct': `${this.placedPercent}%`,
        '--rq-progress-stop': `${progressStop}%`
      }
    },
    currentApplication() {
      if (!this.applications.length) {
        return null
      }

      return [...this.applications]
        .sort((left, right) => this.statusRank(right.status) - this.statusRank(left.status))[0]
    },
    currentStageRank() {
      if (!this.currentApplication) {
        return STATUS_RANK.applied
      }

      const rank = this.statusRank(this.currentApplication.status)
      return rank > 0 ? rank : STATUS_RANK.applied
    },
    currentStatusTitle() {
      const company = String(this.currentApplication?.company || '').trim()
      if (!company) {
        return 'Current Status'
      }

      return `Current Status - ${company}`
    },
    statusSteps() {
      const labels = [
        { id: 'applied', label: 'Applied' },
        { id: 'shortlisted', label: 'Shortlisted' },
        { id: 'interview', label: 'Interview' },
        { id: 'offer', label: 'Offer' },
        { id: 'placed', label: 'Placed' }
      ]

      return labels.map((step, index) => {
        const rank = index + 1
        const done = rank < this.currentStageRank
        const active = rank === this.currentStageRank

        return {
          ...step,
          done,
          active,
          dotClass: done ? 'is-done' : active ? 'is-active' : 'is-pending',
          meta: active ? (this.currentApplication?.nextStep || 'Current stage') : done ? 'Completed' : 'Pending'
        }
      })
    },
    upcomingDeadlines() {
      return this.drives
        .map((row) => {
          const daysLeft = this.daysUntilDeadline(row.deadline)
          return {
            id: row.id,
            role: row.role,
            company: row.company,
            deadline: row.deadline || '-',
            daysLeft
          }
        })
        .filter((row) => row.daysLeft >= 0)
        .sort((left, right) => left.daysLeft - right.daysLeft)
        .slice(0, 5)
    },
    urgentDeadlineCount() {
      return this.upcomingDeadlines.filter((row) => row.daysLeft <= 3).length
    }
  },
  methods: {
    normalizeStatus(status) {
      const normalized = String(status || '').toLowerCase()
      if (normalized === 'interviewed') return 'interview'
      if (normalized === 'offered' || normalized === 'selected') return 'offer'
      if (normalized === 'accepted' || normalized === 'placed') return 'placed'
      if (normalized === 'shortlisted') return 'shortlisted'
      if (normalized === 'rejected') return 'rejected'
      return 'applied'
    },
    statusRank(status) {
      return STATUS_RANK[this.normalizeStatus(status)] ?? STATUS_RANK.applied
    },
    percent(count, total) {
      const parsedTotal = Number(total || 0)
      const parsedCount = Number(count || 0)
      if (parsedTotal <= 0 || parsedCount <= 0) {
        return 0
      }

      return Math.round((parsedCount / parsedTotal) * 100)
    },
    daysUntilDeadline(deadline) {
      if (!deadline || deadline === '-') {
        return -1
      }

      const parsed = new Date(`${deadline} ${new Date().getFullYear()}`)
      if (Number.isNaN(parsed.getTime())) {
        return -1
      }

      const today = new Date()
      const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate())
      const deadlineStart = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate())
      return Math.ceil((deadlineStart - todayStart) / 86400000)
    },
    driveStateClass(drive) {
      if (drive?.applied) return 'pill-shortlisted'
      if (drive?.isOpen === false) return 'pill-rejected'
      return 'pill-applied'
    },
    driveStateLabel(drive) {
      if (drive?.applied) return 'Applied'
      if (drive?.isOpen === false) return 'Closed'
      return 'Open'
    },
    statusClass(status) {
      const normalized = String(status || '').toLowerCase()
      if (normalized === 'shortlisted' || normalized === 'selected' || normalized === 'accepted') return 'pill-shortlisted'
      if (normalized === 'interview' || normalized === 'interviewed') return 'pill-interview'
      if (normalized === 'offered') return 'pill-offer'
      if (normalized === 'offer') return 'pill-offer'
      if (normalized === 'rejected') return 'pill-rejected'
      return 'pill-applied'
    }
  }
}
</script>
