<template>
  <header class="rq-topbar">
    <div class="rq-topbar-left">
      <div class="rq-breadcrumb">
        <span class="rq-bc-app">Recruitify</span>
        <span class="rq-bc-sep">/</span>
        <span class="rq-bc-page">{{ currentPageTitle }}</span>
      </div>
      <h1 class="rq-page-h1">{{ currentPageTitle }}</h1>
    </div>

    <div class="rq-topbar-right">
      <div
        class="rq-search"
        :class="{ 'is-focused': searchFocused, 'is-active': searchQuery.length > 0 }"
        role="search"
      >
        <svg class="rq-search-ico" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <circle cx="6" cy="6" r="4.5" stroke="currentColor" stroke-width="1.5"/>
          <path d="M9.5 9.5L12 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>

        <input
          ref="searchInput"
          class="rq-search-field"
          type="text"
          :value="searchQuery"
          placeholder="Search drives, companies, roles"
          autocomplete="off"
          aria-label="Search drives, companies, roles"
          aria-keyshortcuts="Control+K"
          @focus="$emit('update:search-focused', true)"
          @blur="$emit('update:search-focused', false)"
          @input="$emit('update:search-query', $event.target.value)"
          @keydown.escape="$emit('update:search-query', '')"
        />

        <kbd class="rq-search-kbd" v-if="!searchQuery">Ctrl+K</kbd>

        <button
          v-if="searchQuery"
          class="rq-search-clear"
          type="button"
          aria-label="Clear search"
          @click="clearSearch"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <button
        class="rq-topbar-icon-btn"
        type="button"
        @click="$emit('navigate', 'notifications')"
        :aria-label="unreadCount > 0 ? `Open notifications (${unreadCount} unread)` : 'Open notifications'"
      >
        <span class="rq-notif-indicator" v-if="unreadCount > 0">{{ unreadCount }}</span>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M13 11H3l1.5-2.5V7a3.5 3.5 0 017 0v1.5L13 11z" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M6.5 13a1.5 1.5 0 003 0" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        </svg>
      </button>

      <button class="rq-topbar-user" type="button" aria-label="Open profile" @click="$emit('navigate', 'profile')">
        <div class="rq-topbar-av">{{ student.initials }}</div>
        <div class="rq-topbar-uinfo">
          <div class="rq-topbar-uname">{{ student.name }}</div>
          <div class="rq-topbar-urole">{{ student.roll }}</div>
        </div>
      </button>
    </div>
  </header>
</template>

<script>
export default {
  name: 'StudentTopbarV2',
  props: {
    currentPageTitle: {
      type: String,
      default: 'Dashboard'
    },
    searchQuery: {
      type: String,
      default: ''
    },
    searchFocused: {
      type: Boolean,
      default: false
    },
    unreadCount: {
      type: Number,
      default: 0
    },
    student: {
      type: Object,
      default: () => ({
        initials: 'ST',
        name: 'Student',
        roll: 'CS00B000'
      })
    }
  },
  emits: ['update:search-query', 'update:search-focused', 'navigate'],
  mounted() {
    document.addEventListener('keydown', this.handleGlobalHotkeys)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleGlobalHotkeys)
  },
  methods: {
    clearSearch() {
      this.$emit('update:search-query', '')
      this.focusSearchInput()
    },
    focusSearchInput() {
      const input = this.$refs.searchInput
      if (input && typeof input.focus === 'function') {
        input.focus()
        this.$emit('update:search-focused', true)
      }
    },
    handleGlobalHotkeys(event) {
      const key = String(event.key || '').toLowerCase()
      const tagName = String(event.target?.tagName || '').toLowerCase()
      const isTypingTarget =
        ['input', 'textarea', 'select'].includes(tagName) ||
        Boolean(event.target?.isContentEditable)

      const isCtrlK = (event.ctrlKey || event.metaKey) && key === 'k'
      const isSlashFocus = key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey

      if (isCtrlK || (isSlashFocus && !isTypingTarget)) {
        event.preventDefault()
        this.focusSearchInput()
      }
    }
  }
}
</script>
