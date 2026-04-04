<template>
  <div class="rq-notif-panel" role="complementary" aria-label="Notifications" @click.stop>
    <div class="rq-notif-hd">
      <span class="rq-card-title">Notifications</span>
      <div style="display:flex;gap:8px;align-items:center">
        <button class="rq-ghost rq-ghost-xs" @click="$emit('mark-all-read')">Mark all read</button>
        <button class="rq-modal-close" @click="$emit('close')" aria-label="Close">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
          </svg>
        </button>
      </div>
    </div>
    <div class="rq-notif-list">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="rq-notif-item"
        :class="{ unread: !notification.read }"
        @click="$emit('mark-read', notification.id)"
      >
        <div class="rq-notif-dot" :class="'ndot-' + notification.type"></div>
        <div class="rq-notif-body">
          <div class="rq-notif-title">{{ notification.title }}</div>
          <div class="rq-notif-sub">{{ notification.sub }}</div>
          <div class="rq-notif-time">{{ notification.time }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NotificationPanel',
  props: {
    notifications: {
      type: Array,
      required: true
    }
  },
  emits: ['close', 'mark-all-read', 'mark-read']
}
</script>
