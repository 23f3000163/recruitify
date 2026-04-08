<template>
  <section class="rq-view">
    <article class="rq-card">
      <header class="rq-card-hd rq-card-hd-split">
        <div class="rq-card-hd-l">
          <span class="rq-card-title">Notifications</span>
          <span v-if="unreadCount > 0" class="rq-pill rq-pill-blue">{{ unreadCount }} unread</span>
        </div>
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
          <article v-if="isLoading" class="rq-notify-item rq-notify-item-system">
            <p class="rq-row-sub">Loading notifications...</p>
          </article>

          <article v-else-if="!notifications.length" class="rq-notify-item rq-notify-item-system">
            <p class="rq-row-title">No notifications yet</p>
            <p class="rq-row-sub">You will see interview, offer, drive, shortlist, and profile updates here.</p>
          </article>

          <article
            v-for="item in notifications"
            :key="item.notification_id"
            class="rq-notify-item"
            :class="[
              `rq-notify-${notificationKind(item)}`,
              { 'is-unread': !item.is_read, 'is-saving': isMarking[item.notification_id] }
            ]"
          >
            <div class="rq-notify-icon-wrap" :class="`rq-notify-icon-${notificationKind(item)}`" aria-hidden="true">
              <span class="rq-notify-icon">{{ notificationIcon(item) }}</span>
            </div>

            <div class="rq-notify-copy">
              <p class="rq-notify-title">{{ item.title || 'Update' }}</p>
              <p class="rq-notify-message">{{ item.message || '-' }}</p>
              <p class="rq-notify-time">{{ formatRelativeTime(item.created_at) }}</p>
            </div>

            <button
              v-if="!item.is_read"
              class="rq-notify-mark-dot"
              type="button"
              :disabled="isMarking[item.notification_id]"
              :aria-label="`Mark notification ${item.title || 'update'} as read`"
              @click="$emit('mark-read', item.notification_id)"
            >
              <span v-if="isMarking[item.notification_id]" class="rq-notify-saving">Saving...</span>
              <span v-else class="rq-notify-dot" aria-hidden="true"></span>
              <span class="rq-sr-only">Mark read</span>
            </button>
            <span v-else class="rq-notify-read">Read</span>
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
    notificationKind(item) {
      const title = String(item?.title || '').toLowerCase()
      const message = String(item?.message || '').toLowerCase()
      const text = `${title} ${message}`

      if (text.includes('interview') || text.includes('schedule') || text.includes('meet')) {
        return 'interview'
      }

      if (text.includes('offer') || text.includes('selected') || text.includes('joining')) {
        return 'offer'
      }

      if (text.includes('drive') || text.includes('deadline') || text.includes('apply') || text.includes('application')) {
        return 'drive'
      }

      if (text.includes('shortlist') || text.includes('eligible') || text.includes('verified')) {
        return 'shortlist'
      }

      if (text.includes('resume') || text.includes('profile') || text.includes('document')) {
        return 'profile'
      }

      return 'general'
    },
    notificationIcon(item) {
      const kind = this.notificationKind(item)
      const iconMap = {
        interview: '🗓️',
        offer: '🎉',
        drive: '🆕',
        shortlist: '✅',
        profile: '📄',
        general: '🔔'
      }
      return iconMap[kind] || '🔔'
    },
    formatRelativeTime(value) {
      if (!value) return '-'
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return '-'

      const deltaMs = Date.now() - parsed.getTime()
      if (deltaMs < 0) {
        return parsed.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
      }

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
