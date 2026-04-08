<template>
  <nav class="nav" :class="{ scrolled }" id="navbar">

  <!-- Logo -->
  <AppLogo class="nav-logo" @click="scrollToTop" />

  <!-- Nav Links + Mega Menu -->
  <div class="nav-mid">
    <div class="mega-wrap">
      <a href="#features" class="nav-link" @click.prevent="scrollToSection('features')">
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
    <a href="#who" class="nav-link" @click.prevent="scrollToSection('who')">How It Works</a>
    <a href="#pipeline" class="nav-link" @click.prevent="scrollToSection('pipeline')">Process</a>
    <a href="#" class="nav-link" @click.prevent="scrollToTop">About</a>
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
import AppLogo from '../common/AppLogo.vue'

export default {
  name: 'Navbar',
  components: {
    AppLogo
  },
  props: {
    scrolled: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
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
    waitForElement(id, retries = 24) {
      return new Promise((resolve) => {
        const probe = (remaining) => {
          const element = document.getElementById(id)
          if (element) {
            resolve(true)
            return
          }
          if (remaining <= 0) {
            resolve(false)
            return
          }
          window.setTimeout(() => probe(remaining - 1), 40)
        }
        probe(retries)
      })
    },
    async ensureLandingReady() {
      if (this.$route.path !== '/') {
        await this.$router.push('/')
      }
      return this.waitForElement('navbar')
    },
    getTopOffset() {
      const navbar = document.getElementById('navbar')
      return Number(navbar?.offsetHeight || 66) + 12
    },
    async scrollToTop() {
      const ready = await this.ensureLandingReady()
      if (!ready) {
        return
      }
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      })
    },
    async scrollToSection(sectionId) {
      const ready = await this.ensureLandingReady()
      if (!ready) {
        return
      }

      const found = await this.waitForElement(sectionId)
      if (!found) {
        return
      }

      const section = document.getElementById(sectionId)
      if (!section) {
        return
      }

      const destination =
        window.scrollY + section.getBoundingClientRect().top - this.getTopOffset()

      window.scrollTo({
        top: Math.max(destination, 0),
        behavior: 'smooth'
      })
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
