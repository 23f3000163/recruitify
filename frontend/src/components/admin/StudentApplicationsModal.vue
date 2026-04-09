<template>
  <Transition name="rq-modal">
    <div v-if="selectedStudent" class="rq-modal-overlay" @click.self="$emit('close')" role="dialog" aria-modal="true" :aria-label="selectedStudent.name + ' applications'">
      <div class="rq-modal">
        <div class="rq-modal-hd">
          <div class="rq-entity">
            <div class="rq-av rq-av-md" :style="{ background: selectedStudent.color }">{{ selectedStudent.initials }}</div>
            <div><div class="rq-ename">{{ selectedStudent.name }}</div><div class="rq-esub">{{ selectedStudent.roll }}</div></div>
          </div>
          <button class="rq-modal-close" @click="$emit('close')" aria-label="Close">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          </button>
        </div>
        <div class="rq-tbl-wrap">
          <table class="rq-tbl">
            <thead><tr><th>Drive</th><th>Company</th><th>Applied On</th><th>Status</th></tr></thead>
            <tbody>
              <tr v-for="a in selectedStudent.appList" :key="a.id || (a.drive + '-' + a.date)">
                <td class="rq-sm">{{ a.drive }}</td>
                <td class="rq-sm rq-dim">{{ a.company }}</td>
                <td class="rq-sm rq-dim rq-mono">{{ a.date }}</td>
                <td><span class="rq-status-pill" :class="'pill-' + a.status">{{ formatStatusLabel(a.rawStatus || a.status) }}</span></td>
              </tr>
              <tr v-if="!selectedStudent.appList || !selectedStudent.appList.length">
                <td colspan="4">
                  <div class="rq-empty"><b>No applications found</b><span>This student has not applied to any drives yet.</span></div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script>
export default {
  name: 'StudentApplicationsModal',
  props: {
    selectedStudent: {
      type: Object,
      default: null
    }
  },
  emits: ['close'],
  methods: {
    formatStatusLabel(status) {
      const normalized = String(status || 'applied').trim().toLowerCase()
      if (!normalized) return 'Applied'
      return normalized.charAt(0).toUpperCase() + normalized.slice(1)
    }
  }
}
</script>
