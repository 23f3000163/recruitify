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
