<template>
  <aside class="rq-admin-notif-panel" role="complementary" aria-label="Admin notifications" @click.stop>
    <div class="rq-admin-notif-hd">
      <span class="rq-card-title">Notifications</span>
      <div class="rq-admin-notif-actions">
        <button
          class="rq-ghost rq-ghost-xs"
          type="button"
          :disabled="isMarkingAll || unreadCount === 0 || isLoading"
          @click="$emit('mark-all-read')"
        >
          {{ isMarkingAll ? 'Saving...' : 'Mark all read' }}
        </button>
        <button class="rq-modal-close" type="button" aria-label="Close notifications" @click="$emit('close')">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
          </svg>
        </button>
      </div>
    </div>

    <p v-if="errorMessage" class="rq-admin-notif-error" role="alert">{{ errorMessage }}</p>

    <div class="rq-admin-notif-list" :aria-busy="isLoading ? 'true' : 'false'">
      <article v-if="isLoading" class="rq-admin-notif-item">
        <div class="rq-notif-body">
          <div class="rq-notif-title">Loading notifications...</div>
        </div>
      </article>

      <article v-else-if="!notifications.length" class="rq-admin-notif-item">
        <div class="rq-notif-body">
          <div class="rq-notif-title">No notifications yet</div>
          <div class="rq-notif-sub">You will see admin alerts here.</div>
        </div>
      </article>

      <article
        v-for="notification in notifications"
        :key="notification.id"
        class="rq-admin-notif-item"
        :class="{ unread: !notification.read }"
        @click="markRead(notification)"
      >
        <div class="rq-notif-dot" :class="`ndot-${notification.type}`"></div>
        <div class="rq-notif-body">
          <div class="rq-notif-title">{{ notification.title }}</div>
          <div class="rq-notif-sub">{{ notification.sub }}</div>
          <div class="rq-notif-time">{{ notification.time }}</div>
        </div>
      </article>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'AdminNotificationPanel',
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
  emits: ['close', 'mark-read', 'mark-all-read'],
  methods: {
    markRead(notification) {
      if (!notification || notification.read || this.isMarking[notification.id]) {
        return
      }
      this.$emit('mark-read', notification.id)
    }
  }
}
</script>
