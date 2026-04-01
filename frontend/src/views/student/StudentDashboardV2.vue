<template>
  <div class="rq-app" :class="{ 'is-collapsed': sidebarCollapsed }">
    <StudentSidebar
      :sidebar-collapsed="sidebarCollapsed"
      :active-view="activeView"
      :nav-items="navItems"
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

      <main class="rq-page" role="main">
        <StudentDashboardHome
          v-if="activeView === 'dashboard'"
          :student-first-name="student.firstName"
          :time-of-day="timeOfDay"
          :today-date="todayDate"
          :live-open-count="liveOpenCount"
          :stat-cards="statCards"
          :drives="filteredDrives"
          :applications="filteredApplications"
        />

        <StudentSectionPlaceholder
          v-else-if="activeView === 'drives'"
          title="Placement Drives"
          description="Scaffold ready. Next step will connect this view to live drives search and apply endpoints."
        />

        <StudentSectionPlaceholder
          v-else-if="activeView === 'applications'"
          title="My Applications"
          description="Scaffold ready. Next step will wire application timeline, filtering, and export actions."
        />

        <StudentSectionPlaceholder
          v-else-if="activeView === 'notifications'"
          title="Notifications"
          description="Scaffold ready. Next step will connect read and mark-all actions to backend notifications APIs."
        />

        <StudentSectionPlaceholder
          v-else-if="activeView === 'profile'"
          title="My Profile"
          description="Scaffold ready. Next step will connect profile update and resume actions to student profile APIs."
        />

        <StudentSectionPlaceholder
          v-else
          title="Placement History"
          description="Scaffold ready. Next step will connect offer and placement outcomes with downloadable artifacts."
        />
      </main>
    </div>
  </div>
</template>

<script>
import StudentDashboardHome from '../../components/student/v2/StudentDashboardHome.vue'
import StudentSectionPlaceholder from '../../components/student/v2/StudentSectionPlaceholder.vue'
import StudentSidebar from '../../components/student/v2/StudentSidebar.vue'
import StudentTopbar from '../../components/student/v2/StudentTopbar.vue'
import './StudentDashboardV2.css'

export default {
  name: 'StudentDashboardV2',
  components: {
    StudentSidebar,
    StudentTopbar,
    StudentDashboardHome,
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
        year: 3
      },
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
      statCards: [
        { id: 'applied', label: 'Applied', value: '6', sub: 'Applications submitted' },
        { id: 'shortlisted', label: 'Shortlisted', value: '2', sub: 'Moved to next stage' },
        { id: 'interview', label: 'Interviewing', value: '1', sub: 'Interviews in progress' },
        { id: 'offer', label: 'Offers', value: '1', sub: 'Offers received' }
      ],
      drives: [
        { id: 1, role: 'Software Engineer Intern', company: 'Google', salary: '12 LPA', deadline: 'Apr 15' },
        { id: 2, role: 'Product Analyst', company: 'Microsoft', salary: '18 LPA', deadline: 'Apr 20' },
        { id: 3, role: 'Cloud Support Engineer', company: 'Amazon', salary: '22 LPA', deadline: 'Apr 12' }
      ],
      applications: [
        { id: 1, role: 'Software Engineer Intern', company: 'Google', status: 'interview', statusLabel: 'Interview' },
        { id: 2, role: 'Product Analyst', company: 'Microsoft', status: 'offer', statusLabel: 'Offer' },
        { id: 3, role: 'Data Engineer', company: 'Infosys', status: 'shortlisted', statusLabel: 'Shortlisted' }
      ],
      notifications: [
        { id: 1, title: 'Interview scheduled', read: false },
        { id: 2, title: 'Offer received', read: false },
        { id: 3, title: 'New drive posted', read: true }
      ]
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
    liveOpenCount() {
      return this.filteredDrives.length
    },
    unreadCount() {
      return this.notifications.filter((item) => !item.read).length
    },
    filteredDrives() {
      const query = this.searchQuery.trim().toLowerCase()
      if (!query) {
        return this.drives
      }

      return this.drives.filter(
        (item) =>
          item.role.toLowerCase().includes(query) ||
          item.company.toLowerCase().includes(query)
      )
    },
    filteredApplications() {
      const query = this.searchQuery.trim().toLowerCase()
      if (!query) {
        return this.applications
      }

      return this.applications.filter(
        (item) =>
          item.role.toLowerCase().includes(query) ||
          item.company.toLowerCase().includes(query)
      )
    }
  },
  methods: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    navigate(viewId) {
      this.activeView = viewId
    }
  }
}
</script>
