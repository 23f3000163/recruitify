<template>
  <header class="cq-topbar">
    <div class="cq-topbar-left">
      <p class="cq-crumb">Company Workspace</p>
      <h1 class="cq-page-title">{{ currentPageTitle }}</h1>
    </div>

    <div class="cq-topbar-right">
      <p class="cq-access-chip" v-if="dashboardMessage">{{ dashboardMessage }}</p>
      <p class="cq-sync-chip" :class="`is-${syncTone}`" role="status" aria-live="polite" v-if="syncNote">{{ syncNote }}</p>

      <button
        class="cq-top-user"
        type="button"
        :aria-expanded="showUserMenu ? 'true' : 'false'"
        :aria-controls="userMenuId"
        @click.stop="toggleUserMenu"
      >
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
        <div v-if="showUserMenu" :id="userMenuId" class="cq-user-menu topbar" @click.stop>
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
    },
    syncNote: {
      type: String,
      default: ''
    },
    syncTone: {
      type: String,
      default: 'info'
    }
  },
  emits: ['request-logout'],
  data() {
    return {
      showUserMenu: false,
      userMenuId: 'company-topbar-user-menu'
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
    document.addEventListener('keydown', this.handleKeydown)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeUserMenu)
    document.removeEventListener('keydown', this.handleKeydown)
  },
  methods: {
    toggleUserMenu() {
      this.showUserMenu = !this.showUserMenu
    },
    handleKeydown(event) {
      if (event.key === 'Escape' && this.showUserMenu) {
        this.showUserMenu = false
      }
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
