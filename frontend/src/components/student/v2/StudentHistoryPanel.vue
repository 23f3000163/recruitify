<template>
  <section class="rq-view">
    <article class="rq-card">
      <header class="rq-card-hd">
        <span class="rq-card-title">Placement History</span>
      </header>

      <div class="rq-card-body">
        <div class="rq-summary-grid">
          <article class="rq-summary-card">
            <p class="rq-summary-label">Total Applied</p>
            <p class="rq-summary-value">{{ Number(summary.total_applied || 0).toLocaleString() }}</p>
          </article>
          <article class="rq-summary-card">
            <p class="rq-summary-label">Offers Received</p>
            <p class="rq-summary-value">{{ Number(summary.offers_received || 0).toLocaleString() }}</p>
          </article>
          <article class="rq-summary-card">
            <p class="rq-summary-label">Placements</p>
            <p class="rq-summary-value">{{ Number(summary.placements_count || 0).toLocaleString() }}</p>
          </article>
          <article class="rq-summary-card">
            <p class="rq-summary-label">Highest Package</p>
            <p class="rq-summary-value">{{ formatPackage(summary.highest_package) }}</p>
          </article>
        </div>

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

          <button class="rq-ghost" type="button" @click="$emit('apply-filters')">
            Apply
          </button>
        </div>

        <p v-if="errorMessage" class="rq-error-text" role="alert" aria-live="assertive">{{ errorMessage }}</p>

        <div class="rq-table-wrap" :aria-busy="isLoading ? 'true' : 'false'" aria-live="polite">
          <table class="rq-table">
            <caption class="rq-sr-only">Placement history with downloadable documents</caption>
            <thead>
              <tr>
                <th scope="col">Role</th>
                <th scope="col">Company</th>
                <th scope="col">Outcome</th>
                <th scope="col">Status</th>
                <th scope="col">Updated</th>
                <th scope="col">Documents</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isLoading">
                <td colspan="6" class="rq-empty-row">Loading placement history...</td>
              </tr>

              <tr v-else-if="!historyItems.length">
                <td colspan="6" class="rq-empty-row">No history records found.</td>
              </tr>

              <tr v-for="row in historyItems" :key="row.application_id">
                <td>
                  <p class="rq-row-title">{{ row.drive?.job_title || 'Role unavailable' }}</p>
                  <p class="rq-row-sub">{{ row.drive?.job_location || '-' }}</p>
                </td>
                <td>{{ row.company?.company_name || '-' }}</td>
                <td>
                  <span class="rq-status-pill" :class="outcomeClass(row.outcome)">
                    {{ outcomeLabel(row.outcome) }}
                  </span>
                </td>
                <td>
                  <span class="rq-status-pill" :class="statusClass(row.status)">
                    {{ row.status_label || statusLabel(row.status) }}
                  </span>
                </td>
                <td>{{ formatDateTime(row.updated_at) }}</td>
                <td>
                  <div class="rq-inline-actions">
                    <button
                      v-if="row.offer?.offer_id"
                      class="rq-ghost"
                      type="button"
                      :disabled="Boolean(isDownloading[`offer-${row.offer.offer_id}`])"
                      :aria-label="`Download offer letter for ${row.drive?.job_title || 'selected role'}`"
                      @click="$emit('download-offer', row.offer.offer_id)"
                    >
                      {{ isDownloading[`offer-${row.offer.offer_id}`] ? 'Downloading...' : 'Offer Letter' }}
                    </button>

                    <button
                      v-if="row.placement?.placement_id"
                      class="rq-ghost"
                      type="button"
                      :disabled="Boolean(isDownloading[`placement-${row.placement.placement_id}`])"
                      :aria-label="`Download placement document for ${row.drive?.job_title || 'selected role'}`"
                      @click="$emit('download-placement', row.placement.placement_id)"
                    >
                      {{ isDownloading[`placement-${row.placement.placement_id}`] ? 'Downloading...' : 'Placement Doc' }}
                    </button>

                    <span v-if="!row.offer && !row.placement" class="rq-row-sub">-</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="rq-mobile-list" :aria-busy="isLoading ? 'true' : 'false'" aria-live="polite">
          <article v-if="isLoading" class="rq-mobile-empty">
            Loading placement history...
          </article>

          <article v-else-if="!historyItems.length" class="rq-mobile-empty">
            No history records found.
          </article>

          <details
            v-for="row in historyItems"
            :key="`mobile-${row.application_id}`"
            class="rq-mobile-item"
          >
            <summary class="rq-mobile-summary">
              <div class="rq-mobile-head">
                <p class="rq-mobile-title">{{ row.drive?.job_title || 'Role unavailable' }}</p>
                <p class="rq-mobile-sub">{{ row.company?.company_name || '-' }}</p>
              </div>

              <div class="rq-mobile-primary">
                <span class="rq-status-pill" :class="outcomeClass(row.outcome)">
                  {{ outcomeLabel(row.outcome) }}
                </span>

                <button
                  v-if="primaryDocument(row)"
                  class="rq-ghost"
                  type="button"
                  :disabled="isDocDownloading(primaryDocument(row))"
                  @click.stop.prevent="triggerDocumentDownload(primaryDocument(row))"
                >
                  {{ isDocDownloading(primaryDocument(row)) ? 'Downloading...' : primaryDocument(row).label }}
                </button>
              </div>
            </summary>

            <div class="rq-mobile-meta">
              <p class="rq-row-sub">Location: {{ row.drive?.job_location || '-' }}</p>
              <p class="rq-row-sub">Updated: {{ formatDateTime(row.updated_at) }}</p>

              <div>
                <span class="rq-status-pill" :class="statusClass(row.status)">
                  {{ row.status_label || statusLabel(row.status) }}
                </span>
              </div>

              <div
                v-if="row.offer?.offer_id || row.placement?.placement_id"
                class="rq-mobile-aux-actions"
              >
                <button
                  v-if="row.offer?.offer_id"
                  class="rq-ghost"
                  type="button"
                  :disabled="Boolean(isDownloading[`offer-${row.offer.offer_id}`])"
                  @click.stop.prevent="$emit('download-offer', row.offer.offer_id)"
                >
                  {{ isDownloading[`offer-${row.offer.offer_id}`] ? 'Downloading...' : 'Offer Letter' }}
                </button>

                <button
                  v-if="row.placement?.placement_id"
                  class="rq-ghost"
                  type="button"
                  :disabled="Boolean(isDownloading[`placement-${row.placement.placement_id}`])"
                  @click.stop.prevent="$emit('download-placement', row.placement.placement_id)"
                >
                  {{ isDownloading[`placement-${row.placement.placement_id}`] ? 'Downloading...' : 'Placement Doc' }}
                </button>
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
  name: 'StudentHistoryPanelV2',
  props: {
    historyItems: {
      type: Array,
      default: () => []
    },
    summary: {
      type: Object,
      default: () => ({
        total_applied: 0,
        offers_received: 0,
        placements_count: 0,
        highest_package: 0
      })
    },
    pagination: {
      type: Object,
      default: () => ({ page: 1, pages: 0 })
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
    isDownloading: {
      type: Object,
      default: () => ({})
    }
  },
  emits: [
    'update:query-text',
    'apply-filters',
    'page-change',
    'download-offer',
    'download-placement'
  ],
  methods: {
    formatPackage(value) {
      const parsed = Number(value)
      if (Number.isNaN(parsed) || parsed <= 0) {
        return '-'
      }
      return `INR ${parsed.toLocaleString('en-IN')}`
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
    },
    outcomeLabel(outcome) {
      const normalized = String(outcome || '').toLowerCase()
      const labels = {
        in_progress: 'In Progress',
        offer_released: 'Offer Released',
        placed: 'Placed',
        rejected: 'Rejected'
      }
      return labels[normalized] || (normalized ? normalized : 'In Progress')
    },
    outcomeClass(outcome) {
      const normalized = String(outcome || '').toLowerCase()
      if (normalized === 'placed') return 'pill-shortlisted'
      if (normalized === 'offer_released') return 'pill-offer'
      if (normalized === 'rejected') return 'pill-rejected'
      return 'pill-applied'
    },
    primaryDocument(row) {
      if (row?.placement?.placement_id) {
        return {
          type: 'placement',
          id: row.placement.placement_id,
          key: `placement-${row.placement.placement_id}`,
          label: 'Placement Doc'
        }
      }
      if (row?.offer?.offer_id) {
        return {
          type: 'offer',
          id: row.offer.offer_id,
          key: `offer-${row.offer.offer_id}`,
          label: 'Offer Letter'
        }
      }
      return null
    },
    isDocDownloading(document) {
      return Boolean(document && this.isDownloading[document.key])
    },
    triggerDocumentDownload(document) {
      if (!document) {
        return
      }
      if (document.type === 'offer') {
        this.$emit('download-offer', document.id)
        return
      }
      this.$emit('download-placement', document.id)
    }
  }
}
</script>
