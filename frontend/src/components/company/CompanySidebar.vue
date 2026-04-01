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
        @click="$emit('select-view', item.id)"
      >
        <span class="cq-nav-ico" aria-hidden="true">{{ item.icon }}</span>
        <span class="cq-nav-label" v-if="!sidebarCollapsed">{{ item.label }}</span>
      </button>
    </nav>

    <div class="cq-side-user-wrap">
      <button class="cq-side-user" type="button" @click.stop="toggleUserMenu">
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
        <div v-if="showUserMenu" class="cq-user-menu" @click.stop>
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
      showUserMenu: false
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
