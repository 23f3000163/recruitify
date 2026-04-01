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

      <div class="cq-table-wrap">
        <table class="cq-table cq-application-table">
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Drive</th>
              <th>Status</th>
              <th>Applied</th>
              <th>Updated</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="6" class="cq-empty-cell">Loading applications...</td>
            </tr>

            <tr v-else-if="!applications.length">
              <td colspan="6" class="cq-empty-cell">
                No applications found for this filter.
              </td>
            </tr>

            <tr v-for="row in applications" :key="row.application_id">
              <td>
                <p class="cq-drive-title">{{ row.student_name || 'Candidate' }}</p>
                <p class="cq-drive-sub">{{ row.student_email || '-' }}</p>
              </td>
              <td>{{ row.drive_title || '-' }}</td>
              <td>
                <span class="cq-status-pill" :class="statusClass(row.status)">
                  {{ statusLabel(row.status) }}
                </span>
              </td>
              <td>{{ formatDate(row.application_date) }}</td>
              <td>{{ formatDate(row.updated_at) }}</td>
              <td class="cq-row-actions">
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
                    @click="updateStatus(row)"
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
  </section>
</template>

<script>
import { companyApi } from '../../api/api'

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
    }
  },
  created() {
    this.loadApplications(1)
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
    async updateStatus(row) {
      const targetStatus = this.statusDraft[row.application_id] || row.status
      if (targetStatus === row.status || this.isUpdating[row.application_id]) {
        return
      }

      this.isUpdating = {
        ...this.isUpdating,
        [row.application_id]: true
      }

      try {
        await companyApi.updateApplicationStatus(row.application_id, {
          status: targetStatus,
          rejection_reason: targetStatus === 'rejected' ? 'Rejected by company review.' : null
        })
        await this.loadApplications(this.pagination.page || 1)
        this.$emit('applications-updated')
      } catch (error) {
        this.errorMessage =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to update application status.'
      } finally {
        this.isUpdating = {
          ...this.isUpdating,
          [row.application_id]: false
        }
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
