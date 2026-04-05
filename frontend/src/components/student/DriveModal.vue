<template>
  <section v-if="drive" class="rq-view" aria-live="polite">
    <article class="rq-card">
      <header class="rq-card-hd">
        <span class="rq-card-title">Drive Details</span>
        <button class="rq-ghost" type="button" @click="$emit('close')">Close</button>
      </header>
      <div class="rq-card-body">
        <p class="rq-row-title">{{ drive.job_title || drive.title || 'Role unavailable' }}</p>
        <p class="rq-row-sub">{{ drive.company?.name || drive.company?.company_name || '-' }}</p>
        <p class="rq-row-sub">Location: {{ drive.job_location || drive.location || '-' }}</p>
        <p class="rq-row-sub">Deadline: {{ formatDate(drive.application_deadline) }}</p>
      </div>
      <footer class="rq-panel-footer rq-panel-footer-start">
        <button class="rq-btn-primary" type="button" @click="$emit('apply', Number(drive.drive_id || drive.id))">
          Apply Now
        </button>
      </footer>
    </article>
  </section>
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
