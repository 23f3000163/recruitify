<template>
  <section class="rq-view">
    <div class="rq-toolbar">
      <div class="rq-chips">
        <button v-for="f in driveFilters" :key="f.v" class="rq-chip-btn" :class="{ on: driveFilter === f.v }" @click="$emit('update-drive-filter', f.v)">{{ f.l }}</button>
      </div>
      <div class="rq-table-tools">
        <select class="rq-sel" :disabled="isLoading" :value="driveSortBy" @change="$emit('update-drive-sort-by', $event.target.value)" aria-label="Sort drives">
          <option value="created_at">Newest</option>
          <option value="job_title">Title</option>
          <option value="status">Status</option>
          <option value="salary_lpa">Salary</option>
          <option value="application_deadline">Deadline</option>
        </select>
        <button class="rq-ghost rq-ghost-xs" :disabled="isLoading" @click="$emit('toggle-drive-order')">{{ driveOrder === 'asc' ? 'Asc' : 'Desc' }}</button>
      </div>
      <div style="flex: 1"></div>
      <div class="rq-pager">
        <button class="rq-ghost rq-ghost-xs" @click="$emit('prev-drive-page')" :disabled="isLoading || drivePage <= 1">Prev</button>
        <span class="rq-pager-info">Page {{ drivePage }} / {{ Math.max(drivePages, 1) }} · {{ driveTotal }}</span>
        <button class="rq-ghost rq-ghost-xs" @click="$emit('next-drive-page')" :disabled="isLoading || drivePage >= drivePages">Next</button>
      </div>
    </div>

    <div v-if="errorMessage" class="rq-state rq-state-error">
      <span>{{ errorMessage }}</span>
      <button class="rq-ghost rq-ghost-xs" @click="$emit('retry')" :disabled="isLoading">Retry</button>
    </div>

    <div class="rq-drives-grid">
      <template v-if="isLoading && !filteredDrives.length">
        <div v-for="n in 4" :key="`drive-skeleton-${n}`" class="rq-drive-card rq-drive-card-skeleton">
          <div class="rq-drive-top">
            <span class="rq-skeleton rq-skeleton-avatar rq-skeleton-drive-avatar"></span>
            <div class="rq-drive-meta">
              <div class="rq-skeleton rq-skeleton-line rq-skeleton-cell-lg"></div>
              <div class="rq-skeleton rq-skeleton-line rq-skeleton-cell-sm"></div>
            </div>
          </div>
          <div class="rq-drive-chips">
            <span class="rq-skeleton rq-skeleton-line rq-skeleton-chip"></span>
            <span class="rq-skeleton rq-skeleton-line rq-skeleton-chip"></span>
            <span class="rq-skeleton rq-skeleton-line rq-skeleton-chip"></span>
          </div>
        </div>
      </template>
      <template v-else>
        <div v-for="d in filteredDrives" :key="d.id" class="rq-drive-card">
          <div class="rq-drive-top">
            <div class="rq-av rq-av-lg" :style="{ background: d.color }">{{ d.initials }}</div>
            <div class="rq-drive-meta">
              <div class="rq-drive-title">{{ d.title }}</div>
              <div class="rq-drive-co">{{ d.company }}</div>
            </div>
            <span class="rq-status-pill" :class="'pill-' + d.status">{{ d.status }}</span>
          </div>
          <div class="rq-drive-chips">
            <span class="rq-dc">💰 {{ d.salary }}</span>
            <span class="rq-dc">👥 {{ d.applicants }} applied</span>
            <span class="rq-dc">📅 {{ d.deadline }}</span>
            <span class="rq-dc">🎓 CGPA ≥ {{ d.minCgpa }}</span>
            <span class="rq-dc">🏫 {{ d.branches }}</span>
            <span class="rq-dc">📚 {{ d.years || 'All Years' }}</span>
            <span class="rq-dc">🛠️ {{ d.requiredSkills || 'Skills -' }}</span>
          </div>
          <div class="rq-drive-actions">
            <template v-if="d.status === 'pending'">
              <button class="rq-btn-ok rq-btn-full" :disabled="isDriveBusy(d.id)" @click="$emit('change-drive-status', d, 'approved')">
                <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1.5 5.5l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                Approve Drive
              </button>
              <button class="rq-btn-no rq-btn-icon" :disabled="isDriveBusy(d.id)" @click="$emit('change-drive-status', d, 'rejected')" title="Reject">
                <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M2 2l7 7M9 2l-7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
              </button>
            </template>
            <button class="rq-ghost rq-ghost-xs" :disabled="isDriveBusy(d.id)" @click="$emit('remove-drive', d)">Remove</button>
          </div>
        </div>
        <div v-if="!filteredDrives.length" class="rq-drives-empty">
          <div class="rq-empty"><div class="rq-empty-ico">📋</div><b>No drives match</b><span>Try a different filter.</span></div>
        </div>
      </template>
    </div>
  </section>
</template>

<script>
export default {
  name: 'DrivesPanel',
  props: {
    filteredDrives: { type: Array, required: true },
    driveFilters: { type: Array, required: true },
    driveFilter: { type: String, required: true },
    drivePage: { type: Number, required: true },
    drivePages: { type: Number, required: true },
    driveTotal: { type: Number, required: true },
    driveSortBy: { type: String, required: true },
    driveOrder: { type: String, required: true },
    isLoading: { type: Boolean, default: false },
    errorMessage: { type: String, default: '' },
    pendingDriveActions: { type: Object, default: () => ({}) }
  },
  emits: [
    'update-drive-filter',
    'update-drive-sort-by',
    'toggle-drive-order',
    'set-drive-page',
    'prev-drive-page',
    'next-drive-page',
    'retry',
    'change-drive-status',
    'remove-drive'
  ],
  methods: {
    isDriveBusy(driveId) {
      return this.isLoading || !!this.pendingDriveActions[driveId]
    }
  }
}
</script>
