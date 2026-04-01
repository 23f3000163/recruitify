<template>
  <div class="rq-app" :class="{ 'is-collapsed': sidebarCollapsed }">
    <StudentSidebar
      :sidebar-collapsed="sidebarCollapsed"
      :active-view="activeView"
      :nav-items="mainNavItems"
      :profile-nav-items="profileNavItems"
      :student="student"
      @toggle-sidebar="toggleSidebar"
      @navigate="navigate"
    />

    <div class="rq-main">
      <StudentTopbar
        :current-page-title="currentPageTitle"
        :search-query="searchQuery"
        :search-focused="searchFocused"
        :unread-count="unreadCount"
        :student="student"
        @update:search-query="searchQuery = $event"
        @update:search-focused="searchFocused = $event"
        @navigate="navigate"
      />

      <div
        v-if="actionNote"
        class="rq-action-note"
        :class="`tone-${actionTone}`"
        role="status"
        aria-live="polite"
      >
        {{ actionNote }}
      </div>

      <main class="rq-page" role="main">
        <StudentDashboardHome
          v-if="activeView === 'dashboard'"
          :student-first-name="student.firstName"
          :time-of-day="timeOfDay"
          :today-date="todayDate"
          :live-open-count="liveOpenCount"
          :is-loading="isLoadingDashboard"
          :error-message="dashboardError"
          :stat-cards="statCards"
          :drives="dashboardDrives"
          :applications="dashboardApplications"
        />

        <StudentDrivesPanel
          v-else-if="activeView === 'drives'"
          :drives="drives"
          :pagination="drivesPagination"
          :query-text="driveFilters.query"
          :company-filter="driveFilters.company"
          :role-filter="driveFilters.role"
          :skills-filter="driveFilters.skills"
          :include-expired="driveFilters.includeExpired"
          :is-loading="isLoadingDrives"
          :error-message="drivesError"
          :is-applying="isApplyingDrive"
          @update:query-text="driveFilters.query = $event"
          @update:company-filter="driveFilters.company = $event"
          @update:role-filter="driveFilters.role = $event"
          @update:skills-filter="driveFilters.skills = $event"
          @update:include-expired="driveFilters.includeExpired = $event"
          @apply-filters="applyDriveFilters"
          @page-change="loadDrives"
          @apply-drive="applyToDrive"
        />

        <StudentApplicationsPanel
          v-else-if="activeView === 'applications'"
          :applications="applications"
          :pagination="applicationsPagination"
          :status-filter="statusFilter"
          :query-text="queryText"
          :is-loading="isLoadingApplications"
          :error-message="applicationsError"
          :is-responding="isRespondingOffer"
          @update:status-filter="statusFilter = $event"
          @update:query-text="queryText = $event"
          @apply-filters="applyApplicationFilters"
          @page-change="loadApplications"
          @respond-offer="respondToOffer"
        />

        <StudentNotificationsPanel
          v-else-if="activeView === 'notifications'"
          :notifications="notifications"
          :is-loading="isLoadingNotifications"
          :unread-count="unreadCount"
          :error-message="notificationsError"
          :is-marking="isMarkingNotification"
          :is-marking-all="isMarkingAllNotifications"
          @mark-read="markNotificationRead"
          @mark-all="markAllNotificationsRead"
        />

        <StudentProfilePanel
          v-else-if="activeView === 'profile'"
          :profile-form="profileForm"
          :is-saving="isSavingProfile"
          :error-message="profileError"
          @update-field="updateProfileField"
          @save-profile="saveProfile"
        />

        <StudentHistoryPanel
          v-else-if="activeView === 'history'"
          :history-items="historyItems"
          :summary="historySummary"
          :pagination="historyPagination"
          :query-text="historyQuery"
          :is-loading="isLoadingHistory"
          :error-message="historyError"
          :is-downloading="isDownloadingDocument"
          @update:query-text="historyQuery = $event"
          @apply-filters="applyHistoryFilters"
          @page-change="loadHistory"
          @download-offer="downloadOfferDocument"
          @download-placement="downloadPlacementDocument"
        />

        <StudentSectionPlaceholder
          v-else
          title="Section unavailable"
          description="This section is not available in the current dashboard state."
        />
      </main>
    </div>
  </div>
</template>

<script>
import { authApi, studentApi } from '../../api/api'
import StudentApplicationsPanel from '../../components/student/v2/StudentApplicationsPanel.vue'
import StudentDashboardHome from '../../components/student/v2/StudentDashboardHome.vue'
import StudentDrivesPanel from '../../components/student/v2/StudentDrivesPanel.vue'
import StudentHistoryPanel from '../../components/student/v2/StudentHistoryPanel.vue'
import StudentNotificationsPanel from '../../components/student/v2/StudentNotificationsPanel.vue'
import StudentProfilePanel from '../../components/student/v2/StudentProfilePanel.vue'
import StudentSectionPlaceholder from '../../components/student/v2/StudentSectionPlaceholder.vue'
import StudentSidebar from '../../components/student/v2/StudentSidebar.vue'
import StudentTopbar from '../../components/student/v2/StudentTopbar.vue'
import './StudentDashboardV2.css'

const STORAGE_KEYS = Object.freeze({
  activeView: 'student.v2.activeView',
  sidebarCollapsed: 'student.v2.sidebarCollapsed'
})

const ACTION_NOTE_TIMEOUT_MS = 3200

export default {
  name: 'StudentDashboardV2',
  components: {
    StudentSidebar,
    StudentTopbar,
    StudentDashboardHome,
    StudentDrivesPanel,
    StudentHistoryPanel,
    StudentApplicationsPanel,
    StudentNotificationsPanel,
    StudentProfilePanel,
    StudentSectionPlaceholder
  },
  data() {
    const now = new Date()
    const hour = now.getHours()

    return {
      sidebarCollapsed: false,
      activeView: 'dashboard',
      searchQuery: '',
      searchFocused: false,
      isLoadingDashboard: false,
      isLoadingDrives: false,
      isLoadingApplications: false,
      isLoadingNotifications: false,
      isLoadingHistory: false,
      isSavingProfile: false,
      dashboardError: '',
      drivesError: '',
      applicationsError: '',
      notificationsError: '',
      historyError: '',
      profileError: '',
      actionNote: '',
      actionTone: 'info',
      actionNoteTimerId: null,
      timeOfDay: hour < 12 ? 'morning' : hour < 17 ? 'afternoon' : 'evening',
      todayDate: now.toLocaleDateString('en-IN', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      }),
      student: {
        firstName: 'Priya',
        name: 'Priya Sharma',
        initials: 'PS',
        roll: 'CS21B042',
        branch: 'CSE',
        year: 3,
        email: ''
      },
      summary: {
        applications_total: 0,
        applied: 0,
        shortlisted: 0,
        interviewed: 0,
        selected: 0,
        waitlisted: 0,
        rejected: 0,
        offers_released: 0,
        offers_accepted: 0,
        offers_rejected: 0
      },
      recentApplications: [],
      drivesPreview: [],
      navItems: [
        {
          id: 'dashboard',
          label: 'Dashboard',
          svg: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="1" y="1" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.4"/><rect x="9" y="1" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.4"/><rect x="1" y="9" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.4"/><rect x="9" y="9" width="6" height="6" rx="1.5" stroke="currentColor" stroke-width="1.4"/></svg>'
        },
        {
          id: 'drives',
          label: 'Placement Drives',
          svg: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="1" y="3" width="14" height="11" rx="2" stroke="currentColor" stroke-width="1.4"/><path d="M5 3V2M11 3V2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M1 7h14" stroke="currentColor" stroke-width="1.4"/></svg>'
        },
        {
          id: 'applications',
          label: 'My Applications',
          svg: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 2h10a1 1 0 011 1v11a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z" stroke="currentColor" stroke-width="1.4"/><path d="M5 6h6M5 9h4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>'
        },
        {
          id: 'notifications',
          label: 'Notifications',
          svg: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M13 11H3l1.5-2.5V7a3.5 3.5 0 017 0v1.5L13 11z" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M6.5 13a1.5 1.5 0 003 0" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>'
        }
      ],
      profileNavItems: [
        {
          id: 'profile',
          label: 'My Profile',
          svg: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="5" r="3" stroke="currentColor" stroke-width="1.4"/><path d="M2 14c0-3.3 2.7-5 6-5s6 1.7 6 5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>'
        },
        {
          id: 'history',
          label: 'History',
          svg: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1.4"/><path d="M8 5v3.5l2 2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        }
      ],
      applications: [],
      applicationsPagination: {
        page: 1,
        pages: 0,
        total: 0,
        limit: 10
      },
      drives: [],
      drivesPagination: {
        page: 1,
        pages: 0,
        total: 0,
        limit: 8
      },
      driveFilters: {
        query: '',
        company: '',
        role: '',
        skills: '',
        includeExpired: false
      },
      isApplyingDrive: {},
      statusFilter: 'all',
      queryText: '',
      isRespondingOffer: {},
      notifications: [],
      notificationsPagination: {
        page: 1,
        pages: 0,
        total: 0,
        limit: 8
      },
      unreadNotificationsCount: 0,
      isMarkingNotification: {},
      isMarkingAllNotifications: false,
      historyItems: [],
      historySummary: {
        total_applied: 0,
        offers_received: 0,
        placements_count: 0,
        highest_package: 0
      },
      historyPagination: {
        page: 1,
        pages: 0,
        total: 0,
        limit: 10
      },
      historyQuery: '',
      isDownloadingDocument: {},
      profileForm: {
        college_name: 'Institute of Technology',
        branch: 'CSE',
        year: 3,
        cgpa: 8.5,
        roll_number: 'CS21B042',
        phone: '',
        resume_url: '',
        skills: '',
        experience_summary: ''
      }
    }
  },
  computed: {
    currentPageTitle() {
      const labels = {
        dashboard: 'Dashboard',
        drives: 'Placement Drives',
        applications: 'My Applications',
        notifications: 'Notifications',
        profile: 'My Profile',
        history: 'Placement History'
      }
      return labels[this.activeView] || 'Dashboard'
    },
    mainNavItems() {
      return this.navItems.map((item) => ({
        ...item,
        badgeCount: item.id === 'notifications' ? this.unreadCount : 0
      }))
    },
    statCards() {
      return [
        {
          id: 'applied',
          label: 'Applied',
          value: Number(this.summary.applied || 0).toLocaleString(),
          sub: 'Applications submitted'
        },
        {
          id: 'shortlisted',
          label: 'Shortlisted',
          value: Number(this.summary.shortlisted || 0).toLocaleString(),
          sub: 'Moved to next stage'
        },
        {
          id: 'interviewed',
          label: 'Interviewed',
          value: Number(this.summary.interviewed || 0).toLocaleString(),
          sub: 'Interview rounds completed'
        },
        {
          id: 'offers',
          label: 'Offers Accepted',
          value: Number(this.summary.offers_accepted || 0).toLocaleString(),
          sub: 'Confirmed offer decisions'
        }
      ]
    },
    liveOpenCount() {
      return this.dashboardDrives.length
    },
    unreadCount() {
      return Number(this.unreadNotificationsCount || 0)
    },
    dashboardDrives() {
      const query = this.searchQuery.trim().toLowerCase()
      if (!query) {
        return this.drivesPreview
      }

      return this.drivesPreview.filter(
        (item) =>
          item.role.toLowerCase().includes(query) ||
          item.company.toLowerCase().includes(query)
      )
    },
    dashboardApplications() {
      const query = this.searchQuery.trim().toLowerCase()
      if (!query) {
        return this.recentApplications
      }

      return this.recentApplications.filter(
        (item) =>
          item.role.toLowerCase().includes(query) ||
          item.company.toLowerCase().includes(query)
      )
    }
  },
  watch: {
    activeView(nextValue) {
      this.persistPreference(STORAGE_KEYS.activeView, String(nextValue || 'dashboard'))
    },
    sidebarCollapsed(nextValue) {
      this.persistPreference(STORAGE_KEYS.sidebarCollapsed, nextValue ? '1' : '0')
    }
  },
  created() {
    this.restoreViewState()
    this.restoreSidebarState()
    this.bootstrap()
  },
  beforeUnmount() {
    if (this.actionNoteTimerId) {
      clearTimeout(this.actionNoteTimerId)
      this.actionNoteTimerId = null
    }
  },
  methods: {
    async bootstrap() {
      const bootTasks = [
        this.hydrateIdentity(),
        this.loadDashboard(),
        this.loadApplications(1),
        this.loadNotifications(1),
        this.loadProfile()
      ]

      if (this.activeView === 'drives') {
        bootTasks.push(this.loadDrives(1))
      }
      if (this.activeView === 'history') {
        bootTasks.push(this.loadHistory(1))
      }

      await Promise.all(bootTasks)
    },
    async hydrateIdentity() {
      try {
        const response = await authApi.getMe()
        const data = response?.data?.data || {}

        const displayName = String(data.username || this.student.name || 'Student').trim()
        const chunks = displayName.split(/\s+/).filter(Boolean)
        const initials = chunks
          .slice(0, 2)
          .map((chunk) => chunk[0]?.toUpperCase() || '')
          .join('') || 'ST'

        this.student = {
          ...this.student,
          firstName: chunks[0] || this.student.firstName,
          name: displayName,
          initials,
          email: data.email || ''
        }
      } catch (error) {
        // Keep UI usable even if identity hydration fails.
      }
    },
    async loadDashboard() {
      this.isLoadingDashboard = true
      this.dashboardError = ''

      try {
        const response = await studentApi.getDashboard()
        const payload = response?.data?.data || {}
        const summary = payload.summary || {}

        this.summary = {
          applications_total: Number(summary.applications_total || 0),
          applied: Number(summary.applied || 0),
          shortlisted: Number(summary.shortlisted || 0),
          interviewed: Number(summary.interviewed || 0),
          selected: Number(summary.selected || 0),
          waitlisted: Number(summary.waitlisted || 0),
          rejected: Number(summary.rejected || 0),
          offers_released: Number(summary.offers_released || 0),
          offers_accepted: Number(summary.offers_accepted || 0),
          offers_rejected: Number(summary.offers_rejected || 0)
        }

        this.unreadNotificationsCount = Number(
          payload.unread_notifications || this.unreadNotificationsCount || 0
        )

        const rows = Array.isArray(payload.recent_applications)
          ? payload.recent_applications
          : []

        this.recentApplications = rows.map((row) => ({
          id: row.application_id || row.id,
          role: row.drive?.title || 'Role unavailable',
          company: row.company?.name || '-',
          status: row.status || 'applied',
          statusLabel: row.status_label || this.statusLabel(row.status)
        }))

        this.drivesPreview = this.buildDrivesPreview(rows)
      } catch (error) {
        this.dashboardError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load dashboard summary.'
        this.publishActionNote(this.dashboardError, 'error')
      } finally {
        this.isLoadingDashboard = false
      }
    },
    buildDrivesPreview(rows) {
      const unique = new Map()

      rows.forEach((row) => {
        const driveId = row.drive?.id || row.drive_id || `drive-${row.application_id}`
        if (unique.has(driveId)) {
          return
        }

        const salaryLpa = Number(row.drive?.salary_lpa || 0)
        unique.set(driveId, {
          id: driveId,
          role: row.drive?.title || 'Opportunity',
          company: row.company?.name || '-',
          salary: salaryLpa > 0 ? `${salaryLpa.toLocaleString()} LPA` : '-',
          deadline: this.formatShortDate(row.drive?.application_deadline)
        })
      })

      return Array.from(unique.values()).slice(0, 6)
    },
    async loadDrives(page = 1) {
      this.isLoadingDrives = true
      this.drivesError = ''

      try {
        const response = await studentApi.getDrives({
          page,
          limit: this.drivesPagination.limit,
          q: this.driveFilters.query,
          company: this.driveFilters.company,
          role: this.driveFilters.role,
          skills: this.driveFilters.skills,
          include_expired: this.driveFilters.includeExpired
        })

        const data = response?.data?.data || {}
        this.drives = Array.isArray(data.items) ? data.items : []
        this.drivesPagination = {
          page: Number(data.page || page),
          pages: Number(data.pages || 0),
          total: Number(data.total || 0),
          limit: Number(data.limit || this.drivesPagination.limit)
        }
      } catch (error) {
        this.drivesError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load drives.'
      } finally {
        this.isLoadingDrives = false
      }
    },
    async applyDriveFilters() {
      await this.loadDrives(1)
    },
    async applyToDrive(driveId) {
      const parsedDriveId = Number(driveId)
      if (!parsedDriveId || this.isApplyingDrive[parsedDriveId]) {
        return
      }

      this.isApplyingDrive = {
        ...this.isApplyingDrive,
        [parsedDriveId]: true
      }

      try {
        const response = await studentApi.applyToDrive(parsedDriveId)
        const data = response?.data?.data || {}
        await Promise.all([
          this.loadDrives(this.drivesPagination.page || 1),
          this.loadDashboard(),
          this.loadApplications(1)
        ])

        if (data.already_applied) {
          this.publishActionNote('You already applied to this drive.', 'info')
        } else {
          this.publishActionNote('Application submitted successfully.', 'success')
        }
      } catch (error) {
        this.drivesError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to apply for this drive.'
        this.publishActionNote(this.drivesError, 'error')
      } finally {
        this.isApplyingDrive = {
          ...this.isApplyingDrive,
          [parsedDriveId]: false
        }
      }
    },
    async loadApplications(page = 1) {
      this.isLoadingApplications = true
      this.applicationsError = ''

      try {
        const response = await studentApi.getApplications({
          page,
          limit: this.applicationsPagination.limit,
          status: this.statusFilter,
          q: this.queryText
        })

        const data = response?.data?.data || {}
        this.applications = Array.isArray(data.items) ? data.items : []
        this.applicationsPagination = {
          page: Number(data.page || page),
          pages: Number(data.pages || 0),
          total: Number(data.total || 0),
          limit: Number(data.limit || this.applicationsPagination.limit)
        }
      } catch (error) {
        this.applicationsError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load applications.'
      } finally {
        this.isLoadingApplications = false
      }
    },
    async applyApplicationFilters() {
      await this.loadApplications(1)
    },
    async respondToOffer(offerId, targetStatus) {
      const parsedOfferId = Number(offerId)
      if (!parsedOfferId || this.isRespondingOffer[parsedOfferId]) {
        return
      }

      this.isRespondingOffer = {
        ...this.isRespondingOffer,
        [parsedOfferId]: true
      }

      try {
        await studentApi.respondToOffer(parsedOfferId, { status: targetStatus })
        await Promise.all([
          this.loadDashboard(),
          this.loadApplications(this.applicationsPagination.page || 1),
          this.loadNotifications(1)
        ])
        this.publishActionNote(`Offer response submitted: ${targetStatus}.`, 'success')
      } catch (error) {
        this.applicationsError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to submit offer response.'
        this.publishActionNote(this.applicationsError, 'error')
      } finally {
        this.isRespondingOffer = {
          ...this.isRespondingOffer,
          [parsedOfferId]: false
        }
      }
    },
    async loadNotifications(page = 1) {
      this.isLoadingNotifications = true
      this.notificationsError = ''

      try {
        const response = await studentApi.getNotifications({
          page,
          limit: this.notificationsPagination.limit,
          is_read: 'all'
        })

        const data = response?.data?.data || {}
        this.notifications = Array.isArray(data.items) ? data.items : []
        this.notificationsPagination = {
          page: Number(data.page || page),
          pages: Number(data.pages || 0),
          total: Number(data.total || 0),
          limit: Number(data.limit || this.notificationsPagination.limit)
        }

        if (typeof data.unread_count === 'number') {
          this.unreadNotificationsCount = data.unread_count
        }
      } catch (error) {
        this.notificationsError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load notifications.'
      } finally {
        this.isLoadingNotifications = false
      }
    },
    async markNotificationRead(notificationId) {
      const parsedId = Number(notificationId)
      if (!parsedId || this.isMarkingNotification[parsedId]) {
        return
      }

      this.isMarkingNotification = {
        ...this.isMarkingNotification,
        [parsedId]: true
      }

      try {
        const response = await studentApi.markNotificationRead(parsedId)
        const data = response?.data?.data || {}

        this.notifications = this.notifications.map((item) =>
          item.notification_id === parsedId
            ? { ...item, is_read: true }
            : item
        )

        if (typeof data.unread_count === 'number') {
          this.unreadNotificationsCount = data.unread_count
        }

        this.publishActionNote('Notification marked as read.', 'success')
      } catch (error) {
        this.notificationsError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to update notification.'
        this.publishActionNote(this.notificationsError, 'error')
      } finally {
        this.isMarkingNotification = {
          ...this.isMarkingNotification,
          [parsedId]: false
        }
      }
    },
    async markAllNotificationsRead() {
      if (this.isMarkingAllNotifications || this.unreadNotificationsCount === 0) {
        return
      }

      this.isMarkingAllNotifications = true
      try {
        const response = await studentApi.markAllNotificationsRead()
        const data = response?.data?.data || {}

        this.notifications = this.notifications.map((item) => ({
          ...item,
          is_read: true
        }))
        this.unreadNotificationsCount = Number(data.unread_count || 0)
        this.publishActionNote('All notifications marked as read.', 'success')
      } catch (error) {
        this.notificationsError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to update notifications.'
        this.publishActionNote(this.notificationsError, 'error')
      } finally {
        this.isMarkingAllNotifications = false
      }
    },
    async loadProfile() {
      this.profileError = ''

      try {
        const response = await studentApi.getProfile()
        const studentPayload = response?.data?.data?.student || {}

        this.profileForm = {
          ...this.profileForm,
          college_name: studentPayload.college_name || '',
          branch: studentPayload.branch || '',
          year: studentPayload.year ?? '',
          cgpa: studentPayload.cgpa ?? '',
          roll_number: studentPayload.roll_number || '',
          phone: studentPayload.phone || '',
          resume_url: studentPayload.resume_url || '',
          skills: studentPayload.skills || '',
          experience_summary: studentPayload.experience_summary || ''
        }

        this.student = {
          ...this.student,
          branch: studentPayload.branch || this.student.branch,
          year: Number(studentPayload.year || this.student.year),
          roll: studentPayload.roll_number || this.student.roll
        }
      } catch (error) {
        this.profileError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load profile data.'
      }
    },
    async loadHistory(page = 1) {
      this.isLoadingHistory = true
      this.historyError = ''

      try {
        const response = await studentApi.getHistory({
          page,
          limit: this.historyPagination.limit,
          q: this.historyQuery
        })

        const data = response?.data?.data || {}
        this.historyItems = Array.isArray(data.items) ? data.items : []
        this.historySummary = {
          total_applied: Number(data.summary?.total_applied || 0),
          offers_received: Number(data.summary?.offers_received || 0),
          placements_count: Number(data.summary?.placements_count || 0),
          highest_package: Number(data.summary?.highest_package || 0)
        }
        this.historyPagination = {
          page: Number(data.page || page),
          pages: Number(data.pages || 0),
          total: Number(data.total || 0),
          limit: Number(data.limit || this.historyPagination.limit)
        }
      } catch (error) {
        this.historyError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to load placement history.'
      } finally {
        this.isLoadingHistory = false
      }
    },
    async applyHistoryFilters() {
      await this.loadHistory(1)
    },
    async downloadOfferDocument(offerId) {
      await this.downloadDocument('offer', Number(offerId))
    },
    async downloadPlacementDocument(placementId) {
      await this.downloadDocument('placement', Number(placementId))
    },
    async downloadDocument(type, id) {
      if (!id || id <= 0) {
        return
      }

      const key = `${type}-${id}`
      if (this.isDownloadingDocument[key]) {
        return
      }

      this.isDownloadingDocument = {
        ...this.isDownloadingDocument,
        [key]: true
      }

      try {
        const response =
          type === 'offer'
            ? await studentApi.downloadOfferDocument(id)
            : await studentApi.downloadPlacementDocument(id)

        const fallbackName =
          type === 'offer'
            ? `offer-letter-${id}.txt`
            : `placement-confirmation-${id}.txt`

        const filename = this.extractFilename(response?.headers, fallbackName)
        this.triggerFileDownload(response?.data, filename)
        this.publishActionNote(`Downloaded ${filename}.`, 'success')
      } catch (error) {
        this.historyError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to download document.'
        this.publishActionNote(this.historyError, 'error')
      } finally {
        this.isDownloadingDocument = {
          ...this.isDownloadingDocument,
          [key]: false
        }
      }
    },
    extractFilename(headers, fallback) {
      const disposition = String(
        headers?.['content-disposition'] || headers?.['Content-Disposition'] || ''
      )
      const match = disposition.match(/filename\*?=(?:UTF-8''|\")?([^\";]+)/i)
      if (match && match[1]) {
        return decodeURIComponent(match[1]).trim()
      }
      return fallback
    },
    triggerFileDownload(payload, filename) {
      if (
        typeof window === 'undefined' ||
        !window.URL ||
        typeof window.URL.createObjectURL !== 'function' ||
        typeof document === 'undefined'
      ) {
        return
      }

      const blob = payload instanceof Blob ? payload : new Blob([payload || ''])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      if (typeof window.URL.revokeObjectURL === 'function') {
        window.URL.revokeObjectURL(url)
      }
    },
    updateProfileField(field, value) {
      this.profileForm = {
        ...this.profileForm,
        [field]: value
      }
    },
    async saveProfile() {
      this.isSavingProfile = true
      this.profileError = ''

      const year = Number(this.profileForm.year)
      const cgpa = Number(this.profileForm.cgpa)
      const payload = {
        college_name: String(this.profileForm.college_name || '').trim(),
        branch: String(this.profileForm.branch || '').trim(),
        year: Number.isNaN(year) ? this.profileForm.year : year,
        cgpa: Number.isNaN(cgpa) ? this.profileForm.cgpa : cgpa,
        roll_number: String(this.profileForm.roll_number || '').trim(),
        phone: String(this.profileForm.phone || '').trim(),
        resume_url: String(this.profileForm.resume_url || '').trim(),
        skills: String(this.profileForm.skills || '').trim(),
        experience_summary: String(this.profileForm.experience_summary || '').trim()
      }

      try {
        const response = await studentApi.updateProfile(payload)
        const studentPayload = response?.data?.data?.student || {}

        this.profileForm = {
          ...this.profileForm,
          college_name: studentPayload.college_name || payload.college_name,
          branch: studentPayload.branch || payload.branch,
          year: studentPayload.year ?? payload.year,
          cgpa: studentPayload.cgpa ?? payload.cgpa,
          roll_number: studentPayload.roll_number || payload.roll_number,
          phone: studentPayload.phone || payload.phone,
          resume_url: studentPayload.resume_url || payload.resume_url,
          skills: studentPayload.skills || payload.skills,
          experience_summary:
            studentPayload.experience_summary || payload.experience_summary
        }

        this.student = {
          ...this.student,
          branch: studentPayload.branch || this.student.branch,
          year: Number(studentPayload.year || this.student.year),
          roll: studentPayload.roll_number || this.student.roll
        }
        this.publishActionNote('Profile updated successfully.', 'success')
      } catch (error) {
        this.profileError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to save profile.'
        this.publishActionNote(this.profileError, 'error')
      } finally {
        this.isSavingProfile = false
      }
    },
    formatShortDate(value) {
      if (!value) {
        return '-'
      }

      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) {
        return '-'
      }

      return parsed.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric'
      })
    },
    statusLabel(status) {
      const normalized = String(status || '').trim().toLowerCase()
      const labels = {
        applied: 'Applied',
        shortlisted: 'Shortlisted',
        interviewed: 'Interviewed',
        selected: 'Selected',
        waitlisted: 'Waitlisted',
        rejected: 'Rejected',
        offered: 'Offer Released',
        accepted: 'Offer Accepted'
      }
      return labels[normalized] || (normalized ? normalized : 'Updated')
    },
    restoreViewState() {
      try {
        const storedView = localStorage.getItem(STORAGE_KEYS.activeView)
        if (storedView) {
          this.activeView = storedView
        }
      } catch (error) {
        // Ignore storage read failures and keep defaults.
      }
    },
    restoreSidebarState() {
      try {
        const stored = localStorage.getItem(STORAGE_KEYS.sidebarCollapsed)
        this.sidebarCollapsed = stored === '1'
      } catch (error) {
        // Ignore storage read failures and keep defaults.
      }
    },
    persistPreference(key, value) {
      try {
        localStorage.setItem(key, value)
      } catch (error) {
        // Ignore storage write failures and keep dashboard functional.
      }
    },
    publishActionNote(message, tone = 'info') {
      if (!message) {
        return
      }

      if (this.actionNoteTimerId) {
        clearTimeout(this.actionNoteTimerId)
      }

      this.actionNote = String(message)
      this.actionTone = tone

      this.actionNoteTimerId = setTimeout(() => {
        this.actionNote = ''
        this.actionTone = 'info'
        this.actionNoteTimerId = null
      }, ACTION_NOTE_TIMEOUT_MS)
    },
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    navigate(viewId) {
      this.activeView = viewId

      if (viewId === 'drives' && !this.drives.length) {
        this.loadDrives(1)
      }
      if (viewId === 'applications' && !this.applications.length) {
        this.loadApplications(1)
      }
      if (viewId === 'notifications' && !this.notifications.length) {
        this.loadNotifications(1)
      }
      if (viewId === 'history' && !this.historyItems.length) {
        this.loadHistory(1)
      }
    }
  }
}
</script>
