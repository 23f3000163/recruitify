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
            <thead><tr><th>Drive</th><th>Company</th><th>Applied On</th><th>Status</th><th>Action</th></tr></thead>
            <tbody>
              <tr v-for="a in selectedStudent.appList" :key="a.id || (a.drive + '-' + a.date)">
                <td class="rq-sm">{{ a.drive }}</td>
                <td class="rq-sm rq-dim">{{ a.company }}</td>
                <td class="rq-sm rq-dim rq-mono">{{ a.date }}</td>
                <td><span class="rq-status-pill" :class="'pill-' + a.status">{{ a.rawStatus || a.status }}</span></td>
                <td>
                  <select
                    class="rq-app-status-select"
                    :value="a.rawStatus || 'applied'"
                    :disabled="isApplicationBusy(a.id)"
                    @change="$emit('update-app-status', a, $event.target.value)"
                  >
                    <option value="applied">Applied</option>
                    <option value="shortlisted">Shortlisted</option>
                    <option value="waitlisted">Waitlisted</option>
                    <option value="rejected">Rejected</option>
                  </select>
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
    },
    pendingApplicationActions: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['close', 'update-app-status'],
  methods: {
    isApplicationBusy(applicationId) {
      return !!this.pendingApplicationActions[applicationId]
    }
  }
}
</script>
