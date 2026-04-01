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
                <th scope="col">Updated</th>
                <th scope="col">Offer Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isLoading">
                <td colspan="5" class="rq-empty-row">Loading applications...</td>
              </tr>

              <tr v-else-if="!applications.length">
                <td colspan="5" class="rq-empty-row">No applications found for this filter.</td>
              </tr>

              <tr v-for="row in applications" :key="row.application_id">
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
                <td>{{ formatDateTime(row.updated_at) }}</td>
                <td>
                  <div v-if="canRespondToOffer(row.offer)" class="rq-inline-actions">
                    <button
                      class="rq-ghost"
                      type="button"
                      :disabled="isResponding[row.offer.offer_id]"
                      :aria-label="`Accept offer for ${row.drive?.title || 'selected role'}`"
                      @click="$emit('respond-offer', row.offer.offer_id, 'accepted')"
                    >
                      {{ isResponding[row.offer.offer_id] ? 'Saving...' : 'Accept' }}
                    </button>
                    <button
                      class="rq-ghost rq-ghost-danger"
                      type="button"
                      :disabled="isResponding[row.offer.offer_id]"
                      :aria-label="`Reject offer for ${row.drive?.title || 'selected role'}`"
                      @click="$emit('respond-offer', row.offer.offer_id, 'rejected')"
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
  name: 'StudentApplicationsPanelV2',
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
    }
  },
  emits: [
    'update:status-filter',
    'update:query-text',
    'apply-filters',
    'page-change',
    'respond-offer'
  ],
  methods: {
    canRespondToOffer(offer) {
      return String(offer?.status || '').toLowerCase() === 'offered'
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
