<template>
  <section class="rq-view">
    <div class="rq-toolbar">
      <div class="rq-chips">
        <button
          v-for="filter in driveFilters"
          :key="filter.v"
          class="rq-chip-btn"
          :class="{ on: driveFilter === filter.v }"
          @click="$emit('update:drive-filter', filter.v)"
        >
          {{ filter.l }}
        </button>
      </div>
      <div style="flex:1"></div>
      <button class="rq-ghost" :disabled="isExportBusy" @click="$emit('export-drives')">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M6 1v7M3 6l3 3 3-3M1 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        {{ exportLabel }}
      </button>
      <button
        class="rq-btn-primary"
        @click="requestDriveCreation"
        :class="{ 'btn-locked': companyStatus !== 'approved' }"
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M6 1v10M1 6h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        </svg>
        New Drive
      </button>
    </div>

    <div class="rq-drives-grid">
      <div
        v-for="drive in filteredDrives"
        :key="drive.id"
        class="rq-drive-card"
        @click="$emit('open-applications', drive.id)"
      >
        <div class="rq-drive-top">
          <div class="rq-av rq-av-lg" :style="{ background: drive.avatarColor }">{{ drive.initials }}</div>
          <div class="rq-drive-meta">
            <div class="rq-drive-title">{{ drive.title }}</div>
            <div class="rq-drive-co">{{ drive.role }} · {{ drive.type }}</div>
          </div>
          <span class="rq-status-pill" :class="'pill-' + drive.status">{{ drive.status }}</span>
        </div>

        <div class="rq-drive-chips">
          <span class="rq-dc">💰 {{ drive.salary }}</span>
          <span class="rq-dc">👥 {{ drive.applicants }} applied</span>
          <span class="rq-dc">📅 {{ drive.deadline }}</span>
          <span class="rq-dc">🎓 CGPA ≥ {{ drive.minCgpa }}</span>
          <span class="rq-dc">🏫 {{ drive.branches }}</span>
          <span class="rq-dc">📚 {{ drive.years || 'All Years' }}</span>
          <span class="rq-dc">🛠️ {{ drive.requiredSkills || 'Skills -' }}</span>
        </div>

        <div class="rq-drive-stages">
          <div v-for="stage in drive.stages" :key="stage.label" class="rq-ds-item">
            <div class="rq-ds-val" :style="{ color: stage.color }">{{ stage.count }}</div>
            <div class="rq-ds-label">{{ stage.label }}</div>
          </div>
        </div>

        <div class="rq-drive-actions" v-if="drive.status === 'approved' || drive.status === 'active'" @click.stop>
          <button class="rq-ghost" @click="$emit('open-applications', drive.id)">View Applications</button>
          <button v-if="drive.status === 'active'" class="rq-ghost rq-ghost-xs" @click="$emit('close-drive', drive)">
            Close Drive
          </button>
        </div>

        <div v-if="drive.status === 'pending'" class="rq-drive-pending-note">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1.2" />
            <path d="M6 4v2.5l1.5 1" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          Awaiting admin approval before going live
        </div>
      </div>

      <div v-if="!filteredDrives.length" class="rq-drives-empty">
        <div class="rq-empty">
          <div class="rq-empty-ico">📋</div>
          <b>No drives yet</b>
          <span>Create a placement drive to get started.</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'DrivesView',
  props: {
    driveFilters: {
      type: Array,
      required: true
    },
    driveFilter: {
      type: String,
      required: true
    },
    filteredDrives: {
      type: Array,
      required: true
    },
    companyStatus: {
      type: String,
      required: true
    },
    isExportBusy: {
      type: Boolean,
      default: false
    },
    exportLabel: {
      type: String,
      default: 'Export CSV'
    }
  },
  emits: ['update:drive-filter', 'export-drives', 'request-new-drive', 'open-applications', 'close-drive'],
  methods: {
    requestDriveCreation() {
      this.$emit('request-new-drive')
    }
  }
}
</script>
