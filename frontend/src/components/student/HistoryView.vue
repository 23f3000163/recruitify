<template>
  <section class="rq-view">
    <article class="rq-card">
      <header class="rq-card-hd">
        <span class="rq-card-title">Placement History</span>
      </header>

      <div class="rq-card-body">
        <div class="rq-summary-grid rq-history-summary-grid">
          <article class="rq-summary-card rq-history-summary-card rq-history-summary-applied">
            <p class="rq-summary-value rq-history-summary-value">{{ Number(summary.total_applied || 0).toLocaleString() }}</p>
            <p class="rq-summary-label rq-history-summary-label">Total Applied</p>
          </article>
          <article class="rq-summary-card rq-history-summary-card rq-history-summary-offers">
            <p class="rq-summary-value rq-history-summary-value">{{ Number(summary.offers_received || 0).toLocaleString() }}</p>
            <p class="rq-summary-label rq-history-summary-label">Offers Received</p>
          </article>
          <article class="rq-summary-card rq-history-summary-card rq-history-summary-placements">
            <p class="rq-summary-value rq-history-summary-value">{{ Number(summary.placements_count || 0).toLocaleString() }}</p>
            <p class="rq-summary-label rq-history-summary-label">Placements</p>
          </article>
          <article class="rq-summary-card rq-history-summary-card rq-history-summary-package">
            <p class="rq-summary-value rq-history-summary-value">{{ formatPackage(summary.highest_package) }}</p>
            <p class="rq-summary-label rq-history-summary-label">Highest Package</p>
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

          <button
            class="rq-ghost"
            type="button"
            :disabled="isHistoryExportBusy"
            @click="$emit('export-history')"
          >
            {{ historyExportButtonLabel }}
          </button>
        </div>

        <p v-if="historyExportStatus === 'completed'" class="rq-row-sub" aria-live="polite">
          Export completed and downloaded.
        </p>
        <p v-else-if="historyExportStatus === 'failed'" class="rq-error-text" aria-live="assertive">
          Export failed. Please retry.
        </p>

        <p v-if="errorMessage" class="rq-error-text" role="alert" aria-live="assertive">{{ errorMessage }}</p>

        <div class="rq-table-wrap" :aria-busy="isLoading ? 'true' : 'false'" aria-live="polite">
          <table class="rq-table rq-history-table">
            <caption class="rq-sr-only">Placement history with downloadable documents</caption>
            <thead>
              <tr>
                <th scope="col">Role</th>
                <th scope="col">Company</th>
                <th scope="col">Outcome</th>
                <th scope="col">Status</th>
                <th scope="col">Package</th>
                <th scope="col">Updated</th>
                <th scope="col">Documents</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isLoading">
                <td colspan="7" class="rq-empty-row">Loading placement history...</td>
              </tr>

              <tr v-else-if="!historyItems.length">
                <td colspan="7" class="rq-empty-row">No history records found.</td>
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
                <td class="rq-history-package-cell">{{ packageLabel(row) }}</td>
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
              <p class="rq-row-sub">Package: {{ packageLabel(row) }}</p>
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
  name: 'StudentHistoryView',
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
    },
    historyExportStatus: {
      type: String,
      default: 'idle'
    },
    isHistoryExportBusy: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'update:query-text',
    'apply-filters',
    'page-change',
    'download-offer',
    'download-placement',
    'export-history'
  ],
  computed: {
    historyExportButtonLabel() {
      const status = String(this.historyExportStatus || 'idle').toLowerCase()
      if (status === 'queued') {
        return 'Export queued...'
      }
      if (status === 'running') {
        return 'Export running...'
      }
      return 'Export CSV'
    }
  },
  methods: {
    formatPackage(value) {
      const lpa = this.normalizePackageLpa(value)
      if (!lpa) {
        return '-'
      }

      const formatted = Number.isInteger(lpa)
        ? lpa.toLocaleString('en-IN')
        : lpa.toLocaleString('en-IN', { maximumFractionDigits: 1 })

      return `₹${formatted} LPA`
    },
    normalizePackageLpa(value) {
      const parsed = Number(value)
      if (Number.isNaN(parsed) || parsed <= 0) {
        return 0
      }

      // Backend values can be annual INR or already in LPA.
      if (parsed >= 100000) {
        return parsed / 100000
      }
      return parsed
    },
    packageLabel(row) {
      const candidates = [
        row?.drive?.salary_lpa,
        row?.drive?.ctc_lpa,
        row?.drive?.package_lpa,
        row?.salary_lpa,
        row?.offer?.salary_lpa,
        row?.offer?.salary,
        row?.placement?.salary_lpa,
        row?.placement?.salary,
        row?.placement?.package_lpa
      ]

      for (const candidate of candidates) {
        const lpa = this.normalizePackageLpa(candidate)
        if (lpa > 0) {
          return this.formatPackage(candidate)
        }
      }

      return '-'
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
