<template>
  <section class="auth-shell">
    <div class="auth-wrap">
      <section class="auth-panel auth-form-panel">
        <h2 class="auth-title auth-title-split">
          <span class="auth-title-line">Create your Recruitify account.</span>
          <span class="auth-title-line auth-title-line-soft">{{ registerText.line2 }}</span>
        </h2>
        <p class="auth-subtitle">{{ registerText.subtitle }}</p>

        <div class="auth-tabs">
          <button
            class="auth-tab"
            :class="{ active: activeRole === 'student' }"
            type="button"
            @click="switchRole('student')"
          >
            Student
          </button>
          <button
            class="auth-tab"
            :class="{ active: activeRole === 'company' }"
            type="button"
            @click="switchRole('company')"
          >
            Company
          </button>
        </div>

        <p class="auth-note">{{ registerText.note }}</p>

        <div v-if="errorMessage" class="auth-alert error">{{ errorMessage }}</div>
        <div v-if="successMessage" class="auth-alert success">{{ successMessage }}</div>

        <StudentForm
          v-if="activeRole === 'student'"
          :is-loading="isLoading"
          @submit="submitStudent"
        />

        <CompanyForm
          v-else
          :is-loading="isLoading"
          @submit="submitCompany"
        />

        <div class="auth-actions" style="margin-top: 14px;">
          <span style="color: var(--t2); font-size: 0.92rem;">Already have an account?</span>
          <button class="auth-inline-link" type="button" @click="goLogin">Sign in</button>
        </div>
      </section>
    </div>
  </section>
</template>

<script>
import StudentForm from '../components/auth/StudentForm.vue'
import CompanyForm from '../components/auth/CompanyForm.vue'
import { authApi } from '../api/api'

export default {
  name: 'RegisterView',
  components: {
    StudentForm,
    CompanyForm
  },
  computed: {
    registerText() {
      if (this.activeRole === 'company') {
        return {
          line2: 'Company registration',
          subtitle: 'Complete the form to create your company account.',
          note: 'Company accounts require admin approval before first login.'
        }
      }

      return {
        line2: 'Student registration',
        subtitle: 'Complete the form to create your student account.',
        note: 'Student accounts can log in right after registration.'
      }
    }
  },
  data() {
    return {
      activeRole: this.getInitialRole(),
      isLoading: false,
      errorMessage: '',
      successMessage: ''
    }
  },
  watch: {
    '$route.path': {
      immediate: false,
      handler() {
        this.activeRole = this.getInitialRole()
        this.errorMessage = ''
        this.successMessage = ''
      }
    }
  },
  methods: {
    getInitialRole() {
      if (this.$route.path.includes('/company')) return 'company'
      return 'student'
    },
    switchRole(role) {
      if (this.isLoading || role === this.activeRole) return

      this.activeRole = role
      this.errorMessage = ''
      this.successMessage = ''
      this.$router.push(role === 'student' ? '/register/student' : '/register/company')
    },
    goLogin() {
      this.$router.push('/login')
    },
    async submitStudent(payload) {
      await this.handleRegistration('student', payload)
    },
    async submitCompany(payload) {
      await this.handleRegistration('company', payload)
    },
    async handleRegistration(role, payload) {
      if (this.isLoading) return

      this.isLoading = true
      this.errorMessage = ''
      this.successMessage = ''

      try {
        if (role === 'student') {
          const response = await authApi.registerStudent(payload)
          this.successMessage = response.data?.data?.message || 'Student account created successfully.'
        } else {
          const response = await authApi.registerCompany(payload)
          this.successMessage = response.data?.message || 'Pending admin approval.'
        }

        setTimeout(() => {
          this.$router.push('/login')
        }, 1000)
      } catch (error) {
        this.errorMessage = error.response?.data?.error || error.response?.data?.message || 'Registration failed. Please check your details.'
      } finally {
        this.isLoading = false
      }
    }
  }
}
</script>
