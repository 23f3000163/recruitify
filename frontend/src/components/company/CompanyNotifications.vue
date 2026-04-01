<template>
  <section class="cq-module">
    <article class="cq-panel cq-module-shell">
      <header class="cq-panel-head cq-module-head">
        <div>
          <h2>Notifications</h2>
          <p>Track student offer responses and workflow updates in one feed.</p>
        </div>

        <button
          class="cq-btn"
          type="button"
          :disabled="isMarkingAll || unreadCount === 0 || isLoading"
          @click="markAllRead"
        >
          {{ isMarkingAll ? 'Saving...' : `Mark All Read (${unreadCount})` }}
        </button>
      </header>

      <div class="cq-module-tools cq-module-tools-compact">
        <label class="cq-field">
          <span>Read Status</span>
          <select v-model="readFilter">
            <option value="all">All</option>
            <option value="false">Unread</option>
            <option value="true">Read</option>
          </select>
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
              <th>Title</th>
              <th>Message</th>
              <th>Received</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="5" class="cq-empty-cell">Loading notifications...</td>
            </tr>

            <tr v-else-if="!notifications.length">
              <td colspan="5" class="cq-empty-cell">No notifications found for this filter.</td>
            </tr>

            <tr v-for="row in notifications" :key="row.notification_id">
              <td data-label="Title">
                <p class="cq-drive-title">{{ row.title || 'Update' }}</p>
              </td>
              <td data-label="Message">
                <p class="cq-drive-sub">{{ row.message || '-' }}</p>
              </td>
              <td data-label="Received">{{ formatDateTime(row.created_at) }}</td>
              <td data-label="Status">
                <span class="cq-status-pill" :class="notificationStatusClass(row)">
                  {{ row.is_read ? 'Read' : 'Unread' }}
                </span>
              </td>
              <td data-label="Action" class="cq-row-actions">
                <button
                  class="cq-ghost-btn"
                  type="button"
                  :disabled="row.is_read || isMarking[row.notification_id]"
                  @click="markRead(row.notification_id)"
                >
                  {{ isMarking[row.notification_id] ? 'Saving...' : 'Mark Read' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="cq-drive-footer">
        <p class="cq-muted">{{ pagination.total }} notifications total</p>

        <div class="cq-pager" v-if="pagination.pages > 1">
          <button
            class="cq-ghost-btn"
            type="button"
            :disabled="pagination.page <= 1 || isLoading"
            @click="loadNotifications(pagination.page - 1)"
          >
            Previous
          </button>
          <span>Page {{ pagination.page }} of {{ pagination.pages }}</span>
          <button
            class="cq-ghost-btn"
            type="button"
            :disabled="pagination.page >= pagination.pages || isLoading"
            @click="loadNotifications(pagination.page + 1)"
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
  name: 'CompanyNotifications',
  emits: ['notifications-updated'],
  data() {
    return {
      isLoading: false,
      errorMessage: '',
      readFilter: 'all',
      notifications: [],
      unreadCount: 0,
      isMarking: {},
      isMarkingAll: false,
      pagination: {
        page: 1,
        pages: 0,
        total: 0,
        limit: 10
      }
    }
  },
  created() {
    this.loadNotifications(1)
  },
  methods: {
    async loadNotifications(page = 1) {
      this.isLoading = true
      this.errorMessage = ''

      try {
        const response = await companyApi.getNotifications({
          page,
          limit: this.pagination.limit,
          is_read: this.readFilter
        })

        const data = response?.data?.data || {}

        this.notifications = Array.isArray(data.items) ? data.items : []
        this.unreadCount = Number(data.unread_count || 0)
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
          'Unable to load notifications.'
      } finally {
        this.isLoading = false
      }
    },
    applyFilters() {
      this.loadNotifications(1)
    },
    async markRead(notificationId) {
      const parsedId = Number(notificationId)
      if (!parsedId || this.isMarking[parsedId]) {
        return
      }

      this.isMarking = {
        ...this.isMarking,
        [parsedId]: true
      }

      try {
        await companyApi.markNotificationRead(parsedId)
        await this.loadNotifications(this.pagination.page || 1)
        this.$emit('notifications-updated')
      } catch (error) {
        this.errorMessage =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to update notification.'
      } finally {
        this.isMarking = {
          ...this.isMarking,
          [parsedId]: false
        }
      }
    },
    async markAllRead() {
      if (this.isMarkingAll || this.unreadCount === 0) {
        return
      }

      this.isMarkingAll = true
      try {
        await companyApi.markAllNotificationsRead()
        await this.loadNotifications(1)
        this.$emit('notifications-updated')
      } catch (error) {
        this.errorMessage =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to update notifications.'
      } finally {
        this.isMarkingAll = false
      }
    },
    notificationStatusClass(notification) {
      return notification?.is_read ? 'is-selected' : 'is-waitlisted'
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
