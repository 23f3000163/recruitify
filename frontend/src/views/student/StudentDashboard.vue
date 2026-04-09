<template>
  <div class="rq-app rq-student-app" :class="{ 'is-collapsed': sidebarCollapsed }">
    <StudentSidebar
      :sidebar-collapsed="sidebarCollapsed"
      :active-view="activeView"
      :nav-items="mainNavItems"
      :profile-nav-items="profileNavItems"
      :student="student"
      @toggle-sidebar="toggleSidebar"
      @navigate="navigate"
      @request-logout="handleLogout"
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
        @request-logout="handleLogout"
      />

      <StudentToast :message="actionNote" :tone="actionTone" />

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
          :summary="summary"
          @switch-view="navigate"
          @apply-drive="openDriveModal"
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
          @open-drive="openDriveDetails"
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
          :is-scoring="isScoringMatch"
          @update:status-filter="statusFilter = $event"
          @update:query-text="queryText = $event"
          @apply-filters="applyApplicationFilters"
          @page-change="loadApplications"
          @respond-offer="respondToOffer"
          @score-application="scoreApplicationMatch"
          @open-application="openApplicationDetails"
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
          :is-uploading-resume="isUploadingResume"
          :resume-file-name="resumeFileName"
          :student-name="student.name"
          :error-message="profileError"
          @update-field="updateProfileField"
          @upload-resume="uploadResume"
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
          :history-export-status="historyExportStatus"
          :is-history-export-busy="isHistoryExportBusy"
          @update:query-text="historyQuery = $event"
          @apply-filters="applyHistoryFilters"
          @page-change="loadHistory"
          @download-offer="downloadOfferDocument"
          @download-placement="downloadPlacementDocument"
          @export-history="startHistoryExport"
        />

        <StudentSectionPlaceholder
          v-else
          title="Section unavailable"
          description="This section is not available in the current dashboard state."
        />
      </main>

      <DriveApplyModal
        :show="showDriveModal"
        :drive="selectedDrive"
        :student="studentData"
        :profile-complete="isProfileComplete()"
        @close="closeDriveModal"
        @apply="applyToDrive"
        @navigate-profile="goToProfile"
      />

      <StudentApplicationModal
        :application="selectedApplication"
        :screening-result="selectedApplicationScore"
        :score-note="selectedApplicationScoreNote"
        :is-scoring="isSelectedApplicationScoring"
        :is-responding="isSelectedOfferResponding"
        @close="closeApplicationDetails"
        @score-application="scoreApplicationMatch"
        @respond-offer="respondToOffer"
      />
    </div>
  </div>
</template>

<script>
import { authApi, studentApi } from '../../api/api'
import DriveApplyModal from '../../components/DriveApplyModal.vue'
import StudentApplicationModal from '../../components/student/ApplicationModal.vue'
import StudentApplicationsPanel from '../../components/student/ApplicationsView.vue'
import StudentDashboardHome from '../../components/student/DashboardOverview.vue'
import StudentDrivesPanel from '../../components/student/DrivesView.vue'
import StudentHistoryPanel from '../../components/student/HistoryView.vue'
import StudentNotificationsPanel from '../../components/student/NotificationsView.vue'
import StudentProfilePanel from '../../components/student/ProfileView.vue'
import StudentSectionPlaceholder from '../../components/student/StudentSectionPlaceholder.vue'
import StudentSidebar from '../../components/student/Sidebar.vue'
import StudentToast from '../../components/student/Toast.vue'
import StudentTopbar from '../../components/student/Topbar.vue'
import './StudentDashboard.css'

const STORAGE_KEYS = Object.freeze({
  activeView: 'student.dashboard.activeView',
  sidebarCollapsed: 'student.dashboard.sidebarCollapsed'
})

const ACTION_NOTE_TIMEOUT_MS = 3200
const MAX_RESUME_UPLOAD_BYTES = 5 * 1024 * 1024
const ALLOWED_RESUME_FILE_EXTENSIONS = ['pdf', 'doc', 'docx']
const EXPORT_POLL_INTERVAL_MS = 2500
const EXPORT_POLL_MAX_ATTEMPTS = 48

export default {
  name: 'StudentDashboard',
  components: {
    StudentSidebar,
    StudentTopbar,
    StudentToast,
    StudentDashboardHome,
    StudentDrivesPanel,
    StudentHistoryPanel,
    StudentApplicationsPanel,
    StudentNotificationsPanel,
    StudentProfilePanel,
    StudentSectionPlaceholder,
    DriveApplyModal,
    StudentApplicationModal
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
      isUploadingResume: false,
      dashboardError: '',
      drivesError: '',
      applicationsError: '',
      notificationsError: '',
      historyError: '',
      profileError: '',
      resumeFileName: '',
      actionNote: '',
      actionTone: 'info',
      actionNoteTimerId: null,
      atsScoreNotice: '',
      atsScoreNoticeTimerId: null,
      atsScoreNoticeApplicationId: 0,
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
          svg: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 6.5L8 2l6 4.5V14a1 1 0 01-1 1H3a1 1 0 01-1-1V6.5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 15V9h4v6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
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
      isScoringMatch: {},
      atsScoresByApplication: {},
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
      historyExportStatus: 'idle',
      historyExportJobId: '',
      historyExportAttempts: 0,
      historyExportTimerId: null,
      isDownloadingDocument: {},
      showDriveModal: false,
      selectedDrive: null,
      selectedApplication: null,
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
    dashboardDriveSource() {
      if (Array.isArray(this.drives) && this.drives.length > 0) {
        return this.drives.map((drive) => this.mapDriveForDashboard(drive))
      }

      return this.drivesPreview
    },
    liveOpenCount() {
      return this.dashboardDriveSource.length
    },
    unreadCount() {
      return Number(this.unreadNotificationsCount || 0)
    },
    dashboardDrives() {
      const source = this.dashboardDriveSource
      const query = this.searchQuery.trim().toLowerCase()
      if (!query) {
        return source
      }

      return source.filter(
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
    },
    selectedApplicationScore() {
      const applicationId = Number(this.selectedApplication?.application_id || this.selectedApplication?.id || 0)
      if (!applicationId) {
        return null
      }
      return this.atsScoresByApplication[applicationId] || null
    },
    selectedApplicationScoreNote() {
      const applicationId = Number(this.selectedApplication?.application_id || this.selectedApplication?.id || 0)
      if (!applicationId || this.atsScoreNoticeApplicationId !== applicationId) {
        return ''
      }

      return this.atsScoreNotice
    },
    selectedOfferId() {
      return Number(this.selectedApplication?.offer?.offer_id || 0)
    },
    isSelectedOfferResponding() {
      if (!this.selectedOfferId) {
        return false
      }
      return Boolean(this.isRespondingOffer[this.selectedOfferId])
    },
    isSelectedApplicationScoring() {
      const applicationId = Number(this.selectedApplication?.application_id || this.selectedApplication?.id || 0)
      if (!applicationId) {
        return false
      }
      return Boolean(this.isScoringMatch[applicationId])
    },
    studentData() {
      return {
        full_name: String(this.student?.name || '').trim(),
        email: String(this.student?.email || '').trim(),
        phone: String(this.profileForm?.phone || '').trim(),
        branch: String(this.profileForm?.branch || this.student?.branch || '').trim(),
        year: this.profileForm?.year ?? this.student?.year ?? '',
        cgpa: this.profileForm?.cgpa ?? '',
        resume_url: String(this.profileForm?.resume_url || '').trim()
      }
    },
    isHistoryExportBusy() {
      return this.historyExportStatus === 'queued' || this.historyExportStatus === 'running'
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
    this.clearHistoryExportPolling()

    if (this.actionNoteTimerId) {
      clearTimeout(this.actionNoteTimerId)
      this.actionNoteTimerId = null
    }

    this.clearAtsScoreNotice()
  },
  methods: {
    async bootstrap() {
      const bootTasks = [
        this.hydrateIdentity(),
        this.loadDashboard(),
        this.loadDrives(1),
        this.loadApplications(1),
        this.loadNotifications(1),
        this.loadProfile()
      ]

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
          package: this.formatSalaryLpa(row.drive?.salary_lpa),
          appliedOn: this.formatShortDate(row.application_date || row.applied_at || row.updated_at),
          status: row.status || 'applied',
          statusLabel: row.status_label || this.statusLabel(row.status),
          nextStep: this.nextStepForStatus(row.status, row.latest_interview)
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
          deadline: this.formatShortDate(row.drive?.application_deadline),
          branchLabel: this.resolveDriveBranchLabel(row.drive || {}),
          cgpaLabel: this.resolveDriveCgpaLabel(row.drive || {}),
          yearLabel: this.resolveDriveYearLabel(row.drive || {}),
          skillsLabel: this.resolveDriveSkillsLabel(row.drive || row || {}),
          applied: true,
          isOpen: true,
          isEligible: true
        })
      })

      return Array.from(unique.values()).slice(0, 6)
    },
    mapDriveForDashboard(drive) {
      const driveId = drive.drive_id || drive.id
      const salaryLpa = Number(drive.salary_lpa || drive.drive?.salary_lpa || 0)

      return {
        id: driveId,
        role: drive.job_title || drive.title || drive.role || 'Opportunity',
        company:
          drive.company?.name ||
          drive.company?.company_name ||
          drive.company_name ||
          '-',
        salary: salaryLpa > 0 ? `${salaryLpa.toLocaleString()} LPA` : '-',
        deadline: this.formatShortDate(drive.application_deadline || drive.drive?.application_deadline),
        branchLabel: this.resolveDriveBranchLabel(drive),
        cgpaLabel: this.resolveDriveCgpaLabel(drive),
        yearLabel: this.resolveDriveYearLabel(drive),
        skillsLabel: this.resolveDriveSkillsLabel(drive),
        applied: Boolean(drive.already_applied || drive.applied),
        isOpen: drive.is_open !== false,
        isEligible: drive.is_eligible !== false
      }
    },
    resolveDriveBranchLabel(drive) {
      const branchArray = Array.isArray(drive?.eligible_branches)
        ? drive.eligible_branches
        : Array.isArray(drive?.eligibleBranches)
          ? drive.eligibleBranches
          : []

      if (branchArray.length) {
        return branchArray.slice(0, 2).join(', ')
      }

      const branchText = String(drive?.branch || drive?.branches || '').trim()
      return branchText || '-'
    },
    resolveDriveCgpaLabel(drive) {
      const minCgpa = Number(
        drive?.min_cgpa ||
        drive?.minCgpa ||
        drive?.required_cgpa ||
        drive?.cgpa_cutoff ||
        0
      )

      if (!Number.isNaN(minCgpa) && minCgpa > 0) {
        return `CGPA ${minCgpa}+`
      }

      const existingLabel = String(drive?.cgpa_label || drive?.cgpa_requirement || '').trim()
      return existingLabel || 'CGPA -'
    },
    resolveDriveYearLabel(drive) {
      const years = Array.isArray(drive?.eligible_years)
        ? drive.eligible_years
        : Array.isArray(drive?.eligibleYears)
          ? drive.eligibleYears
          : []

      const normalizedYears = years
        .map((value) => Number(value))
        .filter((value) => Number.isInteger(value) && value > 0)

      if (normalizedYears.length) {
        return `Year ${normalizedYears.join(', ')}`
      }

      const existingLabel = String(drive?.year_label || drive?.year_requirement || '').trim()
      return existingLabel || 'Year -'
    },
    formatRequiredSkills(rawValue) {
      const entries = Array.isArray(rawValue)
        ? rawValue
        : String(rawValue || '').split(',')

      const normalized = [...new Set(entries
        .map((item) => String(item || '').trim())
        .filter(Boolean))]

      if (!normalized.length) {
        return 'Skills -'
      }

      if (normalized.length <= 2) {
        return normalized.join(', ')
      }

      return `${normalized.slice(0, 2).join(', ')} +${normalized.length - 2}`
    },
    resolveDriveSkillsLabel(drive) {
      const directRaw = drive?.required_skills ?? drive?.requiredSkills
      const directLabel = this.formatRequiredSkills(directRaw)
      if (directLabel !== 'Skills -') {
        return directLabel
      }

      const existingLabel = String(
        drive?.skillsLabel ||
        drive?.skills_label ||
        drive?.skills_requirement ||
        ''
      ).trim()

      return existingLabel || 'Skills -'
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
    async scoreApplicationMatch(application) {
      const applicationId = Number(application?.application_id || application?.id || 0)
      const driveId = Number(
        application?.drive?.id ||
        application?.drive_id ||
        application?.job_id ||
        0
      )

      if (!applicationId || this.isScoringMatch[applicationId]) {
        return
      }

      if (!driveId) {
        this.publishActionNote('ATS match is unavailable for this application right now.', 'info')
        return
      }

      this.isScoringMatch = {
        ...this.isScoringMatch,
        [applicationId]: true
      }

      try {
        const response = await studentApi.scoreResumeForJob(driveId)
        const scorePayload = response?.data?.data || null

        this.atsScoresByApplication = {
          ...this.atsScoresByApplication,
          [applicationId]: scorePayload
        }
        this.selectedApplication = application

        const score = Number(scorePayload?.analysis?.score || 0)
        this.setAtsScoreNotice(applicationId, score)
      } catch (error) {
        const message =
          error?.response?.data?.error ||
          error?.response?.data?.message ||
          error?.message ||
          'Unable to evaluate ATS keyword match.'
        this.applicationsError = message
        this.publishActionNote(message, 'error')
      } finally {
        this.isScoringMatch = {
          ...this.isScoringMatch,
          [applicationId]: false
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
        this.resumeFileName = this.deriveResumeFileName(studentPayload.resume_url)

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
    clearHistoryExportPolling({ resetState = true } = {}) {
      if (this.historyExportTimerId) {
        clearTimeout(this.historyExportTimerId)
        this.historyExportTimerId = null
      }

      if (resetState) {
        this.historyExportStatus = 'idle'
        this.historyExportJobId = ''
        this.historyExportAttempts = 0
      }
    },
    scheduleHistoryExportPoll() {
      if (this.historyExportTimerId) {
        clearTimeout(this.historyExportTimerId)
      }

      this.historyExportTimerId = setTimeout(() => {
        this.pollHistoryExportStatus()
      }, EXPORT_POLL_INTERVAL_MS)
    },
    async startHistoryExport() {
      if (this.isHistoryExportBusy) {
        this.publishActionNote('History export is already in progress.', 'info')
        return
      }

      this.clearHistoryExportPolling()

      try {
        const response = await studentApi.triggerHistoryExportJob()
        const payload = response?.data?.data || {}
        const jobId = String(payload.job_id || '').trim()

        if (!jobId) {
          this.publishActionNote('Unable to start history export. Please retry.', 'error')
          return
        }

        const initialStatus = String(payload.status || 'queued').toLowerCase() === 'running'
          ? 'running'
          : 'queued'
        this.historyExportStatus = initialStatus
        this.historyExportJobId = jobId
        this.historyExportAttempts = 0

        if (payload.active_job_reused) {
          this.publishActionNote('Tracking existing history export job...', 'info')
        } else if (initialStatus === 'running') {
          this.publishActionNote('History export is running in the background...', 'info')
        } else {
          this.publishActionNote('History export queued. Preparing your CSV...', 'info')
        }

        this.scheduleHistoryExportPoll()
      } catch (error) {
        const message =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to start history export.'
        this.historyExportStatus = 'failed'
        this.publishActionNote(message, 'error')
      }
    },
    async pollHistoryExportStatus() {
      const jobId = String(this.historyExportJobId || '').trim()
      if (!jobId) {
        this.clearHistoryExportPolling()
        return
      }

      if (this.historyExportAttempts >= EXPORT_POLL_MAX_ATTEMPTS) {
        this.historyExportStatus = 'failed'
        this.historyExportJobId = ''
        this.historyExportAttempts = 0
        this.publishActionNote('History export timed out. Please retry.', 'warning')
        return
      }

      try {
        const statusResponse = await studentApi.getExportStatus(jobId)
        const data = statusResponse?.data?.data || {}
        const job = data.job || {}
        const artifact = data.artifact || {}
        const jobStatus = String(job.status || '').toLowerCase()
        const artifactStatus = String(artifact.status || '').toLowerCase()

        if (jobStatus === 'completed' && artifactStatus === 'ready') {
          const downloadResponse = await studentApi.downloadExport(jobId)
          const fallbackName = `history-export-${Date.now()}.csv`
          const filename = this.extractFilename(downloadResponse?.headers, fallbackName)
          this.triggerFileDownload(downloadResponse?.data, filename)
          this.historyExportStatus = 'completed'
          this.historyExportJobId = ''
          this.historyExportAttempts = 0
          this.historyExportTimerId = null
          this.publishActionNote(`Downloaded ${filename}.`, 'success')
          return
        }

        const hasFailed =
          jobStatus === 'failed' ||
          jobStatus === 'cancelled' ||
          artifactStatus === 'failed' ||
          artifactStatus === 'expired'
        if (hasFailed) {
          this.historyExportStatus = 'failed'
          this.historyExportJobId = ''
          this.historyExportAttempts = 0
          this.historyExportTimerId = null

          const fallbackFailureMessage = artifactStatus === 'expired'
            ? 'History export artifact expired. Please retry.'
            : 'Unable to complete history export. Please retry.'
          const errorMessage = job.error_message || fallbackFailureMessage
          this.publishActionNote(errorMessage, 'error')
          return
        }

        const nextStatus = jobStatus === 'running' ? 'running' : 'queued'
        if (nextStatus !== this.historyExportStatus) {
          this.publishActionNote(
            nextStatus === 'running'
              ? 'History export is running in the background...'
              : 'History export queued. Preparing your CSV...',
            'info'
          )
        }

        this.historyExportStatus = nextStatus
        this.historyExportAttempts += 1

        if (this.historyExportAttempts >= EXPORT_POLL_MAX_ATTEMPTS) {
          this.historyExportStatus = 'failed'
          this.historyExportJobId = ''
          this.historyExportAttempts = 0
          this.historyExportTimerId = null
          this.publishActionNote('History export timed out. Please retry.', 'warning')
          return
        }

        this.scheduleHistoryExportPoll()
      } catch (error) {
        this.historyExportAttempts += 1
        if (this.historyExportAttempts >= EXPORT_POLL_MAX_ATTEMPTS) {
          this.historyExportStatus = 'failed'
          this.historyExportJobId = ''
          this.historyExportAttempts = 0
          this.historyExportTimerId = null
          const message =
            error.response?.data?.error ||
            error.response?.data?.message ||
            'Unable to fetch history export status.'
          this.publishActionNote(`${message} Please retry export.`, 'warning')
          return
        }

        this.scheduleHistoryExportPoll()
      }
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
    openDriveDetails(drive) {
      this.openDriveModal(drive)
    },
    openDriveModal(drive) {
      this.selectedDrive = drive || null
      this.showDriveModal = Boolean(drive)
    },
    closeDriveModal() {
      this.showDriveModal = false
      this.selectedDrive = null
    },
    isProfileComplete() {
      const s = this.studentData
      return Boolean(
        s.full_name &&
        s.email &&
        s.phone &&
        s.branch &&
        s.cgpa &&
        s.resume_url
      )
    },
    goToProfile() {
      this.closeDriveModal()
      this.navigate('profile')
    },
    openApplicationDetails(application) {
      const applicationId = Number(application?.application_id || application?.id || 0)
      this.clearApplicationScore(applicationId)
      this.selectedApplication = application || null
    },
    closeApplicationDetails() {
      const applicationId = Number(this.selectedApplication?.application_id || this.selectedApplication?.id || 0)
      this.clearApplicationScore(applicationId)
      this.selectedApplication = null
    },
    clearApplicationScore(applicationId) {
      const parsedId = Number(applicationId)
      if (!parsedId) {
        return
      }

      if (Object.prototype.hasOwnProperty.call(this.atsScoresByApplication, parsedId)) {
        const nextScores = { ...this.atsScoresByApplication }
        delete nextScores[parsedId]
        this.atsScoresByApplication = nextScores
      }

      if (this.atsScoreNoticeApplicationId === parsedId) {
        this.clearAtsScoreNotice()
      }
    },
    clearAtsScoreNotice() {
      if (this.atsScoreNoticeTimerId) {
        clearTimeout(this.atsScoreNoticeTimerId)
        this.atsScoreNoticeTimerId = null
      }

      this.atsScoreNotice = ''
      this.atsScoreNoticeApplicationId = 0
    },
    setAtsScoreNotice(applicationId, score) {
      const parsedId = Number(applicationId)
      if (!parsedId) {
        return
      }

      this.clearAtsScoreNotice()
      this.atsScoreNoticeApplicationId = parsedId
      this.atsScoreNotice = `ATS match score: ${Number(score || 0)}%`
      this.atsScoreNoticeTimerId = setTimeout(() => {
        this.atsScoreNotice = ''
        this.atsScoreNoticeApplicationId = 0
        this.atsScoreNoticeTimerId = null
      }, ACTION_NOTE_TIMEOUT_MS)
    },
    updateProfileField(field, value) {
      this.profileForm = {
        ...this.profileForm,
        [field]: value
      }

      if (field === 'resume_url') {
        this.resumeFileName = this.deriveResumeFileName(value)
      }
    },
    deriveResumeFileName(resumeUrl) {
      const normalizedUrl = String(resumeUrl || '').trim()
      if (!normalizedUrl) {
        return ''
      }

      const sanitizedUrl = normalizedUrl.split('?')[0].split('#')[0]
      const segments = sanitizedUrl.split('/').filter(Boolean)
      if (!segments.length) {
        return ''
      }

      const finalSegment = segments[segments.length - 1]
      try {
        return decodeURIComponent(finalSegment)
      } catch (error) {
        return finalSegment
      }
    },
    validateResumeFile(file) {
      if (!file) {
        return 'Please choose a resume file to upload.'
      }

      const fileName = String(file.name || '').trim()
      const extension = fileName.includes('.')
        ? fileName.split('.').pop().toLowerCase()
        : ''

      if (!ALLOWED_RESUME_FILE_EXTENSIONS.includes(extension)) {
        return 'Only PDF, DOC, or DOCX files are allowed.'
      }

      const fileSize = Number(file.size || 0)
      if (fileSize <= 0) {
        return 'Uploaded resume file is empty.'
      }

      if (fileSize > MAX_RESUME_UPLOAD_BYTES) {
        return 'Resume file must be 5 MB or smaller.'
      }

      return ''
    },
    async uploadResume(file) {
      if (this.isUploadingResume || this.isSavingProfile) {
        return
      }

      const validationError = this.validateResumeFile(file)
      if (validationError) {
        this.profileError = validationError
        this.publishActionNote(validationError, 'error')
        return
      }

      this.isUploadingResume = true
      this.profileError = ''

      try {
        const response = await studentApi.uploadResume(file)
        const studentPayload = response?.data?.data?.student || {}
        const resolvedResumeUrl =
          studentPayload.resume_url || this.profileForm.resume_url || ''

        this.profileForm = {
          ...this.profileForm,
          resume_url: resolvedResumeUrl
        }
        this.resumeFileName = this.deriveResumeFileName(resolvedResumeUrl)

        this.publishActionNote('Resume uploaded successfully.', 'success')
      } catch (error) {
        this.profileError =
          error.response?.data?.error ||
          error.response?.data?.message ||
          'Unable to upload resume.'
        this.publishActionNote(this.profileError, 'error')
      } finally {
        this.isUploadingResume = false
      }
    },
    validateStudentProfilePayload(payload) {
      if (!payload.college_name) {
        return 'College name is required.'
      }
      if (!payload.branch) {
        return 'Branch is required.'
      }
      if (!payload.roll_number) {
        return 'Roll number is required.'
      }

      const year = Number(payload.year)
      if (!Number.isInteger(year) || year < 1 || year > 6) {
        return 'Year must be a whole number between 1 and 6.'
      }

      const cgpa = Number(payload.cgpa)
      if (Number.isNaN(cgpa) || cgpa < 0 || cgpa > 10) {
        return 'CGPA must be between 0 and 10.'
      }

      const phone = String(payload.phone || '').trim()
      if (phone && !/^\d{10}$/.test(phone)) {
        return 'Phone number must be exactly 10 digits.'
      }

      const resumeUrl = String(payload.resume_url || '').trim()
      if (resumeUrl && !/^https?:\/\//i.test(resumeUrl)) {
        return 'Resume URL must start with http:// or https://.'
      }

      return ''
    },
    normalizeSkillsForSave(rawSkills) {
      const parts = String(rawSkills || '')
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)

      const deduped = []
      const seen = new Set()

      parts.forEach((item) => {
        const key = item.toLowerCase()
        if (seen.has(key)) {
          return
        }

        seen.add(key)
        deduped.push(item)
      })

      return deduped.join(', ')
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
        skills: this.normalizeSkillsForSave(this.profileForm.skills),
        experience_summary: String(this.profileForm.experience_summary || '').trim()
      }

      const validationError = this.validateStudentProfilePayload(payload)
      if (validationError) {
        this.profileError = validationError
        this.publishActionNote(validationError, 'error')
        this.isSavingProfile = false
        return
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
        this.resumeFileName = this.deriveResumeFileName(this.profileForm.resume_url)

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
    formatSalaryLpa(value) {
      const parsed = Number(value)
      if (Number.isNaN(parsed) || parsed <= 0) {
        return '-'
      }

      return `${parsed.toLocaleString('en-IN')} LPA`
    },
    nextStepForStatus(status, latestInterview) {
      const normalized = String(status || '').toLowerCase()

      if (normalized === 'interviewed' || normalized === 'interview') {
        const interviewDate = latestInterview?.interview_date
        const formatted = this.formatShortDate(interviewDate)
        return formatted !== '-' ? `Interview on ${formatted}` : 'Interview in progress'
      }
      if (normalized === 'shortlisted') {
        return 'Awaiting interview schedule'
      }
      if (normalized === 'offered' || normalized === 'selected') {
        return 'Review offer details'
      }
      if (normalized === 'accepted' || normalized === 'placed') {
        return 'Offer accepted'
      }
      if (normalized === 'rejected') {
        return 'Application closed'
      }

      return 'Awaiting update'
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
    handleLogout() {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('user_id')

      if (this.$router && typeof this.$router.push === 'function') {
        this.$router.push('/login')
        return
      }

      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    },
    navigate(viewId) {
      const nextView = typeof viewId === 'string' && viewId ? viewId : 'dashboard'
      const previousView = this.activeView
      const isViewChanging = nextView !== previousView

      this.activeView = nextView

      if (isViewChanging) {
        this.closeDriveModal()
        this.closeApplicationDetails()

        if (previousView === 'history' && nextView !== 'history') {
          this.clearHistoryExportPolling()
        }
      }

      if (nextView === 'drives' && !this.drives.length) {
        this.loadDrives(1)
      }
      if (nextView === 'applications' && !this.applications.length) {
        this.loadApplications(1)
      }
      if (nextView === 'notifications' && !this.notifications.length) {
        this.loadNotifications(1)
      }
      if (nextView === 'history' && !this.historyItems.length) {
        this.loadHistory(1)
      }
    }
  }
}
</script>
