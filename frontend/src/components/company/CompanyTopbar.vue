<template>
  <header class="cq-topbar">
    <div class="cq-topbar-left">
      <p class="cq-crumb">Company Workspace</p>
      <h1 class="cq-page-title">{{ currentPageTitle }}</h1>
    </div>

    <div class="cq-topbar-right">
      <p class="cq-access-chip" v-if="dashboardMessage">{{ dashboardMessage }}</p>

      <button class="cq-top-user" type="button" @click.stop="toggleUserMenu">
        <div class="cq-user-avatar">{{ initials }}</div>
        <div class="cq-user-meta">
          <p class="cq-user-name">{{ companyName || 'Company User' }}</p>
          <p class="cq-user-role">{{ companyEmail || 'company@recruitify.dev' }}</p>
        </div>
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>

      <Transition name="cq-fade">
        <div v-if="showUserMenu" class="cq-user-menu topbar" @click.stop>
          <button type="button" class="cq-user-menu-btn danger" @click="requestLogout">
            Log out
          </button>
        </div>
      </Transition>
    </div>
  </header>
</template>

<script>
export default {
  name: 'CompanyTopbar',
  props: {
    currentPageTitle: {
      type: String,
      default: 'Overview'
    },
    companyName: {
      type: String,
      default: ''
    },
    companyEmail: {
      type: String,
      default: ''
    },
    dashboardMessage: {
      type: String,
      default: ''
    }
  },
  emits: ['request-logout'],
  data() {
    return {
      showUserMenu: false
    }
  },
  computed: {
    initials() {
      const source = this.companyName || this.companyEmail || 'Company'
      return source
        .trim()
        .split(/\s+|@/)
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase() || '')
        .join('')
    }
  },
  mounted() {
    document.addEventListener('click', this.closeUserMenu)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeUserMenu)
  },
  methods: {
    toggleUserMenu() {
      this.showUserMenu = !this.showUserMenu
    },
    closeUserMenu() {
      this.showUserMenu = false
    },
    requestLogout() {
      this.showUserMenu = false
      this.$emit('request-logout')
    }
  }
}
</script>
