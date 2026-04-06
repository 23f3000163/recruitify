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
          <table class="rq-table">
            <caption class="rq-sr-only">Student applications with offer response actions</caption>
            <thead>
              <tr>
                <th scope="col">Role</th>
                <th scope="col">Company</th>
                <th scope="col">Status</th>
                <th scope="col">Interview</th>
                <th scope="col">Updated</th>
                <th scope="col">ATS Match</th>
                <th scope="col">Offer Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isLoading">
                <td colspan="7" class="rq-empty-row">Loading applications...</td>
              </tr>

              <tr v-else-if="!applications.length">
                <td colspan="7" class="rq-empty-row">No applications found for this filter.</td>
              </tr>

              <tr v-for="row in applications" :key="row.application_id" @click="$emit('open-application', row)">
                <td>
                  <p class="rq-row-title">{{ row.drive?.title || 'Role unavailable' }}</p>
                  <p class="rq-row-sub">{{ row.drive?.location || '-' }}</p>
                </td>
                <td>{{ row.company?.name || '-' }}</td>
                <td>
                  <span class="rq-status-pill" :class="statusClass(row.status)">
                    {{ row.status_label || statusLabel(row.status) }}
                  </span>
                  <p v-if="row.notes" class="rq-inline-note">Note: {{ row.notes }}</p>
                  <p v-if="row.rejection_reason" class="rq-inline-note">Reason: {{ row.rejection_reason }}</p>
                </td>
                <td>
                  <div v-if="row.latest_interview" class="rq-interview-cell">
                    <p class="rq-row-title">{{ formatDateTime(row.latest_interview.interview_date) }}</p>
                    <p class="rq-row-sub">
                      {{ interviewModeLabel(row.latest_interview.interview_mode) }}
                      <template v-if="row.latest_interview.interviewer_name">
                        • {{ row.latest_interview.interviewer_name }}
                      </template>
                    </p>
                    <p
                      v-if="row.latest_interview.feedback"
                      class="rq-inline-note"
                    >
                      Feedback: {{ row.latest_interview.feedback }}
                    </p>
                    <span
                      class="rq-status-pill"
                      :class="interviewResultClass(row.latest_interview.result)"
                    >
                      {{ interviewResultLabel(row.latest_interview.result) }}
                    </span>
                  </div>
                  <span v-else class="rq-row-sub">Not scheduled</span>
                </td>
                <td>{{ formatDateTime(row.updated_at) }}</td>
                <td>
                  <button
                    class="rq-ghost rq-ghost-xs"
                    type="button"
                    :disabled="isScoring[row.application_id]"
                    :aria-label="`Run ATS match for ${row.drive?.title || 'this role'}`"
                    @click.stop="$emit('score-application', row)"
                  >
                    {{ isScoring[row.application_id] ? 'Scoring...' : 'Check Match' }}
                  </button>
                </td>
                <td>
                  <div v-if="canRespondToOffer(row.offer)" class="rq-inline-actions">
                    <button
                      class="rq-ghost"
                      type="button"
                      :disabled="isResponding[row.offer.offer_id]"
                      :aria-label="`Accept offer for ${row.drive?.title || 'selected role'}`"
                      @click.stop="$emit('respond-offer', row.offer.offer_id, 'accepted')"
                    >
                      {{ isResponding[row.offer.offer_id] ? 'Saving...' : 'Accept' }}
                    </button>
                    <button
                      class="rq-ghost rq-ghost-danger"
                      type="button"
                      :disabled="isResponding[row.offer.offer_id]"
                      :aria-label="`Reject offer for ${row.drive?.title || 'selected role'}`"
                      @click.stop="$emit('respond-offer', row.offer.offer_id, 'rejected')"
                    >
                      {{ isResponding[row.offer.offer_id] ? 'Saving...' : 'Reject' }}
                    </button>
                  </div>
                  <span v-else-if="row.offer" class="rq-offer-state">
                    {{ statusLabel(row.offer.status) }}
                  </span>
                  <span v-else class="rq-row-sub">-</span>
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
                <p class="rq-mobile-title">{{ row.drive?.title || 'Role unavailable' }}</p>
                <p class="rq-mobile-sub">{{ row.company?.name || '-' }}</p>
              </div>

              <div class="rq-mobile-primary">
                <span class="rq-status-pill" :class="statusClass(row.status)">
                  {{ row.status_label || statusLabel(row.status) }}
                </span>

                <button
                  class="rq-ghost rq-ghost-xs"
                  type="button"
                  :disabled="isScoring[row.application_id]"
                  :aria-label="`Run ATS match for ${row.drive?.title || 'this role'}`"
                  @click.stop.prevent="$emit('score-application', row)"
                >
                  {{ isScoring[row.application_id] ? 'Scoring...' : 'Check Match' }}
                </button>

                <button
                  v-if="canRespondToOffer(row.offer)"
                  class="rq-btn-primary rq-btn-primary-compact"
                  type="button"
                  :disabled="isResponding[row.offer.offer_id]"
                  :aria-label="`Accept offer for ${row.drive?.title || 'selected role'}`"
                  @click.stop.prevent="$emit('respond-offer', row.offer.offer_id, 'accepted')"
                >
                  {{ isResponding[row.offer.offer_id] ? 'Saving...' : 'Accept' }}
                </button>
              </div>
            </summary>

            <div class="rq-mobile-meta">
              <p class="rq-row-sub">Location: {{ row.drive?.location || '-' }}</p>
              <p class="rq-row-sub">Updated: {{ formatDateTime(row.updated_at) }}</p>

              <div>
                <p v-if="row.notes" class="rq-inline-note">Note: {{ row.notes }}</p>
                <p v-if="row.rejection_reason" class="rq-inline-note">Reason: {{ row.rejection_reason }}</p>
              </div>

              <div v-if="row.latest_interview" class="rq-interview-cell">
                <p class="rq-row-title">{{ formatDateTime(row.latest_interview.interview_date) }}</p>
                <p class="rq-row-sub">
                  {{ interviewModeLabel(row.latest_interview.interview_mode) }}
                  <template v-if="row.latest_interview.interviewer_name">
                    • {{ row.latest_interview.interviewer_name }}
                  </template>
                </p>
                <p v-if="row.latest_interview.feedback" class="rq-inline-note">
                  Feedback: {{ row.latest_interview.feedback }}
                </p>
                <span class="rq-status-pill" :class="interviewResultClass(row.latest_interview.result)">
                  {{ interviewResultLabel(row.latest_interview.result) }}
                </span>
              </div>
              <p v-else class="rq-row-sub">Interview: Not scheduled</p>

              <div
                v-if="canRespondToOffer(row.offer)"
                class="rq-mobile-aux-actions"
              >
                <button
                  class="rq-ghost rq-ghost-danger"
                  type="button"
                  :disabled="isResponding[row.offer.offer_id]"
                  :aria-label="`Reject offer for ${row.drive?.title || 'selected role'}`"
                  @click.stop.prevent="$emit('respond-offer', row.offer.offer_id, 'rejected')"
                >
                  {{ isResponding[row.offer.offer_id] ? 'Saving...' : 'Reject' }}
                </button>
              </div>
              <span v-else-if="row.offer" class="rq-offer-state">
                Offer: {{ statusLabel(row.offer.status) }}
              </span>
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
    canRespondToOffer(offer) {
      return String(offer?.status || '').toLowerCase() === 'offered'
    },
    interviewModeLabel(mode) {
      const normalized = String(mode || '').toLowerCase()
      const labels = {
        online: 'Online Interview',
        offline: 'On-site Interview',
        both: 'Hybrid Interview'
      }
      return labels[normalized] || 'Interview'
    },
    interviewResultLabel(result) {
      const normalized = String(result || '').toLowerCase()
      if (!normalized || normalized === 'pending') return 'Pending'
      if (normalized === 'pass') return 'Passed'
      if (normalized === 'fail') return 'Not Selected'
      return normalized
    },
    interviewResultClass(result) {
      const normalized = String(result || '').toLowerCase()
      if (normalized === 'pass') return 'pill-shortlisted'
      if (normalized === 'fail') return 'pill-rejected'
      return 'pill-applied'
    },
    formatDateTime(value) {
      if (!value) return '-'
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return '-'
      return parsed.toLocaleString()
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
