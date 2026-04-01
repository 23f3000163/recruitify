<template>
  <section class="cq-module">
    <article class="cq-panel cq-module-shell">
      <header class="cq-panel-head cq-module-head">
        <div>
          <h2>Offers</h2>
          <p>Release offers and monitor acceptance outcomes from one table.</p>
        </div>

        <button
          class="cq-btn"
          type="button"
          aria-haspopup="dialog"
          :aria-expanded="showCreateModal ? 'true' : 'false'"
          aria-controls="company-offer-modal"
          @click="openCreateModal($event)"
        >
          + Release Offer
        </button>
      </header>

      <div class="cq-module-tools">
        <label class="cq-field">
          <span>Status</span>
          <select v-model="statusFilter">
            <option value="all">All</option>
            <option value="offered">Offered</option>
            <option value="accepted">Accepted</option>
            <option value="rejected">Rejected</option>
          </select>
        </label>

        <label class="cq-field">
          <span>Drive</span>
          <select v-model="driveFilter">
            <option value="all">All Drives</option>
            <option v-for="drive in driveOptions" :key="drive.id" :value="String(drive.id)">
              {{ drive.title }}
            </option>
          </select>
        </label>

        <label class="cq-field cq-drive-search">
          <span>Search</span>
          <input
            v-model.trim="queryText"
            type="text"
            placeholder="Candidate, role, or drive"
            @keyup.enter="applyFilters"
          />
        </label>

        <button class="cq-ghost-btn" type="button" @click="applyFilters">
          Apply
        </button>
      </div>

      <p v-if="errorMessage" class="cq-inline-error">{{ errorMessage }}</p>

      <div class="cq-table-wrap is-mobile-cards">
        <table class="cq-table cq-offer-table">
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Drive</th>
              <th>Position</th>
              <th>Salary</th>
              <th>Joining Date</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="7" class="cq-empty-cell">Loading offers...</td>
            </tr>

            <tr v-else-if="!offers.length">
              <td colspan="7" class="cq-empty-cell">
                No offers available for this filter.
              </td>
            </tr>

            <tr v-for="row in offers" :key="row.offer_id">
              <td data-label="Candidate">
                <p class="cq-drive-title">{{ row.student_name || 'Candidate' }}</p>
                <p class="cq-drive-sub">{{ row.student_email || '-' }}</p>
              </td>
              <td data-label="Drive">{{ row.drive_title || '-' }}</td>
              <td data-label="Position">{{ row.position || '-' }}</td>
              <td data-label="Salary">{{ formatCurrency(row.salary) }}</td>
              <td data-label="Joining Date">{{ formatDate(row.joining_date) }}</td>
              <td data-label="Status">
                <span
                  class="cq-status-pill"
                  :class="offerStatusClass(row.status)"
                  :aria-label="`Offer status ${statusLabel(row.status)}`"
                >
                  {{ statusLabel(row.status) }}
                </span>
              </td>
              <td data-label="Created">{{ formatDate(row.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="cq-drive-footer">
        <p class="cq-muted">{{ pagination.total }} offers total</p>

        <div class="cq-pager" v-if="pagination.pages > 1">
          <button
            class="cq-ghost-btn"
            type="button"
            :disabled="pagination.page <= 1 || isLoading"
            @click="loadOffers(pagination.page - 1)"
          >
            Previous
          </button>
          <span>Page {{ pagination.page }} of {{ pagination.pages }}</span>
          <button
            class="cq-ghost-btn"
            type="button"
            :disabled="pagination.page >= pagination.pages || isLoading"
            @click="loadOffers(pagination.page + 1)"
          >
            Next
          </button>
        </div>
      </footer>
    </article>

    <Transition name="cq-fade">
      <div v-if="showCreateModal" class="cq-modal-backdrop" @click.self="closeCreateModal">
        <article
          id="company-offer-modal"
          class="cq-modal cq-modal-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="company-offer-modal-title"
        >
          <header class="cq-modal-head">
            <h2 id="company-offer-modal-title">Release Offer</h2>
            <button class="cq-modal-close" type="button" aria-label="Close" @click="closeCreateModal">x</button>
          </header>

          <form class="cq-drive-form" @submit.prevent="submitCreateOffer">
            <label class="cq-field">
              <span>Application</span>
              <select v-model="offerForm.application_id" required>
                <option value="" disabled>Select application</option>
                <option v-for="option in offerCandidates" :key="option.id" :value="option.id">
                  {{ option.label }}
                </option>
              </select>
            </label>

            <div class="cq-form-grid">
              <label class="cq-field">
                <span>Salary</span>
                <input v-model.number="offerForm.salary" type="number" min="1" step="1000" required />
              </label>

              <label class="cq-field">
                <span>Joining Date</span>
                <input v-model="offerForm.joining_date" type="date" />
              </label>
            </div>

            <label class="cq-field">
              <span>Position</span>
              <input v-model.trim="offerForm.position" type="text" placeholder="Defaults to drive title if empty" />
            </label>

            <p v-if="formError" class="cq-inline-error">{{ formError }}</p>

            <div class="cq-form-actions">
              <button class="cq-ghost-btn" type="button" :disabled="isCreating" @click="closeCreateModal">
                Cancel
              </button>
              <button class="cq-btn" type="submit" :disabled="isCreating">
                {{ isCreating ? 'Releasing...' : 'Release Offer' }}
              </button>
            </div>
          </form>
        </article>
      </div>
    </Transition>
  </section>
</template>

<script>
import { nextTick } from 'vue'
import { companyApi } from '../../api/api'

const DEFAULT_OFFER_FORM = () => ({
  application_id: '',
  salary: '',
  position: '',
  joining_date: ''
})

export default {
  name: 'CompanyOffers',
  emits: ['offers-updated'],
  data() {
    return {
      isLoading: false,
      errorMessage: '',
      statusFilter: 'all',
      driveFilter: 'all',
      queryText: '',
      offers: [],
      driveOptions: [],
      pagination: {
        page: 1,
        pages: 0,
        total: 0,
        limit: 10
      },
      showCreateModal: false,
      offerCandidates: [],
      offerForm: DEFAULT_OFFER_FORM(),
      formError: '',
      isCreating: false,
      lastModalFocusTarget: null
    }
  },
  created() {
    this.loadOffers(1)
  },
  mounted() {
    document.addEventListener('keydown', this.handleGlobalKeydown)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleGlobalKeydown)
  },
  methods: {
    async loadOffers(page = 1) {
      this.isLoading = true
      this.errorMessage = ''

      try {
        const params = {
          page,
          limit: this.pagination.limit,
          status: this.statusFilter,
          q: this.queryText
        }

        if (this.driveFilter !== 'all') {
          params.drive_id = this.driveFilter
        }

        const response = await companyApi.getOffers(params)
        const data = response?.data?.data || {}

        this.offers = Array.isArray(data.items) ? data.items : []
        this.driveOptions = Array.isArray(data.drive_options) ? data.drive_options : []
        this.pagination = {
          page: Number(data.page || page),
          pages: Number(data.pages || 0),
          total: Number(data.total || 0),
          limit: Number(data.limit || this.pagination.limit)
        }
      } catch (error) {
        this.errorMessage =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load offers right now.'
      } finally {
        this.isLoading = false
      }
    },
    applyFilters() {
      this.loadOffers(1)
    },
    async openCreateModal(event) {
      this.lastModalFocusTarget = event?.currentTarget || document.activeElement || null
      this.offerForm = DEFAULT_OFFER_FORM()
      this.formError = ''
      this.showCreateModal = true

      try {
        const response = await companyApi.getApplications({
          page: 1,
          limit: 120,
          status: 'all'
        })
        const items = Array.isArray(response?.data?.data?.items) ? response.data.data.items : []

        this.offerCandidates = items
          .filter((row) => !row.has_offer && ['shortlisted', 'interviewed', 'selected'].includes(row.status))
          .map((row) => ({
            id: row.application_id,
            label: `${row.student_name || 'Candidate'} - ${row.drive_title || 'Drive'} (${this.statusLabel(row.status)})`
          }))
      } catch (error) {
        this.formError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load applications for offers.'
      }
    },
    closeCreateModal() {
      if (this.isCreating) return
      this.showCreateModal = false
      const target = this.lastModalFocusTarget
      this.lastModalFocusTarget = null
      if (target && typeof target.focus === 'function') {
        nextTick(() => target.focus())
      }
    },
    handleGlobalKeydown(event) {
      if (event.key === 'Escape' && this.showCreateModal && !this.isCreating) {
        event.preventDefault()
        this.closeCreateModal()
      }
    },
    async submitCreateOffer() {
      this.formError = ''

      if (!this.offerForm.application_id) {
        this.formError = 'Please select an application.'
        return
      }

      if (!this.offerForm.salary || Number(this.offerForm.salary) <= 0) {
        this.formError = 'Salary must be greater than zero.'
        return
      }

      this.isCreating = true
      try {
        await companyApi.createOffer({
          application_id: Number(this.offerForm.application_id),
          salary: Number(this.offerForm.salary),
          position: this.offerForm.position,
          joining_date: this.offerForm.joining_date || null
        })

        this.showCreateModal = false
        await this.loadOffers(1)
        this.$emit('offers-updated')
      } catch (error) {
        this.formError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to release offer.'
      } finally {
        this.isCreating = false
      }
    },
    formatDate(value) {
      if (!value) return '-'
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return '-'
      return parsed.toLocaleDateString()
    },
    formatCurrency(value) {
      const parsed = Number(value)
      if (Number.isNaN(parsed)) return '-'
      return parsed.toLocaleString()
    },
    statusLabel(value) {
      const source = String(value || '')
      if (!source) return 'Unknown'
      return source.charAt(0).toUpperCase() + source.slice(1)
    },
    offerStatusClass(status) {
      const normalized = String(status || '').toLowerCase()
      if (normalized === 'accepted') return 'is-accepted'
      if (normalized === 'rejected') return 'is-rejected'
      return 'is-offered'
    }
  }
}
</script>
