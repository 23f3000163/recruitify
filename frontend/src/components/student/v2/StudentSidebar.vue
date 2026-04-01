<template>
  <aside class="rq-sidebar" :aria-expanded="!sidebarCollapsed">
    <button
      class="rq-sidebar-toggle"
      type="button"
      @click="$emit('toggle-sidebar')"
      :aria-label="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
        <path
          v-if="!sidebarCollapsed"
          d="M9 2L5 7l4 5"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <path
          v-else
          d="M5 2l4 5-4 5"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </button>

    <div class="rq-sb-header">
      <div class="rq-logo">
        <div class="rq-logo-mark">R</div>
        <span class="rq-logo-text" v-show="!sidebarCollapsed">Recruitify<span class="rq-logo-dot">.</span></span>
      </div>
    </div>

    <div class="rq-sb-role" v-show="!sidebarCollapsed">
      <span class="rq-role-pill rq-role-student">Student</span>
    </div>

    <nav class="rq-nav" role="navigation" aria-label="Student navigation">
      <span class="rq-nav-section" v-show="!sidebarCollapsed">MAIN</span>
      <button
        v-for="item in navItems"
        :key="item.id"
        class="rq-nav-btn"
        :class="{ 'is-active': activeView === item.id }"
        type="button"
        @click="$emit('navigate', item.id)"
        :aria-current="activeView === item.id ? 'page' : undefined"
      >
        <span class="rq-nav-icon" aria-hidden="true" v-html="item.svg"></span>
        <span class="rq-nav-label" v-show="!sidebarCollapsed">{{ item.label }}</span>
      </button>

      <span class="rq-nav-section" v-show="!sidebarCollapsed">PROFILE</span>
      <button
        v-for="item in profileNavItems"
        :key="item.id"
        class="rq-nav-btn"
        :class="{ 'is-active': activeView === item.id }"
        type="button"
        @click="$emit('navigate', item.id)"
      >
        <span class="rq-nav-icon" aria-hidden="true" v-html="item.svg"></span>
        <span class="rq-nav-label" v-show="!sidebarCollapsed">{{ item.label }}</span>
      </button>
    </nav>

    <div class="rq-sb-user">
      <div class="rq-user-av">{{ student.initials }}</div>
      <div class="rq-user-info" v-show="!sidebarCollapsed">
        <div class="rq-user-name">{{ student.name }}</div>
        <div class="rq-user-role">{{ student.branch }} - Y{{ student.year }}</div>
      </div>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'StudentSidebarV2',
  props: {
    sidebarCollapsed: {
      type: Boolean,
      default: false
    },
    activeView: {
      type: String,
      default: 'dashboard'
    },
    navItems: {
      type: Array,
      default: () => []
    },
    profileNavItems: {
      type: Array,
      default: () => []
    },
    student: {
      type: Object,
      default: () => ({
        initials: 'ST',
        name: 'Student',
        branch: 'CSE',
        year: 4
      })
    }
  },
  emits: ['toggle-sidebar', 'navigate']
}
</script>
