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

        <div class="rq-drive-catalog" :aria-busy="isLoading ? 'true' : 'false'" aria-live="polite">
          <article v-if="isLoading" class="rq-mobile-empty">
            Loading drives...
          </article>

          <article v-else-if="!drives.length" class="rq-mobile-empty">
            No drives found for this filter.
          </article>

          <article v-for="row in drives" :key="row.drive_id" class="rq-drive-catalog-card">
            <div class="rq-drive-catalog-left">
              <div class="rq-drive-catalog-avatar" :style="avatarStyle(row)">
                {{ companyInitials(row) }}
              </div>

              <div class="rq-drive-catalog-body">
                <p class="rq-row-title">{{ row.job_title || 'Role unavailable' }}</p>

                <div class="rq-drive-catalog-company-row">
                  <p class="rq-row-sub">{{ row.company?.name || '-' }}</p>
                  <span class="rq-status-pill" :class="driveStateClass(row)">
                    {{ driveStateLabel(row) }}
                  </span>
                </div>

                <div class="rq-drive-meta">
                  <span v-for="chip in driveChips(row)" :key="`${row.drive_id}-${chip.key}`" class="rq-drive-chip">
                    <span class="rq-drive-chip-icon" aria-hidden="true">{{ chip.icon }}</span>
                    {{ chip.label }}
                  </span>
                </div>

                <p v-if="!row.is_eligible && row.ineligibility_reasons?.length" class="rq-inline-note">
                  {{ row.ineligibility_reasons.join('; ') }}
                </p>
              </div>
            </div>

            <div class="rq-drive-catalog-actions">
              <button
                class="rq-btn-primary rq-drive-catalog-apply"
                :class="applyButtonClass(row)"
                type="button"
                :disabled="isApplyDisabled(row)"
                :aria-label="`${applyButtonLabel(row)} for ${row.job_title || 'drive'}`"
                @click.stop="$emit('open-drive', row)"
              >
                {{ applyButtonLabel(row) }}
              </button>
            </div>
          </article>
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
    companyInitials(row) {
      const company = String(row?.company?.name || '').trim()
      if (!company) return 'D'

      const chunks = company.split(/\s+/).filter(Boolean)
      if (chunks.length === 1) {
        return chunks[0].slice(0, 1).toUpperCase()
      }

      return `${chunks[0][0] || ''}${chunks[1][0] || ''}`.toUpperCase()
    },
    avatarStyle(row) {
      const palette = ['#2563EB', '#059669', '#D97706', '#EF4444', '#7C3AED']
      const seed = Number(row?.drive_id || 0)
      return { background: palette[Math.abs(seed) % palette.length] }
    },
    driveChips(row) {
      const chips = [
        { key: 'salary', icon: '💰', label: this.formatSalary(row.salary_lpa) },
        { key: 'branch', icon: '🎓', label: this.formatBranches(row.eligible_branches) },
        { key: 'cgpa', icon: '📊', label: this.formatCgpa(row.min_cgpa) },
        { key: 'year', icon: '📚', label: this.formatYears(row.eligible_years) },
        { key: 'skills', icon: '🛠️', label: this.formatRequiredSkills(row.required_skills || row.requiredSkills) },
        { key: 'deadline', icon: '📅', label: this.formatShortDate(row.application_deadline) }
      ]

      const seatCount = Number(row?.openings || row?.total_openings || row?.seats || row?.vacancies || 0)
      if (!Number.isNaN(seatCount) && seatCount > 0) {
        chips.push({ key: 'seats', icon: '👥', label: `${seatCount} seats` })
      }

      return chips.filter((chip) => String(chip.label || '').trim() && chip.label !== '-')
    },
    applyButtonLabel(row) {
      if (this.isApplying[row.drive_id]) return 'Applying...'
      if (row.already_applied) return 'Applied'
      if (!row.is_open) return 'Closed'
      if (!row.is_eligible) return 'Not eligible'
      return 'Apply Now'
    },
    applyButtonClass(row) {
      if (row.already_applied) return 'is-applied'
      if (!row.is_open || !row.is_eligible) return 'is-disabled'
      return ''
    },
    isApplyDisabled(row) {
      return Boolean(this.isApplying[row.drive_id] || row.already_applied || !row.is_open || !row.is_eligible)
    },
    driveStateLabel(row) {
      return row.is_open ? 'Open' : 'Closed'
    },
    driveStateClass(row) {
      return row.is_open ? 'pill-shortlisted' : 'pill-rejected'
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
    },
    formatShortDate(value) {
      if (!value) return '-'
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return '-'
      return parsed.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric'
      })
    },
    formatBranches(value) {
      const list = Array.isArray(value)
        ? value.map((item) => String(item || '').trim()).filter(Boolean)
        : []
      if (list.length) {
        return list.length > 2 ? `${list.slice(0, 2).join(', ')}` : list.join(', ')
      }
      return '-'
    },
    formatCgpa(value) {
      const minCgpa = Number(value)
      if (Number.isNaN(minCgpa) || minCgpa <= 0) return '-'
      return `CGPA ${minCgpa}+`
    },
    formatYears(value) {
      const list = Array.isArray(value)
        ? value.map((item) => Number(item)).filter((item) => Number.isInteger(item) && item > 0)
        : []
      if (!list.length) return '-'
      return `Year ${list.join(', ')}`
    },
    formatRequiredSkills(value) {
      const entries = Array.isArray(value)
        ? value
        : String(value || '').split(',')

      const normalized = [...new Set(entries
        .map((item) => String(item || '').trim())
        .filter(Boolean))]

      if (!normalized.length) {
        return 'Skills -'
      }

      if (normalized.length <= 2) {
        return normalized.join(', ')
      }

      return `${normalized.slice(0, 2).join(', ')} +${normalized.length - 2}`
    }
  }
}
</script>
