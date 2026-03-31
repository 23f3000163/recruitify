<template>
  <section class="auth-shell">
    <div class="auth-wrap">
      <section class="auth-panel auth-form-panel">
        <h2 class="auth-title auth-title-split">
          <span class="auth-title-line">Welcome to Recruitify.</span>
          <span class="auth-title-line auth-title-line-soft">Sign in to continue</span>
        </h2>
        <p class="auth-subtitle">Use your registered email and password to access your account.</p>

        <div v-if="errorMessage" class="auth-alert error">{{ errorMessage }}</div>

        <form class="auth-form" @submit.prevent="login">
          <div class="auth-field">
            <label class="auth-label" for="login-email">Email</label>
            <input
              id="login-email"
              v-model.trim="form.email"
              class="auth-input"
              type="email"
              placeholder="you@example.com"
              autocomplete="email"
              required
            />
          </div>

          <div class="auth-field">
            <label class="auth-label" for="login-password">Password</label>
            <div class="auth-input-wrap">
              <input
                id="login-password"
                v-model="form.password"
                class="auth-input"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Enter your password"
                autocomplete="current-password"
                required
              />
              <button
                class="auth-password-toggle"
                type="button"
                @click="showPassword = !showPassword"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
              >
                <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M1.5 12s3.75-7.5 10.5-7.5S22.5 12 22.5 12s-3.75 7.5-10.5 7.5S1.5 12 1.5 12Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.8"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M3 3l18 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                  <path d="M10.58 10.58A2 2 0 0 0 13.4 13.4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                  <path d="M9.88 5.09A10.94 10.94 0 0 1 12 4.5c6.75 0 10.5 7.5 10.5 7.5a18.63 18.63 0 0 1-3.12 4.17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M6.61 6.61A18.7 18.7 0 0 0 1.5 12s3.75 7.5 10.5 7.5a10.9 10.9 0 0 0 4.7-1.05" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>

          <button class="auth-submit" type="submit" :disabled="isLoading">
            {{ isLoading ? 'Signing in...' : 'Sign In' }}
          </button>
        </form>

        <div class="auth-actions" style="margin-top: 14px;">
          <span style="color: var(--t2); font-size: 0.92rem;">New to Recruitify?</span>
          <button class="auth-inline-link" type="button" @click="goRegister">
            Create account
          </button>
        </div>
      </section>
    </div>
  </section>
</template>

<script>
import { authApi } from '../api/api'

export default {
  name: 'LoginView',
  data() {
    return {
      form: {
        email: '',
        password: ''
      },
      showPassword: false,
      isLoading: false,
      errorMessage: ''
    }
  },
  methods: {
    goRegister() {
      this.$router.push('/register/student')
    },
    getRedirectPath(role) {
      if (role === 'admin') return '/admin'
      if (role === 'student') return '/student'
      if (role === 'company') return '/company'
      return null
    },
    async login() {
      if (this.isLoading) return

      this.errorMessage = ''
      this.isLoading = true

      try {
        const response = await authApi.login(this.form)
        const token = response.data?.data?.token
        const role = response.data?.data?.role
        const userId = response.data?.data?.user_id
        const redirectPath = this.getRedirectPath(role)

        if (!token || !redirectPath) {
          this.errorMessage = 'Invalid login response from server.'
          return
        }

        localStorage.setItem('token', token)
        localStorage.setItem('role', role)
        localStorage.setItem('user_id', String(userId || ''))

        this.$router.push(redirectPath)
      } catch (error) {
        this.errorMessage = error.response?.data?.error || error.response?.data?.message || 'Login failed. Please try again.'
      } finally {
        this.isLoading = false
      }
    }
  }
}
</script>