<template>
  <section class="rq-view">
    <div class="rq-toolbar">
      <div class="rq-search rq-search-inline" :class="{ 'is-focused': appSearchFocused }">
        <svg class="rq-search-ico" width="14" height="14" viewBox="0 0 14 14" fill="none">
          <circle cx="6" cy="6" r="4.5" stroke="currentColor" stroke-width="1.5" />
          <path d="M9.5 9.5L12 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
        </svg>
        <input
          :value="appSearch"
          @input="$emit('update:app-search', $event.target.value)"
          @focus="$emit('set-search-focus', true)"
          @blur="$emit('set-search-focus', false)"
          placeholder="Search students…"
          class="rq-search-field"
          aria-label="Search applications"
        />
      </div>

      <select class="rq-select" :value="appDriveFilter" @change="$emit('update:app-drive-filter', normalizeDriveFilter($event.target.value))" aria-label="Filter by drive">
        <option value="">All Drives</option>
        <option v-for="drive in myDrives" :key="drive.id" :value="drive.id">{{ drive.title }}</option>
      </select>

      <div class="rq-chips">
        <button
          v-for="filter in appStatusFilters"
          :key="filter.v"
          class="rq-chip-btn"
          :class="{ on: appStatusFilter === filter.v }"
          @click="$emit('update:app-status-filter', filter.v)"
        >
          {{ filter.l }}
        </button>
      </div>

      <div style="flex:1"></div>

      <transition name="rq-fade">
        <div v-if="selectedApps.length > 0" class="rq-bulk-actions">
          <span class="rq-bulk-count">{{ selectedApps.length }} selected</span>
          <button class="rq-btn-ok" @click="$emit('bulk-shortlist')" :disabled="actionsDisabled">Shortlist All</button>
          <button class="rq-btn-no" @click="$emit('bulk-reject')" :disabled="actionsDisabled">Reject All</button>
          <button class="rq-ghost rq-ghost-xs" @click="$emit('clear-selected')">Clear</button>
        </div>
      </transition>

      <button class="rq-ghost" @click="$emit('export-applications')">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M6 1v7M3 6l3 3 3-3M1 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        Export CSV
      </button>
    </div>

    <div class="rq-app-stats-row">
      <span class="rq-app-stat-item">
        <span class="rq-app-stat-n" style="color:var(--rq-amber)">{{ filteredApplications.filter((application) => application.status === 'applied').length }}</span>
        Applied
      </span>
      <span class="rq-app-stat-sep">·</span>
      <span class="rq-app-stat-item">
        <span class="rq-app-stat-n" style="color:var(--rq-purple)">{{ filteredApplications.filter((application) => application.status === 'shortlisted').length }}</span>
        Shortlisted
      </span>
      <span class="rq-app-stat-sep">·</span>
      <span class="rq-app-stat-item">
        <span class="rq-app-stat-n" style="color:var(--rq-blue)">{{ filteredApplications.filter((application) => application.status === 'interview').length }}</span>
        Interview
      </span>
      <span class="rq-app-stat-sep">·</span>
      <span class="rq-app-stat-item">
        <span class="rq-app-stat-n" style="color:var(--rq-green)">{{ filteredApplications.filter((application) => application.status === 'offered').length }}</span>
        Offered
      </span>
    </div>

    <div class="rq-card">
      <div class="rq-tbl-wrap">
        <table class="rq-tbl" aria-label="Applications">
          <thead>
            <tr>
              <th scope="col">
                <input type="checkbox" :checked="allPageSelected" @change="$emit('toggle-select-all')" class="rq-checkbox" aria-label="Select all" />
              </th>
              <th scope="col">Student</th>
              <th scope="col">Drive</th>
              <th scope="col">Branch / Year</th>
              <th scope="col">CGPA</th>
              <th scope="col">Applied On</th>
              <th scope="col">Status</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="application in filteredApplications"
              :key="application.id"
              :class="{ 'row-selected': selectedApps.includes(application.id) }"
            >
              <td>
                <input
                  type="checkbox"
                  :checked="selectedApps.includes(application.id)"
                  @change="$emit('toggle-select-app', application.id)"
                  class="rq-checkbox"
                  :aria-label="'Select ' + application.student"
                />
              </td>
              <td>
                <div class="rq-entity">
                  <div class="rq-av rq-av-md" :style="{ background: application.color }">{{ application.initials }}</div>
                  <div>
                    <div class="rq-ename">{{ application.student }}</div>
                    <div class="rq-esub">{{ application.email }}</div>
                  </div>
                </div>
              </td>
              <td class="rq-sm rq-dim">{{ application.drive }}</td>
              <td class="rq-sm rq-dim">{{ application.branch }} · Y{{ application.year }}</td>
              <td>
                <span class="rq-cgpa" :class="application.cgpa >= 8.5 ? 'cgpa-hi' : application.cgpa >= 7 ? 'cgpa-md' : 'cgpa-lo'">
                  {{ application.cgpa }}
                </span>
              </td>
              <td class="rq-sm rq-dim rq-mono">{{ application.date }}</td>
              <td>
                <span class="rq-status-pill" :class="'pill-app-' + application.status">{{ application.status }}</span>
              </td>
              <td>
                <div class="rq-acts">
                  <template v-if="application.status === 'applied' || application.status === 'pending'">
                    <button class="rq-ghost rq-ghost-xs" @click="$emit('screen-application', application)" :disabled="actionsDisabled || isScoring[application.id]">
                      {{ isScoring[application.id] ? 'Scoring...' : 'ATS Score' }}
                    </button>
                    <button class="rq-btn-ok" @click="$emit('shortlist', application)" :disabled="actionsDisabled">
                      <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                        <path d="M1.5 5.5l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                      Shortlist
                    </button>
                    <button class="rq-btn-no" @click="$emit('reject', application)" title="Reject" :disabled="actionsDisabled">
                      <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                        <path d="M2 2l7 7M9 2l-7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                      </svg>
                    </button>
                  </template>
                  <template v-if="application.status === 'shortlisted'">
                    <button class="rq-ghost rq-ghost-xs" @click="$emit('screen-application', application)" :disabled="actionsDisabled || isScoring[application.id]">
                      {{ isScoring[application.id] ? 'Scoring...' : 'ATS Score' }}
                    </button>
                    <button class="rq-btn-purple" @click="$emit('advance', application, 'interview')" :disabled="actionsDisabled">
                      <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                        <rect x="1" y="2" width="9" height="8" rx="1" stroke="currentColor" stroke-width="1.3" />
                        <path d="M4 5l2 1.5L8 5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                      Interview
                    </button>
                    <button class="rq-btn-no" @click="$emit('reject', application)" title="Reject" :disabled="actionsDisabled">
                      <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                        <path d="M2 2l7 7M9 2l-7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                      </svg>
                    </button>
                  </template>
                  <template v-if="application.status === 'interview'">
                    <button class="rq-ghost rq-ghost-xs" @click="$emit('screen-application', application)" :disabled="actionsDisabled || isScoring[application.id]">
                      {{ isScoring[application.id] ? 'Scoring...' : 'ATS Score' }}
                    </button>
                    <button class="rq-btn-ok" @click="$emit('advance', application, 'offered')" :disabled="actionsDisabled">Offer</button>
                    <button class="rq-btn-no" @click="$emit('reject', application)" title="Reject" :disabled="actionsDisabled">
                      <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                        <path d="M2 2l7 7M9 2l-7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                      </svg>
                    </button>
                  </template>
                  <template v-if="['offered', 'rejected'].includes(application.status)">
                    <button class="rq-ghost rq-ghost-xs" @click="$emit('screen-application', application)" :disabled="actionsDisabled || isScoring[application.id]">
                      {{ isScoring[application.id] ? 'Scoring...' : 'ATS Score' }}
                    </button>
                  </template>
                </div>
              </td>
            </tr>
            <tr v-if="!filteredApplications.length">
              <td colspan="8">
                <div class="rq-empty">
                  <div class="rq-empty-ico">📥</div>
                  <b>No applications found</b>
                  <span>Try adjusting your filters.</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'ApplicationsView',
  props: {
    appSearch: {
      type: String,
      required: true
    },
    appSearchFocused: {
      type: Boolean,
      required: true
    },
    appDriveFilter: {
      type: [String, Number],
      default: ''
    },
    appStatusFilter: {
      type: String,
      required: true
    },
    appStatusFilters: {
      type: Array,
      required: true
    },
    myDrives: {
      type: Array,
      required: true
    },
    selectedApps: {
      type: Array,
      required: true
    },
    filteredApplications: {
      type: Array,
      required: true
    },
    isScoring: {
      type: Object,
      default: () => ({})
    },
    allPageSelected: {
      type: Boolean,
      required: true
    },
    companyStatus: {
      type: String,
      required: true
    }
  },
  emits: [
    'update:app-search',
    'set-search-focus',
    'update:app-drive-filter',
    'update:app-status-filter',
    'toggle-select-all',
    'toggle-select-app',
    'bulk-shortlist',
    'bulk-reject',
    'clear-selected',
    'export-applications',
    'shortlist',
    'reject',
    'advance',
    'screen-application'
  ],
  computed: {
    actionsDisabled() {
      return this.companyStatus !== 'approved'
    }
  },
  methods: {
    normalizeDriveFilter(value) {
      if (value === '') {
        return ''
      }

      const parsed = Number(value)
      return Number.isNaN(parsed) ? value : parsed
    }
  }
}
</script>
