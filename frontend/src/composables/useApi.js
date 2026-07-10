import { ref } from 'vue'

export function useApi(apiFn, { fallbackMessage = 'Something went wrong. Please try again.' } = {}) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref('')

  async function execute(...args) {
    loading.value = true
    error.value = ''

    try {
      const response = await apiFn(...args)
      data.value = response
      return response
    } catch (err) {
      error.value =
        err?.response?.data?.error ||
        err?.response?.data?.message ||
        fallbackMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, execute }
}
