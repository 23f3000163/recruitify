<template>
  <div class="rq-app rq-company-app" :class="{ 'is-collapsed': sidebarCollapsed }" @click="closeAllPanels">
    <Sidebar
      :sidebar-collapsed="sidebarCollapsed"
      :nav-items="navItems"
      :active-view="activeView"
      :company-profile="companyProfile"
      @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed"
      @select-view="handleNavClick"
      @request-logout="handleLogout"
    />

    <div class="rq-main">
      <Topbar
        :current-page-title="currentPageTitle"
        :company-profile="companyProfile"
        :unread-notif-count="unreadNotifCount"
        @toggle-notifications="toggleNotificationsPanel"
        @open-profile="activeView = 'profile'"
        @request-logout="handleLogout"
      />

      <Transition name="rq-slide">
        <NotificationPanel
          v-if="showNotifPanel"
          :notifications="notifications"
          :unread-count="unreadNotifCount"
          :error-message="notificationsError"
          :is-loading="isLoadingNotifications"
          :is-marking="isMarkingNotification"
          :is-marking-all="isMarkingAllNotifications"
          @close="closeNotificationsPanel"
          @mark-all-read="markAllRead"
          @mark-read="markNotificationRead"
        />
      </Transition>
      <div v-if="showNotifPanel" class="rq-notif-backdrop" @click="closeNotificationsPanel"></div>

      <main class="rq-page" role="main">
        <section v-if="isLoading" class="rq-card">
          <div class="rq-card-body">
            <div class="rq-empty">
              <div class="rq-empty-ico">⏳</div>
              <b>Loading dashboard</b>
              <span>Fetching company profile, drives, and applications.</span>
            </div>
          </div>
        </section>

        <section v-else-if="loadError" class="rq-card">
          <div class="rq-card-body">
            <div class="rq-empty">
              <div class="rq-empty-ico">⚠️</div>
              <b>Unable to load dashboard</b>
              <span>{{ loadError }}</span>
              <button class="rq-btn-primary" @click="bootstrapDashboard">Retry</button>
            </div>
          </div>
        </section>

        <template v-else>
          <div v-if="companyProfile.status === 'pending'" class="rq-approval-gate">
            <div class="rq-gate-icon">
              <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                <circle cx="14" cy="14" r="12" stroke="#D97706" stroke-width="2" />
                <path d="M14 8v6l4 3" stroke="#D97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </div>
            <div class="rq-gate-text">
              <strong>Your company registration is under review.</strong>
              <span>
                The admin team will approve your profile within 24-48 hours. You can view your profile and
                prepare drives in the meantime. Full functionality unlocks after approval.
              </span>
            </div>
            <div class="rq-gate-actions">
              <button class="rq-btn-ok" @click="activeView = 'profile'">View Profile →</button>
            </div>
          </div>

          <DashboardOverview
            v-if="activeView === 'dashboard'"
            :kpi-cards="kpiCards"
            :active-drives-funnel="activeDrivesFunnel"
            :company-profile="companyProfile"
            :pending-applications-count="pendingApplicationsCount"
            :recent-applications="recentApplications"
            :can-manage-actions="canManageApplications"
            @open-view="activeView = $event"
            @shortlist="shortlistApp"
            @reject="rejectApp"
          />

          <DrivesView
            v-if="activeView === 'drives'"
            :drive-filters="driveFilters"
            :drive-filter="driveFilter"
            :filtered-drives="filteredDrives"
            :company-status="companyProfile.status"
            @update:drive-filter="driveFilter = $event"
            @export-drives="doExport('drives')"
            @request-new-drive="openNewDriveModal"
            @open-applications="openApplicationsForDrive"
            @close-drive="closeDrive"
          />

          <ApplicationsView
            v-if="activeView === 'applications'"
            :app-search="appSearch"
            :app-search-focused="appSearchFocused"
            :app-drive-filter="appDriveFilter"
            :app-status-filter="appStatusFilter"
            :app-status-filters="appStatusFilters"
            :my-drives="myDrives"
            :selected-apps="selectedApps"
            :filtered-applications="filteredApplications"
            :all-page-selected="allPageSelected"
            :company-status="companyProfile.status"
            @update:app-search="appSearch = $event"
            @set-search-focus="appSearchFocused = $event"
            @update:app-drive-filter="appDriveFilter = $event"
            @update:app-status-filter="appStatusFilter = $event"
            @toggle-select-all="toggleSelectAll"
            @toggle-select-app="toggleSelectApp"
            @bulk-shortlist="bulkShortlist"
            @bulk-reject="bulkReject"
            @clear-selected="selectedApps = []"
            @export-applications="doExport('applications')"
            @shortlist="shortlistApp"
            @reject="rejectApp"
            @advance="advanceStage"
          />

          <ProfileView
            v-if="activeView === 'profile'"
            :company-profile="companyProfile"
            :profile-edit-mode="profileEditMode"
            :profile-edit="profileEdit"
            @toggle-edit="toggleProfileEdit"
            @update-field="updateProfileField"
            @save="saveProfile"
            @cancel="cancelProfileEdit"
          />

          <AnalyticsView
            v-if="activeView === 'analytics'"
            :analytics="analytics"
            :offer-rate-pct="offerRatePct"
            :donut-circ="donutCirc"
            :offer-rate-offset="offerRateOffset"
            :my-drives="myDrives"
            :branch-applicants="branchApplicants"
            :max-branch-count="maxBranchCount"
            @export-analytics="doExport('analytics')"
          />
        </template>
      </main>
    </div>

    <Transition name="rq-modal">
      <NewDriveModal
        v-if="showNewDriveModal"
        :new-drive="newDrive"
        @close="closeNewDriveModal"
        @submit="submitNewDrive"
        @update-field="setNewDriveField"
      />
    </Transition>

    <Transition name="rq-toast">
      <Toast v-if="toast.show" :toast="toast" @dismiss="toast.show = false" />
    </Transition>
  </div>
</template>

<script>
import ApplicationsView from '../../components/company/ApplicationsView.vue'
import AnalyticsView from '../../components/company/AnalyticsView.vue'
import DashboardOverview from '../../components/company/DashboardOverview.vue'
import DrivesView from '../../components/company/DrivesView.vue'
import NewDriveModal from '../../components/company/NewDriveModal.vue'
import NotificationPanel from '../../components/company/NotificationPanel.vue'
import ProfileView from '../../components/company/ProfileView.vue'
import Sidebar from '../../components/company/Sidebar.vue'
import Toast from '../../components/layout/Toast.vue'
import Topbar from '../../components/company/Topbar.vue'
import { companyApi, parseApiError } from '../../api/api'
import './CompanyDashboard.css'

const SUMMARY_DEFAULTS = Object.freeze({
  active_drives: 0,
  applications_received: 0,
  interviews_scheduled: 0,
  offers_released: 0,
  offers_accepted: 0,
  offers_rejected: 0,
  unread_notifications: 0
})

const DRIVE_FILTERS = Object.freeze([
  { l: 'All', v: '' },
  { l: 'Active', v: 'active' },
  { l: 'Pending', v: 'pending' },
  { l: 'Closed', v: 'closed' }
])

const APP_STATUS_FILTERS = Object.freeze([
  { l: 'All', v: '' },
  { l: 'Applied', v: 'applied' },
  { l: 'Shortlisted', v: 'shortlisted' },
  { l: 'Interview', v: 'interview' },
  { l: 'Offered', v: 'offered' },
  { l: 'Rejected', v: 'rejected' }
])

const AVATAR_COLORS = Object.freeze([
  '#2563EB',
  '#059669',
  '#D97706',
  '#7C3AED',
  '#DC2626',
  '#0284C7',
  '#6366F1',
  '#DB2777',
  '#65A30D',
  '#0D9488'
])

const BRANCH_COLORS = Object.freeze(['#2563EB', '#059669', '#D97706', '#7C3AED', '#DC2626'])

const NAV_SVGS = Object.freeze({
  home: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 6.5L8 2l6 4.5V14a1 1 0 01-1 1H3a1 1 0 01-1-1V6.5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 15V9h4v6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  drives: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="3" y="2" width="10" height="13" rx="1.5" stroke="currentColor" stroke-width="1.5"/><path d="M6 7h4M6 10h4M6 13h2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M5.5 2A1.5 1.5 0 018 1a1.5 1.5 0 012.5 1" stroke="currentColor" stroke-width="1.5"/></svg>`,
  apps: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="5" r="3" stroke="currentColor" stroke-width="1.5"/><path d="M2 14c0-3.314 2.686-5 6-5s6 1.686 6 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
  analytics: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 12l4-4 3 3 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 14.5h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
  profile: `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="3" width="12" height="12" rx="1" stroke="currentColor" stroke-width="1.5"/><path d="M5 7h2M9 7h2M5 10h2M9 10h2M7 15V12h2v3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M5 3V2a1 1 0 011-1h4a1 1 0 011 1v1" stroke="currentColor" stroke-width="1.5"/></svg>`
})

function createDefaultProfile() {
  return {
    name: 'Company',
    initials: 'CO',
    domain: '-',
    hrName: '-',
    hrEmail: '-',
    industry: '-',
    location: '-',
    registeredOn: '-',
    about: '-',
    status: 'pending',
    avatarColor: '#2563EB'
  }
}

function createDefaultNewDrive() {
  return {
    title: '',
    type: 'Full-time',
    salary: '',
    deadline: '',
    minCgpa: 7.5,
    branches: 'CSE',
    description: ''
  }
}

export default {
  name: 'CompanyDashboard',
  components: {
    Sidebar,
    Topbar,
    NotificationPanel,
    DashboardOverview,
    DrivesView,
    ApplicationsView,
    ProfileView,
    AnalyticsView,
    NewDriveModal,
    Toast
  },
  data() {
    return {
      isLoading: true,
      loadError: '',
      sidebarCollapsed: false,
      activeView: 'dashboard',
      showNotifPanel: false,
      showNewDriveModal: false,
      profileEditMode: false,

      companyProfile: createDefaultProfile(),
      profileEdit: {},
      dashboardSummary: { ...SUMMARY_DEFAULTS },

      myDrives: [],
      allApplications: [],
      notifications: [],
      notificationsError: '',
      isLoadingNotifications: false,
      isMarkingNotification: {},
      isMarkingAllNotifications: false,

      driveFilter: '',
      appSearch: '',
      appSearchFocused: false,
      appDriveFilter: '',
      appStatusFilter: '',
      selectedApps: [],

      newDrive: createDefaultNewDrive(),

      toast: { show: false, message: '', icon: '', type: 'success' },
      toastTimerId: null
    }
  },
  computed: {
    navItems() {
      return [
        { id: 'dashboard', label: 'Dashboard', svg: NAV_SVGS.home, badge: null, locked: false },
        { id: 'drives', label: 'Placement Drives', svg: NAV_SVGS.drives, badge: null, locked: true },
        {
          id: 'applications',
          label: 'Applications',
          svg: NAV_SVGS.apps,
          badge: this.pendingApplicationsCount > 0 ? this.pendingApplicationsCount : null,
          locked: true
        },
        { id: 'analytics', label: 'Analytics', svg: NAV_SVGS.analytics, badge: null, locked: false },
        { id: 'profile', label: 'Company Profile', svg: NAV_SVGS.profile, badge: null, locked: false }
      ]
    },
    currentPageTitle() {
      const labels = {
        dashboard: 'Dashboard',
        drives: 'Placement Drives',
        applications: 'Applications',
        profile: 'Company Profile',
        analytics: 'Analytics'
      }
      return labels[this.activeView] || 'Dashboard'
    },
    driveFilters() {
      return DRIVE_FILTERS
    },
    appStatusFilters() {
      return APP_STATUS_FILTERS
    },
    unreadNotifCount() {
      return this.notifications.filter((notification) => !notification.read).length
    },
    pendingApplicationsCount() {
      return this.allApplications.filter((application) => application.status === 'applied').length
    },
    activeDrivesFunnel() {
      return this.myDrives.filter((drive) => drive.status === 'active')
    },
    filteredDrives() {
      if (!this.driveFilter) {
        return this.myDrives
      }
      return this.myDrives.filter((drive) => drive.status === this.driveFilter)
    },
    filteredApplications() {
      const query = String(this.appSearch || '').trim().toLowerCase()

      return this.allApplications.filter((application) => {
        const matchesQuery =
          !query ||
          String(application.student || '').toLowerCase().includes(query) ||
          String(application.roll || '').toLowerCase().includes(query) ||
          String(application.email || '').toLowerCase().includes(query)

        const matchesDrive = !this.appDriveFilter || Number(application.driveId) === Number(this.appDriveFilter)
        const matchesStatus = !this.appStatusFilter || application.status === this.appStatusFilter

        return matchesQuery && matchesDrive && matchesStatus
      })
    },
    recentApplications() {
      return [...this.allApplications].sort((left, right) => Number(right.id) - Number(left.id)).slice(0, 8)
    },
    allPageSelected() {
      return this.filteredApplications.length > 0 && this.filteredApplications.every((application) => this.selectedApps.includes(application.id))
    },
    analytics() {
      return {
        applied: this.allApplications.filter((application) => application.status === 'applied').length,
        shortlisted: this.allApplications.filter((application) => application.status === 'shortlisted').length,
        interview: this.allApplications.filter((application) => application.status === 'interview').length,
        offered: this.allApplications.filter((application) => application.status === 'offered').length,
        rejected: this.allApplications.filter((application) => application.status === 'rejected').length
      }
    },
    branchApplicants() {
      const counts = {}

      this.allApplications.forEach((application) => {
        const branch = String(application.branch || 'OTHER').toUpperCase()
        counts[branch] = (counts[branch] || 0) + 1
      })

      const entries = Object.entries(counts)
      if (!entries.length) {
        return []
      }

      return entries
        .sort((left, right) => right[1] - left[1])
        .map(([name, count], index) => ({
          name,
          count,
          color: BRANCH_COLORS[index % BRANCH_COLORS.length]
        }))
    },
    maxBranchCount() {
      return Math.max(...this.branchApplicants.map((branch) => branch.count), 1)
    },
    donutCirc() {
      return +(2 * Math.PI * 46).toFixed(2)
    },
    offerRatePct() {
      return this.analytics.applied > 0 ? Math.round((this.analytics.offered / this.analytics.applied) * 100) : 0
    },
    offerRateOffset() {
      return +(this.donutCirc * (1 - this.analytics.offered / Math.max(this.analytics.applied, 1))).toFixed(2)
    },
    kpiCards() {
      const activeDrives = this.myDrives.filter((drive) => drive.status === 'active').length
      const totalApplications = this.allApplications.length
      const shortlisted = this.analytics.shortlisted
      const offers = this.analytics.offered

      return [
        {
          id: 'drives',
          label: 'Active Drives',
          value: String(activeDrives),
          link: 'drives',
          delta: `${this.myDrives.filter((drive) => drive.status === 'pending').length} pending approval`,
          up: false,
          pct: this.pct(activeDrives, Math.max(this.myDrives.length, 1)),
          color: '#2563EB',
          colorLt: '#EFF6FF',
          svg: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="4" y="2" width="12" height="16" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M7 8h6M7 11h6M7 14h4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>`
        },
        {
          id: 'applications',
          label: 'Total Applications',
          value: String(totalApplications),
          link: 'applications',
          delta: `${this.pendingApplicationsCount} awaiting review`,
          up: true,
          pct: this.pct(totalApplications, Math.max(this.dashboardSummary.applications_received, totalApplications, 1)),
          color: '#059669',
          colorLt: '#ECFDF5',
          svg: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="6" r="4" stroke="currentColor" stroke-width="1.6"/><path d="M3 18c0-3.866 3.134-6 7-6s7 2.134 7 6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>`
        },
        {
          id: 'shortlisted',
          label: 'Shortlisted',
          value: String(shortlisted),
          link: 'applications',
          delta: `${this.analytics.interview} in interview stage`,
          up: false,
          pct: this.pct(shortlisted, Math.max(totalApplications, 1)),
          color: '#7C3AED',
          colorLt: '#F5F3FF',
          svg: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 2l2.1 4.3L17 7.6l-3.5 3.4.8 4.8L10 13.6l-4.3 2.2.8-4.8L3 7.6l4.9-.9z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`
        },
        {
          id: 'offered',
          label: 'Offers Extended',
          value: String(offers),
          link: 'analytics',
          delta: `${this.offerRatePct}% offer rate`,
          up: true,
          pct: this.pct(offers, Math.max(totalApplications, 1)),
          color: '#D97706',
          colorLt: '#FFFBEB',
          svg: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3 10l5 5 9-9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`
        }
      ]
    },
    canManageApplications() {
      return this.companyProfile.status === 'approved'
    }
  },
  watch: {
    profileEditMode(nextValue) {
      if (nextValue) {
        this.profileEdit = { ...this.companyProfile }
      }
    }
  },
  created() {
    this.bootstrapDashboard()
  },
  beforeUnmount() {
    if (this.toastTimerId) {
      clearTimeout(this.toastTimerId)
      this.toastTimerId = null
    }
  },
  methods: {
    pct(value, total) {
      return total > 0 ? Math.round((value / total) * 100) : 0
    },
    buildSummaryFromLoadedData(summaryPayload = null) {
      const mappedSummary = companyApi.mapDashboardSummary(summaryPayload || {})
      const hasSummaryPayload = Boolean(summaryPayload)

      if (hasSummaryPayload) {
        return mappedSummary
      }

      return {
        ...mappedSummary,
        active_drives: this.myDrives.filter((drive) => ['active', 'pending'].includes(drive.status)).length,
        applications_received: this.allApplications.length,
        interviews_scheduled: this.allApplications.filter((application) => application.status === 'interview').length,
        offers_released: this.allApplications.filter((application) => application.status === 'offered').length,
        offers_accepted: this.allApplications.filter((application) => application.status === 'placed').length,
        offers_rejected: this.allApplications.filter((application) => application.status === 'rejected').length,
        unread_notifications: this.notifications.filter((notification) => !notification.read).length
      }
    },
    closeAllPanels() {
      this.closeNotificationsPanel()
    },
    closeNotificationsPanel() {
      this.showNotifPanel = false
    },
    toggleNotificationsPanel() {
      if (this.showNotifPanel) {
        this.closeNotificationsPanel()
        return
      }

      this.showNotifPanel = true
      this.loadNotifications({ silent: true })
    },
    handleLogout() {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('user_id')
      this.$router.push('/login')
    },
    handleNavClick(item) {
      if (item.locked && this.companyProfile.status !== 'approved') {
        this.toast_show('This section is available after admin approval.', 'warning')
        return
      }

      this.activeView = item.id
      this.showNotifPanel = false
    },
    initialsFor(value) {
      const safe = String(value || '').trim()
      if (!safe) {
        return 'NA'
      }

      const parts = safe.split(/\s+/).filter(Boolean)
      if (parts.length === 1) {
        return parts[0].slice(0, 2).toUpperCase()
      }

      return `${parts[0][0] || ''}${parts[1][0] || ''}`.toUpperCase()
    },
    colorFor(value) {
      const safe = String(value || '')
      let hash = 0

      for (let index = 0; index < safe.length; index += 1) {
        hash = (hash * 31 + safe.charCodeAt(index)) >>> 0
      }

      return AVATAR_COLORS[hash % AVATAR_COLORS.length]
    },
    normalizeCompanyStatus(rawStatus) {
      const normalized = String(rawStatus || '').trim().toLowerCase()
      if (['approved', 'pending', 'rejected'].includes(normalized)) {
        return normalized
      }
      return 'approved'
    },
    normalizeApplicationStatus(rawStatus) {
      const normalized = String(rawStatus || '').trim().toLowerCase()
      const aliases = {
        pending: 'applied',
        waitlisted: 'shortlisted',
        interviewed: 'interview',
        selected: 'offered',
        offered: 'offered',
        placed: 'offered'
      }
      return aliases[normalized] || normalized || 'applied'
    },
    normalizeDriveStatus(rawStatus) {
      const normalized = String(rawStatus || '').trim().toLowerCase()
      if (normalized === 'approved') {
        return 'active'
      }
      if (normalized === 'active' || normalized === 'pending' || normalized === 'closed') {
        return normalized
      }
      return 'pending'
    },
    formatDate(rawValue) {
      if (!rawValue) {
        return '-'
      }

      const parsed = new Date(rawValue)
      if (Number.isNaN(parsed.getTime())) {
        return String(rawValue)
      }

      return parsed.toISOString().slice(0, 10)
    },
    formatDeadline(rawValue) {
      if (!rawValue) {
        return '-'
      }

      const parsed = new Date(rawValue)
      if (Number.isNaN(parsed.getTime())) {
        return String(rawValue)
      }

      return parsed.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric'
      })
    },
    formatRelativeTime(rawValue) {
      if (!rawValue) {
        return 'recently'
      }

      const parsed = new Date(rawValue)
      if (Number.isNaN(parsed.getTime())) {
        return 'recently'
      }

      const deltaMs = Date.now() - parsed.getTime()
      const deltaMinutes = Math.max(1, Math.floor(deltaMs / 60000))

      if (deltaMinutes < 60) {
        return `${deltaMinutes} min ago`
      }

      const deltaHours = Math.floor(deltaMinutes / 60)
      if (deltaHours < 24) {
        return `${deltaHours} hr ago`
      }

      const deltaDays = Math.floor(deltaHours / 24)
      return deltaDays === 1 ? 'Yesterday' : `${deltaDays} days ago`
    },
    normalizeNotificationType(notification) {
      const text = `${notification.title || ''} ${notification.message || ''}`.toLowerCase()

      if (text.includes('reject') || text.includes('failed')) {
        return 'danger'
      }
      if (text.includes('accept') || text.includes('approved') || text.includes('success')) {
        return 'success'
      }
      if (text.includes('pending') || text.includes('deadline')) {
        return 'warning'
      }
      return 'info'
    },
    normalizeApplication(item) {
      const id = Number(item.application_id || item.id || 0)
      const studentName = item.student_name || item?.student?.name || 'Candidate'
      const branch = item.student_branch || item?.student?.branch || 'OTHER'

      return {
        id,
        driveId: Number(item.drive_id || item.job_id || item?.drive?.id || 0),
        student: studentName,
        roll: item.roll_number || item.student_roll || `APP-${id}`,
        branch,
        year: item.student_year || item?.student?.year || '-',
        cgpa: Number(item.student_cgpa || item?.student?.cgpa || 0),
        email: item.student_email || item?.student?.email || '-',
        drive: item.drive_title || item?.drive?.title || 'Drive',
        date: this.formatDate(item.applied_at || item.application_date || item.created_at),
        status: this.normalizeApplicationStatus(item.status || item.legacy_status),
        initials: this.initialsFor(studentName),
        color: this.colorFor(studentName),
        notes: item.notes || '',
        rejectionReason: item.rejection_reason || ''
      }
    },
    buildDriveStages(driveId) {
      const perDriveApps = this.allApplications.filter((application) => Number(application.driveId) === Number(driveId))
      const countByStatus = (status) => perDriveApps.filter((application) => application.status === status).length

      return [
        { label: 'Applied', count: countByStatus('applied'), color: '#D97706' },
        { label: 'Shortlisted', count: countByStatus('shortlisted'), color: '#7C3AED' },
        { label: 'Interview', count: countByStatus('interview'), color: '#2563EB' },
        { label: 'Offered', count: countByStatus('offered'), color: '#059669' }
      ]
    },
    normalizeDrive(item) {
      const id = Number(item.id || item.drive_id || 0)
      const title = item.title || item.job_title || 'Placement Drive'
      const status = this.normalizeDriveStatus(item.status)
      const salary = item.salary_lpa ? `₹${Number(item.salary_lpa).toFixed(1)} LPA` : 'Not specified'
      const branches = Array.isArray(item.eligible_branches) && item.eligible_branches.length
        ? item.eligible_branches.join(', ')
        : 'CSE'

      return {
        id,
        title,
        role: item.job_title || title,
        type: item.interview_mode ? String(item.interview_mode).toUpperCase() : 'Full-time',
        salary,
        applicants: Number(item.applications_count || 0),
        deadline: this.formatDeadline(item.deadline || item.application_deadline),
        status,
        initials: this.initialsFor(this.companyProfile.name),
        avatarColor: this.companyProfile.avatarColor,
        minCgpa: Number(item.min_cgpa || 0),
        branches,
        stages: this.buildDriveStages(id)
      }
    },
    normalizeNotification(item) {
      return {
        id: Number(item.notification_id || item.id || 0),
        title: item.title || 'Notification',
        sub: item.message || '-',
        time: this.formatRelativeTime(item.created_at || item.sent_at),
        type: this.normalizeNotificationType(item),
        read: Boolean(item.is_read)
      }
    },
    normalizeCompanyProfile(profilePayload, dashboardUser = {}) {
      const companyName = profilePayload.company_name || dashboardUser.company_name || profilePayload.username || 'Company'
      const domain = profilePayload.website || profilePayload.domain || '-'
      const hrName = profilePayload.hr_contact_name || profilePayload.hrName || profilePayload.username || 'HR Manager'
      const hrEmail = profilePayload.hr_contact_email || profilePayload.email || '-'

      return {
        ...createDefaultProfile(),
        name: companyName,
        initials: this.initialsFor(companyName),
        domain,
        hrName,
        hrEmail,
        industry: profilePayload.industry || '-',
        location: profilePayload.location || '-',
        registeredOn: this.formatDate(profilePayload.created_at),
        about: profilePayload.company_description || profilePayload.about || '-',
        status: this.normalizeCompanyStatus(profilePayload.approval_status || dashboardUser.approval_status),
        avatarColor: this.colorFor(companyName)
      }
    },
    applyApplicationUpdate(applicationId, updatedPayload = {}) {
      const target = this.allApplications.find((application) => Number(application.id) === Number(applicationId))
      if (!target) {
        return
      }

      if (updatedPayload.status || updatedPayload.legacy_status) {
        target.status = this.normalizeApplicationStatus(updatedPayload.status || updatedPayload.legacy_status)
      }
      if (Object.prototype.hasOwnProperty.call(updatedPayload, 'notes')) {
        target.notes = updatedPayload.notes || ''
      }
      if (Object.prototype.hasOwnProperty.call(updatedPayload, 'rejection_reason')) {
        target.rejectionReason = updatedPayload.rejection_reason || ''
      }

      this.refreshDriveStats()
    },
    refreshDriveStats() {
      this.myDrives = this.myDrives.map((drive) => {
        const driveApps = this.allApplications.filter((application) => Number(application.driveId) === Number(drive.id))

        return {
          ...drive,
          applicants: driveApps.length,
          stages: this.buildDriveStages(drive.id)
        }
      })
    },
    parseBranches(rawText) {
      const text = String(rawText || '').trim()
      if (!text || text.toLowerCase() === 'all') {
        return ['CSE', 'ECE', 'MECH', 'EE', 'OTHER']
      }

      const map = {
        cse: 'CSE',
        ece: 'ECE',
        mech: 'MECH',
        me: 'MECH',
        ee: 'EE',
        eee: 'EE',
        other: 'OTHER'
      }

      const branches = text
        .split(',')
        .map((branch) => map[String(branch || '').trim().toLowerCase()] || 'OTHER')
        .filter((branch, index, self) => branch && self.indexOf(branch) === index)

      return branches.length ? branches : ['CSE']
    },
    parseSalaryLpa(rawValue) {
      const parsed = parseFloat(String(rawValue || '').replace(/[^0-9.]/g, ''))
      if (Number.isNaN(parsed)) {
        return null
      }
      return parsed
    },
    normalizeInput(value) {
      const text = String(value || '').trim()
      return text === '-' ? '' : text
    },
    isValidEmail(value) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || '').trim())
    },
    isValidWebsite(value) {
      const text = String(value || '').trim()
      if (!text) {
        return true
      }
      return /^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(\/.*)?$/.test(text)
    },
    validateCompanyProfilePayload(payload) {
      if (!payload.company_name || payload.company_name.length < 2) {
        return 'Company name must be at least 2 characters.'
      }
      if (!payload.hr_contact_name || payload.hr_contact_name.length < 2) {
        return 'HR contact name must be at least 2 characters.'
      }
      if (!payload.hr_contact_email) {
        return 'HR contact email is required.'
      }
      if (!this.isValidEmail(payload.hr_contact_email)) {
        return 'Enter a valid HR contact email.'
      }
      if (!payload.industry) {
        return 'Industry is required.'
      }
      if (!this.isValidWebsite(payload.website)) {
        return 'Enter a valid website/domain.'
      }
      return ''
    },
    validateNewDrivePayload(newDrive, salaryLpa) {
      const title = String(newDrive.title || '').trim()
      if (!title) {
        return 'Please fill in all required fields.'
      }
      if (title.length < 3) {
        return 'Drive title must be at least 3 characters.'
      }

      if (salaryLpa === null || salaryLpa <= 0 || salaryLpa > 200) {
        return 'CTC / Stipend must be a valid number between 0 and 200.'
      }

      const minCgpa = Number(newDrive.minCgpa)
      if (Number.isNaN(minCgpa) || minCgpa < 0 || minCgpa > 10) {
        return 'Minimum CGPA must be between 0 and 10.'
      }

      if (!newDrive.deadline) {
        return 'Please fill in all required fields.'
      }

      const deadlineDate = new Date(`${newDrive.deadline}T00:00:00`)
      if (Number.isNaN(deadlineDate.getTime())) {
        return 'Enter a valid application deadline.'
      }

      const today = new Date()
      today.setHours(0, 0, 0, 0)
      if (deadlineDate < today) {
        return 'Application deadline cannot be in the past.'
      }

      return ''
    },
    handleApiError(error, fallbackMessage, options = {}) {
      const message = parseApiError(error, fallbackMessage)
      const statusCode = error?.response?.status

      if (statusCode === 401) {
        this.$router.push('/login')
      }

      if (options.showToast) {
        if (statusCode === 403) {
          this.toast_show('You do not have permission to perform this action.', 'warning')
        } else {
          this.toast_show(message, 'danger')
        }
      }

      return message
    },
    async bootstrapDashboard() {
      this.isLoading = true
      this.loadError = ''
      this.notificationsError = ''

      const [dashboardResult, profileResult, drivesResult, applicationsResult, notificationsResult] = await Promise.allSettled([
        companyApi.getDashboardData(),
        companyApi.getProfile(),
        companyApi.getDrives({ page: 1, limit: 100 }),
        companyApi.getApplications({ page: 1, limit: 100 }),
        companyApi.getNotifications({ page: 1, limit: 100, is_read: 'all' })
      ])

      const blockingErrors = []
      const nonBlockingErrors = []
      let shouldDeriveSummary = false
      const loadedState = {
        profile: false,
        drives: false,
        applications: false
      }

      if (profileResult.status === 'fulfilled') {
        const profilePayload = profileResult.value?.data?.data || {}
        this.companyProfile = this.normalizeCompanyProfile(profilePayload)
        loadedState.profile = true
      } else {
        blockingErrors.push(this.handleApiError(profileResult.reason, 'Failed to load company profile.'))
      }

      if (applicationsResult.status === 'fulfilled') {
        const items = applicationsResult.value?.data?.data?.items || []
        this.allApplications = Array.isArray(items) ? items.map((item) => this.normalizeApplication(item)) : []
        loadedState.applications = true
      } else {
        nonBlockingErrors.push(this.handleApiError(applicationsResult.reason, 'Failed to load applications.'))
        shouldDeriveSummary = true
      }

      if (drivesResult.status === 'fulfilled') {
        const items = drivesResult.value?.data?.data?.items || []
        this.myDrives = Array.isArray(items) ? items.map((item) => this.normalizeDrive(item)) : []
        this.refreshDriveStats()
        loadedState.drives = true
      } else {
        nonBlockingErrors.push(this.handleApiError(drivesResult.reason, 'Failed to load drives.'))
        shouldDeriveSummary = true
      }

      if (notificationsResult.status === 'fulfilled') {
        const items = notificationsResult.value?.data?.data?.items || []
        this.notifications = Array.isArray(items) ? items.map((item) => this.normalizeNotification(item)) : []
        this.notificationsError = ''
      } else {
        const message = this.handleApiError(notificationsResult.reason, 'Failed to load notifications.')
        this.notificationsError = message
        nonBlockingErrors.push(message)
        shouldDeriveSummary = true
      }

      if (dashboardResult.status === 'fulfilled') {
        const dashboardData = dashboardResult.value || {}
        this.dashboardSummary = this.buildSummaryFromLoadedData(dashboardData.summary || null)
      } else {
        nonBlockingErrors.push(this.handleApiError(dashboardResult.reason, 'Failed to load dashboard summary.'))
        shouldDeriveSummary = true
      }

      if (shouldDeriveSummary) {
        this.dashboardSummary = this.buildSummaryFromLoadedData()
      }

      const hasCoreData = loadedState.profile && (loadedState.drives || loadedState.applications)

      if (blockingErrors.length || !hasCoreData) {
        this.loadError = blockingErrors[0] || nonBlockingErrors[0] || 'Unable to load dashboard right now.'
      } else if (nonBlockingErrors.length) {
        this.toast_show('Some dashboard sections are temporarily unavailable. Showing available data.', 'warning')
      }

      this.isLoading = false
    },
    async loadNotifications(options = {}) {
      const silent = Boolean(options.silent)
      this.isLoadingNotifications = true

      if (!silent) {
        this.notificationsError = ''
      }

      try {
        const response = await companyApi.getNotifications({ page: 1, limit: 100, is_read: 'all' })
        const items = response?.data?.data?.items || []
        this.notifications = Array.isArray(items) ? items.map((item) => this.normalizeNotification(item)) : []
        this.notificationsError = ''
      } catch (error) {
        const message = this.handleApiError(error, 'Failed to load notifications.')
        this.notificationsError = message
        if (!silent) {
          this.toast_show(message, 'danger')
        }
      } finally {
        this.isLoadingNotifications = false
      }
    },
    async updateApplicationStatus(application, payload, successMessage) {
      if (!this.canManageApplications) {
        this.toast_show('Application actions are enabled only after admin approval.', 'warning')
        return false
      }

      try {
        const response = await companyApi.updateApplicationStatus(application.id, payload)
        this.applyApplicationUpdate(application.id, response?.data?.data || {})
        this.toast_show(successMessage, 'success')
        return true
      } catch (error) {
        this.handleApiError(error, 'Unable to update application status.', { showToast: true })
        return false
      }
    },
    async shortlistApp(application) {
      await this.updateApplicationStatus(application, { status: 'shortlisted' }, `${application.student} shortlisted.`)
    },
    async rejectApp(application) {
      await this.updateApplicationStatus(
        application,
        { status: 'rejected', rejection_reason: 'Not selected for this role.' },
        `${application.student} marked as rejected.`
      )
    },
    async advanceStage(application, stage) {
      const messages = {
        interview: `Interview stage set for ${application.student}.`,
        offered: `Offer stage set for ${application.student}.`
      }
      await this.updateApplicationStatus(application, { status: stage }, messages[stage] || 'Application status updated.')
    },
    toggleSelectAll() {
      if (this.allPageSelected) {
        this.selectedApps = []
        return
      }
      this.selectedApps = this.filteredApplications.map((application) => application.id)
    },
    toggleSelectApp(applicationId) {
      const index = this.selectedApps.indexOf(applicationId)
      if (index > -1) {
        this.selectedApps.splice(index, 1)
      } else {
        this.selectedApps.push(applicationId)
      }
    },
    async bulkShortlist() {
      if (!this.canManageApplications) {
        this.toast_show('Application actions are enabled only after admin approval.', 'warning')
        return
      }

      let successCount = 0
      for (const applicationId of this.selectedApps) {
        const application = this.allApplications.find((entry) => entry.id === applicationId)
        if (!application || !['applied', 'pending'].includes(application.status)) {
          continue
        }

        const ok = await this.updateApplicationStatus(application, { status: 'shortlisted' }, `${application.student} shortlisted.`)
        if (ok) {
          successCount += 1
        }
      }

      this.selectedApps = []
      this.toast_show(`${successCount} applications shortlisted`, 'success')
    },
    async bulkReject() {
      if (!this.canManageApplications) {
        this.toast_show('Application actions are enabled only after admin approval.', 'warning')
        return
      }

      let successCount = 0
      for (const applicationId of this.selectedApps) {
        const application = this.allApplications.find((entry) => entry.id === applicationId)
        if (!application) {
          continue
        }

        const ok = await this.updateApplicationStatus(
          application,
          { status: 'rejected', rejection_reason: 'Not selected for this role.' },
          `${application.student} marked as rejected.`
        )

        if (ok) {
          successCount += 1
        }
      }

      this.selectedApps = []
      this.toast_show(`${successCount} applications rejected`, 'warning')
    },
    openNewDriveModal() {
      if (this.companyProfile.status !== 'approved') {
        this.toast_show('Drives can only be created after admin approval.', 'warning')
        return
      }

      this.newDrive = createDefaultNewDrive()
      this.showNewDriveModal = true
    },
    closeNewDriveModal() {
      this.showNewDriveModal = false
    },
    setNewDriveField(field, value) {
      this.newDrive = {
        ...this.newDrive,
        [field]: value
      }
    },
    async submitNewDrive() {
      if (!this.newDrive.title || !this.newDrive.salary || !this.newDrive.deadline) {
        this.toast_show('Please fill in all required fields.', 'warning')
        return
      }

      const salaryLpa = this.parseSalaryLpa(this.newDrive.salary)
      const driveValidationError = this.validateNewDrivePayload(this.newDrive, salaryLpa)
      if (driveValidationError) {
        this.toast_show(driveValidationError, 'warning')
        return
      }

      const payload = {
        job_title: String(this.newDrive.title || '').trim(),
        job_description: this.newDrive.description || 'Role details shared during screening.',
        required_skills: '',
        experience_required: '0-2 years',
        benefits: 'As per company policy',
        min_cgpa: Number(this.newDrive.minCgpa || 0),
        eligible_branches: this.parseBranches(this.newDrive.branches),
        eligible_years: [3, 4],
        salary_lpa: salaryLpa,
        job_location: this.companyProfile.location === '-' ? '' : this.companyProfile.location,
        application_deadline: `${this.newDrive.deadline}T23:59:59+00:00`,
        interview_mode: 'both'
      }

      try {
        await companyApi.createDrive(payload)
        const drivesResponse = await companyApi.getDrives({ page: 1, limit: 100 })
        const items = drivesResponse?.data?.data?.items || []
        this.myDrives = items.map((item) => this.normalizeDrive(item))
        this.refreshDriveStats()
        this.showNewDriveModal = false
        this.toast_show(`"${this.newDrive.title}" submitted for admin approval.`, 'success')
      } catch (error) {
        this.handleApiError(error, 'Unable to create drive.', { showToast: true })
      }
    },
    async closeDrive(drive) {
      try {
        await companyApi.updateDrive(drive.id, { status: 'closed' })
        drive.status = 'closed'
        this.toast_show(`Drive "${drive.title}" closed.`, 'info')
      } catch (error) {
        this.handleApiError(error, 'Unable to close drive.', { showToast: true })
      }
    },
    openApplicationsForDrive(driveId) {
      this.activeView = 'applications'
      this.appDriveFilter = driveId
    },
    toggleProfileEdit() {
      this.profileEditMode = !this.profileEditMode
      if (this.profileEditMode) {
        this.profileEdit = { ...this.companyProfile }
      }
    },
    updateProfileField(field, value) {
      this.profileEdit = {
        ...this.profileEdit,
        [field]: value
      }
    },
    cancelProfileEdit() {
      this.profileEditMode = false
      this.profileEdit = { ...this.companyProfile }
    },
    async saveProfile() {
      const payload = {
        company_name: this.normalizeInput(this.profileEdit.name),
        website: this.normalizeInput(this.profileEdit.domain),
        hr_contact_name: this.normalizeInput(this.profileEdit.hrName),
        hr_contact_email: this.normalizeInput(this.profileEdit.hrEmail),
        industry: this.normalizeInput(this.profileEdit.industry),
        company_description: this.normalizeInput(this.profileEdit.about),
        location: this.normalizeInput(this.profileEdit.location)
      }

      const profileValidationError = this.validateCompanyProfilePayload(payload)
      if (profileValidationError) {
        this.toast_show(profileValidationError, 'warning')
        return
      }

      try {
        const response = await companyApi.updateProfile(payload)
        const updatedPayload = response?.data?.data || {}

        this.companyProfile = this.normalizeCompanyProfile(
          {
            ...updatedPayload,
            company_name: updatedPayload.company_name || this.profileEdit.name,
            website: updatedPayload.website || this.profileEdit.domain,
            hr_contact_name: updatedPayload.hr_contact_name || this.profileEdit.hrName,
            hr_contact_email: updatedPayload.hr_contact_email || this.profileEdit.hrEmail,
            industry: updatedPayload.industry || this.profileEdit.industry,
            company_description: updatedPayload.company_description || this.profileEdit.about,
            location: updatedPayload.location || this.profileEdit.location,
            approval_status: updatedPayload.approval_status || this.companyProfile.status
          },
          {}
        )

        this.profileEditMode = false
        this.toast_show('Profile updated successfully.', 'success')
      } catch (error) {
        this.handleApiError(error, 'Unable to update company profile.', { showToast: true })
      }
    },
    async markNotificationRead(notificationId) {
      const targetId = Number(notificationId)
      if (!targetId || this.isMarkingNotification[targetId]) {
        return
      }

      const target = this.notifications.find((notification) => Number(notification.id) === targetId)
      if (!target || target.read) {
        return
      }

      this.isMarkingNotification = {
        ...this.isMarkingNotification,
        [targetId]: true
      }

      target.read = true
      try {
        await companyApi.markNotificationRead(targetId)
        this.notificationsError = ''
      } catch (error) {
        target.read = false
        this.notificationsError = this.handleApiError(error, 'Unable to mark notification as read.', { showToast: true })
      } finally {
        this.isMarkingNotification = {
          ...this.isMarkingNotification,
          [targetId]: false
        }
      }
    },
    async markAllRead() {
      if (this.isMarkingAllNotifications || this.unreadNotifCount === 0) {
        return
      }

      this.isMarkingAllNotifications = true
      const previous = this.notifications.map((notification) => ({ ...notification }))

      try {
        this.notifications = this.notifications.map((notification) => ({
          ...notification,
          read: true
        }))

        await companyApi.markAllNotificationsRead()
        this.notificationsError = ''
        this.toast_show('All notifications marked as read.', 'success')
      } catch (error) {
        this.notifications = previous
        this.notificationsError = this.handleApiError(error, 'Unable to mark all notifications as read.', { showToast: true })
      } finally {
        this.isMarkingAllNotifications = false
      }
    },
    doExport(scope) {
      let rows = []
      if (scope === 'drives') {
        rows = [
          'Title,Role,Salary,Status,Applicants,Deadline',
          ...this.myDrives.map(
            (drive) => `${drive.title},${drive.role},${drive.salary},${drive.status},${drive.applicants},${drive.deadline}`
          )
        ]
      } else {
        rows = [
          'Student,Roll,Branch,CGPA,Drive,Status',
          ...this.allApplications.map(
            (application) =>
              `${application.student},${application.roll},${application.branch},${application.cgpa},${application.drive},${application.status}`
          )
        ]
      }

      const blob = new Blob([rows.join('\n')], { type: 'text/csv' })
      const link = Object.assign(document.createElement('a'), {
        href: URL.createObjectURL(blob),
        download: `recruitify-${scope}-${Date.now()}.csv`
      })

      link.click()
      URL.revokeObjectURL(link.href)
      this.toast_show(`${scope} data downloaded as CSV.`, 'success')
    },
    toast_show(message, type = 'success') {
      const icons = {
        success: '✅',
        danger: '❌',
        warning: '⚠️',
        info: 'ℹ️'
      }

      this.toast = {
        show: true,
        message,
        type,
        icon: icons[type] || 'ℹ️'
      }

      if (this.toastTimerId) {
        clearTimeout(this.toastTimerId)
      }

      this.toastTimerId = setTimeout(() => {
        this.toast.show = false
        this.toastTimerId = null
      }, 3500)
    }
  }
}
</script>
