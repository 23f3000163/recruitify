<template>
  <section class="rq-view">
    <div class="rq-greeting-bar">
      <div>
        <span class="rq-greeting-hi">Good {{ timeOfDay }}, {{ studentFirstName }}</span>
        <span class="rq-greeting-sub">{{ todayDate }}</span>
      </div>
      <div class="rq-live-pill">{{ liveOpenCount }} drives open</div>
    </div>

    <div class="rq-kpi-grid">
      <article v-for="card in statCards" :key="card.id" class="rq-kpi">
        <div class="rq-kpi-val">{{ card.value }}</div>
        <div class="rq-kpi-label">{{ card.label }}</div>
        <div class="rq-kpi-sub">{{ card.sub }}</div>
      </article>
    </div>

    <article v-if="errorMessage" class="rq-card">
      <div class="rq-card-body">
        <p class="rq-error-text">{{ errorMessage }}</p>
      </div>
    </article>

    <div class="rq-row-2">
      <article class="rq-card">
        <header class="rq-card-hd">
          <span class="rq-card-title">Eligible Drives</span>
        </header>
        <div class="rq-card-body">
          <div v-if="isLoading" class="rq-list">
            <p class="rq-empty-text">Loading dashboard highlights...</p>
          </div>
          <div v-else-if="drives.length" class="rq-list">
            <div v-for="drive in drives.slice(0, 4)" :key="drive.id" class="rq-list-row">
              <div>
                <p class="rq-list-title">{{ drive.role }}</p>
                <p class="rq-list-sub">{{ drive.company }} - {{ drive.salary }}</p>
              </div>
              <span class="rq-pill rq-pill-blue">{{ drive.deadline }}</span>
            </div>
          </div>
          <p v-else class="rq-empty-text">No eligible drives yet.</p>
        </div>
      </article>

      <article class="rq-card">
        <header class="rq-card-hd">
          <span class="rq-card-title">Recent Applications</span>
        </header>
        <div class="rq-card-body">
          <div v-if="isLoading" class="rq-list">
            <p class="rq-empty-text">Loading recent applications...</p>
          </div>
          <div v-else-if="applications.length" class="rq-list">
            <div v-for="row in applications.slice(0, 4)" :key="row.id" class="rq-list-row">
              <div>
                <p class="rq-list-title">{{ row.role }}</p>
                <p class="rq-list-sub">{{ row.company }}</p>
              </div>
              <span class="rq-status-pill" :class="statusClass(row.status)">{{ row.statusLabel }}</span>
            </div>
          </div>
          <p v-else class="rq-empty-text">No applications yet.</p>
        </div>
      </article>
    </div>
  </section>
</template>

<script>
export default {
  name: 'StudentDashboardHomeV2',
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
    }
  },
  methods: {
    statusClass(status) {
      const normalized = String(status || '').toLowerCase()
      if (normalized === 'shortlisted' || normalized === 'selected' || normalized === 'accepted') return 'pill-shortlisted'
      if (normalized === 'interview' || normalized === 'interviewed') return 'pill-interview'
      if (normalized === 'offered') return 'pill-offer'
      if (normalized === 'offer') return 'pill-offer'
      if (normalized === 'rejected') return 'pill-rejected'
      return 'pill-applied'
    }
  }
}
</script>
