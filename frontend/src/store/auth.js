import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    role: localStorage.getItem('role') || null,
    userId: localStorage.getItem('user_id') || null
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token)
  },
  actions: {
    setAuth(token, role, userId) {
      this.token = token
      this.role = role
      this.userId = userId

      localStorage.setItem('token', token)
      localStorage.setItem('role', role)
      localStorage.setItem('user_id', String(userId || ''))
    },
    logout() {
      this.token = null
      this.role = null
      this.userId = null

      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('user_id')
    }
  }
})
