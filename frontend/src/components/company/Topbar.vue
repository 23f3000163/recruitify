<template>
  <header class="rq-topbar" @click.stop>
    <div class="rq-topbar-left">
      <div class="rq-breadcrumb">
        <span class="rq-bc-app">Recruitify</span>
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
          <path d="M3.5 2l3 3-3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span class="rq-bc-page">{{ currentPageTitle }}</span>
      </div>
      <h1 class="rq-page-h1">{{ currentPageTitle }}</h1>
    </div>

    <div class="rq-topbar-right">
      <div v-if="companyProfile.status === 'pending'" class="rq-status-banner banner-pending">
        <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
          <circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" stroke-width="1.4" />
          <path d="M6.5 4v3l2 1.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        Pending admin approval
      </div>
      <div v-if="companyProfile.status === 'approved'" class="rq-status-banner banner-approved">
        <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
          <circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" stroke-width="1.4" />
          <path d="M4 6.5l2 2 3-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        Verified &amp; Approved
      </div>

      <div class="rq-topbar-sep"></div>

      <div class="rq-notif-trigger" @click.stop="$emit('toggle-notifications')">
        <button class="rq-topbar-icon-btn" :aria-label="`${unreadNotifCount} notifications`">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M13 11H3l1.5-2.5V7a3.5 3.5 0 017 0v1.5L13 11z" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M6.5 13a1.5 1.5 0 003 0" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
          </svg>
        </button>
        <span v-if="unreadNotifCount > 0" class="rq-notif-badge-outer">{{ unreadNotifCount }}</span>
      </div>

      <div class="rq-user-menu-wrap" ref="userMenuWrap" @click.stop>
        <button
          type="button"
          class="rq-topbar-user"
          @click="toggleUserMenu"
          :aria-expanded="userMenuOpen"
          aria-haspopup="menu"
        >
          <div class="rq-topbar-av" :style="{ background: companyProfile.avatarColor }">{{ companyProfile.initials }}</div>
          <div class="rq-topbar-uinfo">
            <div class="rq-topbar-uname">{{ companyProfile.hrName }}</div>
            <div class="rq-topbar-urole">HR Manager</div>
          </div>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M3 4.5l3 3 3-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>

        <Transition name="rq-user-menu-fade">
          <div v-if="userMenuOpen" class="rq-user-menu rq-user-menu-right" role="menu">
            <button type="button" class="rq-user-menu-item" @click="openProfile" role="menuitem">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <circle cx="6.5" cy="4" r="2.2" stroke="currentColor" stroke-width="1.3" />
                <path d="M2.5 11c0-2.2 1.8-3.6 4-3.6s4 1.4 4 3.6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" />
              </svg>
              Profile
            </button>
            <button type="button" class="rq-user-menu-item rq-user-menu-item-danger" @click="requestLogout" role="menuitem">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <path d="M8.5 2.5h2a1 1 0 011 1v6a1 1 0 01-1 1h-2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
                <path d="M5.5 9.5l3-3-3-3M8.5 6.5h-7" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
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
    currentPageTitle: {
      type: String,
      required: true
    },
    unreadNotifCount: {
      type: Number,
      required: true
    },
    companyProfile: {
      type: Object,
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
  emits: ['toggle-notifications', 'open-profile', 'request-logout'],
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
    openProfile() {
      this.userMenuOpen = false
      this.$emit('open-profile')
    },
    requestLogout() {
      this.userMenuOpen = false
      this.$emit('request-logout')
    }
  }
}
</script>
