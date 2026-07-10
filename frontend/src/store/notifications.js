import { defineStore } from 'pinia'

export const useNotificationStore = defineStore('notifications', {
  state: () => ({
    items: [],
    unreadCount: 0
  }),
  actions: {
    setNotifications(items = [], unreadCount = null) {
      this.items = items
      this.unreadCount = unreadCount !== null
        ? unreadCount
        : items.filter((item) => !item.is_read).length
    },
    markRead(notificationId) {
      const notification = this.items.find(
        (item) => item.id === notificationId || item.notification_id === notificationId
      )

      if (notification && !notification.is_read) {
        notification.is_read = true
        this.unreadCount = Math.max(0, this.unreadCount - 1)
      }
    },
    markAllRead() {
      this.items.forEach((item) => {
        item.is_read = true
      })
      this.unreadCount = 0
    },
    clear() {
      this.items = []
      this.unreadCount = 0
    }
  }
})
