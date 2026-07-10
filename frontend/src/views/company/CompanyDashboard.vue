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
            @open-view="activeView = $event"
          />

          <DrivesView
            v-if="activeView === 'drives'"
            :drive-filters="driveFilters"
            :drive-filter="driveFilter"
            :filtered-drives="filteredDrives"
            :company-status="companyProfile.status"
            @update:drive-filter="driveFilter = $event"
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
            :is-scoring="isScoringResume"
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
            @shortlist="shortlistApp"
            @reject="rejectApp"
            @advance="advanceStage"
            @update-interview-result="openInterviewResultModal"
            @screen-application="screenApplicationResume"
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
            :applications="allApplications"
            :is-export-busy="isCompanyExportBusy('applications')"
            :export-label="companyExportButtonLabel('applications')"
            @export-analytics="doExport('applications')"
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

    <Transition name="rq-modal">
      <div
        v-if="showScreeningModal"
        class="rq-modal-overlay"
        @click.self="closeScreeningModal"
      >
        <div class="rq-modal rq-modal-lg">
          <div class="rq-modal-hd">
            <div>
              <h3 class="rq-card-title">ATS Keyword Screening</h3>
              <p class="rq-sm rq-dim">
                {{ screeningResult?.job?.title || 'Application' }}
              </p>
            </div>
            <button class="rq-modal-close" type="button" @click="closeScreeningModal">×</button>
          </div>

          <div class="rq-modal-body">
            <p v-if="screeningError" class="rq-state rq-state-error">{{ screeningError }}</p>

            <template v-else-if="screeningResult">
              <div class="rq-app-stats-row">
                <span class="rq-app-stat-item">
                  <span class="rq-app-stat-n" style="color:var(--blue)">{{ screeningResult.analysis?.score || 0 }}%</span>
                  Match Score
                </span>
                <span class="rq-app-stat-sep">·</span>
                <span class="rq-app-stat-item">
                  <span class="rq-app-stat-n" style="color:var(--green)">{{ screeningResult.analysis?.matched_count || 0 }}</span>
                  Matched
                </span>
                <span class="rq-app-stat-sep">·</span>
                <span class="rq-app-stat-item">
                  <span class="rq-app-stat-n" style="color:var(--red)">{{ (screeningResult.analysis?.missing_keywords || []).length }}</span>
                  Missing
                </span>
              </div>

              <div>
                <p class="rq-sm rq-dim"><strong>Recommendation:</strong> {{ screeningResult.analysis?.recommendation || 'n/a' }}</p>
              </div>

              <div>
                <p class="rq-sm" style="font-weight:700; margin-bottom:6px;">Matched Keywords</p>
                <div class="rq-drive-chips">
                  <span
                    v-for="keyword in screeningResult.analysis?.matched_keywords || []"
                    :key="`hit-${keyword}`"
                    class="rq-status-pill pill-approved"
                  >
                    {{ keyword }}
                  </span>
                  <span
                    v-if="!(screeningResult.analysis?.matched_keywords || []).length"
                    class="rq-sm rq-dim"
                  >
                    No matched keywords found.
                  </span>
                </div>
              </div>

              <div>
                <p class="rq-sm" style="font-weight:700; margin-bottom:6px;">Missing Keywords</p>
                <div class="rq-drive-chips">
                  <span
                    v-for="keyword in screeningResult.analysis?.missing_keywords || []"
                    :key="`miss-${keyword}`"
                    class="rq-status-pill pill-rejected"
                  >
                    {{ keyword }}
                  </span>
                  <span
                    v-if="!(screeningResult.analysis?.missing_keywords || []).length"
                    class="rq-sm rq-dim"
                  >
                    No missing keywords. Candidate fully matches current keyword set.
                  </span>
                </div>
              </div>
            </template>
          </div>

          <div class="rq-modal-ft">
            <button class="rq-ghost" type="button" @click="closeScreeningModal">Close</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="rq-modal">
      <div
        v-if="showInterviewModal"
        class="rq-modal-overlay"
        @click.self="closeInterviewModal"
      >
        <div class="rq-modal">
          <div class="rq-modal-hd">
            <div>
              <h3 class="rq-card-title">Schedule Interview</h3>
              <p class="rq-sm rq-dim">
                {{ interviewTargetApp?.student || 'Candidate' }} · {{ interviewTargetApp?.drive || 'Drive' }}
              </p>
            </div>
            <button class="rq-modal-close" type="button" @click="closeInterviewModal">×</button>
          </div>

          <div class="rq-modal-body">
            <p v-if="interviewFormError" class="rq-sm" style="color:var(--red); font-weight:700;">{{ interviewFormError }}</p>

            <div class="rq-form-group">
              <label class="rq-form-label">Interview Date and Time</label>
              <input
                v-model="interviewForm.interview_date"
                type="datetime-local"
                class="rq-form-input"
              />
            </div>

            <div class="rq-form-group">
              <label class="rq-form-label">Interview Mode</label>
              <select v-model="interviewForm.interview_mode" class="rq-form-input rq-select-field">
                <option value="online">Online</option>
                <option value="offline">Offline</option>
              </select>
            </div>

            <div class="rq-form-group">
              <label class="rq-form-label">Interviewer Name</label>
              <input
                v-model="interviewForm.interviewer_name"
                type="text"
                class="rq-form-input"
                placeholder="Panel or interviewer"
              />
            </div>

            <div v-if="interviewForm.interview_mode === 'online'" class="rq-form-group">
              <label class="rq-form-label">Interview Link</label>
              <input
                v-model="interviewForm.interview_link"
                type="url"
                class="rq-form-input"
                placeholder="https://meet.example.com/session"
              />
            </div>

            <div v-else class="rq-form-group">
              <label class="rq-form-label">Interview Location</label>
              <input
                v-model="interviewForm.interview_location"
                type="text"
                class="rq-form-input"
                placeholder="Block, room, office address"
              />
            </div>
          </div>

          <div class="rq-modal-ft">
            <button class="rq-ghost" type="button" @click="closeInterviewModal">Cancel</button>
            <button class="rq-btn-purple" type="button" :disabled="isSubmittingInterview" @click="submitInterviewModal">
              {{ isSubmittingInterview ? 'Scheduling...' : 'Schedule Interview' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="rq-modal">
      <div
        v-if="showOfferModal"
        class="rq-modal-overlay"
        @click.self="closeOfferModal"
      >
        <div class="rq-modal">
          <div class="rq-modal-hd">
            <div>
              <h3 class="rq-card-title">Release Offer</h3>
              <p class="rq-sm rq-dim">
                {{ offerTargetApp?.student || 'Candidate' }} · {{ offerTargetApp?.drive || 'Drive' }}
              </p>
            </div>
            <button class="rq-modal-close" type="button" @click="closeOfferModal">×</button>
          </div>

          <div class="rq-modal-body">
            <p v-if="offerFormError" class="rq-sm" style="color:var(--red); font-weight:700;">{{ offerFormError }}</p>

            <div class="rq-form-group">
              <label class="rq-form-label">Position</label>
              <input
                v-model="offerForm.position"
                type="text"
                class="rq-form-input"
                placeholder="Offered role title"
              />
            </div>

            <div class="rq-form-group">
              <label class="rq-form-label">Salary (INR per annum)</label>
              <input
                v-model="offerForm.salary"
                type="number"
                min="1"
                step="1"
                class="rq-form-input"
                placeholder="1450000"
              />
            </div>

            <div class="rq-form-group">
              <label class="rq-form-label">Joining Date</label>
              <input
                v-model="offerForm.joining_date"
                type="date"
                class="rq-form-input"
              />
            </div>
          </div>

          <div class="rq-modal-ft">
            <button class="rq-ghost" type="button" @click="closeOfferModal">Cancel</button>
            <button class="rq-btn-ok" type="button" :disabled="isSubmittingOffer" @click="submitOfferModal">
              {{ isSubmittingOffer ? 'Releasing...' : 'Release Offer' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="rq-modal">
      <div
        v-if="showInterviewResultModal"
        class="rq-modal-overlay"
        @click.self="closeInterviewResultModal"
      >
        <div class="rq-modal">
          <div class="rq-modal-hd">
            <div>
              <h3 class="rq-card-title">Update Interview Result</h3>
              <p class="rq-sm rq-dim">
                {{ interviewResultTargetApp?.student || 'Candidate' }} · {{ interviewResultTargetApp?.drive || 'Drive' }}
              </p>
            </div>
            <button class="rq-modal-close" type="button" @click="closeInterviewResultModal">×</button>
          </div>

          <div class="rq-modal-body">
            <p v-if="interviewResultFormError" class="rq-sm" style="color:var(--red); font-weight:700;">{{ interviewResultFormError }}</p>
            <p v-if="isLoadingInterviewRecord" class="rq-sm rq-dim">Loading latest interview details...</p>

            <template v-else>
              <div class="rq-form-group">
                <label class="rq-form-label">Interview Outcome</label>
                <select v-model="interviewResultForm.result" class="rq-form-input rq-select-field" :disabled="!interviewResultInterviewId">
                  <option value="">Select outcome</option>
                  <option value="pass">Pass</option>
                  <option value="fail">Fail</option>
                </select>
              </div>

              <div class="rq-form-group">
                <label class="rq-form-label">Feedback (Optional)</label>
                <textarea
                  v-model="interviewResultForm.feedback"
                  class="rq-form-input rq-form-textarea"
                  rows="3"
                  placeholder="Share panel feedback for this candidate"
                  :disabled="!interviewResultInterviewId"
                ></textarea>
              </div>
            </template>
          </div>

          <div class="rq-modal-ft">
            <button class="rq-ghost" type="button" @click="closeInterviewResultModal">Cancel</button>
            <button
              class="rq-btn-purple"
              type="button"
              :disabled="isSubmittingInterviewResult || isLoadingInterviewRecord || !interviewResultInterviewId"
              @click="submitInterviewResultModal"
            >
              {{ isSubmittingInterviewResult ? 'Saving...' : 'Save Result' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="rq-modal">
      <div
        v-if="showRejectModal"
        class="rq-modal-overlay"
        @click.self="closeRejectModal"
      >
        <div class="rq-modal">
          <div class="rq-modal-hd">
            <div>
              <h3 class="rq-card-title">Reject Application</h3>
              <p class="rq-sm rq-dim">
                {{ rejectTargetApp?.student || 'Candidate' }} · {{ rejectTargetApp?.drive || 'Drive' }}
              </p>
            </div>
            <button class="rq-modal-close" type="button" @click="closeRejectModal">×</button>
          </div>

          <div class="rq-modal-body">
            <p v-if="rejectFormError" class="rq-sm" style="color:var(--red); font-weight:700;">{{ rejectFormError }}</p>

            <div class="rq-form-group">
              <label class="rq-form-label">Rejection Reason</label>
              <textarea
                v-model="rejectForm.rejection_reason"
                class="rq-form-input rq-form-textarea"
                rows="3"
                placeholder="Share why the profile could not be selected"
              ></textarea>
            </div>

            <div class="rq-form-group">
              <label class="rq-form-label">Internal Notes (Optional)</label>
              <textarea
                v-model="rejectForm.notes"
                class="rq-form-input rq-form-textarea"
                rows="3"
                placeholder="Additional panel notes"
              ></textarea>
            </div>
          </div>

          <div class="rq-modal-ft">
            <button class="rq-ghost" type="button" @click="closeRejectModal">Cancel</button>
            <button class="rq-btn-no" type="button" :disabled="isSubmittingReject" @click="submitRejectModal">
              {{ isSubmittingReject ? 'Rejecting...' : 'Reject Candidate' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="rq-modal">
      <div
        v-if="showBulkShortlistModal"
        class="rq-modal-overlay"
        @click.self="closeBulkShortlistModal"
      >
        <div class="rq-modal">
          <div class="rq-modal-hd">
            <div>
              <h3 class="rq-card-title">Bulk Shortlist</h3>
              <p class="rq-sm rq-dim">Selected applications: {{ selectedApps.length }}</p>
            </div>
            <button class="rq-modal-close" type="button" @click="closeBulkShortlistModal">×</button>
          </div>

          <div class="rq-modal-body">
            <p v-if="bulkShortlistFormError" class="rq-sm" style="color:var(--red); font-weight:700;">{{ bulkShortlistFormError }}</p>

            <div class="rq-form-group">
              <label class="rq-form-label">Feedback Note (Optional)</label>
              <textarea
                v-model="bulkShortlistForm.notes"
                class="rq-form-input rq-form-textarea"
                rows="3"
                placeholder="Shared note for shortlisted candidates"
              ></textarea>
            </div>
          </div>

          <div class="rq-modal-ft">
            <button class="rq-ghost" type="button" @click="closeBulkShortlistModal">Cancel</button>
            <button class="rq-btn-ok" type="button" :disabled="isSubmittingBulkShortlist" @click="submitBulkShortlistModal">
              {{ isSubmittingBulkShortlist ? 'Shortlisting...' : 'Shortlist Selected' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="rq-modal">
      <div
        v-if="showBulkRejectModal"
        class="rq-modal-overlay"
        @click.self="closeBulkRejectModal"
      >
        <div class="rq-modal">
          <div class="rq-modal-hd">
            <div>
              <h3 class="rq-card-title">Bulk Reject</h3>
              <p class="rq-sm rq-dim">Selected applications: {{ selectedApps.length }}</p>
            </div>
            <button class="rq-modal-close" type="button" @click="closeBulkRejectModal">×</button>
          </div>

          <div class="rq-modal-body">
            <p v-if="bulkRejectFormError" class="rq-sm" style="color:var(--red); font-weight:700;">{{ bulkRejectFormError }}</p>

            <div class="rq-form-group">
              <label class="rq-form-label">Rejection Reason</label>
              <textarea
                v-model="bulkRejectForm.rejection_reason"
                class="rq-form-input rq-form-textarea"
                rows="3"
                placeholder="Shared rejection reason for selected candidates"
              ></textarea>
            </div>

            <div class="rq-form-group">
              <label class="rq-form-label">Internal Notes (Optional)</label>
              <textarea
                v-model="bulkRejectForm.notes"
                class="rq-form-input rq-form-textarea"
                rows="3"
                placeholder="Additional panel notes"
              ></textarea>
            </div>
          </div>

          <div class="rq-modal-ft">
            <button class="rq-ghost" type="button" @click="closeBulkRejectModal">Cancel</button>
            <button class="rq-btn-no" type="button" :disabled="isSubmittingBulkReject" @click="submitBulkRejectModal">
              {{ isSubmittingBulkReject ? 'Rejecting...' : 'Reject Selected' }}
            </button>
          </div>
        </div>
      </div>
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
import { companyApi, parseApiError } from '../../services/api'
import { parseBooleanFlag, parseServerDate } from '../../utils/dateTime'
import { useAuthStore } from '../../store/auth'
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
const DEFAULT_OFFER_SALARY = 600000
const EXPORT_POLL_INTERVAL_MS = 2500
const EXPORT_POLL_MAX_ATTEMPTS = 48
const COMPANY_EXPORT_SCOPE_BY_VIEW = Object.freeze({
  drives: 'drives',
  applications: 'applications',
  analytics: 'applications'
})

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
    eligible_years: [],
    required_skills: [],
    experience_required: '',
    description: ''
  }
}

function createDefaultInterviewForm() {
  return {
    interview_date: '',
    interview_mode: 'online',
    interviewer_name: '',
    interview_link: '',
    interview_location: ''
  }
}

function createDefaultInterviewResultForm() {
  return {
    result: '',
    feedback: ''
  }
}

function createDefaultOfferForm() {
  return {
    position: '',
    salary: '',
    joining_date: ''
  }
}

function createDefaultRejectForm() {
  return {
    rejection_reason: '',
    notes: ''
  }
}

function createDefaultBulkShortlistForm() {
  return {
    notes: ''
  }
}

function createDefaultBulkRejectForm() {
  return {
    rejection_reason: '',
    notes: ''
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
      isScoringResume: {},
      showScreeningModal: false,
      screeningResult: null,
      screeningError: '',

      newDrive: createDefaultNewDrive(),

      showInterviewModal: false,
      showInterviewResultModal: false,
      showOfferModal: false,
      showRejectModal: false,
      interviewTargetApp: null,
      interviewResultTargetApp: null,
      interviewResultInterviewId: null,
      offerTargetApp: null,
      rejectTargetApp: null,
      interviewForm: createDefaultInterviewForm(),
      interviewResultForm: createDefaultInterviewResultForm(),
      offerForm: createDefaultOfferForm(),
      rejectForm: createDefaultRejectForm(),
      interviewFormError: '',
      interviewResultFormError: '',
      offerFormError: '',
      rejectFormError: '',
      isSubmittingInterview: false,
      isLoadingInterviewRecord: false,
      isSubmittingInterviewResult: false,
      isSubmittingOffer: false,
      isSubmittingReject: false,

      showBulkShortlistModal: false,
      showBulkRejectModal: false,
      bulkShortlistForm: createDefaultBulkShortlistForm(),
      bulkRejectForm: createDefaultBulkRejectForm(),
      bulkShortlistFormError: '',
      bulkRejectFormError: '',
      isSubmittingBulkShortlist: false,
      isSubmittingBulkReject: false,

      toast: { show: false, message: '', icon: '', type: 'success' },
      toastTimerId: null,
      companyExportJobs: {},
      companyExportTimers: {}
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
    },
    activeView(nextValue) {
      this.clearCompanyExportPollsForView(nextValue)
    }
  },
  created() {
    this.bootstrapDashboard()
  },
  beforeUnmount() {
    this.clearCompanyExportPollsForView(null, true)

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
    closeScreeningModal() {
      this.showScreeningModal = false
      this.screeningError = ''
      this.screeningResult = null
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
      useAuthStore().logout()
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

      const parsed = parseServerDate(rawValue)
      if (!parsed) {
        return String(rawValue)
      }

      return parsed.toISOString().slice(0, 10)
    },
    formatDeadline(rawValue) {
      if (!rawValue) {
        return '-'
      }

      const parsed = parseServerDate(rawValue)
      if (!parsed) {
        return String(rawValue)
      }

      return parsed.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric'
      })
    },
    formatEligibleYears(rawYears) {
      const years = Array.isArray(rawYears)
        ? rawYears
            .map((year) => Number(year))
            .filter((year) => year >= 1 && year <= 4)
        : []

      const normalized = [...new Set(years)].sort((left, right) => left - right)
      if (!normalized.length) {
        return 'All Years'
      }

      const suffixByYear = { 1: 'st', 2: 'nd', 3: 'rd', 4: 'th' }
      return normalized.map((year) => `${year}${suffixByYear[year] || 'th'} Year`).join(', ')
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
    formatRelativeTime(rawValue) {
      if (!rawValue) {
        return 'recently'
      }

      const parsed = parseServerDate(rawValue)
      if (!parsed) {
        return 'recently'
      }

      const deltaMs = Date.now() - parsed.getTime()
      if (deltaMs < 0) {
        return parsed.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
      }

      const deltaMinutes = Math.floor(deltaMs / 60000)
      if (deltaMinutes < 1) {
        return 'Just now'
      }

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
        hasOffer: Boolean(item.has_offer || item.placement_offer),
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
      const years = this.formatEligibleYears(item.eligible_years || item.eligibleYears)
      const requiredSkills = this.formatRequiredSkills(item.required_skills || item.requiredSkills)

      return {
        id,
        title,
        role: item.job_title || title,
        type: item.interview_mode ? String(item.interview_mode).toUpperCase() : 'Full-time',
        salary,
        applicants: Number(item.applications_count || 0),
        deadline: this.formatDeadline(item.deadline || item.application_deadline),
        deadlineRaw: item.deadline || item.application_deadline || null,
        status,
        initials: this.initialsFor(this.companyProfile.name),
        avatarColor: this.companyProfile.avatarColor,
        minCgpa: Number(item.min_cgpa || 0),
        branches,
        years,
        requiredSkills,
        stages: this.buildDriveStages(id)
      }
    },
    normalizeNotification(item) {
      const timestamp = item.created_at || item.sent_at || item.timestamp || item.time || ''
      return {
        id: Number(item.notification_id || item.id || 0),
        title: item.title || 'Notification',
        sub: item.message || '-',
        time: this.formatRelativeTime(timestamp),
        type: this.normalizeNotificationType(item),
        read: parseBooleanFlag(item.is_read ?? item.read)
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
      if (Object.prototype.hasOwnProperty.call(updatedPayload, 'has_offer')) {
        target.hasOffer = Boolean(updatedPayload.has_offer)
      }
      if (Object.prototype.hasOwnProperty.call(updatedPayload, 'hasOffer')) {
        target.hasOffer = Boolean(updatedPayload.hasOffer)
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

      const eligibleYears = Array.isArray(newDrive.eligible_years)
        ? [...new Set(newDrive.eligible_years.map((year) => Number(year)).filter((year) => year >= 1 && year <= 4))]
        : []

      if (!eligibleYears.length) {
        return 'Select at least one eligible year.'
      }

      const experienceRequired = String(newDrive.experience_required || '').trim()
      if (!experienceRequired) {
        return 'Please select experience required.'
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
      const nonBlockingSections = []
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
        nonBlockingSections.push('applications')
        nonBlockingErrors.push(this.handleApiError(applicationsResult.reason, 'Failed to load applications.'))
        shouldDeriveSummary = true
      }

      if (drivesResult.status === 'fulfilled') {
        const items = drivesResult.value?.data?.data?.items || []
        this.myDrives = Array.isArray(items) ? items.map((item) => this.normalizeDrive(item)) : []
        this.refreshDriveStats()
        loadedState.drives = true
      } else {
        nonBlockingSections.push('drives')
        nonBlockingErrors.push(this.handleApiError(drivesResult.reason, 'Failed to load drives.'))
        shouldDeriveSummary = true
      }

      if (notificationsResult.status === 'fulfilled') {
        const items = notificationsResult.value?.data?.data?.items || []
        this.notifications = Array.isArray(items) ? items.map((item) => this.normalizeNotification(item)) : []
        this.notificationsError = ''
      } else {
        nonBlockingSections.push('notifications')
        const message = this.handleApiError(notificationsResult.reason, 'Failed to load notifications.')
        this.notificationsError = message
        nonBlockingErrors.push(message)
        shouldDeriveSummary = true
      }

      if (dashboardResult.status === 'fulfilled') {
        const dashboardData = dashboardResult.value || {}
        this.dashboardSummary = this.buildSummaryFromLoadedData(dashboardData.summary || null)
      } else {
        nonBlockingSections.push('summary')
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
        const failedSections = new Set(nonBlockingSections)
        const suppressEmptyStateWarning =
          failedSections.size === 2 &&
          failedSections.has('applications') &&
          failedSections.has('summary') &&
          this.myDrives.length === 0 &&
          this.allApplications.length === 0

        const suppressApplicationsOnlyEmptyWarning =
          failedSections.size === 1 &&
          failedSections.has('applications') &&
          this.myDrives.length === 0 &&
          this.allApplications.length === 0 &&
          Number(this.dashboardSummary?.applications_received || 0) === 0

        if (suppressEmptyStateWarning || suppressApplicationsOnlyEmptyWarning) {
          this.isLoading = false
          return
        }

        const unavailableSections = [...new Set(nonBlockingSections)].join(', ')
        const warningMessage = unavailableSections
          ? `Some dashboard sections are temporarily unavailable (${unavailableSections}). Showing available data.`
          : 'Some dashboard sections are temporarily unavailable. Showing available data.'
        this.toast_show(warningMessage, 'warning')
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
    toDateTimeLocalValue(rawValue) {
      const parsed = rawValue instanceof Date ? rawValue : new Date(rawValue)
      if (Number.isNaN(parsed.getTime())) {
        return ''
      }

      const timezoneOffsetMs = parsed.getTimezoneOffset() * 60000
      return new Date(parsed.getTime() - timezoneOffsetMs).toISOString().slice(0, 16)
    },
    toDateValue(rawValue) {
      const parsed = rawValue instanceof Date ? rawValue : new Date(rawValue)
      if (Number.isNaN(parsed.getTime())) {
        return ''
      }

      const timezoneOffsetMs = parsed.getTimezoneOffset() * 60000
      return new Date(parsed.getTime() - timezoneOffsetMs).toISOString().slice(0, 10)
    },
    findDriveForApplication(application) {
      return this.myDrives.find((drive) => Number(drive.id) === Number(application?.driveId)) || null
    },
    resolveOfferSalary(application) {
      const drive = this.findDriveForApplication(application)
      const lpaCandidates = [
        Number(drive?.salaryLpa),
        this.parseSalaryLpa(drive?.salary)
      ]

      for (const candidate of lpaCandidates) {
        const value = Number(candidate)
        if (Number.isFinite(value) && value > 0) {
          return Math.round(value * 100000)
        }
      }

      return DEFAULT_OFFER_SALARY
    },
    openInterviewModal(application) {
      if (!this.canManageApplications) {
        this.toast_show('Application actions are enabled only after admin approval.', 'warning')
        return
      }

      if (!application?.id) {
        return
      }

      const interviewDate = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000)
      interviewDate.setHours(10, 0, 0, 0)

      this.interviewTargetApp = application
      this.interviewForm = {
        ...createDefaultInterviewForm(),
        interview_date: this.toDateTimeLocalValue(interviewDate),
        interview_mode: 'online',
        interviewer_name: this.normalizeInput(this.companyProfile.hrName)
      }
      this.interviewFormError = ''
      this.showInterviewModal = true
    },
    closeInterviewModal() {
      this.showInterviewModal = false
      this.interviewTargetApp = null
      this.interviewForm = createDefaultInterviewForm()
      this.interviewFormError = ''
      this.isSubmittingInterview = false
    },
    async openInterviewResultModal(application) {
      if (!this.canManageApplications) {
        this.toast_show('Application actions are enabled only after admin approval.', 'warning')
        return
      }

      if (!application?.id) {
        return
      }

      this.showInterviewResultModal = true
      this.interviewResultTargetApp = application
      this.interviewResultInterviewId = null
      this.interviewResultForm = createDefaultInterviewResultForm()
      this.interviewResultFormError = ''
      this.isLoadingInterviewRecord = true

      try {
        const params = {
          page: 1,
          limit: 100
        }

        if (application.driveId) {
          params.drive_id = application.driveId
        }

        const response = await companyApi.getInterviews(params)
        const items = Array.isArray(response?.data?.data?.items) ? response.data.data.items : []
        const targetInterview = items.find((item) => Number(item.application_id) === Number(application.id))

        if (!targetInterview) {
          this.interviewResultFormError = 'No scheduled interview found for this application. Schedule an interview first.'
          this.toast_show(this.interviewResultFormError, 'warning')
          return
        }

        this.interviewResultInterviewId = Number(targetInterview.interview_id || targetInterview.id || 0)

        const existingResult = String(targetInterview.result || '').trim().toLowerCase()
        this.interviewResultForm = {
          ...createDefaultInterviewResultForm(),
          result: ['pass', 'fail'].includes(existingResult) ? existingResult : '',
          feedback: this.normalizeInput(targetInterview.feedback)
        }
      } catch (error) {
        this.interviewResultFormError = this.handleApiError(error, 'Unable to load interview details.')
        this.toast_show(this.interviewResultFormError, 'danger')
      } finally {
        this.isLoadingInterviewRecord = false
      }
    },
    closeInterviewResultModal() {
      this.showInterviewResultModal = false
      this.interviewResultTargetApp = null
      this.interviewResultInterviewId = null
      this.interviewResultForm = createDefaultInterviewResultForm()
      this.interviewResultFormError = ''
      this.isLoadingInterviewRecord = false
      this.isSubmittingInterviewResult = false
    },
    validateInterviewResultForm() {
      if (!this.interviewResultTargetApp?.id) {
        return 'Select an application before updating interview result.'
      }

      if (!this.interviewResultInterviewId) {
        return 'Interview record is unavailable for this application.'
      }

      const result = String(this.interviewResultForm.result || '').trim().toLowerCase()
      if (!['pass', 'fail'].includes(result)) {
        return 'Select interview outcome.'
      }

      return ''
    },
    buildInterviewResultPayload(formValues = null) {
      const formPayload = formValues || this.interviewResultForm
      const payload = {
        result: String(formPayload.result || '').trim().toLowerCase()
      }

      const feedback = this.normalizeInput(formPayload.feedback)
      if (feedback) {
        payload.feedback = feedback
      }

      return payload
    },
    async submitInterviewResultModal() {
      if (this.isSubmittingInterviewResult || this.isLoadingInterviewRecord) {
        return
      }

      const validationError = this.validateInterviewResultForm()
      if (validationError) {
        this.interviewResultFormError = validationError
        return
      }

      this.isSubmittingInterviewResult = true
      this.interviewResultFormError = ''

      try {
        const payload = this.buildInterviewResultPayload(this.interviewResultForm)
        const response = await companyApi.updateInterviewResult(this.interviewResultInterviewId, payload)
        const nextStatus = response?.data?.data?.application_status || (payload.result === 'pass' ? 'offered' : 'rejected')

        const updatePayload = {
          status: nextStatus,
          has_offer: false
        }
        if (payload.result === 'fail') {
          updatePayload.rejection_reason = payload.feedback || 'Rejected after interview'
        } else {
          updatePayload.rejection_reason = ''
        }

        this.applyApplicationUpdate(this.interviewResultTargetApp.id, updatePayload)

        const statusText = payload.result === 'pass' ? 'passed' : 'not selected'
        this.toast_show(`Interview result updated: ${this.interviewResultTargetApp.student} ${statusText}.`, 'success')
        this.closeInterviewResultModal()
      } catch (error) {
        this.interviewResultFormError = this.handleApiError(error, 'Unable to update interview result.')
        this.toast_show(this.interviewResultFormError, 'danger')
      } finally {
        this.isSubmittingInterviewResult = false
      }
    },
    validateInterviewForm() {
      if (!this.interviewTargetApp?.id) {
        return 'Select an application before scheduling an interview.'
      }

      const mode = String(this.interviewForm.interview_mode || '').trim().toLowerCase()
      if (!this.interviewForm.interview_date) {
        return 'Interview date and time is required.'
      }

      const parsedInterviewDate = new Date(this.interviewForm.interview_date)
      if (Number.isNaN(parsedInterviewDate.getTime())) {
        return 'Enter a valid interview date and time.'
      }

      if (!['online', 'offline'].includes(mode)) {
        return 'Select a valid interview mode.'
      }

      if (mode === 'online' && !this.normalizeInput(this.interviewForm.interview_link)) {
        return 'Interview link is required for online interviews.'
      }

      if (mode === 'offline' && !this.normalizeInput(this.interviewForm.interview_location)) {
        return 'Interview location is required for offline interviews.'
      }

      return ''
    },
    buildInterviewPayload(application, formValues = null) {
      const formPayload = formValues || this.interviewForm
      const mode = String(formPayload.interview_mode || 'online').trim().toLowerCase()
      const parsedInterviewDate = new Date(formPayload.interview_date)

      const payload = {
        application_id: Number(application.id),
        interview_date: parsedInterviewDate.toISOString(),
        interview_mode: mode
      }

      const interviewerName = this.normalizeInput(formPayload.interviewer_name || this.companyProfile.hrName)
      if (interviewerName) {
        payload.interviewer_name = interviewerName
      }

      const interviewLink = this.normalizeInput(formPayload.interview_link)
      const interviewLocation = this.normalizeInput(formPayload.interview_location)

      if (mode === 'online' && interviewLink) {
        payload.interview_link = interviewLink
      }

      if (mode === 'offline' && interviewLocation) {
        payload.interview_location = interviewLocation
      }

      return payload
    },
    async submitInterviewModal() {
      if (this.isSubmittingInterview) {
        return
      }

      const validationError = this.validateInterviewForm()
      if (validationError) {
        this.interviewFormError = validationError
        return
      }

      this.isSubmittingInterview = true
      this.interviewFormError = ''

      try {
        const payload = this.buildInterviewPayload(this.interviewTargetApp, this.interviewForm)
        const ok = await this.scheduleInterviewForApplication(this.interviewTargetApp, payload)
        if (ok) {
          this.closeInterviewModal()
        }
      } finally {
        this.isSubmittingInterview = false
      }
    },
    openOfferModal(application) {
      if (!this.canManageApplications) {
        this.toast_show('Application actions are enabled only after admin approval.', 'warning')
        return
      }

      if (!application?.id) {
        return
      }

      if (application.hasOffer) {
        this.toast_show('Offer has already been released for this candidate.', 'info')
        return
      }

      const drive = this.findDriveForApplication(application)
      const joiningDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)

      this.offerTargetApp = application
      this.offerForm = {
        ...createDefaultOfferForm(),
        position: drive?.role || drive?.title || application.drive || 'Placement Offer',
        salary: String(this.resolveOfferSalary(application)),
        joining_date: this.toDateValue(joiningDate)
      }
      this.offerFormError = ''
      this.showOfferModal = true
    },
    closeOfferModal() {
      this.showOfferModal = false
      this.offerTargetApp = null
      this.offerForm = createDefaultOfferForm()
      this.offerFormError = ''
      this.isSubmittingOffer = false
    },
    validateOfferForm() {
      if (!this.offerTargetApp?.id) {
        return 'Select an application before releasing an offer.'
      }

      const position = this.normalizeInput(this.offerForm.position)
      if (!position) {
        return 'Position is required.'
      }

      const salary = parseFloat(String(this.offerForm.salary || '').replace(/,/g, '').trim())
      if (!Number.isFinite(salary) || salary <= 0) {
        return 'Salary must be a valid positive number.'
      }

      if (!this.offerForm.joining_date) {
        return 'Joining date is required.'
      }

      const parsedJoiningDate = new Date(`${this.offerForm.joining_date}T00:00:00`)
      if (Number.isNaN(parsedJoiningDate.getTime())) {
        return 'Enter a valid joining date.'
      }

      const today = new Date()
      today.setHours(0, 0, 0, 0)
      if (parsedJoiningDate < today) {
        return 'Joining date cannot be in the past.'
      }

      return ''
    },
    buildOfferPayload(application, formValues = null) {
      const formPayload = formValues || this.offerForm
      const drive = this.findDriveForApplication(application)
      const salary = parseFloat(String(formPayload.salary || '').replace(/,/g, '').trim())

      return {
        application_id: Number(application.id),
        salary: Number.isFinite(salary) ? salary : this.resolveOfferSalary(application),
        position: this.normalizeInput(formPayload.position) || drive?.role || drive?.title || application.drive || 'Placement Offer',
        joining_date: this.normalizeInput(formPayload.joining_date) || this.toDateValue(new Date(Date.now() + 30 * 24 * 60 * 60 * 1000))
      }
    },
    async submitOfferModal() {
      if (this.isSubmittingOffer) {
        return
      }

      const validationError = this.validateOfferForm()
      if (validationError) {
        this.offerFormError = validationError
        return
      }

      this.isSubmittingOffer = true
      this.offerFormError = ''

      try {
        const payload = this.buildOfferPayload(this.offerTargetApp, this.offerForm)
        const ok = await this.createOfferForApplication(this.offerTargetApp, payload)
        if (ok) {
          this.closeOfferModal()
        }
      } finally {
        this.isSubmittingOffer = false
      }
    },
    openRejectModal(application) {
      if (!this.canManageApplications) {
        this.toast_show('Application actions are enabled only after admin approval.', 'warning')
        return
      }

      if (!application?.id) {
        return
      }

      this.rejectTargetApp = application
      this.rejectForm = {
        ...createDefaultRejectForm(),
        rejection_reason: this.normalizeInput(application.rejectionReason),
        notes: this.normalizeInput(application.notes)
      }
      this.rejectFormError = ''
      this.showRejectModal = true
    },
    closeRejectModal() {
      this.showRejectModal = false
      this.rejectTargetApp = null
      this.rejectForm = createDefaultRejectForm()
      this.rejectFormError = ''
      this.isSubmittingReject = false
    },
    validateRejectForm() {
      if (!this.rejectTargetApp?.id) {
        return 'Select an application before submitting rejection feedback.'
      }

      const rejectionReason = this.normalizeInput(this.rejectForm.rejection_reason)
      if (!rejectionReason) {
        return 'Rejection reason is required.'
      }

      if (rejectionReason.length < 5) {
        return 'Rejection reason must be at least 5 characters.'
      }

      return ''
    },
    async submitRejectModal() {
      if (this.isSubmittingReject) {
        return
      }

      const validationError = this.validateRejectForm()
      if (validationError) {
        this.rejectFormError = validationError
        return
      }

      this.isSubmittingReject = true
      this.rejectFormError = ''

      try {
        const payload = {
          status: 'rejected',
          rejection_reason: this.normalizeInput(this.rejectForm.rejection_reason),
          notes: this.normalizeInput(this.rejectForm.notes)
        }

        const ok = await this.updateApplicationStatus(
          this.rejectTargetApp,
          payload,
          `${this.rejectTargetApp.student} marked as rejected.`
        )

        if (ok) {
          this.closeRejectModal()
        }
      } finally {
        this.isSubmittingReject = false
      }
    },
    async scheduleInterviewForApplication(application, payloadOverride = null) {
      if (!this.canManageApplications) {
        this.toast_show('Application actions are enabled only after admin approval.', 'warning')
        return false
      }

      try {
        const payload = payloadOverride || this.buildInterviewPayload(application)
        const response = await companyApi.scheduleInterview(payload)
        const nextStatus = response?.data?.data?.application_status || 'interview'
        this.applyApplicationUpdate(application.id, { status: nextStatus })
        this.toast_show(`Interview scheduled for ${application.student}.`, 'success')
        return true
      } catch (error) {
        this.handleApiError(error, 'Unable to schedule interview.', { showToast: true })
        return false
      }
    },
    async createOfferForApplication(application, payloadOverride = null) {
      if (!this.canManageApplications) {
        this.toast_show('Application actions are enabled only after admin approval.', 'warning')
        return false
      }

      try {
        const payload = payloadOverride || this.buildOfferPayload(application)
        const response = await companyApi.createOffer(payload)
        const nextStatus = response?.data?.data?.application_status || 'offered'
        this.applyApplicationUpdate(application.id, { status: nextStatus, has_offer: true })
        this.toast_show(`Offer released for ${application.student}.`, 'success')
        return true
      } catch (error) {
        this.handleApiError(error, 'Unable to release offer.', { showToast: true })
        return false
      }
    },
    async screenApplicationResume(application) {
      const applicationId = Number(application?.id || application?.application_id || 0)
      if (!applicationId || this.isScoringResume[applicationId]) {
        return
      }

      this.screeningError = ''
      this.screeningResult = null
      this.showScreeningModal = false

      this.isScoringResume = {
        ...this.isScoringResume,
        [applicationId]: true
      }

      try {
        const response = await companyApi.scoreApplicationResume(applicationId)
        this.screeningResult = response?.data?.data || null
        this.screeningError = ''
        this.showScreeningModal = true
      } catch (error) {
        const parsedMessage = parseApiError(error, 'Unable to run ATS screening.')
        this.screeningError = this.normalizeAtsErrorMessage(parsedMessage)
        this.showScreeningModal = true
        this.toast_show(this.screeningError, 'danger')
      } finally {
        this.isScoringResume = {
          ...this.isScoringResume,
          [applicationId]: false
        }
      }
    },
    normalizeAtsErrorMessage(rawMessage) {
      const message = String(rawMessage || '').trim()
      const normalized = message.toLowerCase()

      if (normalized.includes('job_id must be an integer') || normalized.includes('job_id is required')) {
        return 'ATS scoring received an invalid job context. Please refresh and make sure you are signed in as a company user.'
      }

      if (normalized.includes('application_id must be an integer') || normalized.includes('application_id is required')) {
        return 'ATS scoring received an invalid application reference. Please refresh the applications table and retry.'
      }

      return message || 'Unable to run ATS screening.'
    },
    async shortlistApp(application) {
      await this.updateApplicationStatus(application, { status: 'shortlisted' }, `${application.student} shortlisted.`)
    },
    async rejectApp(application) {
      this.openRejectModal(application)
    },
    async advanceStage(application, stage) {
      if (!application?.id) {
        return
      }

      if (stage === 'interview') {
        this.openInterviewModal(application)
        return
      }

      if (stage === 'offered') {
        if (application.status === 'interview') {
          this.openInterviewResultModal(application)
          return
        }

        this.openOfferModal(application)
        return
      }

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

      this.openBulkShortlistModal()
    },
    closeBulkShortlistModal() {
      this.showBulkShortlistModal = false
      this.bulkShortlistForm = createDefaultBulkShortlistForm()
      this.bulkShortlistFormError = ''
      this.isSubmittingBulkShortlist = false
    },
    openBulkShortlistModal() {
      if (!this.canManageApplications) {
        this.toast_show('Application actions are enabled only after admin approval.', 'warning')
        return
      }

      if (!this.selectedApps.length) {
        this.toast_show('Select at least one application first.', 'warning')
        return
      }

      this.bulkShortlistForm = createDefaultBulkShortlistForm()
      this.bulkShortlistFormError = ''
      this.showBulkShortlistModal = true
    },
    validateBulkShortlistForm() {
      if (!this.selectedApps.length) {
        return 'Select at least one application before bulk shortlist.'
      }

      return ''
    },
    async submitBulkShortlistModal() {
      if (this.isSubmittingBulkShortlist) {
        return
      }

      const validationError = this.validateBulkShortlistForm()
      if (validationError) {
        this.bulkShortlistFormError = validationError
        return
      }

      this.isSubmittingBulkShortlist = true
      this.bulkShortlistFormError = ''

      let successCount = 0
      try {
        const selectedApplicationIds = [...this.selectedApps]
        const notes = this.normalizeInput(this.bulkShortlistForm.notes)

        for (const applicationId of selectedApplicationIds) {
          const application = this.allApplications.find((entry) => entry.id === applicationId)
          if (!application || !['applied', 'pending'].includes(application.status)) {
            continue
          }

          const payload = {
            status: 'shortlisted'
          }
          if (notes) {
            payload.notes = notes
          }

          const ok = await this.updateApplicationStatus(application, payload, `${application.student} shortlisted.`)
          if (ok) {
            successCount += 1
          }
        }
      } finally {
        this.isSubmittingBulkShortlist = false
      }

      this.selectedApps = []
      this.closeBulkShortlistModal()
      this.toast_show(`${successCount} applications shortlisted`, 'success')
    },
    async bulkReject() {
      if (!this.canManageApplications) {
        this.toast_show('Application actions are enabled only after admin approval.', 'warning')
        return
      }

      this.openBulkRejectModal()
    },
    closeBulkRejectModal() {
      this.showBulkRejectModal = false
      this.bulkRejectForm = createDefaultBulkRejectForm()
      this.bulkRejectFormError = ''
      this.isSubmittingBulkReject = false
    },
    openBulkRejectModal() {
      if (!this.canManageApplications) {
        this.toast_show('Application actions are enabled only after admin approval.', 'warning')
        return
      }

      if (!this.selectedApps.length) {
        this.toast_show('Select at least one application first.', 'warning')
        return
      }

      this.bulkRejectForm = createDefaultBulkRejectForm()
      this.bulkRejectFormError = ''
      this.showBulkRejectModal = true
    },
    validateBulkRejectForm() {
      if (!this.selectedApps.length) {
        return 'Select at least one application before bulk reject.'
      }

      const rejectionReason = this.normalizeInput(this.bulkRejectForm.rejection_reason)
      if (!rejectionReason) {
        return 'Rejection reason is required for bulk reject.'
      }

      if (rejectionReason.length < 5) {
        return 'Rejection reason must be at least 5 characters.'
      }

      return ''
    },
    async submitBulkRejectModal() {
      if (this.isSubmittingBulkReject) {
        return
      }

      const validationError = this.validateBulkRejectForm()
      if (validationError) {
        this.bulkRejectFormError = validationError
        return
      }

      this.isSubmittingBulkReject = true
      this.bulkRejectFormError = ''

      let successCount = 0
      try {
        const selectedApplicationIds = [...this.selectedApps]
        const rejectionReason = this.normalizeInput(this.bulkRejectForm.rejection_reason)
        const notes = this.normalizeInput(this.bulkRejectForm.notes)

        for (const applicationId of selectedApplicationIds) {
          const application = this.allApplications.find((entry) => entry.id === applicationId)
          if (!application) {
            continue
          }

          const payload = {
            status: 'rejected',
            rejection_reason: rejectionReason
          }
          if (notes) {
            payload.notes = notes
          }

          const ok = await this.updateApplicationStatus(
            application,
            payload,
            `${application.student} marked as rejected.`
          )

          if (ok) {
            successCount += 1
          }
        }
      } finally {
        this.isSubmittingBulkReject = false
      }

      this.selectedApps = []
      this.closeBulkRejectModal()
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

      const eligibleYears = Array.isArray(this.newDrive.eligible_years)
        ? [...new Set(this.newDrive.eligible_years.map((year) => Number(year)).filter((year) => year >= 1 && year <= 4))]
        : []

      const requiredSkills = Array.isArray(this.newDrive.required_skills)
        ? this.newDrive.required_skills
            .map((skill) => String(skill || '').trim())
            .filter(Boolean)
        : []

      const payload = {
        job_title: String(this.newDrive.title || '').trim(),
        job_description: this.newDrive.description || 'Role details shared during screening.',
        required_skills: requiredSkills.join(','),
        experience_required: String(this.newDrive.experience_required || '').trim(),
        benefits: 'As per company policy',
        min_cgpa: Number(this.newDrive.minCgpa || 0),
        eligible_branches: this.parseBranches(this.newDrive.branches),
        eligible_years: eligibleYears,
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
    getCompanyExportTrigger(scope) {
      const normalizedScope = String(scope || '').trim().toLowerCase()
      if (normalizedScope === 'drives') {
        return companyApi.triggerDrivesExportJob
      }
      if (normalizedScope === 'applications') {
        return companyApi.triggerApplicationsExportJob
      }
      return null
    },
    isCompanyExportBusy(scope) {
      const status = this.companyExportJobs[String(scope || '').toLowerCase()]?.status
      return status === 'queued' || status === 'running'
    },
    companyExportButtonLabel(scope) {
      const normalizedScope = String(scope || '').toLowerCase()
      const status = this.companyExportJobs[normalizedScope]?.status

      if (status === 'queued') {
        return 'Export queued...'
      }
      if (status === 'running') {
        return 'Export running...'
      }
      return 'Export CSV'
    },
    updateCompanyExportState(scope, patch) {
      const normalizedScope = String(scope || '').toLowerCase()
      const current = this.companyExportJobs[normalizedScope] || {
        jobId: '',
        attempts: 0,
        status: 'idle',
        announcedRunning: false
      }

      this.companyExportJobs = {
        ...this.companyExportJobs,
        [normalizedScope]: {
          ...current,
          ...patch
        }
      }
    },
    clearCompanyExportPoll(scope, options = {}) {
      const { preserveState = false } = options
      const normalizedScope = String(scope || '').toLowerCase()
      const timerId = this.companyExportTimers[normalizedScope]
      if (timerId) {
        clearTimeout(timerId)
      }

      const nextTimers = { ...this.companyExportTimers }
      delete nextTimers[normalizedScope]
      this.companyExportTimers = nextTimers

      if (!preserveState) {
        const nextJobs = { ...this.companyExportJobs }
        delete nextJobs[normalizedScope]
        this.companyExportJobs = nextJobs
      }
    },
    clearCompanyExportPollsForView(viewId, clearAll = false) {
      const allowedScope = clearAll ? null : COMPANY_EXPORT_SCOPE_BY_VIEW[viewId] || null
      Object.keys(this.companyExportTimers).forEach((scope) => {
        if (clearAll || scope !== allowedScope) {
          this.clearCompanyExportPoll(scope)
        }
      })
    },
    scheduleCompanyExportPoll(scope) {
      const normalizedScope = String(scope || '').toLowerCase()
      const timerId = setTimeout(() => {
        this.pollCompanyExport(normalizedScope)
      }, EXPORT_POLL_INTERVAL_MS)

      this.companyExportTimers = {
        ...this.companyExportTimers,
        [normalizedScope]: timerId
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
    async pollCompanyExport(scope) {
      const normalizedScope = String(scope || '').toLowerCase()
      const exportJob = this.companyExportJobs[normalizedScope]
      if (!exportJob?.jobId) {
        this.clearCompanyExportPoll(normalizedScope)
        return
      }

      if (exportJob.attempts >= EXPORT_POLL_MAX_ATTEMPTS) {
        this.clearCompanyExportPoll(normalizedScope)
        this.toast_show(`${normalizedScope} export timed out. Please retry.`, 'warning')
        return
      }

      try {
        const statusResponse = await companyApi.getExportStatus(exportJob.jobId)
        const data = statusResponse?.data?.data || {}
        const job = data.job || {}
        const artifact = data.artifact || {}
        const jobStatus = String(job.status || '').toLowerCase()
        const artifactStatus = String(artifact.status || '').toLowerCase()

        if (jobStatus === 'completed' && artifactStatus === 'ready') {
          const downloadResponse = await companyApi.downloadExport(exportJob.jobId)
          const fallbackName = `recruitify-${normalizedScope}-${Date.now()}.csv`
          const filename = this.extractFilename(downloadResponse?.headers, fallbackName)
          this.triggerFileDownload(downloadResponse?.data, filename)
          this.clearCompanyExportPoll(normalizedScope)
          this.toast_show(`${normalizedScope} export downloaded successfully.`, 'success')
          return
        }

        const hasFailed =
          jobStatus === 'failed' ||
          jobStatus === 'cancelled' ||
          artifactStatus === 'failed' ||
          artifactStatus === 'expired'

        if (hasFailed) {
          this.clearCompanyExportPoll(normalizedScope)
          const fallbackFailureMessage = artifactStatus === 'expired'
            ? 'Export artifact expired before download. Please retry.'
            : `Unable to complete ${normalizedScope} export. Please retry.`
          this.toast_show(job.error_message || fallbackFailureMessage, 'danger')
          return
        }

        const nextStatus = jobStatus === 'running' ? 'running' : 'queued'
        const nextAttempts = exportJob.attempts + 1
        this.updateCompanyExportState(normalizedScope, {
          status: nextStatus,
          attempts: nextAttempts
        })

        if (nextStatus === 'running' && !exportJob.announcedRunning) {
          this.updateCompanyExportState(normalizedScope, { announcedRunning: true })
          this.toast_show(`${normalizedScope} export is running in the background...`, 'info')
        }

        if (nextAttempts >= EXPORT_POLL_MAX_ATTEMPTS) {
          this.clearCompanyExportPoll(normalizedScope)
          this.toast_show(`${normalizedScope} export timed out. Please retry.`, 'warning')
          return
        }

        this.scheduleCompanyExportPoll(normalizedScope)
      } catch (error) {
        const nextAttempts = (exportJob.attempts || 0) + 1
        this.updateCompanyExportState(normalizedScope, { attempts: nextAttempts })

        if (nextAttempts >= EXPORT_POLL_MAX_ATTEMPTS) {
          this.clearCompanyExportPoll(normalizedScope)
          const message = this.handleApiError(error, 'Unable to fetch export status.')
          this.toast_show(`${message} Please retry the export.`, 'warning')
          return
        }

        this.scheduleCompanyExportPoll(normalizedScope)
      }
    },
    async doExport(scope) {
      const normalizedScope = String(scope || '').trim().toLowerCase()
      const triggerExport = this.getCompanyExportTrigger(normalizedScope)

      if (!triggerExport) {
        this.toast_show('Export option is unavailable for this section.', 'warning')
        return
      }

      if (this.isCompanyExportBusy(normalizedScope)) {
        this.toast_show(`${normalizedScope} export is already in progress.`, 'info')
        return
      }

      this.clearCompanyExportPoll(normalizedScope)

      try {
        const response = await triggerExport()
        const payload = response?.data?.data || {}
        const jobId = String(payload.job_id || '').trim()
        if (!jobId) {
          this.toast_show('Unable to start export job. Please retry.', 'danger')
          return
        }

        const initialStatus = String(payload.status || 'queued').toLowerCase() === 'running'
          ? 'running'
          : 'queued'
        this.updateCompanyExportState(normalizedScope, {
          jobId,
          attempts: 0,
          status: initialStatus,
          announcedRunning: initialStatus === 'running'
        })

        if (payload.active_job_reused) {
          this.toast_show(`Tracking existing ${normalizedScope} export job...`, 'info')
        } else if (initialStatus === 'running') {
          this.toast_show(`${normalizedScope} export is running in the background...`, 'info')
        } else {
          this.toast_show(`${normalizedScope} export queued. Preparing your CSV...`, 'info')
        }

        this.scheduleCompanyExportPoll(normalizedScope)
      } catch (error) {
        const message = this.handleApiError(error, 'Unable to start export.')
        this.toast_show(message, 'danger')
      }
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
