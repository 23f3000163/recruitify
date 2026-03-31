<template>
  <aside class="rq-sidebar" :aria-expanded="!sidebarCollapsed">
    <button
      class="rq-sidebar-toggle"
      @click="$emit('toggle-sidebar')"
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
        <div class="rq-logo-mark">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M3 14L9 4L15 14" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M5.5 10.5h7" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
        </div>
        <span class="rq-logo-text" v-show="!sidebarCollapsed">Recruitify<span class="rq-logo-dot">.</span></span>
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

    <div class="rq-sb-user">
      <div class="rq-user-av">AD</div>
      <div class="rq-user-info" v-show="!sidebarCollapsed">
        <div class="rq-user-name">Admin (TPO)</div>
        <div class="rq-user-role">Full access</div>
      </div>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'Sidebar',
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
  emits: ['toggle-sidebar', 'select-view']
}
</script>
