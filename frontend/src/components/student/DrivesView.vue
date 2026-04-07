<template>
  <section class="rq-view">
    <article class="rq-card">
      <header class="rq-card-hd">
        <span class="rq-card-title">Placement Drives</span>
      </header>

      <div class="rq-card-body">
        <div class="rq-panel-tools">
          <label class="rq-field rq-field-grow">
            <span>Search</span>
            <input
              type="text"
              :value="queryText"
              placeholder="Role, company, location"
              @input="$emit('update:query-text', $event.target.value)"
              @keyup.enter="$emit('apply-filters')"
            />
          </label>

          <label class="rq-field">
            <span>Company</span>
            <input
              type="text"
              :value="companyFilter"
              placeholder="Company name"
              @input="$emit('update:company-filter', $event.target.value)"
              @keyup.enter="$emit('apply-filters')"
            />
          </label>

          <label class="rq-field">
            <span>Role</span>
            <input
              type="text"
              :value="roleFilter"
              placeholder="Job title"
              @input="$emit('update:role-filter', $event.target.value)"
              @keyup.enter="$emit('apply-filters')"
            />
          </label>

          <label class="rq-field">
            <span>Skills</span>
            <input
              type="text"
              :value="skillsFilter"
              placeholder="React, Python"
              @input="$emit('update:skills-filter', $event.target.value)"
              @keyup.enter="$emit('apply-filters')"
            />
          </label>

          <label class="rq-check-field">
            <input
              type="checkbox"
              :checked="includeExpired"
              @change="$emit('update:include-expired', $event.target.checked)"
            />
            <span>Include expired</span>
          </label>

          <button class="rq-ghost" type="button" @click="$emit('apply-filters')">
            Apply
          </button>
        </div>

        <p v-if="errorMessage" class="rq-error-text" role="alert" aria-live="assertive">{{ errorMessage }}</p>

        <div class="rq-table-wrap" :aria-busy="isLoading ? 'true' : 'false'" aria-live="polite">
          <table class="rq-table">
            <caption class="rq-sr-only">Available placement drives and apply actions</caption>
            <thead>
              <tr>
                <th scope="col">Role</th>
                <th scope="col">Company</th>
                <th scope="col">Eligibility</th>
                <th scope="col">Package</th>
                <th scope="col">Deadline</th>
                <th scope="col">State</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isLoading">
                <td colspan="7" class="rq-empty-row">Loading drives...</td>
              </tr>

              <tr v-else-if="!drives.length">
                <td colspan="7" class="rq-empty-row">No drives found for this filter.</td>
              </tr>

              <tr v-for="row in drives" :key="row.drive_id">
                <td>
                  <p class="rq-row-title">{{ row.job_title || 'Role unavailable' }}</p>
                  <p class="rq-row-sub">{{ row.job_location || '-' }}</p>
                </td>
                <td>
                  <p class="rq-row-title">{{ row.company?.name || '-' }}</p>
                  <p class="rq-row-sub">{{ row.company?.industry || '-' }}</p>
                </td>
                <td>
                  <span class="rq-status-pill" :class="eligibilityClass(row)">
                    {{ eligibilityLabel(row) }}
                  </span>
                  <p v-if="!row.is_eligible && row.ineligibility_reasons?.length" class="rq-inline-note">
                    {{ row.ineligibility_reasons.join('; ') }}
                  </p>
                </td>
                <td>{{ formatSalary(row.salary_lpa) }}</td>
                <td>{{ formatDate(row.application_deadline) }}</td>
                <td>
                  <span class="rq-status-pill" :class="driveStateClass(row)">
                    {{ driveStateLabel(row) }}
                  </span>
                </td>
                <td>
                  <div class="rq-inline-actions">
                    <button
                      class="rq-ghost"
                      type="button"
                      :aria-label="`Open details for ${row.job_title || 'drive'}`"
                      @click.stop="$emit('open-drive', row)"
                    >
                      Open
                    </button>
                    <button
                      v-if="canApply(row)"
                      class="rq-btn-primary"
                      type="button"
                      :disabled="isApplying[row.drive_id]"
                      :aria-label="`Apply for ${row.job_title || 'drive'}`"
                      @click.stop="$emit('apply-drive', row.drive_id)"
                    >
                      {{ isApplying[row.drive_id] ? 'Applying...' : 'Apply Now' }}
                    </button>
                    <span v-else class="rq-offer-state">{{ blockedActionLabel(row) }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="rq-mobile-list" :aria-busy="isLoading ? 'true' : 'false'" aria-live="polite">
          <article v-if="isLoading" class="rq-mobile-empty">
            Loading drives...
          </article>

          <article v-else-if="!drives.length" class="rq-mobile-empty">
            No drives found for this filter.
          </article>

          <details
            v-for="row in drives"
            :key="`mobile-${row.drive_id}`"
            class="rq-mobile-item"
          >
            <summary class="rq-mobile-summary">
              <div class="rq-mobile-head">
                <p class="rq-mobile-title">{{ row.job_title || 'Role unavailable' }}</p>
                <p class="rq-mobile-sub">{{ row.company?.name || '-' }}</p>
              </div>

              <div class="rq-mobile-primary">
                <span class="rq-status-pill" :class="driveStateClass(row)">
                  {{ driveStateLabel(row) }}
                </span>

                <button
                  class="rq-ghost rq-btn-primary-compact"
                  type="button"
                  :aria-label="`Open details for ${row.job_title || 'drive'}`"
                  @click.stop.prevent="$emit('open-drive', row)"
                >
                  Open
                </button>

                <button
                  v-if="canApply(row)"
                  class="rq-btn-primary rq-btn-primary-compact"
                  type="button"
                  :disabled="isApplying[row.drive_id]"
                  :aria-label="`Apply for ${row.job_title || 'drive'}`"
                  @click.stop.prevent="$emit('apply-drive', row.drive_id)"
                >
                  {{ isApplying[row.drive_id] ? 'Applying...' : 'Apply' }}
                </button>
                <span v-else class="rq-offer-state">{{ blockedActionLabel(row) }}</span>
              </div>
            </summary>

            <div class="rq-mobile-meta">
              <p class="rq-row-sub">Location: {{ row.job_location || '-' }}</p>
              <p class="rq-row-sub">Package: {{ formatSalary(row.salary_lpa) }}</p>
              <p class="rq-row-sub">Deadline: {{ formatDate(row.application_deadline) }}</p>
              <div>
                <span class="rq-status-pill" :class="eligibilityClass(row)">
                  {{ eligibilityLabel(row) }}
                </span>
                <p
                  v-if="!row.is_eligible && row.ineligibility_reasons?.length"
                  class="rq-inline-note"
                >
                  {{ row.ineligibility_reasons.join('; ') }}
                </p>
              </div>
            </div>
          </details>
        </div>

        <footer class="rq-panel-footer" v-if="pagination.pages > 1">
          <button
            class="rq-ghost"
            type="button"
            :disabled="pagination.page <= 1 || isLoading"
            @click="$emit('page-change', pagination.page - 1)"
          >
            Previous
          </button>
          <span>Page {{ pagination.page }} of {{ pagination.pages }}</span>
          <button
            class="rq-ghost"
            type="button"
            :disabled="pagination.page >= pagination.pages || isLoading"
            @click="$emit('page-change', pagination.page + 1)"
          >
            Next
          </button>
        </footer>
      </div>
    </article>
  </section>
</template>

<script>
export default {
  name: 'StudentDrivesView',
  props: {
    drives: {
      type: Array,
      default: () => []
    },
    pagination: {
      type: Object,
      default: () => ({ page: 1, pages: 0 })
    },
    queryText: {
      type: String,
      default: ''
    },
    companyFilter: {
      type: String,
      default: ''
    },
    roleFilter: {
      type: String,
      default: ''
    },
    skillsFilter: {
      type: String,
      default: ''
    },
    includeExpired: {
      type: Boolean,
      default: false
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    errorMessage: {
      type: String,
      default: ''
    },
    isApplying: {
      type: Object,
      default: () => ({})
    }
  },
  emits: [
    'update:query-text',
    'update:company-filter',
    'update:role-filter',
    'update:skills-filter',
    'update:include-expired',
    'apply-filters',
    'page-change',
    'apply-drive',
    'open-drive'
  ],
  methods: {
    canApply(row) {
      return !row.already_applied && row.is_open && row.is_eligible
    },
    blockedActionLabel(row) {
      if (row.already_applied) return 'Applied'
      if (!row.is_open) return 'Closed'
      if (!row.is_eligible) return 'Not eligible'
      return '-'
    },
    eligibilityLabel(row) {
      if (row.already_applied) return 'Submitted'
      return row.is_eligible ? 'Eligible' : 'Not eligible'
    },
    eligibilityClass(row) {
      if (row.already_applied) return 'pill-offer'
      return row.is_eligible ? 'pill-shortlisted' : 'pill-rejected'
    },
    driveStateLabel(row) {
      return row.is_open ? 'Open' : 'Closed'
    },
    driveStateClass(row) {
      return row.is_open ? 'pill-applied' : 'pill-rejected'
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
    },
    formatSalary(value) {
      const parsed = Number(value)
      if (Number.isNaN(parsed) || parsed <= 0) return '-'
      return `${parsed.toLocaleString('en-IN')} LPA`
    }
  }
}
</script>
