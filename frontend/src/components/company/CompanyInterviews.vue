<template>
  <section class="cq-module">
    <article class="cq-panel cq-module-shell">
      <header class="cq-panel-head cq-module-head">
        <div>
          <h2>Interviews</h2>
          <p>Schedule interview rounds and record outcomes quickly.</p>
        </div>

        <button
          class="cq-btn"
          type="button"
          aria-haspopup="dialog"
          :aria-expanded="showScheduleModal ? 'true' : 'false'"
          aria-controls="company-interview-modal"
          @click="openScheduleModal($event)"
        >
          + Schedule Interview
        </button>
      </header>

      <div class="cq-module-tools cq-module-tools-compact">
        <label class="cq-field">
          <span>Result</span>
          <select v-model="resultFilter">
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="pass">Pass</option>
            <option value="fail">Fail</option>
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

        <button class="cq-ghost-btn" type="button" @click="applyFilters">
          Apply
        </button>
      </div>

      <p v-if="errorMessage" class="cq-inline-error">{{ errorMessage }}</p>

      <div class="cq-table-wrap is-mobile-cards">
        <table class="cq-table cq-interview-table">
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Drive</th>
              <th>Date</th>
              <th>Mode</th>
              <th>Interviewer</th>
              <th>Result</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="7" class="cq-empty-cell">Loading interviews...</td>
            </tr>

            <tr v-else-if="!interviews.length">
              <td colspan="7" class="cq-empty-cell">
                No interview records available for this filter.
              </td>
            </tr>

            <tr v-for="row in interviews" :key="row.interview_id">
              <td data-label="Candidate">
                <p class="cq-drive-title">{{ row.student_name || 'Candidate' }}</p>
                <p class="cq-drive-sub">{{ row.student_email || '-' }}</p>
              </td>
              <td data-label="Drive">{{ row.drive_title || '-' }}</td>
              <td data-label="Date">{{ formatDateTime(row.interview_date) }}</td>
              <td data-label="Mode">{{ statusLabel(row.interview_mode) }}</td>
              <td data-label="Interviewer">{{ row.interviewer_name || '-' }}</td>
              <td data-label="Result">
                <span
                  class="cq-status-pill"
                  :class="resultClass(row.result)"
                  :aria-label="`Interview result ${statusLabel(row.result)}`"
                >
                  {{ statusLabel(row.result) }}
                </span>
              </td>
              <td class="cq-row-actions" data-label="Action">
                <div class="cq-inline-controls">
                  <select
                    :value="resultDraft[row.interview_id] || row.result"
                    @change="setResultDraft(row.interview_id, $event.target.value)"
                  >
                    <option value="pending">Pending</option>
                    <option value="pass">Pass</option>
                    <option value="fail">Fail</option>
                  </select>
                  <button
                    class="cq-ghost-btn"
                    type="button"
                    :disabled="isUpdatingResult[row.interview_id]"
                    @click="saveResult(row)"
                  >
                    {{ isUpdatingResult[row.interview_id] ? 'Saving...' : 'Save' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="cq-drive-footer">
        <p class="cq-muted">{{ pagination.total }} interviews total</p>

        <div class="cq-pager" v-if="pagination.pages > 1">
          <button
            class="cq-ghost-btn"
            type="button"
            :disabled="pagination.page <= 1 || isLoading"
            @click="loadInterviews(pagination.page - 1)"
          >
            Previous
          </button>
          <span>Page {{ pagination.page }} of {{ pagination.pages }}</span>
          <button
            class="cq-ghost-btn"
            type="button"
            :disabled="pagination.page >= pagination.pages || isLoading"
            @click="loadInterviews(pagination.page + 1)"
          >
            Next
          </button>
        </div>
      </footer>
    </article>

    <Transition name="cq-fade">
      <div v-if="showScheduleModal" class="cq-modal-backdrop" @click.self="closeScheduleModal">
        <article
          id="company-interview-modal"
          class="cq-modal cq-modal-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="company-interview-modal-title"
        >
          <header class="cq-modal-head">
            <h2 id="company-interview-modal-title">Schedule Interview</h2>
            <button class="cq-modal-close" type="button" aria-label="Close" @click="closeScheduleModal">x</button>
          </header>

          <form class="cq-drive-form" @submit.prevent="submitScheduleInterview">
            <label class="cq-field">
              <span>Application</span>
              <select v-model="scheduleForm.application_id" required>
                <option value="" disabled>Select application</option>
                <option v-for="option in scheduleCandidates" :key="option.id" :value="option.id">
                  {{ option.label }}
                </option>
              </select>
            </label>

            <div class="cq-form-grid">
              <label class="cq-field">
                <span>Interview Date & Time</span>
                <input v-model="scheduleForm.interview_date" type="datetime-local" required />
              </label>

              <label class="cq-field">
                <span>Mode</span>
                <select v-model="scheduleForm.interview_mode">
                  <option value="online">Online</option>
                  <option value="offline">Offline</option>
                </select>
              </label>
            </div>

            <label class="cq-field">
              <span>Interviewer Name</span>
              <input v-model.trim="scheduleForm.interviewer_name" type="text" placeholder="Panel member" />
            </label>

            <div class="cq-form-grid">
              <label class="cq-field">
                <span>Interview Link</span>
                <input v-model.trim="scheduleForm.interview_link" type="text" placeholder="https://meet.example.com" />
              </label>

              <label class="cq-field">
                <span>Interview Location</span>
                <input v-model.trim="scheduleForm.interview_location" type="text" placeholder="Office address" />
              </label>
            </div>

            <p v-if="scheduleError" class="cq-inline-error">{{ scheduleError }}</p>

            <div class="cq-form-actions">
              <button class="cq-ghost-btn" type="button" :disabled="isScheduling" @click="closeScheduleModal">
                Cancel
              </button>
              <button class="cq-btn" type="submit" :disabled="isScheduling">
                {{ isScheduling ? 'Scheduling...' : 'Schedule' }}
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

const DEFAULT_SCHEDULE_FORM = () => ({
  application_id: '',
  interview_date: '',
  interview_mode: 'online',
  interviewer_name: '',
  interview_link: '',
  interview_location: ''
})

export default {
  name: 'CompanyInterviews',
  emits: ['interviews-updated'],
  data() {
    return {
      isLoading: false,
      errorMessage: '',
      resultFilter: 'all',
      driveFilter: 'all',
      interviews: [],
      driveOptions: [],
      pagination: {
        page: 1,
        pages: 0,
        total: 0,
        limit: 10
      },
      resultDraft: {},
      isUpdatingResult: {},
      showScheduleModal: false,
      scheduleCandidates: [],
      scheduleForm: DEFAULT_SCHEDULE_FORM(),
      scheduleError: '',
      isScheduling: false,
      lastModalFocusTarget: null
    }
  },
  created() {
    this.loadInterviews(1)
  },
  mounted() {
    document.addEventListener('keydown', this.handleGlobalKeydown)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleGlobalKeydown)
  },
  methods: {
    async loadInterviews(page = 1) {
      this.isLoading = true
      this.errorMessage = ''

      try {
        const params = {
          page,
          limit: this.pagination.limit,
          result: this.resultFilter
        }

        if (this.driveFilter !== 'all') {
          params.drive_id = this.driveFilter
        }

        const response = await companyApi.getInterviews(params)
        const data = response?.data?.data || {}

        this.interviews = Array.isArray(data.items) ? data.items : []
        this.driveOptions = Array.isArray(data.drive_options) ? data.drive_options : []
        this.pagination = {
          page: Number(data.page || page),
          pages: Number(data.pages || 0),
          total: Number(data.total || 0),
          limit: Number(data.limit || this.pagination.limit)
        }

        const nextDraft = {}
        this.interviews.forEach((row) => {
          nextDraft[row.interview_id] = row.result
        })
        this.resultDraft = nextDraft
      } catch (error) {
        this.errorMessage =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load interview data.'
      } finally {
        this.isLoading = false
      }
    },
    applyFilters() {
      this.loadInterviews(1)
    },
    setResultDraft(interviewId, result) {
      this.resultDraft = {
        ...this.resultDraft,
        [interviewId]: result
      }
    },
    async saveResult(row) {
      const targetResult = this.resultDraft[row.interview_id] || row.result
      if (targetResult === row.result || this.isUpdatingResult[row.interview_id]) {
        return
      }

      this.isUpdatingResult = {
        ...this.isUpdatingResult,
        [row.interview_id]: true
      }

      try {
        await companyApi.updateInterviewResult(row.interview_id, {
          result: targetResult
        })
        await this.loadInterviews(this.pagination.page || 1)
        this.$emit('interviews-updated')
      } catch (error) {
        this.errorMessage =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to update interview result.'
      } finally {
        this.isUpdatingResult = {
          ...this.isUpdatingResult,
          [row.interview_id]: false
        }
      }
    },
    async openScheduleModal(event) {
      this.lastModalFocusTarget = event?.currentTarget || document.activeElement || null
      this.scheduleForm = DEFAULT_SCHEDULE_FORM()
      this.scheduleError = ''
      this.showScheduleModal = true

      try {
        const response = await companyApi.getApplications({
          page: 1,
          limit: 100,
          status: 'all'
        })
        const items = Array.isArray(response?.data?.data?.items) ? response.data.data.items : []

        this.scheduleCandidates = items
          .filter((row) => row.status !== 'rejected')
          .map((row) => ({
            id: row.application_id,
            label: `${row.student_name || 'Candidate'} - ${row.drive_title || 'Drive'} (${this.statusLabel(row.status)})`
          }))
      } catch (error) {
        this.scheduleError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load applications for scheduling.'
      }
    },
    closeScheduleModal() {
      if (this.isScheduling) return
      this.showScheduleModal = false
      const target = this.lastModalFocusTarget
      this.lastModalFocusTarget = null
      if (target && typeof target.focus === 'function') {
        nextTick(() => target.focus())
      }
    },
    handleGlobalKeydown(event) {
      if (event.key === 'Escape' && this.showScheduleModal && !this.isScheduling) {
        event.preventDefault()
        this.closeScheduleModal()
      }
    },
    async submitScheduleInterview() {
      this.scheduleError = ''

      if (!this.scheduleForm.application_id) {
        this.scheduleError = 'Please select an application.'
        return
      }

      if (!this.scheduleForm.interview_date) {
        this.scheduleError = 'Please select interview date and time.'
        return
      }

      const interviewDate = new Date(this.scheduleForm.interview_date)
      if (Number.isNaN(interviewDate.getTime())) {
        this.scheduleError = 'Interview date is invalid.'
        return
      }

      this.isScheduling = true
      try {
        await companyApi.scheduleInterview({
          application_id: Number(this.scheduleForm.application_id),
          interview_date: interviewDate.toISOString(),
          interview_mode: this.scheduleForm.interview_mode,
          interviewer_name: this.scheduleForm.interviewer_name,
          interview_link: this.scheduleForm.interview_link,
          interview_location: this.scheduleForm.interview_location
        })

        this.showScheduleModal = false
        await this.loadInterviews(1)
        this.$emit('interviews-updated')
      } catch (error) {
        this.scheduleError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to schedule the interview.'
      } finally {
        this.isScheduling = false
      }
    },
    formatDateTime(value) {
      if (!value) return '-'
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return '-'
      return parsed.toLocaleString()
    },
    statusLabel(value) {
      const source = String(value || '')
      if (!source) return 'Unknown'
      return source.charAt(0).toUpperCase() + source.slice(1)
    },
    resultClass(result) {
      const normalized = String(result || '').toLowerCase()
      if (normalized === 'pass') return 'is-pass'
      if (normalized === 'fail') return 'is-fail'
      return 'is-pending'
    }
  }
}
</script>
