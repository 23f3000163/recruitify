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

      <button class="rq-topbar-icon-btn" @click="$emit('open-profile')" aria-label="Settings">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <circle cx="8" cy="8" r="2.2" stroke="currentColor" stroke-width="1.4" />
          <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.2 3.2l1.4 1.4M11.4 11.4l1.4 1.4M3.2 12.8l1.4-1.4M11.4 4.6l1.4-1.4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" />
        </svg>
      </button>

      <div class="rq-topbar-user" @click="$emit('open-profile')">
        <div class="rq-topbar-av" :style="{ background: companyProfile.avatarColor }">{{ companyProfile.initials }}</div>
        <div class="rq-topbar-uinfo">
          <div class="rq-topbar-uname">{{ companyProfile.hrName }}</div>
          <div class="rq-topbar-urole">HR Manager</div>
        </div>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M3 4.5l3 3 3-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
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
  emits: ['toggle-notifications', 'open-profile']
}
</script>
