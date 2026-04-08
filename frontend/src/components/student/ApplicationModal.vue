<template>
  <Transition name="rq-modal">
    <div
      v-if="application"
      class="rq-modal-overlay rq-application-modal-overlay"
      role="dialog"
      aria-modal="true"
      :aria-label="`Application details for ${roleLabel}`"
      @click.self="$emit('close')"
    >
      <article class="rq-modal rq-application-modal">
        <header class="rq-modal-hd rq-application-modal-hd">
          <div class="rq-application-head">
            <div class="rq-application-avatar" :style="avatarStyle">{{ companyInitials }}</div>
            <div class="rq-application-head-copy">
              <h2 class="rq-row-title rq-application-title">{{ roleLabel }}</h2>
              <p class="rq-row-sub rq-application-company">{{ companyLabel }}</p>
            </div>
          </div>

          <button class="rq-modal-close rq-application-modal-close" type="button" aria-label="Close" @click="$emit('close')">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            </svg>
          </button>
        </header>

        <div class="rq-modal-body rq-application-modal-body">
          <div class="rq-application-kpi-grid">
            <div class="rq-application-kpi">
              <span class="rq-application-kpi-label">Status</span>
              <span class="rq-status-pill rq-application-pill-wide rq-application-status-pill" :class="statusClass(application.status)">
                {{ statusText }}
              </span>
            </div>

            <div class="rq-application-kpi">
              <span class="rq-application-kpi-label">Package</span>
              <span class="rq-application-kpi-value rq-application-kpi-amount">{{ packageLabel }}</span>
            </div>

            <div class="rq-application-kpi">
              <span class="rq-application-kpi-label">Applied On</span>
              <span class="rq-application-kpi-value rq-application-kpi-muted rq-application-kpi-date">{{ appliedOnLabel }}</span>
            </div>

            <div class="rq-application-kpi">
              <span class="rq-application-kpi-label">Job Type</span>
              <span class="rq-status-pill rq-pill-neutral rq-application-pill-wide">
                {{ jobTypeLabel }}
              </span>
            </div>
          </div>

          <div class="rq-application-timeline-block">
            <span class="rq-modal-sec-label rq-application-section-label">Application Timeline</span>
            <div class="rq-application-timeline-list">
              <div
                v-for="event in timelineItems"
                :key="event.id"
                class="rq-application-timeline-item"
              >
                <span class="rq-application-timeline-dot" :class="timelineToneClass(event.tone)">
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
                    <path d="M2 5l2 2 4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </span>
                <span class="rq-application-timeline-label">{{ event.label }}</span>
                <span class="rq-application-timeline-date">{{ formatTimelineDate(event.timestamp) }}</span>
              </div>
            </div>
          </div>

          <div class="rq-application-actions-row">
            <div class="rq-application-check-wrap">
              <button
                class="rq-ghost rq-ghost-xs rq-application-check-btn"
                type="button"
                :disabled="isScoring"
                :aria-label="`Run ATS match for ${roleLabel}`"
                @click="$emit('score-application', application)"
              >
                {{ isScoring ? 'Scoring...' : 'Check Match' }}
              </button>
              <p v-if="scoreNote" class="rq-application-score-note">{{ scoreNote }}</p>
            </div>

            <div v-if="canRespondToOffer" class="rq-application-offer-actions">
              <div class="rq-inline-actions">
                <button
                  class="rq-ghost"
                  type="button"
                  :disabled="isResponding"
                  :aria-label="`Accept offer for ${roleLabel}`"
                  @click="$emit('respond-offer', offerId, 'accepted')"
                >
                  {{ isResponding ? 'Saving...' : 'Accept' }}
                </button>
                <button
                  class="rq-ghost rq-ghost-danger"
                  type="button"
                  :disabled="isResponding"
                  :aria-label="`Reject offer for ${roleLabel}`"
                  @click="$emit('respond-offer', offerId, 'rejected')"
                >
                  {{ isResponding ? 'Saving...' : 'Reject' }}
                </button>
              </div>
            </div>
          </div>

          <div v-if="screeningResult" class="rq-screening-block">
            <div class="rq-screening-kpis">
              <div class="rq-screening-kpi">
                <span class="rq-screening-kpi-label">ATS Score</span>
                <span class="rq-screening-kpi-value">{{ Number(screeningResult.analysis?.score || 0) }}%</span>
              </div>
              <div class="rq-screening-kpi">
                <span class="rq-screening-kpi-label">Matched</span>
                <span class="rq-screening-kpi-value">{{ Number(screeningResult.analysis?.matched_count || 0) }}</span>
              </div>
              <div class="rq-screening-kpi">
                <span class="rq-screening-kpi-label">Missing</span>
                <span class="rq-screening-kpi-value">{{ (screeningResult.analysis?.missing_keywords || []).length }}</span>
              </div>
            </div>

            <p class="rq-row-sub">
              Recommendation: {{ screeningResult.analysis?.recommendation || 'n/a' }}
            </p>

            <div class="rq-screening-tags-wrap">
              <p class="rq-row-sub">Matched keywords</p>
              <div class="rq-screening-tags">
                <span
                  v-for="keyword in screeningResult.analysis?.matched_keywords || []"
                  :key="`screen-hit-${keyword}`"
                  class="rq-status-pill pill-shortlisted"
                >
                  {{ keyword }}
                </span>
                <span v-if="!(screeningResult.analysis?.matched_keywords || []).length" class="rq-row-sub">
                  No matched keywords.
                </span>
              </div>
            </div>

            <div class="rq-screening-tags-wrap">
              <p class="rq-row-sub">Missing keywords</p>
              <div class="rq-screening-tags">
                <span
                  v-for="keyword in screeningResult.analysis?.missing_keywords || []"
                  :key="`screen-miss-${keyword}`"
                  class="rq-status-pill pill-rejected"
                >
                  {{ keyword }}
                </span>
                <span v-if="!(screeningResult.analysis?.missing_keywords || []).length" class="rq-row-sub">
                  Full keyword match achieved.
                </span>
              </div>
            </div>
          </div>
        </div>

        <footer class="rq-modal-ft rq-application-modal-ft">
          <button class="rq-ghost rq-application-close-btn" type="button" @click="$emit('close')">Close</button>
        </footer>
      </article>
    </div>
  </Transition>
</template>

<script>
export default {
  name: 'StudentApplicationModal',
  props: {
    application: {
      type: Object,
      default: null
    },
    screeningResult: {
      type: Object,
      default: null
    },
    scoreNote: {
      type: String,
      default: ''
    },
    isScoring: {
      type: Boolean,
      default: false
    },
    isResponding: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'score-application', 'respond-offer'],
  computed: {
    roleLabel() {
      return this.application?.drive?.title || this.application?.drive?.job_title || 'Role unavailable'
    },
    companyLabel() {
      return this.application?.company?.name || this.application?.company?.company_name || '-'
    },
    companyInitials() {
      const value = String(this.companyLabel || '').trim()
      if (!value || value === '-') return 'CO'

      const chunks = value.split(/\s+/).filter(Boolean)
      if (chunks.length === 1) {
        return (chunks[0][0] || 'C').toUpperCase()
      }
      return `${chunks[0][0] || ''}${chunks[1][0] || ''}`.toUpperCase()
    },
    avatarStyle() {
      const palette = ['#0EA5E9', '#2563EB', '#16A34A', '#7C3AED', '#EA580C']
      const seed = Number(this.application?.application_id || this.application?.id || 0)
      const color = palette[Math.abs(seed) % palette.length]
      return { background: color }
    },
    statusText() {
      return this.application?.status_label || this.statusLabel(this.application?.status)
    },
    appliedOnLabel() {
      const value = this.application?.application_date || this.application?.applied_at || this.application?.updated_at
      return this.formatShortDate(value)
    },
    packageLabel() {
      const driveSalary = Number(this.application?.drive?.salary_lpa || 0)
      if (!Number.isNaN(driveSalary) && driveSalary > 0) {
        return `₹${driveSalary.toLocaleString('en-IN')} LPA`
      }

      const offerSalary = Number(this.application?.offer?.salary || 0)
      if (!Number.isNaN(offerSalary) && offerSalary > 0) {
        const lpa = offerSalary / 100000
        const normalized = Number.isInteger(lpa)
          ? lpa.toLocaleString('en-IN')
          : lpa.toLocaleString('en-IN', { maximumFractionDigits: 1 })
        return `₹${normalized} LPA`
      }

      return '-'
    },
    jobTypeLabel() {
      return (
        this.application?.drive?.job_type ||
        this.application?.drive?.type ||
        this.application?.drive?.employment_type ||
        this.application?.job_type ||
        'Full-time'
      )
    },
    timelineItems() {
      const timeline = Array.isArray(this.application?.timeline)
        ? this.application.timeline
          .map((event, index) => ({
            id: event?.id || `timeline-${index}`,
            label: event?.label || 'Updated',
            timestamp: event?.timestamp || '',
            tone: event?.tone || 'info'
          }))
          .filter((event) => Boolean(String(event.timestamp || '').trim()))
          .sort((left, right) => {
            const leftTime = new Date(left.timestamp || '').getTime()
            const rightTime = new Date(right.timestamp || '').getTime()

            if (Number.isNaN(leftTime) && Number.isNaN(rightTime)) return 0
            if (Number.isNaN(leftTime)) return 1
            if (Number.isNaN(rightTime)) return -1
            return leftTime - rightTime
          })
         : []

      if (timeline.length) {
        return timeline
      }

      return [
        {
          id: 'timeline-applied',
          label: 'Applied',
          timestamp: this.application?.application_date || this.application?.applied_at || this.application?.updated_at,
          tone: 'info'
        }
      ]
    },
    offerId() {
      return Number(this.application?.offer?.offer_id || 0)
    },
    canRespondToOffer() {
      return this.offerId > 0 && String(this.application?.offer?.status || '').toLowerCase() === 'offered'
    }
  },
  methods: {
    formatShortDate(value) {
      if (!value) return '-'
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return '-'
      return parsed.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric'
      })
    },
    formatTimelineDate(value) {
      if (!value) return '-'

      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return '-'

      const now = new Date()
      const isToday =
        parsed.getFullYear() === now.getFullYear() &&
        parsed.getMonth() === now.getMonth() &&
        parsed.getDate() === now.getDate()

      if (isToday) {
        return 'Today'
      }

      return this.formatShortDate(parsed)
    },
    statusLabel(status) {
      const normalized = String(status || '').toLowerCase()
      const labels = {
        applied: 'Applied',
        shortlisted: 'Shortlisted',
        interviewed: 'Interviewed',
        selected: 'Selected',
        waitlisted: 'Waitlisted',
        rejected: 'Rejected',
        offered: 'Offer Released',
        accepted: 'Offer Accepted'
      }
      return labels[normalized] || (normalized ? normalized : 'Updated')
    },
    statusClass(status) {
      const normalized = String(status || '').toLowerCase()
      if (normalized === 'shortlisted' || normalized === 'selected' || normalized === 'accepted') {
        return 'pill-shortlisted'
      }
      if (normalized === 'interviewed') return 'pill-interview'
      if (normalized === 'rejected') return 'pill-rejected'
      if (normalized === 'offered') return 'pill-offer'
      return 'pill-applied'
    },
    timelineToneClass(tone) {
      const normalized = String(tone || '').toLowerCase()
      if (normalized === 'error') return 'is-error'
      if (normalized === 'warning') return 'is-warning'
      if (normalized === 'success') return 'is-success'
      return 'is-info'
    }
  }
}
</script>
