<template>
  <aside
    class="rq-student-notif-panel"
    role="complementary"
    aria-label="Student notifications"
    @click.stop
  >
    <div class="rq-student-notif-hd">
      <span class="rq-card-title">Notifications</span>
      <div class="rq-student-notif-actions">
        <button
          class="rq-ghost rq-ghost-xs"
          type="button"
          :disabled="isMarkingAll || unreadCount === 0 || isLoading"
          @click="$emit('mark-all-read')"
        >
          {{ isMarkingAll ? 'Saving...' : 'Mark all read' }}
        </button>
        <button
          class="rq-modal-close"
          type="button"
          aria-label="Close notifications"
          @click="$emit('close')"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
          </svg>
        </button>
      </div>
    </div>

    <p v-if="errorMessage" class="rq-student-notif-error" role="alert">{{ errorMessage }}</p>

    <div class="rq-student-notif-list" :aria-busy="isLoading ? 'true' : 'false'">
      <article v-if="isLoading" class="rq-notify-item rq-notify-item-system">
        <p class="rq-row-sub">Loading notifications...</p>
      </article>

      <article v-else-if="!notifications.length" class="rq-notify-item rq-notify-item-system">
        <p class="rq-row-title">No notifications yet</p>
        <p class="rq-row-sub">You will see your latest placement alerts here.</p>
      </article>

      <article
        v-for="notification in notifications"
        :key="notification.notification_id"
        class="rq-notify-item"
        :class="{ 'is-unread': !notification.is_read }"
        @click="markRead(notification)"
      >
        <div class="rq-notify-copy">
          <p class="rq-notify-title">{{ notification.title || 'Update' }}</p>
          <p class="rq-notify-message">{{ notification.message || '-' }}</p>
          <p class="rq-notify-time">{{ formatRelativeTime(notification.created_at || notification.sent_at) }}</p>
        </div>
        <button
          v-if="!notification.is_read"
          class="rq-notify-mark-dot"
          type="button"
          :disabled="isMarking[notification.notification_id]"
          :aria-label="`Mark notification ${notification.title || 'update'} as read`"
          @click.stop="markRead(notification)"
        >
          <span v-if="isMarking[notification.notification_id]" class="rq-notify-saving">Saving...</span>
          <span v-else class="rq-notify-dot" aria-hidden="true"></span>
          <span class="rq-sr-only">Mark read</span>
        </button>
        <span v-else class="rq-notify-read">Read</span>
      </article>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'StudentNotificationPanel',
  props: {
    notifications: {
      type: Array,
      default: () => []
    },
    unreadCount: {
      type: Number,
      default: 0
    },
    errorMessage: {
      type: String,
      default: ''
    },
    isLoading: {
      type: Boolean,
      default: false
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
  emits: ['close', 'mark-read', 'mark-all-read'],
  methods: {
    markRead(notification) {
      const notificationId = Number(notification?.notification_id || 0)
      if (!notificationId || notification.is_read || this.isMarking[notificationId]) {
        return
      }

      this.$emit('mark-read', notificationId)
    },
    parseNotificationDate(value) {
      const raw = String(value || '').trim()
      if (!raw) {
        return null
      }

      const isoLike = raw.includes('T') ? raw : raw.replace(' ', 'T')
      const hasTimezone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(isoLike)
      const normalized = hasTimezone ? isoLike : `${isoLike}Z`
      const parsed = new Date(normalized)

      if (Number.isNaN(parsed.getTime())) {
        return null
      }

      return parsed
    },
    formatRelativeTime(value) {
      if (!value) return '-'
      const parsed = this.parseNotificationDate(value)
      if (!parsed) return '-'

      const deltaMs = Date.now() - parsed.getTime()
      if (deltaMs < 0) return parsed.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })

      const minutes = Math.floor(deltaMs / (1000 * 60))
      if (minutes < 1) return 'Just now'
      if (minutes < 60) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`

      const hours = Math.floor(minutes / 60)
      if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`

      const days = Math.floor(hours / 24)
      if (days === 1) return 'Yesterday'
      if (days < 7) return `${days} days ago`

      return parsed.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
    }
  }
}
</script>
