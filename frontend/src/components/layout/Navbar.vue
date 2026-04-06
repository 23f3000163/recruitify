<template>
  <nav class="nav" :class="{ scrolled }" id="navbar">

  <!-- Logo -->
  <a class="nav-logo" href="#" @click.prevent="goHome">
    <div class="logo-icon">
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <path d="M3 14 L9 4 L15 14" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M5.5 10.5 h7" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
        <circle cx="9" cy="4" r="1.5" fill="white"/>
      </svg>
    </div>
    <span class="logo-name">Recruitify<span class="logo-dot">.</span></span>
  </a>

  <!-- Nav Links + Mega Menu -->
  <div class="nav-mid">
    <div class="mega-wrap">
      <a href="#features" class="nav-link" @click.prevent="goHash('#features')">
        Features
        <svg class="nav-caret" width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M3 4.5l3 3 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </a>
      <div class="mega">
        <div class="mega-grid">
          <div>
            <div class="mega-col-head">For Students</div>
            <a href="#" class="mega-item" @click.prevent><span class="mega-dot"></span>Auto Eligibility Check</a>
            <a href="#" class="mega-item" @click.prevent><span class="mega-dot"></span>Application Tracking</a>
            <a href="#" class="mega-item" @click.prevent><span class="mega-dot"></span>Resume Upload</a>
            <a href="#" class="mega-item" @click.prevent><span class="mega-dot"></span>Placement History</a>
          </div>
          <div>
            <div class="mega-col-head">For Companies</div>
            <a href="#" class="mega-item" @click.prevent><span class="mega-dot"></span>Drive Management</a>
            <a href="#" class="mega-item" @click.prevent><span class="mega-dot"></span>Applicant Shortlisting</a>
            <a href="#" class="mega-item" @click.prevent><span class="mega-dot"></span>Interview Scheduling</a>
            <a href="#" class="mega-item" @click.prevent><span class="mega-dot"></span>Offer Letters</a>
          </div>
          <div>
            <div class="mega-col-head">For Admin</div>
            <a href="#" class="mega-item" @click.prevent><span class="mega-dot"></span>Company Verification</a>
            <a href="#" class="mega-item" @click.prevent><span class="mega-dot"></span>Placement Analytics</a>
            <a href="#" class="mega-item" @click.prevent><span class="mega-dot"></span>User Management</a>
            <a href="#" class="mega-item" @click.prevent><span class="mega-dot"></span>Reports & CSV Export</a>
          </div>
        </div>
      </div>
    </div>
    <a href="#who" class="nav-link" @click.prevent="goHash('#who')">How It Works</a>
    <a href="#pipeline" class="nav-link" @click.prevent="goHash('#pipeline')">Process</a>
    <a href="#" class="nav-link" @click.prevent="goHome">About</a>
  </div>

  <!-- Role pills -->
  <div class="nav-pills">
    <button class="pill" :class="{ active: activePill === 'Student' }" @click="setActivePill('Student')">Student</button>
    <button class="pill" :class="{ active: activePill === 'Company' }" @click="setActivePill('Company')">Company</button>
    <button class="pill" :class="{ active: activePill === 'Admin' }" @click="setActivePill('Admin')">Admin</button>
  </div>

  <!-- Nav actions -->
  <div class="nav-right">
    <span class="net-pill" :class="{ offline: !isOnline }" :title="isOnline ? 'Connected to internet' : 'Offline mode'">
      <span class="net-dot"></span>
      {{ isOnline ? 'Online' : 'Offline' }}
    </span>
    <button
      v-if="canInstall"
      type="button"
      class="btn-ghost btn-install"
      @click="installApp"
    >
      Install
    </button>
    <a href="/login" class="btn-ghost" @click.prevent="go('/login')">Sign in</a>
    <a href="/register/student" class="btn-cta-nav" @click.prevent="go('/register/student')">
      Get Started
      <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
        <path d="M2 6.5h9M7 3l3.5 3.5L7 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </a>
  </div>

</nav>
</template>

<script>
export default {
  name: 'Navbar',
  props: {
    scrolled: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      activePill: 'Student',
      deferredInstallPrompt: null,
      canInstall: false,
      isOnline: true
    }
  },
  mounted() {
    if (typeof navigator !== 'undefined') {
      this.isOnline = navigator.onLine
    }

    window.addEventListener('beforeinstallprompt', this.handleBeforeInstallPrompt)
    window.addEventListener('appinstalled', this.handleAppInstalled)
    window.addEventListener('online', this.handleOnline)
    window.addEventListener('offline', this.handleOffline)
  },
  beforeUnmount() {
    window.removeEventListener('beforeinstallprompt', this.handleBeforeInstallPrompt)
    window.removeEventListener('appinstalled', this.handleAppInstalled)
    window.removeEventListener('online', this.handleOnline)
    window.removeEventListener('offline', this.handleOffline)
  },
  methods: {
    go(path) {
      this.$router.push(path)
    },
    goHome() {
      this.$router.push('/')
    },
    goHash(hash) {
      this.$router.push({ path: '/', hash })
    },
    setActivePill(pill) {
      this.activePill = pill
    },
    handleBeforeInstallPrompt(event) {
      event.preventDefault()
      this.deferredInstallPrompt = event
      this.canInstall = true
    },
    handleAppInstalled() {
      this.deferredInstallPrompt = null
      this.canInstall = false
    },
    handleOnline() {
      this.isOnline = true
    },
    handleOffline() {
      this.isOnline = false
    },
    async installApp() {
      if (!this.deferredInstallPrompt) {
        return
      }

      this.deferredInstallPrompt.prompt()
      try {
        await this.deferredInstallPrompt.userChoice
      } finally {
        this.deferredInstallPrompt = null
        this.canInstall = false
      }
    }
  }
}
</script>
