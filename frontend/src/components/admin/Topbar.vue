<template>
  <header class="rq-topbar">
    <div class="rq-topbar-left">
      <div class="rq-breadcrumb">
        <span class="rq-bc-app">Recruitify</span>
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true"><path d="M3.5 2l3 3-3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span class="rq-bc-page">{{ currentPageTitle }}</span>
      </div>
      <h1 class="rq-page-h1">{{ currentPageTitle }}</h1>
    </div>

    <div class="rq-topbar-right">
      <div class="rq-search" :class="{ 'is-focused': searchFocused, 'is-active': searchQuery.length > 0 }" role="search">
        <svg class="rq-search-ico" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <circle cx="6" cy="6" r="4.5" stroke="currentColor" stroke-width="1.5"/>
          <path d="M9.5 9.5L12 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <input
          :value="searchQuery"
          @focus="$emit('set-search-focused', true)"
          @blur="onBlur"
          @input="onInput"
          @keydown.escape="$emit('clear-search')"
          @keydown.enter="$emit('commit-search')"
          placeholder="Search  students, companies…"
          class="rq-search-field"
          aria-label="Global search"
          autocomplete="off"
        />

        <button v-if="searchQuery" class="rq-search-clear" @click="$emit('clear-search')" aria-label="Clear search">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
        </button>

        <div v-if="searchDropdownOpen && searchResults.length" class="rq-search-dropdown" role="listbox">
          <button
            v-for="r in searchResults"
            :key="r.id"
            class="rq-search-result"
            @mousedown.prevent="$emit('go-to-result', r)"
            role="option"
          >
            <div class="rq-av rq-av-xs" :style="{ background: r.color }">{{ r.initials }}</div>
            <div class="rq-sr-info">
              <span class="rq-sr-name">{{ r.name }}</span>
              <span class="rq-sr-type">{{ r.type }}</span>
            </div>
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2 5h6M5 2l3 3-3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <div class="rq-search-footer">
            <span>{{ searchResults.length }} result{{ searchResults.length !== 1 ? 's' : '' }}</span>
            <span>↵ to view all</span>
          </div>
        </div>

        <div v-if="searchDropdownOpen && searchQuery && !searchResults.length" class="rq-search-dropdown">
          <div class="rq-search-empty">No results for "<strong>{{ searchQuery }}</strong>"</div>
        </div>
      </div>

      <button class="rq-topbar-icon-btn" @click="$emit('toggle-notifications')" :aria-label="`${pendingCount} pending approvals`">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M13 11H3l1.5-2.5V7a3.5 3.5 0 017 0v1.5L13 11z" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M6.5 13a1.5 1.5 0 003 0" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        </svg>
        <span v-if="pendingCount > 0" class="rq-topbar-badge" aria-label="pending">{{ pendingCount }}</span>
      </button>

      <div class="rq-user-menu-wrap" ref="userMenuWrap" @click.stop>
        <button
          type="button"
          class="rq-topbar-user"
          @click="toggleUserMenu"
          :aria-expanded="userMenuOpen"
          aria-haspopup="menu"
        >
          <div class="rq-topbar-av">AD</div>
          <div class="rq-topbar-uinfo">
            <div class="rq-topbar-uname">Admin</div>
            <div class="rq-topbar-urole">TPO</div>
          </div>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M3 4.5l3 3 3-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>

        <Transition name="rq-user-menu-fade">
          <div v-if="userMenuOpen" class="rq-user-menu rq-user-menu-right" role="menu">
            <button type="button" class="rq-user-menu-item rq-user-menu-item-danger" @click="requestLogout" role="menuitem">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true"><path d="M8.5 2.5h2a1 1 0 011 1v6a1 1 0 01-1 1h-2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M5.5 9.5l3-3-3-3M8.5 6.5h-7" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
              Logout
            </button>
          </div>
        </Transition>
      </div>
    </div>
  </header>
</template>

<script>
export default {
  name: 'Topbar',
  props: {
    currentPageTitle: { type: String, required: true },
    searchQuery: { type: String, required: true },
    searchFocused: { type: Boolean, required: true },
    searchDropdownOpen: { type: Boolean, required: true },
    searchResults: { type: Array, required: true },
    pendingCount: { type: Number, required: true },
    showNotifications: { type: Boolean, required: true }
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
  emits: [
    'set-search-focused',
    'set-search-dropdown-open',
    'update-search-query',
    'handle-search',
    'clear-search',
    'commit-search',
    'go-to-result',
    'toggle-notifications',
    'request-logout'
  ],
  methods: {
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
    },
    onBlur() {
      this.$emit('set-search-focused', false)
      this.$emit('set-search-dropdown-open', this.searchQuery.length > 0)
    },
    onInput(event) {
      this.$emit('update-search-query', event.target.value)
      this.$emit('handle-search')
    }
  }
}
</script>
