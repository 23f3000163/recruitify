<template>
  <div class="cq-app" :class="{ 'is-collapsed': sidebarCollapsed }">
    <CompanySidebar
      :sidebar-collapsed="sidebarCollapsed"
      :nav-items="navItems"
      :active-view="activeView"
      :company-name="companyIdentity.companyName || companyIdentity.username"
      @toggle-sidebar="toggleSidebar"
      @select-view="setActiveView($event)"
      @request-logout="handleLogout"
    />

    <div class="cq-main">
      <CompanyTopbar
        :current-page-title="currentPageTitle"
        :company-name="companyIdentity.companyName || companyIdentity.username"
        :company-email="companyIdentity.email"
        :dashboard-message="dashboardMessage"
        :sync-note="syncNote"
        :sync-tone="syncTone"
        @request-logout="handleLogout"
      />

      <main class="cq-page" role="main">
        <section v-if="isLoading" class="cq-state-card">
          <h2>Loading workspace...</h2>
          <p>Fetching your authenticated company dashboard context.</p>
        </section>

        <section v-else-if="loadError" class="cq-state-card is-error">
          <h2>Unable to load dashboard</h2>
          <p>{{ loadError }}</p>
          <button class="cq-btn" type="button" @click="bootstrapDashboard()">Retry</button>
        </section>

        <CompanyOverview
          v-else-if="activeView === 'overview'"
          :cards="kpiCards"
          :pipeline-stages="pipelineStages"
          :priority-actions="priorityActions"
          :recent-applicants="recentApplicants"
        />

        <DriveManagement
          v-else-if="activeView === 'drives'"
          @drive-updated="handleModuleUpdated('Drives')"
        />

        <CompanyApplications
          v-else-if="activeView === 'applications'"
          @applications-updated="handleModuleUpdated('Applications')"
        />

        <CompanyInterviews
          v-else-if="activeView === 'interviews'"
          @interviews-updated="handleModuleUpdated('Interviews')"
        />

        <CompanyOffers
          v-else-if="activeView === 'offers'"
          @offers-updated="handleModuleUpdated('Offers')"
        />

        <section v-else class="cq-state-card">
          <h2>Unknown view requested</h2>
          <p>This module is not available yet. Return to overview to continue.</p>
          <button class="cq-btn" type="button" @click="setActiveView('overview')">
            Back to Overview
          </button>
        </section>
      </main>
    </div>
  </div>
</template>

<script>
import { authApi, companyApi } from '../../api/api'
import CompanyApplications from '../../components/company/CompanyApplications.vue'
import CompanyInterviews from '../../components/company/CompanyInterviews.vue'
import CompanyOverview from '../../components/company/CompanyOverview.vue'
import CompanyOffers from '../../components/company/CompanyOffers.vue'
import DriveManagement from '../../components/company/DriveManagement.vue'
import CompanySidebar from '../../components/company/CompanySidebar.vue'
import CompanyTopbar from '../../components/company/CompanyTopbar.vue'
import './CompanyDashboard.css'

const DEFAULT_SUMMARY = Object.freeze({
  active_drives: 0,
  applications_received: 0,
  interviews_scheduled: 0,
  offers_released: 0
})

const STORAGE_KEYS = Object.freeze({
  activeView: 'company.dashboard.activeView',
  sidebarCollapsed: 'company.dashboard.sidebarCollapsed'
})

const SYNC_NOTE_TIMEOUT_MS = 4200

export default {
  name: 'CompanyDashboard',
  components: {
    CompanySidebar,
    CompanyTopbar,
    CompanyOverview,
    DriveManagement,
    CompanyApplications,
    CompanyInterviews,
    CompanyOffers
  },
  data() {
    return {
      sidebarCollapsed: false,
      activeView: 'overview',
      isLoading: true,
      loadError: '',
      dashboardMessage: '',
      syncNote: '',
      syncTone: 'info',
      syncNoteTimerId: null,
      companyIdentity: {
        userId: null,
        username: '',
        email: '',
        companyName: ''
      },
      summary: { ...DEFAULT_SUMMARY },
      pipelineStages: [],
      recentApplicants: []
    }
  },
  computed: {
    navItems() {
      return [
        { id: 'overview', label: 'Overview' },
        { id: 'drives', label: 'Drives' },
        { id: 'applications', label: 'Applications' },
        { id: 'interviews', label: 'Interviews' },
        { id: 'offers', label: 'Offers' }
      ]
    },
    currentPageTitle() {
      const labels = {
        overview: 'Overview',
        drives: 'Drive Management',
        applications: 'Applications',
        interviews: 'Interviews',
        offers: 'Offers'
      }
      return labels[this.activeView] || 'Overview'
    },
    kpiCards() {
      return [
        {
          id: 'active_drives',
          label: 'Active Drives',
          value: Number(this.summary.active_drives || 0).toLocaleString(),
          sub: 'Open or approval-pending drives'
        },
        {
          id: 'applications_received',
          label: 'Applications Received',
          value: Number(this.summary.applications_received || 0).toLocaleString(),
          sub: 'Across all listed drives'
        },
        {
          id: 'interviews_scheduled',
          label: 'Interviews Scheduled',
          value: Number(this.summary.interviews_scheduled || 0).toLocaleString(),
          sub: 'Upcoming interview rounds'
        },
        {
          id: 'offers_released',
          label: 'Offers Released',
          value: Number(this.summary.offers_released || 0).toLocaleString(),
          sub: 'Candidates moved to final stage'
        }
      ]
    },
    priorityActions() {
      const actions = []

      if (Number(this.summary.active_drives || 0) === 0) {
        actions.push({
          id: 'create-drive',
          title: 'Create your first placement drive',
          description: 'Add role details, eligibility, and deadline to start receiving applications.',
          state: 'Ready'
        })
      }

      if (Number(this.summary.interviews_scheduled || 0) === 0) {
        actions.push({
          id: 'interview-plan',
          title: 'Prepare interview workflow',
          description: 'Define rounds and panel availability before shortlisting starts.',
          state: 'Planned'
        })
      }

      if (!actions.length) {
        actions.push({
          id: 'review-pipeline',
          title: 'Review candidate progression',
          description: 'Monitor status transitions and remove stalled applications.',
          state: 'In Progress'
        })
      }

      return actions
    }
  },
  watch: {
    activeView(nextValue) {
      this.persistPreference(STORAGE_KEYS.activeView, String(nextValue || 'overview'))
    },
    sidebarCollapsed(nextValue) {
      this.persistPreference(STORAGE_KEYS.sidebarCollapsed, nextValue ? '1' : '0')
    }
  },
  created() {
    this.restoreViewState()
    this.restoreSidebarState()
    this.bootstrapDashboard()
  },
  beforeUnmount() {
    if (this.syncNoteTimerId) {
      clearTimeout(this.syncNoteTimerId)
      this.syncNoteTimerId = null
    }
  },
  methods: {
    async bootstrapDashboard(options = {}) {
      const silent = Boolean(options?.silent)
      const sourceLabel = String(options?.sourceLabel || '').trim()

      if (!silent) {
        this.isLoading = true
        this.loadError = ''
      }

      try {
        const [meResponse, dashboardResponse] = await Promise.all([
          authApi.getMe(),
          companyApi.getDashboard()
        ])

        const meData = meResponse?.data?.data || {}
        const dashboardData = dashboardResponse?.data?.data || {}
        const dashboardUser = dashboardData?.user || {}

        this.companyIdentity = {
          userId: meData.user_id || dashboardUser.user_id || null,
          username: meData.username || 'Company User',
          email: meData.email || '',
          companyName: dashboardUser.company_name || meData.username || 'Company User'
        }

        this.dashboardMessage = dashboardResponse?.data?.message || 'Authenticated'

        const summary = dashboardData.summary || {}
        this.summary = {
          active_drives: Number(summary.active_drives || summary.total_drives || 0),
          applications_received: Number(summary.applications_received || summary.total_applications || 0),
          interviews_scheduled: Number(summary.interviews_scheduled || 0),
          offers_released: Number(summary.offers_released || 0)
        }

        this.pipelineStages = this.buildPipelineStages(dashboardData.pipeline)
        this.recentApplicants = this.normalizeApplicants(dashboardData.recent_applicants)

        if (sourceLabel) {
          this.publishSyncNote(`${sourceLabel} synced`, 'success')
        }
      } catch (error) {
        const message =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Session could not be loaded. Please refresh or login again.'

        if (silent) {
          this.publishSyncNote(message, 'error')
        } else {
          this.loadError = message
        }
      } finally {
        if (!silent) {
          this.isLoading = false
        }
      }
    },
    handleModuleUpdated(sourceLabel) {
      this.bootstrapDashboard({
        silent: true,
        sourceLabel
      })
    },
    setActiveView(nextView) {
      if (this.isSupportedView(nextView)) {
        this.activeView = nextView
        return
      }

      this.activeView = 'overview'
    },
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    isSupportedView(viewId) {
      return this.navItems.some((item) => item.id === viewId)
    },
    restoreViewState() {
      try {
        const storedView = localStorage.getItem(STORAGE_KEYS.activeView)
        if (this.isSupportedView(storedView)) {
          this.activeView = storedView
        }
      } catch (error) {
        // Ignore storage read issues and fallback to defaults.
      }
    },
    restoreSidebarState() {
      try {
        const stored = localStorage.getItem(STORAGE_KEYS.sidebarCollapsed)
        if (stored === '1') {
          this.sidebarCollapsed = true
        }
      } catch (error) {
        // Ignore storage read issues and fallback to defaults.
      }
    },
    persistPreference(key, value) {
      try {
        localStorage.setItem(key, value)
      } catch (error) {
        // Ignore storage write issues so dashboard remains functional.
      }
    },
    publishSyncNote(message, tone = 'info') {
      if (this.syncNoteTimerId) {
        clearTimeout(this.syncNoteTimerId)
      }

      this.syncNote = message
      this.syncTone = tone

      this.syncNoteTimerId = setTimeout(() => {
        this.syncNote = ''
        this.syncTone = 'info'
        this.syncNoteTimerId = null
      }, SYNC_NOTE_TIMEOUT_MS)
    },
    buildPipelineStages(serverStages) {
      if (Array.isArray(serverStages) && serverStages.length) {
        const counts = serverStages.map((stage) => Number(stage.count || 0))
        const maxCount = Math.max(1, ...counts)

        return serverStages.map((stage, index) => ({
          id: stage.id || `stage-${index + 1}`,
          label: stage.label || 'Stage',
          count: Number(stage.count || 0),
          percent: Math.round((Number(stage.count || 0) / maxCount) * 100)
        }))
      }

      const fallbacks = [
        { id: 'pending', label: 'Pending Approval', count: Number(this.summary.active_drives || 0) },
        { id: 'screening', label: 'Application Screening', count: Number(this.summary.applications_received || 0) },
        { id: 'interviews', label: 'Interviews', count: Number(this.summary.interviews_scheduled || 0) },
        { id: 'offers', label: 'Offers', count: Number(this.summary.offers_released || 0) }
      ]
      const maxCount = Math.max(1, ...fallbacks.map((stage) => stage.count))

      return fallbacks.map((stage) => ({
        ...stage,
        percent: Math.round((stage.count / maxCount) * 100)
      }))
    },
    normalizeApplicants(rows) {
      if (!Array.isArray(rows)) {
        return []
      }

      return rows.map((row, index) => ({
        id: row.id || row.application_id || `app-${index + 1}`,
        name: row.name || row.student_name || 'Candidate',
        role: row.role || row.job_title || 'N/A',
        status: row.status || 'pending',
        updatedAt: row.updatedAt || row.updated_at || 'recently'
      }))
    },
    handleLogout() {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('user_id')
      this.$router.push('/login')
    }
  }
}
</script>
