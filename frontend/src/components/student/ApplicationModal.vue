<template>
  <section v-if="application" class="rq-view" aria-live="polite">
    <article class="rq-card">
      <header class="rq-card-hd">
        <span class="rq-card-title">Application Details</span>
        <button class="rq-ghost" type="button" @click="$emit('close')">Close</button>
      </header>
      <div class="rq-card-body">
        <p class="rq-row-title">{{ application.drive?.title || application.drive?.job_title || 'Role unavailable' }}</p>
        <p class="rq-row-sub">{{ application.company?.name || application.company?.company_name || '-' }}</p>
        <p class="rq-row-sub">Status: {{ application.status_label || statusLabel(application.status) }}</p>
        <p class="rq-row-sub">Updated: {{ formatDateTime(application.updated_at) }}</p>

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
    </article>
  </section>
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
    }
  },
  emits: ['close'],
  methods: {
    formatDateTime(value) {
      if (!value) return '-'
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return '-'
      return parsed.toLocaleString()
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
    }
  }
}
</script>
