<template>
  <div class="rq-app rq-admin-app" :class="{ 'is-collapsed': sidebarCollapsed }">
    <Sidebar
      :sidebar-collapsed="sidebarCollapsed"
      :nav-items="navItems"
      :active-view="activeView"
      @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed"
      @select-view="activeView = $event"
      @request-logout="handleLogout"
    />

    <div class="rq-main">
      <Topbar
        :current-page-title="currentPageTitle"
        :search-query="searchQuery"
        :search-focused="searchFocused"
        :search-dropdown-open="searchDropdownOpen"
        :search-results="searchResults"
        :pending-count="unreadNotificationsCount"
        :show-notifications="showNotifications"
        @set-search-focused="searchFocused = $event"
        @set-search-dropdown-open="searchDropdownOpen = $event"
        @update-search-query="searchQuery = $event"
        @handle-search="handleSearch"
        @clear-search="clearSearch"
        @commit-search="commitSearch"
        @go-to-result="goToResult"
        @toggle-notifications="toggleNotificationsPanel"
        @request-logout="handleLogout"
      />

      <Transition name="rq-slide">
        <AdminNotificationPanel
          v-if="showNotifications"
          :notifications="notifications"
          :is-loading="isLoadingNotifications"
          :unread-count="unreadNotificationsCount"
          :error-message="notificationsError"
          :is-marking="isMarkingNotification"
          :is-marking-all="isMarkingAllNotifications"
          @close="closeNotificationsPanel"
          @mark-read="markNotificationRead"
          @mark-all-read="markAllNotificationsRead"
        />
      </Transition>
      <div
        v-if="showNotifications"
        class="rq-admin-notif-backdrop"
        @click="closeNotificationsPanel"
      ></div>

      <main class="rq-page" role="main" @click="searchDropdownOpen = false">
        <DashboardOverview
          v-if="activeView === 'dashboard'"
          :kpi-cards="kpiCards"
          :pending-approvals="pendingApprovals"
          :branch-stats="branchStats"
          :audit-log="auditLog"
          :recent-applications="recentApplications"
          :is-loading="isOverviewLoading"
          :error-message="overviewErrorMessage"
          :pending-company-actions="pendingActions.company"
          :pending-drive-actions="pendingActions.drive"
          :pct="pct"
          @switch-view="activeView = $event"
          @approve-item="approveItem"
          @reject-item="rejectItem"
          @retry="retryOverviewLoad"
          @export="doExport"
        />

        <CompaniesTable
          v-if="activeView === 'companies'"
          :filtered-companies="filteredCompanies"
          :co-search="coSearch"
          :co-search-focused="coSearchFocused"
          :co-filters="coFilters"
          :co-filter="coFilter"
          :co-page="coPage"
          :co-pages="coPages"
          :co-total="coTotal"
          :co-sort-by="coSortBy"
          :co-order="coOrder"
          :is-loading="loading.companies"
          :error-message="loadErrors.companies"
          :pending-company-actions="pendingActions.company"
          @update-co-search="coSearch = $event"
          @set-co-search-focused="coSearchFocused = $event"
          @update-co-filter="coFilter = $event"
          @update-co-sort-by="setCoSortBy"
          @toggle-co-order="toggleCoOrder"
          @set-co-page="setCoPage"
          @prev-co-page="prevCoPage"
          @next-co-page="nextCoPage"
          @retry="fetchCompanies()"
          @export="doExport"
          @change-status="changeCoStatus"
          @remove-company="removeCompany"
        />

        <StudentsTable
          v-if="activeView === 'students'"
          :filtered-students="filteredStudents"
          :stu-search="stuSearch"
          :stu-search-focused="stuSearchFocused"
          :stu-branch="stuBranch"
          :branch-filter-options="branchFilterOptions"
          :stu-page="stuPage"
          :stu-pages="stuPages"
          :stu-total="stuTotal"
          :stu-sort-by="stuSortBy"
          :stu-order="stuOrder"
          :is-loading="loading.students"
          :error-message="loadErrors.students"
          :pending-student-actions="pendingActions.student"
          @update-stu-search="stuSearch = $event"
          @set-stu-search-focused="stuSearchFocused = $event"
          @update-stu-branch="stuBranch = $event"
          @update-stu-sort-by="setStuSortBy"
          @toggle-stu-order="toggleStuOrder"
          @set-stu-page="setStuPage"
          @prev-stu-page="prevStuPage"
          @next-stu-page="nextStuPage"
          @retry="fetchStudents()"
          @export="doExport"
          @show-student-apps="showStudentApps"
          @change-status="changeStuStatus"
        />

        <DrivesPanel
          v-if="activeView === 'drives'"
          :filtered-drives="filteredDrives"
          :drive-filters="driveFilters"
          :drive-filter="driveFilter"
          :drive-page="drivePage"
          :drive-pages="drivePages"
          :drive-total="driveTotal"
          :drive-sort-by="driveSortBy"
          :drive-order="driveOrder"
          :is-loading="loading.drives"
          :error-message="loadErrors.drives"
          :pending-drive-actions="pendingActions.drive"
          @update-drive-filter="driveFilter = $event"
          @update-drive-sort-by="setDriveSortBy"
          @toggle-drive-order="toggleDriveOrder"
          @set-drive-page="setDrivePage"
          @prev-drive-page="prevDrivePage"
          @next-drive-page="nextDrivePage"
          @retry="fetchDrives()"
          @export="doExport"
          @change-drive-status="changeDriveStatus"
          @remove-drive="removeDrive"
        />

        <AnalyticsPanel
          v-if="activeView === 'analytics'"
          :analytics-overview="analyticsOverview"
          :is-loading="loading.analytics"
          :error-message="loadErrors.analytics"
          :top-companies="topCompanies"
          :branch-stats="branchStats"
          :placed-count="placedCount"
          :in-progress-count="inProgressCount"
          :not-placed-count="notPlacedCount"
          :placement-rate-pct="placementRatePct"
          :donut-circ="donutCirc"
          :donut-placed-offset="donutPlacedOffset"
          :pct="pct"
          @retry="fetchAnalyticsOverview()"
          @export="doExport"
        />
      </main>
    </div>

    <StudentApplicationsModal
      :selected-student="selectedStudent"
      :pending-application-actions="pendingActions.application"
      @close="selectedStudent = null"
      @update-app-status="changeApplicationStatus"
    />

    <Transition name="rq-toast">
      <Toast v-if="toast.show" :toast="toast" @dismiss="toast.show = false" />
    </Transition>
  </div>
</template>

<script>
import { adminApi } from '../../api/api'
import AnalyticsPanel from '../../components/admin/AnalyticsPanel.vue'
import AdminNotificationPanel from '../../components/admin/AdminNotificationPanel.vue'
import CompaniesTable from '../../components/admin/CompaniesTable.vue'
import DashboardOverview from '../../components/admin/DashboardOverview.vue'
import DrivesPanel from '../../components/admin/DrivesPanel.vue'
import Sidebar from '../../components/admin/Sidebar.vue'
import StudentApplicationsModal from '../../components/admin/StudentApplicationsModal.vue'
import StudentsTable from '../../components/admin/StudentsTable.vue'
import Toast from '../../components/layout/Toast.vue'
import Topbar from '../../components/admin/Topbar.vue'
import './AdminDashboard.css'

export default {
  name: 'AdminDashboard',
  components: {
    Sidebar,
    Topbar,
    AdminNotificationPanel,
    DashboardOverview,
    CompaniesTable,
    StudentsTable,
    DrivesPanel,
    AnalyticsPanel,
    StudentApplicationsModal,
    Toast
  },
  data() {
    const svgs = {
      home: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 6.5L8 2l6 4.5V14a1 1 0 01-1 1H3a1 1 0 01-1-1V6.5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 15V9h4v6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
      building: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="3" width="12" height="12" rx="1" stroke="currentColor" stroke-width="1.5"/><path d="M5 7h2M9 7h2M5 10h2M9 10h2M7 15V12h2v3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M5 3V2a1 1 0 011-1h4a1 1 0 011 1v1" stroke="currentColor" stroke-width="1.5"/></svg>',
      students: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="5" r="3" stroke="currentColor" stroke-width="1.5"/><path d="M2 14c0-3.314 2.686-5 6-5s6 1.686 6 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>',
      clipboard: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="3" y="2" width="10" height="13" rx="1.5" stroke="currentColor" stroke-width="1.5"/><path d="M6 7h4M6 10h4M6 13h2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M5.5 2A1.5 1.5 0 018 1a1.5 1.5 0 012.5 1" stroke="currentColor" stroke-width="1.5"/></svg>',
      chart: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 12l4-4 3 3 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 14.5h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
    }

    return {
      svgs,
      sidebarCollapsed: false,
      activeView: 'dashboard',
      searchQuery: '',
      searchFocused: false,
      searchDropdownOpen: false,
      searchResults: [],
      searchDebounceTimer: null,
      coSearchDebounceTimer: null,
      stuSearchDebounceTimer: null,
      coSearchFocused: false,
      stuSearchFocused: false,
      coSearch: '',
      coFilter: '',
      coPage: 1,
      coPages: 1,
      coTotal: 0,
      coLimit: 10,
      coSortBy: 'created_at',
      coOrder: 'desc',
      stuSearch: '',
      stuBranch: '',
      stuPage: 1,
      stuPages: 1,
      stuTotal: 0,
      stuLimit: 10,
      stuSortBy: 'created_at',
      stuOrder: 'desc',
      driveFilter: '',
      drivePage: 1,
      drivePages: 1,
      driveTotal: 0,
      driveLimit: 10,
      driveSortBy: 'created_at',
      driveOrder: 'desc',
      selectedStudent: null,
      showNotifications: false,
      notifications: [],
      unreadNotificationsCount: 0,
      notificationsError: '',
      isLoadingNotifications: false,
      isMarkingNotification: {},
      isMarkingAllNotifications: false,
      toast: { show: false, message: '', icon: '', type: 'success' },
      _toastTimer: null,
      loading: {
        dashboard: false,
        companies: false,
        students: false,
        drives: false,
        applications: false,
        activity: false,
        analytics: false
      },
      loadErrors: {
        dashboard: '',
        companies: '',
        students: '',
        drives: '',
        applications: '',
        activity: '',
        analytics: ''
      },
      pendingActions: {
        company: {},
        student: {},
        drive: {},
        application: {}
      },
      dashboardStats: {
        total_students: 0,
        total_companies: 0,
        total_jobs: 0,
        total_applications: 0
      },
      companies: [],
      students: [],
      allDrives: [],
      applications: [],
      auditLog: [],
      analyticsOverview: {
        summary: {},
        placement_trends: [],
        application_funnel: {},
        job_demand_by_skills: [],
        meta: {}
      },
      coFilters: [
        { l: 'All', v: '' },
        { l: 'Approved', v: 'approved' },
        { l: 'Pending', v: 'pending' },
        { l: 'Rejected', v: 'rejected' },
        { l: 'Blacklisted', v: 'blacklisted' }
      ],
      driveFilters: [
        { l: 'All', v: '' },
        { l: 'Approved', v: 'approved' },
        { l: 'Pending', v: 'pending' },
        { l: 'Rejected', v: 'rejected' }
      ]
    }
  },
  computed: {
    currentPageTitle() {
      const labels = {
        dashboard: 'Dashboard',
        companies: 'Companies',
        students: 'Students',
        drives: 'Placement Drives',
        analytics: 'Analytics'
      }
      return labels[this.activeView] || ''
    },
    pendingCount() {
      return Number(this.unreadNotificationsCount || 0)
    },
    navItems() {
      const pendingCompanies = this.companies.filter((c) => c.status === 'pending').length
      const pendingDrives = this.allDrives.filter((d) => d.status === 'pending').length
      return [
        { id: 'dashboard', label: 'Dashboard', svg: this.svgs.home, badge: null },
        { id: 'companies', label: 'Companies', svg: this.svgs.building, badge: pendingCompanies || null },
        { id: 'students', label: 'Students', svg: this.svgs.students, badge: null },
        { id: 'drives', label: 'Placement Drives', svg: this.svgs.clipboard, badge: pendingDrives || null },
        { id: 'analytics', label: 'Analytics', svg: this.svgs.chart, badge: null }
      ]
    },
    pendingApprovals() {
      const companyItems = this.companies
        .filter((co) => co.status === 'pending')
        .map((co) => ({
          id: `company-${co.id}`,
          entityType: 'company',
          entityId: co.id,
          name: co.name,
          sub: 'New registration',
          type: 'Company',
          date: co.createdAtLabel,
          initials: co.initials,
          color: co.color
        }))

      const driveItems = this.allDrives
        .filter((drive) => drive.status === 'pending')
        .map((drive) => ({
          id: `drive-${drive.id}`,
          entityType: 'drive',
          entityId: drive.id,
          name: drive.title,
          sub: `${drive.company} · Drive`,
          type: 'Drive',
          date: drive.createdAtLabel,
          initials: drive.initials,
          color: drive.color
        }))

      return [...companyItems, ...driveItems]
    },
    kpiCards() {
      const totalStudents = Number(this.dashboardStats.total_students || 0)
      const totalCompanies = Number(this.dashboardStats.total_companies || 0)
      const totalDrives = Number(this.dashboardStats.total_jobs || 0)
      const totalApplications = Number(this.dashboardStats.total_applications || 0)
      const placed = this.placedCount
      const processedApplications = this.applications.filter((application) => application.status !== 'pending').length
      const studentDen = totalStudents || 1
      const companyDen = totalCompanies || 1
      const driveDen = totalDrives || 1
      const applicationDen = totalApplications || 1

      return [
        {
          id: 'students',
          label: 'Total Students',
          value: totalStudents.toLocaleString(),
          link: 'students',
          delta: `${this.inProgressCount} in progress`,
          badgeClass: 'badge-blue',
          up: true,
          pct: Math.min(100, Math.round((placed / studentDen) * 100)),
          color: '#2563EB',
          colorLt: '#EFF6FF',
          svg: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="6" r="4" stroke="currentColor" stroke-width="1.6"/><path d="M3 18c0-3.866 3.134-6 7-6s7 2.134 7 6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>'
        },
        {
          id: 'companies',
          label: 'Total Companies',
          value: totalCompanies.toLocaleString(),
          link: 'companies',
          delta: `${this.companies.filter((co) => co.status === 'pending').length} pending`,
          badgeClass: 'badge-green',
          up: true,
          pct: Math.min(100, Math.round(((totalCompanies - this.pendingCount) / companyDen) * 100)),
          color: '#059669',
          colorLt: '#ECFDF5',
          svg: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="2" y="4" width="16" height="14" rx="1.5" stroke="currentColor" stroke-width="1.6"/><path d="M7 9h2M11 9h2M7 13h2M11 13h2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M7 4V3a1 1 0 011-1h4a1 1 0 011 1v1" stroke="currentColor" stroke-width="1.6"/></svg>'
        },
        {
          id: 'drives',
          label: 'Total Placement Drives',
          value: totalDrives.toLocaleString(),
          link: 'drives',
          delta: `${this.allDrives.filter((d) => d.status === 'pending').length} pending approval`,
          badgeClass: 'badge-amber',
          up: false,
          pct: Math.min(100, Math.round((this.allDrives.filter((d) => d.status === 'approved').length / driveDen) * 100)),
          color: '#D97706',
          colorLt: '#FFFBEB',
          svg: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="4" y="2" width="12" height="16" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M7 8h6M7 11h6M7 14h4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>'
        },
        {
          id: 'applications',
          label: 'Total Applications',
          value: totalApplications.toLocaleString(),
          link: null,
          delta: `${processedApplications} processed`,
          badgeClass: 'badge-purple',
          up: true,
          pct: Math.min(100, Math.round((processedApplications / applicationDen) * 100)),
          color: '#7C3AED',
          colorLt: '#F5F3FF',
          svg: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 2l2.1 4.3L17 7.6l-3.5 3.4.8 4.8L10 13.6l-4.3 2.2.8-4.8L3 7.6l4.9-.9z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        }
      ]
    },
    companyNameById() {
      return this.companies.reduce((acc, company) => {
        acc[company.id] = company.name
        return acc
      }, {})
    },
    applicationsByDriveId() {
      return this.applications.reduce((acc, application) => {
        const key = application.driveId
        if (!acc[key]) acc[key] = []
        acc[key].push(application)
        return acc
      }, {})
    },
    applicationsByStudentId() {
      return this.applications.reduce((acc, application) => {
        const key = application.studentId
        if (!acc[key]) acc[key] = []
        acc[key].push(application)
        return acc
      }, {})
    },
    companiesWithMetrics() {
      return this.companies.map((company) => {
        const drives = this.allDrives.filter((drive) => drive.companyId === company.id)
        const applicants = drives.reduce((sum, drive) => sum + (this.applicationsByDriveId[drive.id]?.length || 0), 0)
        return {
          ...company,
          drives: drives.length,
          applicants
        }
      })
    },
    studentsWithMetrics() {
      return this.students.map((student) => {
        const appList = (this.applicationsByStudentId[student.id] || []).map((application) => ({
          id: application.id,
          drive: application.driveTitle,
          company: application.companyName,
          date: application.appliedOn,
          status: application.status,
          rawStatus: application.rawStatus
        }))
        return {
          ...student,
          applications: appList.length,
          appList
        }
      })
    },
    filteredCompanies() {
      return this.companiesWithMetrics.filter((company) => {
        const matchesFilter = !this.coFilter || company.status === this.coFilter
        return matchesFilter
      })
    },
    filteredStudents() {
      return this.studentsWithMetrics.filter((student) => {
        const matchesBranch = !this.stuBranch || student.branch === this.stuBranch
        return matchesBranch
      })
    },
    filteredDrives() {
      return this.allDrives
        .filter((drive) => !this.driveFilter || drive.status === this.driveFilter)
        .map((drive) => ({
          ...drive,
          company: this.companyNameById[drive.companyId] || drive.company,
          applicants: this.applicationsByDriveId[drive.id]?.length || 0
        }))
    },
    recentApplications() {
      return this.applications.slice(0, 5).map((application) => ({
        id: application.id,
        student: application.studentName,
        roll: application.studentRoll,
        drive: application.driveTitle,
        company: application.companyName,
        status: application.status,
        initials: application.initials,
        color: application.color
      }))
    },
    branchStats() {
      const groups = {}
      this.studentsWithMetrics.forEach((student) => {
        const branchKey = student.branch || 'OTHER'
        if (!groups[branchKey]) {
          groups[branchKey] = { name: branchKey, placed: 0, total: 0, color: this.branchColor(branchKey) }
        }
        groups[branchKey].total += 1
        const approved = student.appList.some((application) => application.status === 'approved')
        if (approved) groups[branchKey].placed += 1
      })
      return Object.values(groups)
    },
    topCompanies() {
      const rows = this.companiesWithMetrics.map((company) => {
        const drives = this.allDrives.filter((drive) => drive.companyId === company.id)
        const relatedApplications = drives.flatMap((drive) => this.applicationsByDriveId[drive.id] || [])
        const offers = relatedApplications.filter((application) => application.status === 'approved').length
        const salaryValues = drives.map((drive) => drive.salaryLpa).filter((salary) => Number.isFinite(salary))
        const avg = salaryValues.length ? (salaryValues.reduce((sum, salary) => sum + salary, 0) / salaryValues.length) : 0
        const max = salaryValues.length ? Math.max(...salaryValues) : 0

        return {
          name: company.name,
          drives: drives.length,
          offers,
          avgPkg: avg ? `₹${avg.toFixed(1)} LPA` : '₹0 LPA',
          highest: max ? `₹${max.toFixed(1)} LPA` : '₹0 LPA',
          initials: company.initials,
          color: company.color
        }
      })

      return rows.sort((a, b) => b.offers - a.offers).slice(0, 4)
    },
    placedCount() {
      const studentIds = new Set(this.applications.filter((application) => application.status === 'approved').map((application) => application.studentId))
      return studentIds.size
    },
    inProgressCount() {
      return this.applications.filter((application) => application.status === 'pending').length
    },
    totalEligible() {
      return this.students.length || 1
    },
    donutCirc() {
      return +(2 * Math.PI * 46).toFixed(2)
    },
    placementRatePct() {
      return Math.round((this.placedCount / this.totalEligible) * 100)
    },
    notPlacedCount() {
      return Math.max(0, this.totalEligible - this.placedCount - this.inProgressCount)
    },
    donutPlacedOffset() {
      return +(this.donutCirc * (1 - this.placedCount / this.totalEligible)).toFixed(2)
    },
    branchFilterOptions() {
      const branches = Array.from(new Set(this.students.map((student) => student.branch).filter(Boolean)))
      return ['All', ...branches]
    },
    isOverviewLoading() {
      return this.loading.dashboard || this.loading.companies || this.loading.students || this.loading.drives || this.loading.applications || this.loading.activity
    },
    overviewErrorMessage() {
      return this.loadErrors.dashboard || this.loadErrors.companies || this.loadErrors.students || this.loadErrors.drives || this.loadErrors.applications || this.loadErrors.activity || ''
    }
  },
  async mounted() {
    await this.retryOverviewLoad()
  },
  beforeUnmount() {
    clearTimeout(this.searchDebounceTimer)
    clearTimeout(this.coSearchDebounceTimer)
    clearTimeout(this.stuSearchDebounceTimer)
    clearTimeout(this._toastTimer)
  },
  watch: {
    coSearch(value) {
      clearTimeout(this.coSearchDebounceTimer)
      this.coSearchDebounceTimer = setTimeout(() => {
        this.coPage = 1
        this.fetchCompanies(value)
      }, 220)
    },
    stuSearch(value) {
      clearTimeout(this.stuSearchDebounceTimer)
      this.stuSearchDebounceTimer = setTimeout(() => {
        this.stuPage = 1
        this.fetchStudents(value)
      }, 220)
    }
  },
  methods: {
    setPendingAction(group, id, isPending) {
      if (!group || !id) return
      const next = { ...(this.pendingActions[group] || {}) }
      if (isPending) {
        next[id] = true
      } else {
        delete next[id]
      }
      this.pendingActions[group] = next
    },
    async retryOverviewLoad() {
      await this.fetchCompanies()
      await Promise.all([
        this.fetchDashboard(),
        this.fetchStudents(),
        this.fetchDrives(),
        this.fetchApplications(),
        this.fetchAuditLog(),
        this.fetchAnalyticsOverview(),
        this.loadNotifications({ silent: true })
      ])
    },
    pct(a, b) {
      if (!b) return 0
      return Math.round((a / b) * 100)
    },
    branchColor(name) {
      const key = String(name || 'OTHER').trim().toUpperCase()
      const map = {
        CSE: '#3b82f6',
        OTHER: '#8b5cf6',
        IT: '#22c55e',
        MECH: '#f59e0b',
        ECE: '#06b6d4'
      }
      return map[key] || '#6b7280'
    },
    colorFromKey(key) {
      const colors = [
        'linear-gradient(135deg,#2563EB,#1D4ED8)',
        'linear-gradient(135deg,#059669,#047857)',
        'linear-gradient(135deg,#D97706,#B45309)',
        'linear-gradient(135deg,#7C3AED,#6D28D9)',
        'linear-gradient(135deg,#0EA5E9,#0284C7)',
        'linear-gradient(135deg,#E31837,#B91C1C)',
        'linear-gradient(135deg,#00B4D8,#0077B6)'
      ]
      let hash = 0
      const text = String(key || '')
      for (let i = 0; i < text.length; i += 1) {
        hash = ((hash << 5) - hash) + text.charCodeAt(i)
        hash |= 0
      }
      return colors[Math.abs(hash) % colors.length]
    },
    initialsFromText(text) {
      const parts = String(text || '').split(/\s+/).filter(Boolean)
      if (!parts.length) return 'NA'
      if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
    },
    formatDateLabel(value) {
      if (!value) return '—'
      const date = new Date(value)
      if (Number.isNaN(date.getTime())) return '—'
      return date.toLocaleString()
    },
    formatDateShort(value) {
      if (!value) return '—'
      const date = new Date(value)
      if (Number.isNaN(date.getTime())) return '—'
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
    },
    formatRelativeTime(value) {
      if (!value) return 'recently'

      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) return 'recently'

      const deltaMs = Date.now() - parsed.getTime()
      const deltaMinutes = Math.max(1, Math.floor(deltaMs / 60000))

      if (deltaMinutes < 60) return `${deltaMinutes} min ago`

      const deltaHours = Math.floor(deltaMinutes / 60)
      if (deltaHours < 24) return `${deltaHours} hr ago`

      const deltaDays = Math.floor(deltaHours / 24)
      return deltaDays === 1 ? 'Yesterday' : `${deltaDays} days ago`
    },
    normalizeNotificationType(notification) {
      const text = `${notification.title || ''} ${notification.message || ''}`.toLowerCase()

      if (text.includes('reject') || text.includes('failed')) return 'danger'
      if (text.includes('approve') || text.includes('accepted') || text.includes('success')) return 'success'
      if (text.includes('pending') || text.includes('review')) return 'warning'
      return 'info'
    },
    normalizeNotification(item) {
      const id = Number(item.notification_id || item.id || 0)
      return {
        id,
        title: item.title || 'Notification',
        sub: item.message || '-',
        time: this.formatRelativeTime(item.created_at || item.sent_at),
        type: this.normalizeNotificationType(item),
        read: Boolean(item.is_read)
      }
    },
    closeNotificationsPanel() {
      this.showNotifications = false
    },
    async toggleNotificationsPanel() {
      if (this.showNotifications) {
        this.closeNotificationsPanel()
        return
      }

      this.showNotifications = true
      await this.loadNotifications({ silent: true })
    },
    async loadNotifications(options = {}) {
      const page = Number(options.page || 1)
      const limit = Number(options.limit || 25)
      const silent = Boolean(options.silent)

      this.isLoadingNotifications = true
      if (!silent) {
        this.notificationsError = ''
      }

      try {
        const response = await adminApi.getNotifications({ page, limit, is_read: 'all' })
        const payload = response?.data?.data || {}
        const items = Array.isArray(payload.items) ? payload.items : []

        this.notifications = items.map((item) => this.normalizeNotification(item)).filter((item) => item.id)

        if (typeof payload.unread_count === 'number') {
          this.unreadNotificationsCount = payload.unread_count
        } else {
          this.unreadNotificationsCount = this.notifications.filter((item) => !item.read).length
        }
        this.notificationsError = ''
      } catch (error) {
        const message = error.response?.data?.error || 'Unable to load notifications.'
        this.notificationsError = message
        if (!silent) {
          this.toast_show(message, 'danger')
        }
      } finally {
        this.isLoadingNotifications = false
      }
    },
    async markNotificationRead(notificationId) {
      const targetId = Number(notificationId)
      if (!targetId || this.isMarkingNotification[targetId]) {
        return
      }

      const target = this.notifications.find((item) => item.id === targetId)
      if (!target || target.read) {
        return
      }

      const previousUnread = this.unreadNotificationsCount
      target.read = true
      this.unreadNotificationsCount = Math.max(0, previousUnread - 1)
      this.isMarkingNotification = {
        ...this.isMarkingNotification,
        [targetId]: true
      }

      try {
        const response = await adminApi.markNotificationRead(targetId)
        const payload = response?.data?.data || {}
        if (typeof payload.unread_count === 'number') {
          this.unreadNotificationsCount = payload.unread_count
        }
      } catch (error) {
        target.read = false
        this.unreadNotificationsCount = previousUnread
        const message = error.response?.data?.error || 'Unable to update notification.'
        this.notificationsError = message
        this.toast_show(message, 'danger')
      } finally {
        this.isMarkingNotification = {
          ...this.isMarkingNotification,
          [targetId]: false
        }
      }
    },
    async markAllNotificationsRead() {
      if (this.isMarkingAllNotifications || this.unreadNotificationsCount === 0) {
        return
      }

      const previousNotifications = this.notifications.map((item) => ({ ...item }))
      const previousUnread = this.unreadNotificationsCount

      this.isMarkingAllNotifications = true
      this.notifications = this.notifications.map((item) => ({
        ...item,
        read: true
      }))
      this.unreadNotificationsCount = 0

      try {
        const response = await adminApi.markAllNotificationsRead()
        const payload = response?.data?.data || {}
        this.unreadNotificationsCount = typeof payload.unread_count === 'number' ? payload.unread_count : 0
        this.notificationsError = ''
        this.toast_show('All notifications marked as read.', 'success')
      } catch (error) {
        this.notifications = previousNotifications
        this.unreadNotificationsCount = previousUnread
        const message = error.response?.data?.error || 'Unable to update notifications.'
        this.notificationsError = message
        this.toast_show(message, 'danger')
      } finally {
        this.isMarkingAllNotifications = false
      }
    },
    normalizeDriveStatus(status) {
      if (status === 'approved') return 'approved'
      if (status === 'closed' || status === 'rejected') return 'rejected'
      return 'pending'
    },
    normalizeApplicationStatus(status) {
      if (status === 'selected' || status === 'approved') return 'approved'
      if (status === 'rejected') return 'rejected'
      return 'pending'
    },
    normalizeCompanyStatus(company) {
      if (company.is_active === false || company.is_blacklisted) return 'blacklisted'
      if (company.status === 'approved' || company.status === 'rejected' || company.status === 'pending') return company.status
      if (company.approval_status === 'approved' || company.approval_status === 'rejected' || company.approval_status === 'pending') return company.approval_status
      return 'pending'
    },
    normalizeStudentStatus(student) {
      if (student.is_blacklisted || student.is_active === false) return 'blacklisted'
      return 'active'
    },
    async fetchDashboard() {
      this.loading.dashboard = true
      this.loadErrors.dashboard = ''
      try {
        const response = await adminApi.getDashboard()
        this.dashboardStats = response.data?.data || this.dashboardStats
      } catch (error) {
        const message = error.response?.data?.error || 'Failed to load dashboard'
        this.loadErrors.dashboard = message
        this.toast_show(message, 'danger')
      } finally {
        this.loading.dashboard = false
      }
    },
    async fetchAnalyticsOverview(months = 6) {
      this.loading.analytics = true
      this.loadErrors.analytics = ''
      try {
        const response = await adminApi.getAnalyticsOverview({ months })
        const payload = response?.data?.data || {}
        this.analyticsOverview = {
          summary: payload.summary || {},
          placement_trends: Array.isArray(payload.placement_trends) ? payload.placement_trends : [],
          application_funnel: payload.application_funnel || {},
          job_demand_by_skills: Array.isArray(payload.job_demand_by_skills)
            ? payload.job_demand_by_skills
            : [],
          meta: payload.meta || {}
        }
      } catch (error) {
        const message = error.response?.data?.error || 'Failed to load analytics overview'
        this.loadErrors.analytics = message
      } finally {
        this.loading.analytics = false
      }
    },
    async fetchAuditLog(limit = 20) {
      this.loading.activity = true
      this.loadErrors.activity = ''
      try {
        const response = await adminApi.getActivityLogs({ limit })
        const items = response.data?.data?.items || []
        this.auditLog = items.slice(0, 20).map((log) => {
          const status = String(log.status || 'info').toLowerCase()
          const rawTimestamp = log.timestamp || log.time || ''
          return {
            id: log.id || log.log_id || `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
            action: log.action || 'Activity',
            actor: log.actor || 'Admin',
            target: log.target || '-',
            time: this.formatDateLabel(rawTimestamp),
            timestamp: rawTimestamp,
            status: ['success', 'danger', 'warning', 'info'].includes(status) ? status : 'info'
          }
        })
      } catch (error) {
        const message = error.response?.data?.error || 'Failed to load activity log'
        this.loadErrors.activity = message
        this.toast_show(message, 'danger')
      } finally {
        this.loading.activity = false
      }
    },
    async fetchCompanies(queryText = this.coSearch) {
      this.loading.companies = true
      this.loadErrors.companies = ''
      try {
        const query = String(queryText || '').trim()
        const params = {
          page: this.coPage,
          limit: this.coLimit,
          sort_by: this.coSortBy,
          order: this.coOrder
        }
        const response = query
          ? await adminApi.searchCompanies(query, params)
          : await adminApi.getCompanies(params)
        const payload = response.data?.data || {}
        const items = payload.items || []
        this.coTotal = Number(payload.total || 0)
        this.coPage = Number(payload.page || this.coPage || 1)
        this.coPages = Number(payload.pages || 1)
        this.companies = items.map((company) => ({
          id: company.id || company.company_id,
          name: company.name || company.company_name || 'Unknown Company',
          domain: company.industry || company.website || '—',
          industry: company.industry || '—',
          hr: company.hr_contact_email || '—',
          status: this.normalizeCompanyStatus(company),
          initials: this.initialsFromText(company.name || company.company_name),
          color: this.colorFromKey(company.id || company.company_id),
          createdAtLabel: this.formatDateLabel(company.created_at)
        }))
      } catch (error) {
        const message = error.response?.data?.error || 'Failed to load companies'
        this.loadErrors.companies = message
        this.toast_show(message, 'danger')
      } finally {
        this.loading.companies = false
      }
    },
    async fetchStudents(queryText = this.stuSearch) {
      this.loading.students = true
      this.loadErrors.students = ''
      try {
        const query = String(queryText || '').trim()
        const params = {
          page: this.stuPage,
          limit: this.stuLimit,
          sort_by: this.stuSortBy,
          order: this.stuOrder
        }
        const response = query
          ? await adminApi.searchStudents(query, params)
          : await adminApi.getStudents(params)
        const payload = response.data?.data || {}
        const items = payload.items || []
        this.stuTotal = Number(payload.total || 0)
        this.stuPage = Number(payload.page || this.stuPage || 1)
        this.stuPages = Number(payload.pages || 1)
        this.students = items.map((student) => ({
          id: student.id || student.student_id,
          name: student.name || student.username || 'Unknown Student',
          email: student.email || '—',
          roll: student.roll_number || '-',
          branch: student.branch || 'OTHER',
          year: student.year || '-',
          cgpa: Number(student.cgpa || 0),
          status: this.normalizeStudentStatus(student),
          initials: this.initialsFromText(student.name || student.username),
          color: this.colorFromKey(student.id || student.student_id)
        }))
      } catch (error) {
        const message = error.response?.data?.error || 'Failed to load students'
        this.loadErrors.students = message
        this.toast_show(message, 'danger')
      } finally {
        this.loading.students = false
      }
    },
    async fetchDrives() {
      this.loading.drives = true
      this.loadErrors.drives = ''
      try {
        const response = await adminApi.getJobs({
          page: this.drivePage,
          limit: this.driveLimit,
          sort_by: this.driveSortBy,
          order: this.driveOrder
        })
        const payload = response.data?.data || {}
        const items = payload.items || []
        this.driveTotal = Number(payload.total || 0)
        this.drivePage = Number(payload.page || this.drivePage || 1)
        this.drivePages = Number(payload.pages || 1)
        this.allDrives = items.map((drive) => {
          const salaryLpa = Number(drive.salary_lpa)
          const companyId = drive.company_id
          return {
            id: drive.id || drive.drive_id,
            companyId,
            company: this.companyNameById[companyId] || 'Company',
            title: drive.title || drive.job_title || 'Placement Drive',
            salary: Number.isFinite(salaryLpa) ? `₹${salaryLpa.toFixed(1)} LPA` : '₹0 LPA',
            salaryLpa: Number.isFinite(salaryLpa) ? salaryLpa : 0,
            applicants: 0,
            deadline: this.formatDateShort(drive.application_deadline),
            status: this.normalizeDriveStatus(drive.status),
            initials: this.initialsFromText(this.companyNameById[companyId] || 'Drive'),
            color: this.colorFromKey(drive.id || drive.drive_id),
            minCgpa: drive.min_cgpa || '-',
            branches: Array.isArray(drive.eligible_branches) ? drive.eligible_branches.join(', ') : 'All',
            createdAtLabel: this.formatDateLabel(drive.created_at)
          }
        })
      } catch (error) {
        const message = error.response?.data?.error || 'Failed to load drives'
        this.loadErrors.drives = message
        this.toast_show(message, 'danger')
      } finally {
        this.loading.drives = false
      }
    },
    async fetchApplications() {
      this.loading.applications = true
      this.loadErrors.applications = ''
      try {
        const response = await adminApi.getApplications({ page: 1, limit: 200 })
        const items = response.data?.data?.items || []
        this.applications = items.map((application) => {
          const student = application.student || {}
          const job = application.job || {}
          const rawStatus = String(application.status || 'applied').toLowerCase()
          return {
            id: application.id || application.application_id,
            studentId: student.id || student.student_id || application.student_id,
            studentName: student.name || 'Student',
            studentRoll: student.roll_number || '-',
            driveId: job.id || job.drive_id || application.drive_id,
            driveTitle: job.title || job.job_title || 'Drive',
            companyName: this.companyNameById[job.company_id] || 'Company',
            appliedOn: this.formatDateLabel(application.application_date || application.created_at),
            rawStatus,
            status: this.normalizeApplicationStatus(rawStatus),
            initials: this.initialsFromText(student.name || 'Student'),
            color: this.colorFromKey(student.id || student.student_id || application.id)
          }
        })
      } catch (error) {
        const message = error.response?.data?.error || 'Failed to load applications'
        this.loadErrors.applications = message
        this.toast_show(message, 'danger')
      } finally {
        this.loading.applications = false
      }
    },
    setCoSortBy(sortBy) {
      if (!sortBy || this.coSortBy === sortBy) return
      this.coSortBy = sortBy
      this.coPage = 1
      this.fetchCompanies()
    },
    toggleCoOrder() {
      this.coOrder = this.coOrder === 'asc' ? 'desc' : 'asc'
      this.coPage = 1
      this.fetchCompanies()
    },
    setCoPage(page) {
      const target = Number(page)
      if (!Number.isFinite(target)) return
      const bounded = Math.min(Math.max(1, target), Math.max(1, this.coPages || 1))
      if (bounded === this.coPage) return
      this.coPage = bounded
      this.fetchCompanies()
    },
    prevCoPage() {
      this.setCoPage(this.coPage - 1)
    },
    nextCoPage() {
      this.setCoPage(this.coPage + 1)
    },
    setStuSortBy(sortBy) {
      if (!sortBy || this.stuSortBy === sortBy) return
      this.stuSortBy = sortBy
      this.stuPage = 1
      this.fetchStudents()
    },
    toggleStuOrder() {
      this.stuOrder = this.stuOrder === 'asc' ? 'desc' : 'asc'
      this.stuPage = 1
      this.fetchStudents()
    },
    setStuPage(page) {
      const target = Number(page)
      if (!Number.isFinite(target)) return
      const bounded = Math.min(Math.max(1, target), Math.max(1, this.stuPages || 1))
      if (bounded === this.stuPage) return
      this.stuPage = bounded
      this.fetchStudents()
    },
    prevStuPage() {
      this.setStuPage(this.stuPage - 1)
    },
    nextStuPage() {
      this.setStuPage(this.stuPage + 1)
    },
    setDriveSortBy(sortBy) {
      if (!sortBy || this.driveSortBy === sortBy) return
      this.driveSortBy = sortBy
      this.drivePage = 1
      this.fetchDrives()
    },
    toggleDriveOrder() {
      this.driveOrder = this.driveOrder === 'asc' ? 'desc' : 'asc'
      this.drivePage = 1
      this.fetchDrives()
    },
    setDrivePage(page) {
      const target = Number(page)
      if (!Number.isFinite(target)) return
      const bounded = Math.min(Math.max(1, target), Math.max(1, this.drivePages || 1))
      if (bounded === this.drivePage) return
      this.drivePage = bounded
      this.fetchDrives()
    },
    prevDrivePage() {
      this.setDrivePage(this.drivePage - 1)
    },
    nextDrivePage() {
      this.setDrivePage(this.drivePage + 1)
    },
    async handleSearch() {
      this.searchDropdownOpen = this.searchQuery.length > 0
      clearTimeout(this.searchDebounceTimer)

      if (!this.searchQuery.trim()) {
        this.searchResults = []
        return
      }

      this.searchDebounceTimer = setTimeout(async () => {
        try {
          const [companyResponse, studentResponse] = await Promise.all([
            adminApi.searchCompanies(this.searchQuery, { page: 1, limit: 3 }),
            adminApi.searchStudents(this.searchQuery, { page: 1, limit: 3 })
          ])

          const companyItems = (companyResponse.data?.data?.items || []).map((company) => ({
            id: `co-${company.id || company.company_id}`,
            name: company.name || company.company_name || 'Company',
            type: `Company · ${company.status || company.approval_status || 'pending'}`,
            color: this.colorFromKey(company.id || company.company_id),
            initials: this.initialsFromText(company.name || company.company_name),
            view: 'companies'
          }))

          const studentItems = (studentResponse.data?.data?.items || []).map((student) => ({
            id: `stu-${student.id || student.student_id}`,
            name: student.name || student.username || 'Student',
            type: `Student · ${student.roll_number || '-'}`,
            color: this.colorFromKey(student.id || student.student_id),
            initials: this.initialsFromText(student.name || student.username),
            view: 'students'
          }))

          this.searchResults = [...companyItems, ...studentItems].slice(0, 6)
        } catch (error) {
          this.searchResults = []
        }
      }, 220)
    },
    clearSearch() {
      this.searchQuery = ''
      this.searchResults = []
      this.searchDropdownOpen = false
      clearTimeout(this.searchDebounceTimer)
    },
    commitSearch() {
      if (this.searchResults.length) {
        this.activeView = this.searchResults[0].view
        this.searchDropdownOpen = false
      }
    },
    goToResult(result) {
      this.activeView = result.view
      if (result.view === 'companies') this.coSearch = result.name.split(' ')[0]
      if (result.view === 'students') this.stuSearch = result.name.split(' ')[0]
      this.clearSearch()
    },
    async approveItem(item) {
      if (item.entityType === 'company') {
        await this.changeCoStatus({ id: item.entityId, name: item.name }, 'approved')
      } else {
        await this.changeDriveStatus({ id: item.entityId, title: item.name }, 'approved')
      }
    },
    async rejectItem(item) {
      if (item.entityType === 'company') {
        await this.changeCoStatus({ id: item.entityId, name: item.name }, 'rejected')
      } else {
        await this.changeDriveStatus({ id: item.entityId, title: item.name }, 'rejected')
      }
    },
    async changeCoStatus(company, status) {
      const companyId = company?.id
      if (!companyId) {
        this.toast_show('Invalid company payload', 'danger')
        return
      }

      this.setPendingAction('company', companyId, true)
      try {
        const isRestore = status === 'approved' && company.status === 'blacklisted'
        if (status === 'approved') {
          if (isRestore) {
            await adminApi.activateCompany(companyId)
          } else {
            await adminApi.approveCompany(companyId)
          }
        } else if (status === 'rejected') {
          await adminApi.rejectCompany(companyId)
        } else if (status === 'blacklisted') {
          await adminApi.deactivateCompany(companyId)
        } else {
          this.toast_show('Unsupported company action', 'warning')
          return
        }

        await Promise.all([this.fetchCompanies(), this.fetchDashboard(), this.fetchAuditLog()])
        const message = status === 'approved'
          ? isRestore
            ? `${company.name} restored`
            : `${company.name} approved`
          : status === 'rejected'
            ? `${company.name} rejected`
            : `${company.name} blacklisted`
        this.toast_show(message, status === 'approved' ? 'success' : status === 'rejected' ? 'danger' : 'warning')
      } catch (error) {
        this.toast_show(error.response?.data?.error || 'Company action failed', 'danger')
      } finally {
        this.setPendingAction('company', companyId, false)
      }
    },
    async removeCompany(company) {
      const companyId = company?.id
      if (!companyId) {
        this.toast_show('Invalid company payload', 'danger')
        return
      }

      this.setPendingAction('company', companyId, true)
      try {
        const confirmed = window.confirm(`Remove ${company.name}? This will deactivate the profile.`)
        if (!confirmed) return

        await adminApi.deleteCompany(companyId)
        await Promise.all([this.fetchCompanies(), this.fetchDashboard(), this.fetchAuditLog()])
        this.toast_show(`${company.name} removed`, 'warning')
      } catch (error) {
        this.toast_show(error.response?.data?.error || 'Failed to remove company', 'danger')
      } finally {
        this.setPendingAction('company', companyId, false)
      }
    },
    async changeStuStatus(student, status) {
      const studentId = student?.id
      if (!studentId) {
        this.toast_show('Invalid student payload', 'danger')
        return
      }

      this.setPendingAction('student', studentId, true)
      try {
        if (status === 'blacklisted') {
          await adminApi.deactivateStudent(studentId)
        } else if (status === 'active') {
          await adminApi.activateStudent(studentId)
        } else {
          this.toast_show('Unsupported student action', 'warning')
          return
        }

        await Promise.all([this.fetchStudents(), this.fetchDashboard(), this.fetchAuditLog()])
        const becameActive = status === 'active'
        this.toast_show(becameActive ? `${student.name} restored` : `${student.name} blacklisted`, becameActive ? 'success' : 'warning')
      } catch (error) {
        this.toast_show(error.response?.data?.error || 'Student action failed', 'danger')
      } finally {
        this.setPendingAction('student', studentId, false)
      }
    },
    async changeDriveStatus(drive, status) {
      const driveId = drive?.id
      if (!driveId) {
        this.toast_show('Invalid drive payload', 'danger')
        return
      }

      this.setPendingAction('drive', driveId, true)
      try {
        if (status === 'approved') {
          await adminApi.approveJob(driveId)
        } else if (status === 'rejected') {
          await adminApi.rejectJob(driveId)
        } else {
          this.toast_show('Unsupported drive action', 'warning')
          return
        }
        await Promise.all([this.fetchDrives(), this.fetchDashboard(), this.fetchAuditLog()])
        this.toast_show(status === 'approved' ? `Drive approved — ${drive.title}` : `Drive rejected — ${drive.title}`, status === 'approved' ? 'success' : 'danger')
      } catch (error) {
        this.toast_show(error.response?.data?.error || 'Drive action failed', 'danger')
      } finally {
        this.setPendingAction('drive', driveId, false)
      }
    },
    async removeDrive(drive) {
      const driveId = drive?.id
      if (!driveId) {
        this.toast_show('Invalid drive payload', 'danger')
        return
      }

      this.setPendingAction('drive', driveId, true)
      try {
        const confirmed = window.confirm(`Remove ${drive.title}? This will close the drive.`)
        if (!confirmed) return

        await adminApi.deleteJob(driveId)
        await Promise.all([this.fetchDrives(), this.fetchDashboard(), this.fetchAuditLog()])
        this.toast_show(`Drive removed — ${drive.title}`, 'warning')
      } catch (error) {
        this.toast_show(error.response?.data?.error || 'Failed to remove drive', 'danger')
      } finally {
        this.setPendingAction('drive', driveId, false)
      }
    },
    async changeApplicationStatus(application, nextStatus) {
      try {
        const applicationId = application?.id
        const targetStatus = String(nextStatus || '').trim().toLowerCase()

        if (!applicationId || !targetStatus) {
          this.toast_show('Invalid application payload', 'danger')
          return
        }

        if (targetStatus === application.rawStatus) return

        this.setPendingAction('application', applicationId, true)

        await adminApi.updateApplicationStatus(applicationId, { status: targetStatus })
        await Promise.all([this.fetchApplications(), this.fetchDashboard(), this.fetchAuditLog()])

        if (this.selectedStudent?.id) {
          this.selectedStudent = this.studentsWithMetrics.find((student) => student.id === this.selectedStudent.id) || null
        }

        this.toast_show(`Application updated to ${targetStatus}`, 'success')
      } catch (error) {
        this.toast_show(error.response?.data?.error || 'Failed to update application', 'danger')
      } finally {
        if (application?.id) this.setPendingAction('application', application.id, false)
      }
    },
    showStudentApps(student) {
      this.selectedStudent = student
    },
    doExport(scope) {
      let rows = []

      if (scope === 'companies') {
        rows = ['Company,Domain,Status,Drives,Applicants', ...this.companiesWithMetrics.map((company) => `${company.name},${company.domain},${company.status},${company.drives},${company.applicants}`)]
      } else if (scope === 'students') {
        rows = ['Name,Roll,Branch,CGPA,Applications,Status', ...this.studentsWithMetrics.map((student) => `${student.name},${student.roll},${student.branch},${student.cgpa},${student.applications},${student.status}`)]
      } else if (scope === 'drives') {
        rows = ['Title,Company,Salary,Status,Deadline', ...this.filteredDrives.map((drive) => `${drive.title},${drive.company},${drive.salary},${drive.status},${drive.deadline}`)]
      } else if (scope === 'analytics') {
        rows = ['Company,Drives,Offers,AvgPackage,Highest', ...this.topCompanies.map((company) => `${company.name},${company.drives},${company.offers},${company.avgPkg},${company.highest}`)]
      } else {
        rows = ['Action,Actor,Target,Time', ...this.auditLog.map((log) => `${log.action},${log.actor},${log.target},${log.time}`)]
      }

      const blob = new Blob([rows.join('\n')], { type: 'text/csv' })
      const link = Object.assign(document.createElement('a'), {
        href: URL.createObjectURL(blob),
        download: `recruitify-${scope}-${Date.now()}.csv`
      })
      link.click()
      URL.revokeObjectURL(link.href)
      this.toast_show(`${scope} data downloaded as CSV`, 'success')
    },
    handleLogout() {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('user_id')
      this.$router.push('/login')
    },
    toast_show(message, type = 'success') {
      const icons = { success: 'OK', danger: 'X', warning: '!', info: 'i' }
      this.toast = { show: true, message, type, icon: icons[type] || 'i' }
      clearTimeout(this._toastTimer)
      this._toastTimer = setTimeout(() => {
        this.toast.show = false
      }, 3500)
    }
  }
}
</script>