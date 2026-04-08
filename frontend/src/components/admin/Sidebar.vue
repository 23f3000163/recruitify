<template>
  <aside class="rq-sidebar" :aria-expanded="!sidebarCollapsed" @click="handleSidebarTap">
    <button
      class="rq-sidebar-toggle"
      @click.stop="$emit('toggle-sidebar')"
      :aria-label="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      :title="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path v-if="!sidebarCollapsed" d="M9 2L5 7l4 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        <path v-else d="M5 2l4 5-4 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <div class="rq-sb-header">
      <div class="rq-logo">
        <AppLogo
          as="div"
          :collapsed="sidebarCollapsed"
          aria-label="Recruitify"
          :title="sidebarCollapsed ? 'Recruitify' : undefined"
          style="--app-logo-icon-size: 30px; --app-logo-lockup-width: 156px; --app-logo-lockup-height: 30px;"
        />
      </div>
    </div>

    <div class="rq-sb-role" v-show="!sidebarCollapsed">
      <span class="rq-role-pill">
        <svg width="9" height="9" viewBox="0 0 9 9" fill="currentColor"><path d="M4.5 0L5.7 3H9L6.3 4.9 7.4 8 4.5 6.1 1.6 8l1.1-3.1L0 3h3.3z"/></svg>
        Admin · TPO
      </span>
    </div>

    <nav class="rq-nav" role="navigation" aria-label="Main navigation">
      <span class="rq-nav-section" v-show="!sidebarCollapsed">MENU</span>
      <button
        v-for="item in navItems"
        :key="item.id"
        class="rq-nav-btn"
        :class="{ 'is-active': activeView === item.id }"
        @click="$emit('select-view', item.id)"
        :aria-current="activeView === item.id ? 'page' : undefined"
        :title="sidebarCollapsed ? item.label : ''"
      >
        <span class="rq-nav-icon" aria-hidden="true" v-html="item.svg"></span>
        <span class="rq-nav-label" v-show="!sidebarCollapsed">{{ item.label }}</span>
        <span v-if="item.badge && !sidebarCollapsed" class="rq-nav-badge">{{ item.badge }}</span>
        <span v-if="item.badge && sidebarCollapsed" class="rq-nav-badge-dot" aria-hidden="true"></span>
      </button>
    </nav>

    <div style="flex: 1"></div>

    <div class="rq-sb-user-wrap" ref="userMenuWrap" @click.stop>
      <button
        type="button"
        class="rq-sb-user rq-sb-user-btn"
        @click="toggleUserMenu"
        :aria-expanded="userMenuOpen"
        aria-haspopup="menu"
      >
        <div class="rq-user-av">AD</div>
        <div class="rq-user-info" v-show="!sidebarCollapsed">
          <div class="rq-user-name">Admin (TPO)</div>
          <div class="rq-user-role">Full access</div>
        </div>
        <svg v-show="!sidebarCollapsed" width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M3 4.5l3 3 3-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>

      <Transition name="rq-user-menu-fade">
        <div
          v-if="userMenuOpen"
          class="rq-user-menu rq-user-menu-up"
          :class="{ 'rq-user-menu-collapsed': sidebarCollapsed }"
          role="menu"
        >
          <button type="button" class="rq-user-menu-item rq-user-menu-item-danger" @click="requestLogout" role="menuitem">
            <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true"><path d="M8.5 2.5h2a1 1 0 011 1v6a1 1 0 01-1 1h-2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M5.5 9.5l3-3-3-3M8.5 6.5h-7" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
            Logout
          </button>
        </div>
      </Transition>
      </div>
  </aside>
</template>

<script>
import AppLogo from '../common/AppLogo.vue'

export default {
  name: 'Sidebar',
  components: {
    AppLogo
  },
  props: {
    sidebarCollapsed: {
      type: Boolean,
      required: true
    },
    navItems: {
      type: Array,
      required: true
    },
    activeView: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      userMenuOpen: false
    }
  },
  mounted() {
    document.addEventListener('click', this.handleClickOutside)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside)
  },
  emits: ['toggle-sidebar', 'select-view', 'request-logout'],
  methods: {
    handleSidebarTap(event) {
      const target = event.target
      if (!(target instanceof Element)) return

      if (target.closest('.rq-sidebar-toggle')) return
      if (target.closest('.rq-nav-btn')) return
      if (target.closest('.rq-sb-user-wrap')) return
      if (target.closest('.rq-user-menu')) return

      this.$emit('toggle-sidebar')
    },
    toggleUserMenu() {
      this.userMenuOpen = !this.userMenuOpen
    },
    handleClickOutside(event) {
      if (!this.userMenuOpen) return
      if (this.$refs.userMenuWrap && !this.$refs.userMenuWrap.contains(event.target)) {
        this.userMenuOpen = false
      }
    },
    requestLogout() {
      this.userMenuOpen = false
      this.$emit('request-logout')
    }
  }
}
</script>
