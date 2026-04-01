<template>
  <section class="cq-module">
    <article class="cq-panel cq-module-shell">
      <header class="cq-panel-head cq-module-head">
        <div>
          <h2>Applications</h2>
          <p>Review incoming applications and move candidates through the pipeline.</p>
        </div>
      </header>

      <div class="cq-module-tools">
        <label class="cq-field">
          <span>Status</span>
          <select v-model="statusFilter">
            <option value="all">All</option>
            <option v-for="status in statusOptions" :key="status" :value="status">
              {{ statusLabel(status) }}
            </option>
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
            placeholder="Candidate, email, or drive"
            @keyup.enter="applyFilters"
          />
        </label>

        <button class="cq-ghost-btn" type="button" @click="applyFilters">
          Apply
        </button>
      </div>

      <p v-if="errorMessage" class="cq-inline-error">{{ errorMessage }}</p>

      <div class="cq-table-wrap is-mobile-cards">
        <table class="cq-table cq-application-table">
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Drive</th>
              <th>Status</th>
              <th>Applied</th>
              <th>Updated</th>
              <th>Feedback</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="7" class="cq-empty-cell">Loading applications...</td>
            </tr>

            <tr v-else-if="!applications.length">
              <td colspan="7" class="cq-empty-cell">
                No applications found for this filter.
              </td>
            </tr>

            <tr v-for="row in applications" :key="row.application_id">
              <td data-label="Candidate">
                <p class="cq-drive-title">{{ row.student_name || 'Candidate' }}</p>
                <p class="cq-drive-sub">{{ row.student_email || '-' }}</p>
              </td>
              <td data-label="Drive">{{ row.drive_title || '-' }}</td>
              <td data-label="Status">
                <span
                  class="cq-status-pill"
                  :class="statusClass(row.status)"
                  :aria-label="`Application status ${statusLabel(row.status)}`"
                >
                  {{ statusLabel(row.status) }}
                </span>
              </td>
              <td data-label="Applied">{{ formatDate(row.application_date) }}</td>
              <td data-label="Updated">{{ formatDate(row.updated_at) }}</td>
              <td data-label="Feedback">
                <div v-if="row.notes || row.rejection_reason" class="cq-feedback-stack">
                  <p v-if="row.notes" class="cq-feedback-line">
                    <span class="cq-feedback-label">Note:</span> {{ row.notes }}
                  </p>
                  <p v-if="row.rejection_reason" class="cq-feedback-line">
                    <span class="cq-feedback-label">Reason:</span> {{ row.rejection_reason }}
                  </p>
                </div>
                <span v-else class="cq-muted">-</span>
              </td>
              <td class="cq-row-actions" data-label="Action">
                <div class="cq-inline-controls">
                  <select
                    :value="statusDraft[row.application_id] || row.status"
                    @change="setDraftStatus(row.application_id, $event.target.value)"
                  >
                    <option v-for="status in statusOptions" :key="status" :value="status">
                      {{ statusLabel(status) }}
                    </option>
                  </select>
                  <button
                    class="cq-ghost-btn"
                    type="button"
                    :disabled="isUpdating[row.application_id]"
                    @click="updateStatus(row, $event)"
                  >
                    {{ isUpdating[row.application_id] ? 'Saving...' : 'Update' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="cq-drive-footer">
        <p class="cq-muted">{{ pagination.total }} applications total</p>

        <div class="cq-pager" v-if="pagination.pages > 1">
          <button
            class="cq-ghost-btn"
            type="button"
            :disabled="pagination.page <= 1 || isLoading"
            @click="loadApplications(pagination.page - 1)"
          >
            Previous
          </button>
          <span>Page {{ pagination.page }} of {{ pagination.pages }}</span>
          <button
            class="cq-ghost-btn"
            type="button"
            :disabled="pagination.page >= pagination.pages || isLoading"
            @click="loadApplications(pagination.page + 1)"
          >
            Next
          </button>
        </div>
      </footer>
    </article>

    <Transition name="cq-fade">
      <div v-if="showFeedbackModal" class="cq-modal-backdrop" @click.self="closeFeedbackModal">
        <article
          id="company-application-feedback-modal"
          class="cq-modal cq-modal-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="company-application-feedback-modal-title"
        >
          <header class="cq-modal-head">
            <h2 id="company-application-feedback-modal-title">
              {{ feedbackForm.target_status === 'rejected' ? 'Reject Application' : 'Add Shortlist Feedback' }}
            </h2>
            <button class="cq-modal-close" type="button" aria-label="Close" @click="closeFeedbackModal">x</button>
          </header>

          <form class="cq-drive-form" @submit.prevent="submitFeedbackUpdate">
            <p class="cq-muted">
              {{ feedbackSummaryText }}
            </p>

            <label class="cq-field" v-if="feedbackForm.target_status === 'rejected'">
              <span>Rejection Reason</span>
              <textarea
                v-model="feedbackForm.rejection_reason"
                rows="3"
                maxlength="300"
                placeholder="Share a clear reason for rejection"
                required
              ></textarea>
            </label>

            <label class="cq-field">
              <span>Feedback Note (Optional)</span>
              <textarea
                v-model="feedbackForm.notes"
                rows="3"
                maxlength="500"
                placeholder="Helpful context for this status update"
              ></textarea>
            </label>

            <p v-if="feedbackError" class="cq-inline-error">{{ feedbackError }}</p>

            <div class="cq-form-actions">
              <button class="cq-ghost-btn" type="button" :disabled="isSubmittingFeedback" @click="closeFeedbackModal">
                Cancel
              </button>
              <button class="cq-btn" type="submit" :disabled="isSubmittingFeedback">
                {{ isSubmittingFeedback ? 'Saving...' : 'Save Update' }}
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

const FEEDBACK_MODAL_STATUSES = new Set(['shortlisted', 'rejected'])
const MAX_NOTES_LENGTH = 500
const MAX_REJECTION_REASON_LENGTH = 300

const DEFAULT_FEEDBACK_FORM = () => ({
  application_id: null,
  target_status: '',
  student_name: '',
  drive_title: '',
  notes: '',
  rejection_reason: ''
})

export default {
  name: 'CompanyApplications',
  emits: ['applications-updated'],
  data() {
    return {
      isLoading: false,
      errorMessage: '',
      statusFilter: 'all',
      driveFilter: 'all',
      queryText: '',
      applications: [],
      driveOptions: [],
      statusDraft: {},
      isUpdating: {},
      showFeedbackModal: false,
      feedbackForm: DEFAULT_FEEDBACK_FORM(),
      feedbackError: '',
      isSubmittingFeedback: false,
      lastModalFocusTarget: null,
      pagination: {
        page: 1,
        pages: 0,
        total: 0,
        limit: 10
      }
    }
  },
  computed: {
    statusOptions() {
      return ['applied', 'shortlisted', 'interviewed', 'selected', 'waitlisted', 'rejected']
    },
    feedbackSummaryText() {
      const studentName = this.feedbackForm.student_name || 'candidate'
      const driveTitle = this.feedbackForm.drive_title || 'this drive'
      const statusText = this.statusLabel(this.feedbackForm.target_status).toLowerCase()

      return `Updating ${studentName} for ${driveTitle} to ${statusText}.`
    }
  },
  created() {
    this.loadApplications(1)
  },
  mounted() {
    document.addEventListener('keydown', this.handleGlobalKeydown)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleGlobalKeydown)
  },
  methods: {
    async loadApplications(page = 1) {
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

        const response = await companyApi.getApplications(params)
        const data = response?.data?.data || {}

        this.applications = Array.isArray(data.items) ? data.items : []
        this.driveOptions = Array.isArray(data.drive_options) ? data.drive_options : []
        this.pagination = {
          page: Number(data.page || page),
          pages: Number(data.pages || 0),
          total: Number(data.total || 0),
          limit: Number(data.limit || this.pagination.limit)
        }

        const nextDraft = {}
        this.applications.forEach((row) => {
          nextDraft[row.application_id] = row.status
        })
        this.statusDraft = nextDraft
      } catch (error) {
        this.errorMessage =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load applications right now.'
      } finally {
        this.isLoading = false
      }
    },
    applyFilters() {
      this.loadApplications(1)
    },
    setDraftStatus(applicationId, status) {
      this.statusDraft = {
        ...this.statusDraft,
        [applicationId]: status
      }
    },
    requiresFeedbackModal(status) {
      return FEEDBACK_MODAL_STATUSES.has(String(status || '').toLowerCase())
    },
    openFeedbackModal(row, targetStatus, event) {
      this.lastModalFocusTarget = event?.currentTarget || document.activeElement || null
      this.feedbackError = ''
      this.feedbackForm = {
        application_id: row.application_id,
        target_status: targetStatus,
        student_name: row.student_name || 'Candidate',
        drive_title: row.drive_title || 'Drive',
        notes: row.notes || '',
        rejection_reason: targetStatus === 'rejected' ? row.rejection_reason || '' : ''
      }
      this.showFeedbackModal = true
    },
    closeFeedbackModal(force = false) {
      if (this.isSubmittingFeedback && !force) {
        return
      }

      this.showFeedbackModal = false
      this.feedbackError = ''
      this.feedbackForm = DEFAULT_FEEDBACK_FORM()

      const target = this.lastModalFocusTarget
      this.lastModalFocusTarget = null
      if (target && typeof target.focus === 'function') {
        nextTick(() => target.focus())
      }
    },
    handleGlobalKeydown(event) {
      if (event.key === 'Escape' && this.showFeedbackModal && !this.isSubmittingFeedback) {
        event.preventDefault()
        this.closeFeedbackModal()
      }
    },
    async persistStatusUpdate(applicationId, targetStatus, extraPayload = {}) {
      this.isUpdating = {
        ...this.isUpdating,
        [applicationId]: true
      }

      try {
        await companyApi.updateApplicationStatus(applicationId, {
          status: targetStatus,
          ...extraPayload
        })
        await this.loadApplications(this.pagination.page || 1)
        this.$emit('applications-updated')
        return true
      } catch (error) {
        this.errorMessage =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to update application status.'
        return false
      } finally {
        this.isUpdating = {
          ...this.isUpdating,
          [applicationId]: false
        }
      }
    },
    async updateStatus(row, event) {
      const targetStatus = this.statusDraft[row.application_id] || row.status
      if (targetStatus === row.status || this.isUpdating[row.application_id]) {
        return
      }

      this.errorMessage = ''

      if (this.requiresFeedbackModal(targetStatus)) {
        this.openFeedbackModal(row, targetStatus, event)
        return
      }

      await this.persistStatusUpdate(row.application_id, targetStatus)
    },
    async submitFeedbackUpdate() {
      const targetStatus = this.feedbackForm.target_status
      const applicationId = Number(this.feedbackForm.application_id)

      if (!applicationId || !this.requiresFeedbackModal(targetStatus)) {
        this.feedbackError = 'Unable to submit this update. Please retry.'
        return
      }

      const notes = String(this.feedbackForm.notes || '').trim()
      const rejectionReason = String(this.feedbackForm.rejection_reason || '').trim()

      if (notes.length > MAX_NOTES_LENGTH) {
        this.feedbackError = `Feedback note cannot exceed ${MAX_NOTES_LENGTH} characters.`
        return
      }

      if (targetStatus === 'rejected') {
        if (!rejectionReason) {
          this.feedbackError = 'Rejection reason is required for rejected status.'
          return
        }

        if (rejectionReason.length > MAX_REJECTION_REASON_LENGTH) {
          this.feedbackError = `Rejection reason cannot exceed ${MAX_REJECTION_REASON_LENGTH} characters.`
          return
        }
      }

      this.feedbackError = ''
      this.isSubmittingFeedback = true

      try {
        const wasSaved = await this.persistStatusUpdate(applicationId, targetStatus, {
          notes: notes || null,
          rejection_reason: targetStatus === 'rejected' ? rejectionReason : null
        })

        if (wasSaved) {
          this.closeFeedbackModal(true)
        }
      } finally {
        this.isSubmittingFeedback = false
      }
    },
    formatDate(value) {
      if (!value) return '-'
      const dateValue = new Date(value)
      if (Number.isNaN(dateValue.getTime())) return '-'
      return dateValue.toLocaleDateString()
    },
    statusLabel(status) {
      const source = String(status || '')
      if (!source) return 'Unknown'
      return source.charAt(0).toUpperCase() + source.slice(1)
    },
    statusClass(status) {
      const normalized = String(status || '').toLowerCase()
      if (normalized === 'selected') return 'is-selected'
      if (normalized === 'shortlisted') return 'is-shortlisted'
      if (normalized === 'interviewed') return 'is-interviewed'
      if (normalized === 'waitlisted') return 'is-waitlisted'
      if (normalized === 'rejected') return 'is-rejected'
      return 'is-applied'
    }
  }
}
</script>
