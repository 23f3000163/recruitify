<template>
  <form class="auth-form" @submit.prevent="submit">
    <div class="auth-field">
      <label class="auth-label" for="student-username">Username</label>
      <input
        id="student-username"
        v-model.trim="form.username"
        class="auth-input"
        :class="{ 'input-error': errors.username }"
        type="text"
        placeholder="Enter username"
        autocomplete="username"
        required
      />
      <p v-if="errors.username" class="field-error">{{ errors.username }}</p>
    </div>

    <div class="auth-field">
      <label class="auth-label" for="student-email">Email</label>
      <input
        id="student-email"
        v-model.trim="form.email"
        class="auth-input"
        :class="{ 'input-error': errors.email }"
        type="email"
        placeholder="you@college.edu"
        autocomplete="email"
        required
      />
      <p v-if="errors.email" class="field-error">{{ errors.email }}</p>
    </div>

    <div class="auth-field">
      <label class="auth-label" for="student-password">Password</label>
      <div class="auth-input-wrap">
        <input
          id="student-password"
          v-model="form.password"
          class="auth-input"
          :class="{ 'input-error': errors.password }"
          :type="showPassword ? 'text' : 'password'"
          placeholder="Min 8 chars, upper, lower, number"
          autocomplete="new-password"
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
      <div v-if="form.password" class="pwd-strength">
        <div class="pwd-bar-track">
          <div class="pwd-bar-fill" :style="{ width: (passwordStrength.score / 5 * 100) + '%', background: passwordStrength.color }"></div>
        </div>
        <span class="pwd-label" :style="{ color: passwordStrength.color }">{{ passwordStrength.label }}</span>
      </div>
      <p v-if="errors.password" class="field-error">{{ errors.password }}</p>
    </div>

    <button class="auth-submit" type="submit" :disabled="isLoading">
      {{ isLoading ? 'Creating Student Account...' : 'Create Student Account' }}
    </button>
  </form>
</template>

<script>
export default {
  name: 'StudentForm',
  props: {
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      form: {
        username: '',
        email: '',
        password: ''
      },
      showPassword: false,
      errors: {}
    }
  },
  computed: {
    passwordStrength() {
      const password = this.form.password || ''
      let score = 0

      if (password.length >= 8) score += 1
      if (/[A-Z]/.test(password)) score += 1
      if (/[a-z]/.test(password)) score += 1
      if (/\d/.test(password)) score += 1
      if (/[^A-Za-z0-9]/.test(password)) score += 1

      if (score <= 1) return { score, label: 'Weak', color: '#e74c3c' }
      if (score === 2) return { score, label: 'Fair', color: '#e67e22' }
      if (score === 3) return { score, label: 'Good', color: '#2ecc71' }
      return { score, label: 'Strong', color: '#27ae60' }
    }
  },
  methods: {
    validate() {
      const errors = {}

      if (!this.form.username.trim()) {
        errors.username = 'Username is required.'
      }

      const email = this.form.email.trim()
      if (!email || !email.includes('@') || !email.includes('.')) {
        errors.email = 'Enter a valid email address.'
      }

      if (!this.form.password || this.form.password.length < 8) {
        errors.password = 'Password must be at least 8 characters.'
      }

      this.errors = errors
      return Object.keys(this.errors).length === 0
    },
    submit() {
      if (!this.validate()) return
      this.$emit('submit', { ...this.form })
    }
  }
}
</script>

<style scoped>
.field-error {
  font-size: 12px;
  color: #c0392b;
  margin-top: 4px;
}

.input-error {
  border-color: #c0392b !important;
  background: #fff8f8;
}

.pwd-strength {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
}

.pwd-bar-track {
  flex: 1;
  height: 4px;
  background: #e9ecef;
  border-radius: 2px;
  overflow: hidden;
}

.pwd-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease, background 0.3s ease;
}

.pwd-label {
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}
</style>
