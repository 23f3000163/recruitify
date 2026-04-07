<template>
  <div
    v-if="drive"
    class="rq-modal-overlay"
    role="dialog"
    aria-modal="true"
    aria-label="Drive details"
    @click.self="$emit('close')"
  >
    <div class="rq-modal rq-modal-lg">
      <div class="rq-modal-hd">
        <div>
          <h3 class="rq-card-title">Drive Details</h3>
          <p class="rq-row-sub">{{ drive.company?.name || drive.company?.company_name || '-' }}</p>
        </div>

        <button class="rq-modal-close" type="button" aria-label="Close drive details" @click="$emit('close')">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
          </svg>
        </button>
      </div>

      <div class="rq-modal-body">
        <p class="rq-row-title">{{ drive.job_title || drive.title || 'Role unavailable' }}</p>
        <p class="rq-row-sub">Location: {{ drive.job_location || drive.location || '-' }}</p>
        <p class="rq-row-sub">Deadline: {{ formatDate(drive.application_deadline) }}</p>
        <p class="rq-row-sub">Package: {{ formatSalary(drive.salary_lpa) }}</p>
      </div>

      <div class="rq-modal-ft">
        <button class="rq-ghost" type="button" @click="$emit('close')">Close</button>
        <button class="rq-btn-primary" type="button" @click="$emit('apply', Number(drive.drive_id || drive.id))">
          Apply Now
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StudentDriveModal',
  props: {
    drive: {
      type: Object,
      default: null
    }
  },
  emits: ['close', 'apply'],
  methods: {
    formatSalary(value) {
      const parsed = Number(value)
      if (Number.isNaN(parsed) || parsed <= 0) return '-'
      return `${parsed.toLocaleString('en-IN')} LPA`
    },
    formatDate(value) {
      if (!value) return '-'
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return '-'
      return parsed.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    }
  }
}
</script>
