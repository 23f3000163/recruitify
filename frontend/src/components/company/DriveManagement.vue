<template>
  <section class="cq-drives">
    <article class="cq-panel cq-drives-shell">
      <header class="cq-panel-head cq-drives-head">
        <div>
          <h2>Drive Management</h2>
          <p>Create, filter, and close placement drives from one workspace.</p>
        </div>

        <button
          class="cq-btn"
          type="button"
          aria-haspopup="dialog"
          :aria-expanded="showCreateModal ? 'true' : 'false'"
          aria-controls="company-drive-modal"
          @click="openCreateModal($event)"
        >
          + New Drive
        </button>
      </header>

      <div class="cq-drive-tools">
        <label class="cq-field">
          <span>Status</span>
          <select v-model="statusFilter" @change="applyFilters">
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="closed">Closed</option>
          </select>
        </label>

        <label class="cq-field cq-drive-search">
          <span>Search</span>
          <input
            v-model.trim="queryText"
            type="text"
            placeholder="Search title, skills, or location"
            @keyup.enter="applyFilters"
          />
        </label>

        <button class="cq-ghost-btn" type="button" @click="applyFilters">
          Apply
        </button>
      </div>

      <p v-if="errorMessage" class="cq-inline-error">{{ errorMessage }}</p>

      <div class="cq-table-wrap is-mobile-cards">
        <table class="cq-table cq-drive-table">
          <thead>
            <tr>
              <th>Role</th>
              <th>Status</th>
              <th>Deadline</th>
              <th>Location</th>
              <th>Applications</th>
              <th>Salary (LPA)</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="7" class="cq-empty-cell">Loading drives...</td>
            </tr>

            <tr v-else-if="!drives.length">
              <td colspan="7" class="cq-empty-cell">
                No drives found for the current filter.
              </td>
            </tr>

            <tr v-for="row in drives" :key="row.id">
              <td data-label="Role">
                <p class="cq-drive-title">{{ row.title || row.job_title || 'Untitled Drive' }}</p>
                <p class="cq-drive-sub">{{ row.required_skills || 'Skills not specified' }}</p>
                <p class="cq-drive-sub">{{ formatExperience(row.experience_required) }}</p>
                <p class="cq-drive-sub">{{ formatBenefits(row.benefits) }}</p>
              </td>
              <td data-label="Status">
                <span
                  class="cq-status-pill"
                  :class="statusClass(row.status)"
                  :aria-label="`Drive status ${normalizeStatus(row.status)}`"
                >
                  {{ normalizeStatus(row.status) }}
                </span>
              </td>
              <td data-label="Deadline">{{ formatDate(row.deadline || row.application_deadline) }}</td>
              <td data-label="Location">{{ row.job_location || '-' }}</td>
              <td data-label="Applications">{{ Number(row.applications_count || 0).toLocaleString() }}</td>
              <td data-label="Salary">{{ formatSalary(row.salary_lpa) }}</td>
              <td class="cq-row-actions" data-label="Action">
                <button
                  class="cq-ghost-btn"
                  type="button"
                  :disabled="row.status === 'closed' || pendingCloseActions[row.id]"
                  @click="closeDrive(row)"
                >
                  {{ pendingCloseActions[row.id] ? 'Closing...' : 'Close' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="cq-drive-footer">
        <p class="cq-muted">{{ pagination.total }} drives total</p>

        <div class="cq-pager" v-if="pagination.pages > 1">
          <button
            class="cq-ghost-btn"
            type="button"
            :disabled="pagination.page <= 1 || isLoading"
            @click="loadDrives(pagination.page - 1)"
          >
            Previous
          </button>
          <span>Page {{ pagination.page }} of {{ pagination.pages }}</span>
          <button
            class="cq-ghost-btn"
            type="button"
            :disabled="pagination.page >= pagination.pages || isLoading"
            @click="loadDrives(pagination.page + 1)"
          >
            Next
          </button>
        </div>
      </footer>
    </article>

    <Transition name="cq-fade">
      <div v-if="showCreateModal" class="cq-modal-backdrop" @click.self="closeCreateModal">
        <article
          id="company-drive-modal"
          class="cq-modal cq-drive-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="company-drive-modal-title"
        >
          <header class="cq-modal-head">
            <h2 id="company-drive-modal-title">Create Placement Drive</h2>
            <button class="cq-modal-close" type="button" aria-label="Close" @click="closeCreateModal">x</button>
          </header>

          <form class="cq-drive-form" @submit.prevent="submitCreateDrive">
            <label class="cq-field">
              <span>Job Title</span>
              <input v-model.trim="form.job_title" type="text" required />
            </label>

            <label class="cq-field">
              <span>Job Description</span>
              <textarea v-model.trim="form.job_description" rows="3" required></textarea>
            </label>

            <label class="cq-field">
              <span>Required Skills</span>
              <input v-model.trim="form.required_skills" type="text" placeholder="Python, SQL, DSA" />
            </label>

            <div class="cq-form-grid">
              <label class="cq-field">
                <span>Experience</span>
                <input
                  v-model.trim="form.experience_required"
                  type="text"
                  placeholder="0-2 years / Fresher"
                  required
                />
              </label>

              <label class="cq-field">
                <span>Benefits</span>
                <input
                  v-model.trim="form.benefits"
                  type="text"
                  placeholder="Insurance, hybrid work, bonus"
                  required
                />
              </label>
            </div>

            <div class="cq-form-grid">
              <label class="cq-field">
                <span>Minimum CGPA</span>
                <input v-model.number="form.min_cgpa" type="number" min="0" max="10" step="0.1" required />
              </label>

              <label class="cq-field">
                <span>Salary (LPA)</span>
                <input v-model.number="form.salary_lpa" type="number" min="0" step="0.1" />
              </label>
            </div>

            <div class="cq-form-grid">
              <label class="cq-field">
                <span>Application Deadline</span>
                <input v-model="form.application_deadline" type="date" required />
              </label>

              <label class="cq-field">
                <span>Interview Mode</span>
                <select v-model="form.interview_mode">
                  <option value="online">Online</option>
                  <option value="offline">Offline</option>
                  <option value="both">Both</option>
                </select>
              </label>
            </div>

            <label class="cq-field">
              <span>Location</span>
              <input v-model.trim="form.job_location" type="text" placeholder="Bengaluru / Remote" />
            </label>

            <div class="cq-field">
              <span>Eligible Branches</span>
              <div class="cq-checkbox-grid">
                <label v-for="branch in branchOptions" :key="branch" class="cq-check">
                  <input
                    type="checkbox"
                    :value="branch"
                    :checked="form.eligible_branches.includes(branch)"
                    @change="toggleBranch(branch)"
                  />
                  <span>{{ branch }}</span>
                </label>
              </div>
            </div>

            <div class="cq-field">
              <span>Eligible Years</span>
              <div class="cq-checkbox-grid">
                <label v-for="year in yearOptions" :key="year" class="cq-check">
                  <input
                    type="checkbox"
                    :value="year"
                    :checked="form.eligible_years.includes(year)"
                    @change="toggleYear(year)"
                  />
                  <span>Year {{ year }}</span>
                </label>
              </div>
            </div>

            <p v-if="formError" class="cq-inline-error">{{ formError }}</p>

            <div class="cq-form-actions">
              <button class="cq-ghost-btn" type="button" :disabled="isSubmitting" @click="closeCreateModal">
                Cancel
              </button>
              <button class="cq-btn" type="submit" :disabled="isSubmitting">
                {{ isSubmitting ? 'Creating...' : 'Create Drive' }}
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

const DEFAULT_FORM = () => ({
  job_title: '',
  job_description: '',
  required_skills: '',
  experience_required: '',
  benefits: '',
  min_cgpa: 6,
  salary_lpa: '',
  application_deadline: '',
  interview_mode: 'online',
  job_location: '',
  eligible_branches: ['CSE'],
  eligible_years: [4]
})

export default {
  name: 'DriveManagement',
  emits: ['drive-updated'],
  data() {
    return {
      isLoading: false,
      errorMessage: '',
      statusFilter: 'all',
      queryText: '',
      drives: [],
      pendingCloseActions: {},
      pagination: {
        page: 1,
        pages: 0,
        total: 0,
        limit: 8
      },
      showCreateModal: false,
      isSubmitting: false,
      formError: '',
      form: DEFAULT_FORM(),
      lastModalFocusTarget: null
    }
  },
  computed: {
    branchOptions() {
      return ['CSE', 'ECE', 'MECH', 'EE', 'OTHER']
    },
    yearOptions() {
      return [1, 2, 3, 4]
    }
  },
  created() {
    this.loadDrives(1)
  },
  mounted() {
    document.addEventListener('keydown', this.handleGlobalKeydown)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleGlobalKeydown)
  },
  methods: {
    async loadDrives(page = 1) {
      this.isLoading = true
      this.errorMessage = ''

      try {
        const response = await companyApi.getDrives({
          page,
          limit: this.pagination.limit,
          status: this.statusFilter,
          q: this.queryText
        })

        const data = response?.data?.data || {}
        this.drives = Array.isArray(data.items) ? data.items : []
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
          'Unable to load drives at the moment.'
      } finally {
        this.isLoading = false
      }
    },
    applyFilters() {
      this.loadDrives(1)
    },
    openCreateModal(event) {
      this.lastModalFocusTarget = event?.currentTarget || document.activeElement || null
      this.formError = ''
      this.form = DEFAULT_FORM()
      this.showCreateModal = true
    },
    closeCreateModal() {
      if (this.isSubmitting) return
      this.showCreateModal = false
      const target = this.lastModalFocusTarget
      this.lastModalFocusTarget = null
      if (target && typeof target.focus === 'function') {
        nextTick(() => target.focus())
      }
    },
    handleGlobalKeydown(event) {
      if (event.key === 'Escape' && this.showCreateModal && !this.isSubmitting) {
        event.preventDefault()
        this.closeCreateModal()
      }
    },
    toggleBranch(branch) {
      const next = [...this.form.eligible_branches]
      const index = next.indexOf(branch)
      if (index >= 0) {
        next.splice(index, 1)
      } else {
        next.push(branch)
      }
      this.form.eligible_branches = next
    },
    toggleYear(year) {
      const next = [...this.form.eligible_years]
      const index = next.indexOf(year)
      if (index >= 0) {
        next.splice(index, 1)
      } else {
        next.push(year)
      }
      this.form.eligible_years = next
    },
    async submitCreateDrive() {
      this.formError = ''

      if (!this.form.experience_required.trim()) {
        this.formError = 'Please provide required experience.'
        return
      }

      if (!this.form.benefits.trim()) {
        this.formError = 'Please provide benefits for the drive.'
        return
      }

      if (!this.form.eligible_branches.length) {
        this.formError = 'Select at least one eligible branch.'
        return
      }

      if (!this.form.eligible_years.length) {
        this.formError = 'Select at least one eligible year.'
        return
      }

      this.isSubmitting = true
      try {
        const payload = {
          ...this.form,
          min_cgpa: Number(this.form.min_cgpa),
          salary_lpa: this.form.salary_lpa === '' ? null : Number(this.form.salary_lpa),
          eligible_years: [...this.form.eligible_years].sort((a, b) => a - b),
          eligible_branches: [...this.form.eligible_branches]
        }

        await companyApi.createDrive(payload)
        this.showCreateModal = false
        await this.loadDrives(1)
        this.$emit('drive-updated')
      } catch (error) {
        this.formError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to create the drive. Please try again.'
      } finally {
        this.isSubmitting = false
      }
    },
    async closeDrive(row) {
      if (!row?.id || row.status === 'closed' || this.pendingCloseActions[row.id]) {
        return
      }

      this.pendingCloseActions = {
        ...this.pendingCloseActions,
        [row.id]: true
      }

      try {
        await companyApi.closeDrive(row.id)
        await this.loadDrives(this.pagination.page || 1)
        this.$emit('drive-updated')
      } catch (error) {
        this.errorMessage =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to close drive right now.'
      } finally {
        this.pendingCloseActions = {
          ...this.pendingCloseActions,
          [row.id]: false
        }
      }
    },
    formatDate(value) {
      if (!value) return '-'
      const dateValue = new Date(value)
      if (Number.isNaN(dateValue.getTime())) return '-'
      return dateValue.toLocaleDateString()
    },
    formatSalary(value) {
      if (value === null || value === undefined || value === '') {
        return '-'
      }
      const parsed = Number(value)
      if (Number.isNaN(parsed)) return '-'
      return parsed.toLocaleString()
    },
    formatExperience(value) {
      const source = String(value || '').trim()
      if (!source) return 'Experience not specified'
      return `Experience: ${source}`
    },
    formatBenefits(value) {
      const source = String(value || '').trim()
      if (!source) return 'Benefits not specified'

      const compact = source.replace(/\s+/g, ' ')
      if (compact.length <= 72) {
        return `Benefits: ${compact}`
      }

      return `Benefits: ${compact.slice(0, 69)}...`
    },
    normalizeStatus(status) {
      const source = String(status || 'pending')
      return source.charAt(0).toUpperCase() + source.slice(1)
    },
    statusClass(status) {
      const normalized = String(status || '').toLowerCase()
      if (normalized === 'approved') return 'is-approved'
      if (normalized === 'closed') return 'is-closed'
      return 'is-pending'
    }
  }
}
</script>