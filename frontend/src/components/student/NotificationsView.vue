<template>
  <section class="rq-view">
    <article class="rq-card">
      <header class="rq-card-hd">
        <span class="rq-card-title">Notifications</span>
        <button
          class="rq-ghost"
          type="button"
          :disabled="isMarkingAll || unreadCount === 0 || isLoading"
          :aria-label="`Mark all ${unreadCount} unread notifications as read`"
          @click="$emit('mark-all')"
        >
          {{ isMarkingAll ? 'Saving...' : `Mark all read (${unreadCount})` }}
        </button>
      </header>

      <div class="rq-card-body">
        <p v-if="errorMessage" class="rq-error-text" role="alert" aria-live="assertive">{{ errorMessage }}</p>

        <div class="rq-notify-list" :aria-busy="isLoading ? 'true' : 'false'" aria-live="polite">
          <article v-if="isLoading" class="rq-notify-item">
            <p class="rq-row-sub">Loading notifications...</p>
          </article>

          <article v-else-if="!notifications.length" class="rq-notify-item">
            <p class="rq-row-sub">No notifications available.</p>
          </article>

          <article v-for="item in notifications" :key="item.notification_id" class="rq-notify-item">
            <div>
              <p class="rq-row-title">{{ item.title || 'Update' }}</p>
              <p class="rq-row-sub">{{ item.message || '-' }}</p>
              <p class="rq-row-sub">{{ formatDateTime(item.created_at) }}</p>
            </div>

            <button
              v-if="!item.is_read"
              class="rq-ghost"
              type="button"
              :disabled="isMarking[item.notification_id]"
              :aria-label="`Mark notification ${item.title || 'update'} as read`"
              @click="$emit('mark-read', item.notification_id)"
            >
              {{ isMarking[item.notification_id] ? 'Saving...' : 'Mark read' }}
            </button>
            <span v-else class="rq-status-pill pill-shortlisted">Read</span>
          </article>
        </div>
      </div>
    </article>
  </section>
</template>

<script>
export default {
  name: 'StudentNotificationsView',
  props: {
    notifications: {
      type: Array,
      default: () => []
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    unreadCount: {
      type: Number,
      default: 0
    },
    errorMessage: {
      type: String,
      default: ''
    },
    isMarking: {
      type: Object,
      default: () => ({})
    },
    isMarkingAll: {
      type: Boolean,
      default: false
    }
  },
  emits: ['mark-read', 'mark-all'],
  methods: {
    formatDateTime(value) {
      if (!value) return '-'
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return '-'
      return parsed.toLocaleString()
    }
  }
}
</script>
