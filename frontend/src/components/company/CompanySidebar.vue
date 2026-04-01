<template>
  <aside class="cq-sidebar" :class="{ 'is-collapsed': sidebarCollapsed }">
    <button
      class="cq-sidebar-toggle"
      type="button"
      aria-label="Toggle sidebar"
      @click="$emit('toggle-sidebar')"
    >
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <header class="cq-sidebar-head">
      <div class="cq-logo-mark" aria-hidden="true">R</div>
      <div class="cq-logo-text" v-if="!sidebarCollapsed">Recruitify</div>
    </header>

    <nav class="cq-nav" aria-label="Company dashboard navigation">
      <button
        v-for="item in navItems"
        :key="item.id"
        class="cq-nav-btn"
        :class="{ 'is-active': item.id === activeView }"
        type="button"
        :aria-label="item.label"
        :aria-current="item.id === activeView ? 'page' : null"
        @click="$emit('select-view', item.id)"
      >
        <span class="cq-nav-ico" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path :d="iconPath(item.id)" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
        <span class="cq-nav-label" v-if="!sidebarCollapsed">{{ item.label }}</span>
      </button>
    </nav>

    <div class="cq-side-user-wrap">
      <button
        class="cq-side-user"
        type="button"
        :aria-expanded="showUserMenu ? 'true' : 'false'"
        :aria-controls="userMenuId"
        @click.stop="toggleUserMenu"
      >
        <div class="cq-user-avatar">{{ initials }}</div>
        <div class="cq-user-meta" v-if="!sidebarCollapsed">
          <p class="cq-user-name">{{ companyName || 'Company' }}</p>
          <p class="cq-user-role">Company</p>
        </div>
        <svg v-if="!sidebarCollapsed" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>

      <Transition name="cq-fade">
        <div v-if="showUserMenu" :id="userMenuId" class="cq-user-menu" @click.stop>
          <button type="button" class="cq-user-menu-btn danger" @click="requestLogout">
            Log out
          </button>
        </div>
      </Transition>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'CompanySidebar',
  props: {
    sidebarCollapsed: {
      type: Boolean,
      default: false
    },
    navItems: {
      type: Array,
      default: () => []
    },
    activeView: {
      type: String,
      default: 'overview'
    },
    companyName: {
      type: String,
      default: ''
    }
  },
  emits: ['toggle-sidebar', 'select-view', 'request-logout'],
  data() {
    return {
      showUserMenu: false,
      userMenuId: 'company-sidebar-user-menu'
    }
  },
  computed: {
    initials() {
      const name = (this.companyName || 'Company').trim()
      if (!name) return 'CO'
      return name
        .split(/\s+/)
        .slice(0, 2)
        .map((chunk) => chunk[0]?.toUpperCase() || '')
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
    iconPath(viewId) {
      const icons = {
        overview: 'M3 11.5L12 4l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z',
        drives: 'M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M4 9h16v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z',
        applications: 'M7 4h8l4 4v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z M15 4v4h4',
        interviews: 'M8 3v3M16 3v3M4 9h16M6 6h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2',
        offers: 'M7 12l3 3 7-7M4 12a8 8 0 1 0 16 0a8 8 0 1 0-16 0'
      }

      return icons[viewId] || icons.overview
    },
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
