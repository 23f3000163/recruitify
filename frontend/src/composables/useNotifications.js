import { ref } from 'vue'
import { useApi } from './useApi'

export function useNotifications(fetchFn) {
  const items = ref([])
  const unreadCount = ref(0)
  const { loading, error, execute } = useApi(fetchFn)

  async function fetchNotifications(...args) {
    const response = await execute(...args)
    const data = response?.data?.data || {}
    items.value = Array.isArray(data.items) ? data.items : []
    unreadCount.value = Number(data.unread_count || 0)
    return response
  }

  function markRead(notificationId) {
    const notification = items.value.find(
      (item) => item.id === notificationId || item.notification_id === notificationId
    )

    if (notification && !notification.is_read) {
      notification.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  }

  function markAllRead() {
    items.value.forEach((item) => {
      item.is_read = true
    })
    unreadCount.value = 0
  }

  return { items, unreadCount, loading, error, fetchNotifications, markRead, markAllRead }
}
