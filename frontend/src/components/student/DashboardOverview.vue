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
      <article
        v-for="card in statCards"
        :key="card.id"
        class="rq-kpi"
        :class="kpiClass(card.id)"
      >
        <div class="rq-kpi-header">
          <div class="rq-kpi-icon" v-html="kpiIconSvg(card.id)"></div>
          <span class="rq-kpi-pill" :class="kpiPillClass(card.id)">{{ kpiPillText(card) }}</span>
        </div>
        <div class="rq-kpi-val">{{ card.value }}</div>
        <div class="rq-kpi-label">{{ card.label }}</div>
        <div class="rq-kpi-sub">{{ card.sub }}</div>
        <div class="rq-kpi-bar">
          <div
            class="rq-kpi-bar-fill"
            :class="kpiBarClass(card.id)"
            :style="{ width: kpiBarWidth(card.value) }"
          ></div>
        </div>
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
                <div class="rq-drive-left">
                  <div class="rq-drive-avatar" :style="driveAvatarStyle(drive)">{{ driveInitials(drive) }}</div>
                  <div class="rq-drive-main">
                    <p class="rq-list-title">{{ drive.role }}</p>
                    <div class="rq-drive-company-row">
                      <p class="rq-list-sub">{{ drive.company }}</p>
                      <span class="rq-status-pill" :class="driveStateClass(drive)">{{ driveStateLabel(drive) }}</span>
                    </div>
                  </div>
                </div>
                <div class="rq-drive-meta">
                  <span v-for="chip in driveChips(drive)" :key="chip.key" class="rq-drive-chip">
                    <span class="rq-drive-chip-icon" aria-hidden="true">{{ chip.icon }}</span>
                    {{ chip.label }}
                  </span>
                </div>
                <div class="rq-drive-right">
                  <button
                    class="rq-btn-primary rq-drive-apply-btn"
                    :class="{ 'is-applied': drive.applied }"
                    type="button"
                    :disabled="!canApplyDrive(drive)"
                    @click="$emit('apply-drive', drive)"
                  >
                    {{ driveApplyButtonLabel(drive) }}
                  </button>
                </div>
              </div>
            </div>
            <div v-else class="rq-drive-empty" role="status" aria-live="polite">
              <div class="rq-drive-empty-icon" aria-hidden="true">
                <Briefcase :size="16" class="rq-drive-empty-symbol" />
              </div>
              <p class="rq-drive-empty-title">No eligible drives yet.</p>
              <p class="rq-drive-empty-sub">New drives will appear here.</p>
            </div>
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
          <div v-if="isLoading" class="rq-apps-empty" role="status" aria-live="polite">
            <p class="rq-empty-text">Loading recent applications...</p>
          </div>
          <div v-else-if="!applications.length" class="rq-apps-empty" role="status" aria-live="polite">
            <div class="rq-apps-empty-icon" aria-hidden="true">
              <FileText :size="16" class="rq-apps-empty-symbol" />
            </div>
            <p class="rq-apps-empty-title">No applications yet.</p>
            <p class="rq-apps-empty-sub">Apply to an eligible drive to get started.</p>
          </div>
          <div v-else class="rq-table-wrap">
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
                <tr v-for="row in applications.slice(0, 5)" :key="row.id">
                  <td>
                    <p class="rq-row-title">{{ row.role }}</p>
                    <p class="rq-row-sub">{{ row.company }}</p>
                  </td>
                  <td class="rq-row-sub">{{ row.appliedOn || '-' }}</td>
                  <td class="rq-dashboard-package">{{ row.package || '-' }}</td>
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
        <article class="rq-card rq-progress-card">
          <header class="rq-card-hd">
            <span class="rq-card-title">Placement Progress</span>
            <span v-if="hasApplications" class="rq-pill rq-pill-blue">{{ placementBreakdown.total }} tracked</span>
          </header>
          <div class="rq-card-body">
            <div class="rq-progress-wrap">
              <div class="rq-progress-ring" :style="progressRingStyle">
                <div class="rq-progress-ring-center">
                  <strong>{{ progressCenterValue }}</strong>
                  <span>{{ progressCenterLabel }}</span>
                </div>
              </div>
            </div>
            <p v-if="!hasApplications" class="rq-progress-empty">No applications yet. Placement metrics will appear here after your first application.</p>
            <div class="rq-progress-legend">
              <div class="rq-progress-legend-row">
                <span class="rq-progress-dot dot-placed" aria-hidden="true"></span>
                <span class="rq-progress-label">Placed</span>
                <span class="rq-progress-value">{{ placedPercent }}% ({{ placementBreakdown.placed }})</span>
              </div>
              <div class="rq-progress-legend-row">
                <span class="rq-progress-dot dot-progress" aria-hidden="true"></span>
                <span class="rq-progress-label">In progress</span>
                <span class="rq-progress-value">{{ inProgressPercent }}% ({{ placementBreakdown.inProgress }})</span>
              </div>
              <div class="rq-progress-legend-row">
                <span class="rq-progress-dot dot-pending" aria-hidden="true"></span>
                <span class="rq-progress-label">Pending</span>
                <span class="rq-progress-value">{{ pendingPercent }}% ({{ placementBreakdown.pending }})</span>
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
import { Briefcase, CircleCheck, FileText } from 'lucide-vue-next'

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
    Briefcase,
    CircleCheck,
    FileText
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
  emits: ['switch-view', 'apply-drive'],
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

      const derivedSummaryTotal =
        Number(this.summary?.applied || 0) +
        Number(this.summary?.shortlisted || 0) +
        Number(this.summary?.interviewed || 0) +
        Number(this.summary?.selected || 0) +
        Number(this.summary?.waitlisted || 0) +
        Number(this.summary?.rejected || 0)

      if (derivedSummaryTotal > 0) {
        return derivedSummaryTotal
      }

      return this.applications.length
    },
    hasApplications() {
      return this.applicationTotal > 0
    },
    placementBreakdown() {
      const total = Math.max(Number(this.applicationTotal || 0), 0)
      if (total <= 0) {
        return {
          total: 0,
          placed: 0,
          inProgress: 0,
          pending: 0
        }
      }

      const offersAccepted = Math.max(Number(this.summary?.offers_accepted || 0), 0)
      const selected = Math.max(Number(this.summary?.selected || 0), 0)
      const offersReleased = Math.max(Number(this.summary?.offers_released || 0), 0)
      const shortlisted = Math.max(Number(this.summary?.shortlisted || 0), 0)
      const interviewed = Math.max(Number(this.summary?.interviewed || 0), 0)
      const waitlisted = Math.max(Number(this.summary?.waitlisted || 0), 0)

      // Keep placed aligned with whichever backend signal is populated.
      const placedRaw = Math.max(offersAccepted, selected)
      const placed = Math.min(total, placedRaw)
      const remainingAfterPlaced = Math.max(total - placed, 0)

      const inProgressRaw = shortlisted + interviewed + waitlisted + offersReleased
      const inProgress = Math.min(remainingAfterPlaced, inProgressRaw)
      const pending = Math.max(total - placed - inProgress, 0)

      return {
        total,
        placed,
        inProgress,
        pending
      }
    },
    placedCount() {
      return this.placementBreakdown.placed
    },
    inProgressCount() {
      return this.placementBreakdown.inProgress
    },
    pendingCount() {
      return this.placementBreakdown.pending
    },
    placedPercent() {
      return this.percent(this.placedCount, this.applicationTotal)
    },
    inProgressPercent() {
      return this.percent(this.inProgressCount, this.applicationTotal)
    },
    pendingPercent() {
      if (!this.hasApplications) {
        return 0
      }

      return Math.max(0, 100 - this.placedPercent - this.inProgressPercent)
    },
    progressCenterValue() {
      if (!this.hasApplications) {
        return '0%'
      }
      if (this.placedPercent > 0) {
        return `${this.placedPercent}%`
      }
      if (this.inProgressPercent > 0) {
        return `${this.inProgressPercent}%`
      }
      return `${this.pendingPercent}%`
    },
    progressCenterLabel() {
      if (!this.hasApplications) {
        return 'No data'
      }
      if (this.placedCount > 0) {
        return 'Placed'
      }
      if (this.inProgressCount > 0) {
        return 'In Progress'
      }
      return 'Pending'
    },
    progressRingStyle() {
      const placedPercent = this.hasApplications ? this.placedPercent : 0
      const progressStop = this.hasApplications ? Math.min(100, placedPercent + this.inProgressPercent) : 0
      return {
        '--rq-placed-pct': `${placedPercent}%`,
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
            daysLeft,
            applied: Boolean(row.applied),
            isOpen: row.isOpen !== false,
            isEligible: row.isEligible !== false
          }
        })
        .filter((row) => row.daysLeft >= 0)
        .filter((row) => this.canApplyDrive(row))
        .sort((left, right) => left.daysLeft - right.daysLeft)
        .slice(0, 5)
    },
    urgentDeadlineCount() {
      return this.upcomingDeadlines.filter((row) => row.daysLeft <= 3).length
    }
  },
  methods: {
    kpiClass(cardId) {
      return `rq-kpi-${String(cardId || '').toLowerCase()}`
    },
    kpiIconSvg(cardId) {
      const iconMap = {
        applied:
          '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="8" cy="5" r="2.5" stroke="currentColor" stroke-width="1.4"/><path d="M3 13c0-2.6 2.1-4 5-4s5 1.4 5 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>',
        shortlisted:
          '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="3" y="2" width="10" height="12" rx="2" stroke="currentColor" stroke-width="1.4"/><path d="M6 6h4M6 9h4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>',
        interviewed:
          '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="2" y="3" width="12" height="10" rx="2" stroke="currentColor" stroke-width="1.4"/><path d="M5 1.8v2M11 1.8v2M2 6h12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>',
        offers:
          '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 2.2l1.7 3.4 3.7.5-2.7 2.6.6 3.7L8 10.6l-3.3 1.8.6-3.7L2.6 6.1l3.7-.5L8 2.2z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>'
      }

      return iconMap[cardId] || iconMap.applied
    },
    kpiPillClass(cardId) {
      const pillMap = {
        applied: 'pill-applied',
        shortlisted: 'pill-shortlisted',
        interviewed: 'pill-interview',
        offers: 'pill-offer'
      }

      return pillMap[cardId] || 'pill-applied'
    },
    kpiPillText(card) {
      const parsedValue = Number(String(card?.value || '0').replace(/,/g, '')) || 0
      if (card?.id === 'applied') return `${parsedValue} in progress`
      if (card?.id === 'shortlisted') return `${parsedValue} pending`
      if (card?.id === 'interviewed') return `${parsedValue} scheduled`
      if (card?.id === 'offers') return `${parsedValue} processed`
      return `${parsedValue} total`
    },
    kpiBarClass(cardId) {
      const barMap = {
        applied: 'kpi-bar-applied',
        shortlisted: 'kpi-bar-shortlisted',
        interviewed: 'kpi-bar-interviewed',
        offers: 'kpi-bar-offers'
      }

      return barMap[cardId] || 'kpi-bar-applied'
    },
    kpiBarWidth(value) {
      const current = Number(String(value || '0').replace(/,/g, '')) || 0
      const maxValue = Math.max(
        1,
        ...this.statCards.map((card) => Number(String(card?.value || '0').replace(/,/g, '')) || 0)
      )

      return `${Math.max(8, Math.round((current / maxValue) * 100))}%`
    },
    driveInitials(drive) {
      const company = String(drive?.company || '').trim()
      if (!company) return 'D'

      const segments = company.split(/\s+/).filter(Boolean)
      if (segments.length === 1) return segments[0].slice(0, 1).toUpperCase()
      return `${segments[0][0] || ''}${segments[1][0] || ''}`.toUpperCase()
    },
    driveAvatarStyle(drive) {
      const palette = ['#2563EB', '#059669', '#D97706', '#EF4444']
      const idSeed = Number(drive?.id || 0)
      const color = palette[Math.abs(idSeed) % palette.length]
      return { background: color }
    },
    driveChips(drive) {
      const chips = [
        { key: 'salary', icon: '💰', label: drive?.salary || '-' },
        { key: 'branch', icon: '🎓', label: drive?.branchLabel || '-' },
        { key: 'cgpa', icon: '📊', label: drive?.cgpaLabel || 'CGPA -' },
        { key: 'year', icon: '📚', label: drive?.yearLabel || 'Year -' },
        { key: 'skills', icon: '🛠️', label: this.formatRequiredSkills(drive?.skillsLabel || drive?.requiredSkills || drive?.required_skills) },
        { key: 'deadline', icon: '📅', label: drive?.deadline || '-' }
      ]

      return chips.filter((chip) => String(chip.label || '').trim())
    },
    canApplyDrive(drive) {
      return !drive?.applied && drive?.isOpen !== false && drive?.isEligible !== false
    },
    driveApplyButtonLabel(drive) {
      if (drive?.applied) return 'Applied'
      if (drive?.isOpen === false) return 'Closed'
      if (drive?.isEligible === false) return 'Not eligible'
      return 'Apply'
    },
    normalizeStatus(status) {
      const normalized = String(status || '').toLowerCase()
      if (normalized === 'interviewed') return 'interview'
      if (normalized === 'offer') return 'offer'
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
      if (drive?.isOpen === false) return 'pill-rejected'
      return 'pill-shortlisted'
    },
    driveStateLabel(drive) {
      if (drive?.isOpen === false) return 'Closed'
      return 'Open'
    },
    statusClass(status) {
      const normalized = String(status || '').toLowerCase()
      if (normalized === 'shortlisted' || normalized === 'selected' || normalized === 'accepted' || normalized === 'placed') return 'pill-shortlisted'
      if (normalized === 'interview' || normalized === 'interviewed') return 'pill-interview'
      if (normalized === 'offered') return 'pill-offer'
      if (normalized === 'offer') return 'pill-offer'
      if (normalized === 'rejected') return 'pill-rejected'
      return 'pill-applied'
    },
    formatRequiredSkills(value) {
      const entries = Array.isArray(value)
        ? value
        : String(value || '').split(',')

      const normalized = [...new Set(entries
        .map((item) => String(item || '').trim())
        .filter(Boolean))]

      if (!normalized.length) {
        return 'Skills -'
      }

      if (normalized.length <= 2) {
        return normalized.join(', ')
      }

      return `${normalized.slice(0, 2).join(', ')} +${normalized.length - 2}`
    }
  }
}
</script>
