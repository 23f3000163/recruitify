<template>
  <section class="std-shell">
    <div class="std-wrap">
      <header class="std-head">
        <div>
          <p class="std-kicker">Student Workspace</p>
          <h1>Application Timeline</h1>
          <p>Track your recruitment status, feedback, and next actions in one place.</p>
        </div>

        <button class="std-btn" type="button" :disabled="isRefreshing" @click="refreshAll">
          {{ isRefreshing ? 'Refreshing...' : 'Refresh' }}
        </button>
      </header>

      <p v-if="errorMessage" class="std-alert">{{ errorMessage }}</p>

      <section class="std-summary-grid">
        <article v-for="card in summaryCards" :key="card.id" class="std-summary-card">
          <p class="std-summary-label">{{ card.label }}</p>
          <p class="std-summary-value">{{ card.value }}</p>
          <p class="std-summary-sub">{{ card.sub }}</p>
        </article>
      </section>

      <div class="std-grid">
        <article class="std-panel std-panel-wide">
          <header class="std-panel-head">
            <div>
              <h2>My Applications</h2>
              <p>See status updates, feedback notes, and timeline milestones.</p>
            </div>
          </header>

          <div class="std-tools">
            <label class="std-field">
              <span>Status</span>
              <select v-model="statusFilter">
                <option value="all">All</option>
                <option v-for="status in statusOptions" :key="status" :value="status">
                  {{ statusLabel(status) }}
                </option>
              </select>
            </label>

            <label class="std-field std-search-field">
              <span>Search</span>
              <input
                v-model.trim="queryText"
                type="text"
                placeholder="Role, company, or location"
                @keyup.enter="applyFilters"
              />
            </label>

            <button class="std-btn ghost" type="button" @click="applyFilters">Apply</button>
          </div>

          <div class="std-table-wrap is-mobile-cards">
            <table class="std-table">
              <thead>
                <tr>
                  <th>Role</th>
                  <th>Company</th>
                  <th>Status</th>
                  <th>Updated</th>
                  <th>Timeline</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="isLoadingApplications">
                  <td colspan="5" class="std-empty">Loading applications...</td>
                </tr>

                <tr v-else-if="!applications.length">
                  <td colspan="5" class="std-empty">No applications found for this filter.</td>
                </tr>

                <tr v-for="row in applications" :key="row.application_id">
                  <td data-label="Role">
                    <p class="std-role-title">{{ row.drive?.title || 'Role unavailable' }}</p>
                    <p class="std-role-sub">{{ row.drive?.location || '-' }}</p>
                  </td>
                  <td data-label="Company">{{ row.company?.name || '-' }}</td>
                  <td data-label="Status">
                    <span class="std-status" :class="statusClass(row.status)">
                      {{ row.status_label || statusLabel(row.status) }}
                    </span>
                    <p v-if="row.notes" class="std-meta-note">Note: {{ row.notes }}</p>
                    <p v-if="row.rejection_reason" class="std-meta-note">Reason: {{ row.rejection_reason }}</p>
                  </td>
                  <td data-label="Updated">{{ formatDateTime(row.updated_at) }}</td>
                  <td data-label="Timeline">
                    <ul v-if="safeTimeline(row.timeline).length" class="std-timeline">
                      <li v-for="event in safeTimeline(row.timeline).slice(-3)" :key="event.id">
                        <span class="std-dot" :class="`is-${event.tone || 'info'}`"></span>
                        <div>
                          <p class="std-timeline-label">{{ event.label }}</p>
                          <p class="std-timeline-msg">{{ event.message }}</p>
                        </div>
                      </li>
                    </ul>
                    <span v-else class="std-muted">No timeline events yet.</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <footer class="std-footer">
            <p class="std-muted">{{ pagination.total }} applications total</p>

            <div class="std-pager" v-if="pagination.pages > 1">
              <button
                class="std-btn ghost"
                type="button"
                :disabled="pagination.page <= 1 || isLoadingApplications"
                @click="loadApplications(pagination.page - 1)"
              >
                Previous
              </button>
              <span>Page {{ pagination.page }} of {{ pagination.pages }}</span>
              <button
                class="std-btn ghost"
                type="button"
                :disabled="pagination.page >= pagination.pages || isLoadingApplications"
                @click="loadApplications(pagination.page + 1)"
              >
                Next
              </button>
            </div>
          </footer>
        </article>

        <article class="std-panel">
          <header class="std-panel-head">
            <div>
              <h2>Notifications</h2>
              <p>Unread updates from companies and recruitment events.</p>
            </div>
            <span class="std-badge" :class="{ 'is-empty': unreadCount === 0 }">{{ unreadCount }} unread</span>
          </header>

          <p v-if="isLoadingNotifications" class="std-muted">Loading notifications...</p>

          <ul v-else-if="notifications.length" class="std-notify-list">
            <li v-for="notification in notifications" :key="notification.notification_id" class="std-notify-item">
              <div>
                <p class="std-notify-title">{{ notification.title }}</p>
                <p class="std-notify-message">{{ notification.message }}</p>
                <p class="std-notify-time">{{ formatDateTime(notification.created_at) }}</p>
              </div>

              <button
                v-if="!notification.is_read"
                class="std-btn ghost std-notify-btn"
                type="button"
                :disabled="isMarking[notification.notification_id]"
                @click="markNotificationRead(notification)"
              >
                {{ isMarking[notification.notification_id] ? 'Saving...' : 'Mark Read' }}
              </button>
              <span v-else class="std-read-pill">Read</span>
            </li>
          </ul>

          <p v-else class="std-muted">No notifications yet.</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script>
import { studentApi } from '../../api/api'

export default {
  name: 'StudentDashboard',
  data() {
    return {
      isRefreshing: false,
      isLoadingApplications: false,
      isLoadingNotifications: false,
      errorMessage: '',
      statusFilter: 'all',
      queryText: '',
      summary: {
        applications_total: 0,
        applied: 0,
        shortlisted: 0,
        interviewed: 0,
        selected: 0,
        waitlisted: 0,
        rejected: 0,
        offers_released: 0
      },
      applications: [],
      notifications: [],
      unreadCount: 0,
      isMarking: {},
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
    summaryCards() {
      return [
        {
          id: 'applications',
          label: 'Applications',
          value: this.summary.applications_total,
          sub: 'Total drives applied'
        },
        {
          id: 'shortlisted',
          label: 'Shortlisted',
          value: this.summary.shortlisted,
          sub: 'Moved to next stage'
        },
        {
          id: 'interviewed',
          label: 'Interviews',
          value: this.summary.interviewed,
          sub: 'Interview rounds scheduled'
        },
        {
          id: 'offers',
          label: 'Offers',
          value: this.summary.offers_released,
          sub: 'Offer letters received'
        },
        {
          id: 'notifications',
          label: 'Unread Updates',
          value: this.unreadCount,
          sub: 'Actionable notifications'
        }
      ]
    }
  },
  created() {
    this.refreshAll()
  },
  methods: {
    async refreshAll() {
      this.isRefreshing = true
      this.errorMessage = ''

      await Promise.all([this.loadDashboard(), this.loadApplications(1), this.loadNotifications()])

      this.isRefreshing = false
    },
    async loadDashboard() {
      try {
        const response = await studentApi.getDashboard()
        const data = response?.data?.data || {}

        if (data.summary && typeof data.summary === 'object') {
          this.summary = {
            ...this.summary,
            ...data.summary
          }
        }

        if (typeof data.unread_notifications === 'number') {
          this.unreadCount = data.unread_notifications
        }
      } catch (error) {
        this.errorMessage =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load student dashboard.'
      }
    },
    async loadApplications(page = 1) {
      this.isLoadingApplications = true

      try {
        const params = {
          page,
          limit: this.pagination.limit,
          status: this.statusFilter,
          q: this.queryText
        }

        const response = await studentApi.getApplications(params)
        const data = response?.data?.data || {}

        this.applications = Array.isArray(data.items) ? data.items : []
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
          'Unable to load applications.'
      } finally {
        this.isLoadingApplications = false
      }
    },
    async loadNotifications() {
      this.isLoadingNotifications = true

      try {
        const response = await studentApi.getNotifications({
          page: 1,
          limit: 8,
          is_read: 'all'
        })
        const data = response?.data?.data || {}

        this.notifications = Array.isArray(data.items) ? data.items : []
        this.unreadCount = Number(data.unread_count || 0)
      } catch (error) {
        this.errorMessage =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load notifications.'
      } finally {
        this.isLoadingNotifications = false
      }
    },
    applyFilters() {
      this.loadApplications(1)
    },
    async markNotificationRead(notification) {
      const notificationId = Number(notification?.notification_id)
      if (!notificationId || notification.is_read || this.isMarking[notificationId]) {
        return
      }

      this.isMarking = {
        ...this.isMarking,
        [notificationId]: true
      }

      try {
        const response = await studentApi.markNotificationRead(notificationId)
        const data = response?.data?.data || {}
        const updatedNotification = data.notification || {}

        this.notifications = this.notifications.map((item) => {
          if (item.notification_id !== notificationId) return item
          return {
            ...item,
            ...updatedNotification,
            is_read: true
          }
        })

        if (typeof data.unread_count === 'number') {
          this.unreadCount = data.unread_count
        } else {
          this.unreadCount = Math.max(0, this.unreadCount - 1)
        }
      } catch (error) {
        this.errorMessage =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to update notification.'
      } finally {
        this.isMarking = {
          ...this.isMarking,
          [notificationId]: false
        }
      }
    },
    safeTimeline(timeline) {
      return Array.isArray(timeline) ? timeline : []
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
    },
    formatDateTime(value) {
      if (!value) return '-'
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return '-'
      return parsed.toLocaleString()
    }
  }
}
</script>

<style scoped>
.std-shell {
  min-height: calc(100vh - 86px);
  padding: 96px 4% 40px;
  background:
    radial-gradient(860px circle at 0% -10%, rgba(37, 99, 235, 0.08), transparent 42%),
    radial-gradient(680px circle at 100% -10%, rgba(5, 150, 105, 0.08), transparent 40%),
    var(--parch);
}

.std-wrap {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.std-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}

.std-kicker {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--blue);
  font-weight: 800;
}

.std-head h1 {
  margin-top: 6px;
  font-family: var(--serif);
  font-size: 2rem;
  line-height: 1.08;
  letter-spacing: -0.02em;
}

.std-head p {
  margin-top: 8px;
  color: var(--t2);
}

.std-alert {
  border: 1px solid rgba(220, 38, 38, 0.24);
  background: var(--red-lt);
  color: var(--red);
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 0.86rem;
  font-weight: 600;
}

.std-summary-grid {
  display: grid;
  grid-template-columns: repeat(10, minmax(0, 1fr));
  gap: 12px;
}

.std-summary-card {
  grid-column: span 2;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 14px;
  box-shadow: var(--sh-xs);
}

.std-summary-label {
  font-size: 0.72rem;
  color: var(--t2);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700;
}

.std-summary-value {
  margin-top: 4px;
  font-family: var(--serif);
  font-size: 1.35rem;
  font-weight: 700;
}

.std-summary-sub {
  margin-top: 2px;
  color: var(--t2);
  font-size: 0.8rem;
}

.std-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 12px;
}

.std-panel {
  grid-column: span 4;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 14px;
  box-shadow: var(--sh-xs);
}

.std-panel-wide {
  grid-column: span 8;
}

.std-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.std-panel-head h2 {
  font-family: var(--serif);
  font-size: 1.15rem;
  font-weight: 600;
}

.std-panel-head p {
  margin-top: 3px;
  color: var(--t2);
  font-size: 0.82rem;
}

.std-badge {
  border: 1px solid rgba(37, 99, 235, 0.25);
  background: var(--blue-lt);
  color: var(--blue-d);
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 0.72rem;
  font-weight: 700;
}

.std-badge.is-empty {
  border-color: var(--border);
  background: #f8fafc;
  color: var(--t2);
}

.std-tools {
  display: grid;
  grid-template-columns: 180px 1fr auto;
  gap: 10px;
  align-items: end;
  margin-bottom: 10px;
}

.std-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.std-field > span {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--t2);
  font-weight: 700;
}

.std-field input,
.std-field select {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 9px 10px;
  background: #fff;
  color: var(--ink);
  font-size: 0.84rem;
}

.std-btn {
  border: 1px solid transparent;
  background: var(--ink);
  color: #fff;
  border-radius: 10px;
  padding: 9px 12px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
}

.std-btn.ghost {
  background: #fff;
  color: var(--ink);
  border-color: var(--border);
  font-weight: 600;
}

.std-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.std-table-wrap {
  overflow-x: auto;
}

.std-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 900px;
}

.std-table th,
.std-table td {
  border-bottom: 1px solid var(--border);
  padding: 10px;
  text-align: left;
  font-size: 0.82rem;
  vertical-align: top;
}

.std-table th {
  color: var(--t2);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.std-empty,
.std-muted {
  color: var(--t2);
  font-size: 0.82rem;
}

.std-empty {
  text-align: center;
  padding: 18px 10px;
}

.std-role-title {
  font-size: 0.84rem;
  font-weight: 700;
}

.std-role-sub {
  margin-top: 2px;
  color: var(--t2);
  font-size: 0.76rem;
}

.std-status {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 0.72rem;
  font-weight: 700;
  border: 1px solid transparent;
}

.std-status.is-applied {
  color: #0f172a;
  background: #f8fafc;
  border-color: #cbd5e1;
}

.std-status.is-shortlisted,
.std-status.is-interviewed {
  color: #155e75;
  background: #ecfeff;
  border-color: #67e8f9;
}

.std-status.is-selected {
  color: #065f46;
  background: #ecfdf5;
  border-color: #34d399;
}

.std-status.is-waitlisted {
  color: #92400e;
  background: #fffbeb;
  border-color: #fbbf24;
}

.std-status.is-rejected {
  color: #991b1b;
  background: #fff1f2;
  border-color: #fecdd3;
}

.std-meta-note {
  margin-top: 4px;
  color: var(--t2);
  font-size: 0.76rem;
  line-height: 1.35;
}

.std-timeline {
  list-style: none;
  display: grid;
  gap: 6px;
}

.std-timeline li {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 7px;
}

.std-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  margin-top: 5px;
  background: #64748b;
}

.std-dot.is-success {
  background: #16a34a;
}

.std-dot.is-error {
  background: #dc2626;
}

.std-timeline-label {
  font-size: 0.76rem;
  font-weight: 700;
}

.std-timeline-msg {
  color: var(--t2);
  font-size: 0.74rem;
  line-height: 1.35;
}

.std-footer {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.std-pager {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
}

.std-notify-list {
  list-style: none;
  display: grid;
  gap: 10px;
}

.std-notify-item {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 10px;
  display: grid;
  gap: 8px;
}

.std-notify-title {
  font-size: 0.84rem;
  font-weight: 700;
}

.std-notify-message {
  margin-top: 2px;
  color: var(--t2);
  font-size: 0.78rem;
  line-height: 1.4;
}

.std-notify-time {
  margin-top: 4px;
  color: var(--t3);
  font-size: 0.72rem;
}

.std-notify-btn {
  justify-self: start;
}

.std-read-pill {
  justify-self: start;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 0.72rem;
  color: var(--t2);
  font-weight: 700;
}

@media (max-width: 1160px) {
  .std-summary-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }

  .std-summary-card {
    grid-column: span 2;
  }

  .std-panel,
  .std-panel-wide {
    grid-column: span 12;
  }
}

@media (max-width: 820px) {
  .std-shell {
    padding: 84px 16px 24px;
  }

  .std-head {
    flex-direction: column;
  }

  .std-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .std-summary-card {
    grid-column: span 1;
  }

  .std-tools {
    grid-template-columns: 1fr;
  }

  .std-table-wrap.is-mobile-cards {
    overflow: visible;
  }

  .std-table-wrap.is-mobile-cards .std-table {
    min-width: 0;
    border-collapse: separate;
    border-spacing: 0;
  }

  .std-table-wrap.is-mobile-cards .std-table thead {
    display: none;
  }

  .std-table-wrap.is-mobile-cards .std-table tbody {
    display: grid;
    gap: 10px;
  }

  .std-table-wrap.is-mobile-cards .std-table tr {
    display: grid;
    gap: 8px;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px;
    background: #fff;
  }

  .std-table-wrap.is-mobile-cards .std-table td {
    display: grid;
    grid-template-columns: 100px 1fr;
    gap: 8px;
    padding: 0;
    border-bottom: 0;
  }

  .std-table-wrap.is-mobile-cards .std-table td::before {
    content: attr(data-label);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--t2);
    font-weight: 700;
  }

  .std-table-wrap.is-mobile-cards .std-empty {
    text-align: left;
    padding: 0;
  }

  .std-table-wrap.is-mobile-cards .std-empty::before {
    content: '';
  }

  .std-footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
