<template>
  <section class="rq-view">
    <article class="rq-card">
      <header class="rq-card-hd">
        <span class="rq-card-title">My Applications</span>
      </header>

      <div class="rq-card-body">
        <div class="rq-panel-tools">
          <label class="rq-field">
            <span>Status</span>
            <select :value="statusFilter" @change="$emit('update:status-filter', $event.target.value)">
              <option value="all">All</option>
              <option value="applied">Applied</option>
              <option value="shortlisted">Shortlisted</option>
              <option value="interviewed">Interviewed</option>
              <option value="selected">Selected</option>
              <option value="waitlisted">Waitlisted</option>
              <option value="rejected">Rejected</option>
            </select>
          </label>

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

          <button class="rq-ghost" type="button" @click="$emit('apply-filters')">
            Apply
          </button>
        </div>

        <p v-if="errorMessage" class="rq-error-text" role="alert" aria-live="assertive">{{ errorMessage }}</p>

        <div class="rq-table-wrap" :aria-busy="isLoading ? 'true' : 'false'" aria-live="polite">
          <table class="rq-table rq-applications-table">
            <caption class="rq-sr-only">Student applications with offer response actions</caption>
            <thead>
              <tr>
                <th scope="col">Company / Role</th>
                <th scope="col">Applied On</th>
                <th scope="col">Package</th>
                <th scope="col">Type</th>
                <th scope="col">Status</th>
                <th scope="col">Next Step</th>
                <th scope="col">Details</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isLoading">
                <td colspan="7" class="rq-empty-row">Loading applications...</td>
              </tr>

              <tr v-else-if="!applications.length">
                <td colspan="7" class="rq-empty-row">No applications found for this filter.</td>
              </tr>

              <tr v-for="row in applications" :key="row.application_id">
                <td>
                  <div class="rq-app-role-cell">
                    <div class="rq-app-avatar" :style="avatarStyle(row)">{{ companyInitials(row) }}</div>
                    <div class="rq-app-role-copy">
                      <p class="rq-row-title">{{ roleTitle(row) }}</p>
                      <p class="rq-row-sub">{{ companyName(row) }}</p>
                    </div>
                  </div>
                </td>
                <td>{{ formatShortDate(row.application_date || row.applied_at || row.updated_at) }}</td>
                <td>
                  <span class="rq-app-package">{{ packageLabel(row) }}</span>
                </td>
                <td>
                  <span class="rq-status-pill rq-pill-neutral">{{ jobTypeLabel(row) }}</span>
                </td>
                <td>
                  <span class="rq-status-pill" :class="statusClass(row.status)">
                    {{ row.status_label || statusLabel(row.status) }}
                  </span>
                  <p v-if="row.notes" class="rq-inline-note">Note: {{ row.notes }}</p>
                  <p v-if="row.rejection_reason" class="rq-inline-note">Reason: {{ row.rejection_reason }}</p>
                </td>
                <td>
                  <span class="rq-app-next-step" :class="{ 'is-highlight': isNextStepHighlighted(row) }">
                    {{ nextStepLabel(row) }}
                  </span>
                </td>
                <td>
                  <button
                    class="rq-ghost rq-ghost-xs rq-app-detail-btn"
                    type="button"
                    :aria-label="`View details for ${roleTitle(row)}`"
                    @click.stop="$emit('open-application', row)"
                  >
                    View
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="rq-mobile-list" :aria-busy="isLoading ? 'true' : 'false'" aria-live="polite">
          <article v-if="isLoading" class="rq-mobile-empty">
            Loading applications...
          </article>

          <article v-else-if="!applications.length" class="rq-mobile-empty">
            No applications found for this filter.
          </article>

          <details
            v-for="row in applications"
            :key="`mobile-${row.application_id}`"
            class="rq-mobile-item"
          >
            <summary class="rq-mobile-summary">
              <div class="rq-mobile-head">
                <p class="rq-mobile-title">{{ roleTitle(row) }}</p>
                <p class="rq-mobile-sub">{{ companyName(row) }}</p>
              </div>

              <div class="rq-mobile-primary">
                <span class="rq-status-pill" :class="statusClass(row.status)">
                  {{ row.status_label || statusLabel(row.status) }}
                </span>

                <button
                  class="rq-ghost rq-ghost-xs"
                  type="button"
                  :aria-label="`View details for ${roleTitle(row)}`"
                  @click.stop.prevent="$emit('open-application', row)"
                >
                  View
                </button>
              </div>
            </summary>

            <div class="rq-mobile-meta">
              <p class="rq-row-sub">Applied On: {{ formatShortDate(row.application_date || row.applied_at || row.updated_at) }}</p>
              <p class="rq-row-sub">Package: {{ packageLabel(row) }}</p>
              <p class="rq-row-sub">Type: {{ jobTypeLabel(row) }}</p>
              <p class="rq-row-sub">Next Step: {{ nextStepLabel(row) }}</p>

              <div>
                <p v-if="row.notes" class="rq-inline-note">Note: {{ row.notes }}</p>
                <p v-if="row.rejection_reason" class="rq-inline-note">Reason: {{ row.rejection_reason }}</p>
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
  name: 'StudentApplicationsView',
  props: {
    applications: {
      type: Array,
      default: () => []
    },
    pagination: {
      type: Object,
      default: () => ({ page: 1, pages: 0 })
    },
    statusFilter: {
      type: String,
      default: 'all'
    },
    queryText: {
      type: String,
      default: ''
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    errorMessage: {
      type: String,
      default: ''
    },
    isResponding: {
      type: Object,
      default: () => ({})
    },
    isScoring: {
      type: Object,
      default: () => ({})
    }
  },
  emits: [
    'update:status-filter',
    'update:query-text',
    'apply-filters',
    'page-change',
    'respond-offer',
    'open-application',
    'score-application'
  ],
  methods: {
    roleTitle(row) {
      return row?.drive?.title || row?.drive?.job_title || 'Role unavailable'
    },
    companyName(row) {
      return row?.company?.name || row?.company?.company_name || '-'
    },
    companyInitials(row) {
      const company = String(this.companyName(row) || '').trim()
      if (!company || company === '-') return 'CO'

      const chunks = company.split(/\s+/).filter(Boolean)
      if (chunks.length === 1) {
        return (chunks[0][0] || 'C').toUpperCase()
      }
      return `${chunks[0][0] || ''}${chunks[1][0] || ''}`.toUpperCase()
    },
    avatarStyle(row) {
      const palette = [
        ['#0284C7', '#38BDF8'],
        ['#2563EB', '#60A5FA'],
        ['#4338CA', '#818CF8'],
        ['#0F766E', '#2DD4BF'],
        ['#B45309', '#F59E0B']
      ]
      const seed = Number(row?.application_id || row?.id || 0)
      const [base, edge] = palette[Math.abs(seed) % palette.length]
      return {
        background: `linear-gradient(145deg, ${base}, ${edge})`
      }
    },
    formatDateTime(value) {
      if (!value) return '-'
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return '-'
      return parsed.toLocaleString()
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
    formatTime(value) {
      if (!value) return ''
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return ''
      return parsed.toLocaleTimeString('en-IN', {
        hour: 'numeric',
        minute: '2-digit'
      })
    },
    packageLabel(row) {
      const driveSalary = Number(row?.drive?.salary_lpa || row?.salary_lpa || 0)
      if (!Number.isNaN(driveSalary) && driveSalary > 0) {
        return `₹${driveSalary.toLocaleString('en-IN')} LPA`
      }

      const offerSalary = Number(row?.offer?.salary || 0)
      if (!Number.isNaN(offerSalary) && offerSalary > 0) {
        const lpa = offerSalary / 100000
        const normalized = Number.isInteger(lpa)
          ? lpa.toLocaleString('en-IN')
          : lpa.toLocaleString('en-IN', { maximumFractionDigits: 1 })
        return `₹${normalized} LPA`
      }

      return '-'
    },
    jobTypeLabel(row) {
      return (
        row?.drive?.job_type ||
        row?.drive?.type ||
        row?.drive?.employment_type ||
        row?.job_type ||
        'Full-time'
      )
    },
    nextStepLabel(row) {
      const status = String(row?.status || '').toLowerCase()

      if (status === 'interviewed' || status === 'interview') {
        const interviewAt = row?.latest_interview?.interview_date
        const dateLabel = this.formatShortDate(interviewAt)
        const timeLabel = this.formatTime(interviewAt)
        if (dateLabel !== '-') {
          return timeLabel ? `${dateLabel} ${timeLabel}` : dateLabel
        }
        return 'Interview update pending'
      }

      if (status === 'shortlisted') {
        return 'Awaiting interview date'
      }

      if (status === 'selected' || status === 'offered') {
        const joiningDate = this.formatShortDate(row?.offer?.joining_date)
        if (joiningDate !== '-') {
          return `Accept by ${joiningDate}`
        }
        return 'Awaiting response'
      }

      if (status === 'rejected') {
        return '-'
      }

      return 'Awaiting shortlist'
    },
    isNextStepHighlighted(row) {
      const status = String(row?.status || '').toLowerCase()
      return status === 'interviewed' || status === 'interview'
    },
    statusLabel(status) {
      const normalized = String(status || '').toLowerCase()
      const labels = {
        applied: 'Applied',
        shortlisted: 'Shortlisted',
        interviewed: 'Interviewed',
        selected: 'Selected',
        waitlisted: 'Waitlisted',
        rejected: 'Rejected',
        offered: 'Offer Released',
        accepted: 'Offer Accepted'
      }
      return labels[normalized] || (normalized ? normalized : 'Updated')
    },
    statusClass(status) {
      const normalized = String(status || '').toLowerCase()
      if (normalized === 'shortlisted' || normalized === 'selected' || normalized === 'accepted') {
        return 'pill-shortlisted'
      }
      if (normalized === 'interviewed') return 'pill-interview'
      if (normalized === 'rejected') return 'pill-rejected'
      if (normalized === 'offered') return 'pill-offer'
      return 'pill-applied'
    }
  }
}
</script>
