<template>
  <section class="rq-view">
    <div v-if="errorMessage" class="rq-state rq-state-error">
      <span>{{ errorMessage }}</span>
      <button class="rq-ghost rq-ghost-xs" @click="$emit('retry')" :disabled="isLoading">Retry</button>
    </div>

    <div v-if="isLoading" class="rq-kpi-grid">
      <div v-for="n in 4" :key="`kpi-skeleton-${n}`" class="rq-kpi rq-kpi-skeleton">
        <div class="rq-kpi-header">
          <span class="rq-skeleton rq-skeleton-block rq-skeleton-icon"></span>
          <span class="rq-skeleton rq-skeleton-line rq-skeleton-pill"></span>
        </div>
        <div class="rq-skeleton rq-skeleton-line rq-skeleton-kpi-value"></div>
        <div class="rq-skeleton rq-skeleton-line rq-skeleton-kpi-label"></div>
        <div class="rq-kpi-bar"><div class="rq-skeleton rq-kpi-bar-fill"></div></div>
      </div>
    </div>

    <div v-else class="rq-kpi-grid">
      <div
        v-for="(kpi, i) in kpiCards"
        :key="kpi.id"
        class="rq-kpi rq-kpi-hoverable"
        :style="{ '--c': kpi.color, '--cl': kpi.colorLt, animationDelay: (i * 70) + 'ms' }"
        @click="kpi.link && $emit('switch-view', kpi.link)"
        :class="{ 'rq-kpi-clickable': kpi.link }"
      >
        <div class="rq-kpi-header">
          <div class="rq-kpi-icon" :style="{ background: kpi.colorLt, color: kpi.color }" v-html="kpi.svg"></div>
          <span :class="['status-badge', kpi.badgeClass || 'badge-gray']">{{ kpi.delta }}</span>
        </div>
        <div class="rq-kpi-val">{{ kpi.value }}</div>
        <div class="rq-kpi-label">{{ kpi.label }}</div>
        <div class="rq-kpi-bar"><div class="rq-kpi-bar-fill" :style="{ width: kpi.pct + '%', background: kpi.color }"></div></div>
      </div>
    </div>

    <div class="rq-dashboard-grid">
      <div class="rq-card rq-grid-pending">
        <div class="rq-card-hd">
          <div class="rq-card-hd-l">
            <span class="rq-card-title">Pending Approvals</span>
            <span class="rq-pill rq-pill-amber" v-if="pendingApprovals.length">{{ pendingApprovals.length }} awaiting</span>
            <span class="rq-pill rq-pill-green" v-else>All clear</span>
          </div>
          <button class="rq-ghost" @click="$emit('switch-view', 'companies')">See all companies →</button>
        </div>
        <div class="rq-tbl-wrap">
          <table class="rq-tbl" aria-label="Pending approvals">
            <thead><tr>
              <th scope="col">Entity</th>
              <th scope="col">Type</th>
              <th scope="col">Submitted</th>
              <th scope="col">Actions</th>
            </tr></thead>
            <tbody>
              <tr v-for="item in pendingApprovals" :key="item.id">
                <td>
                  <div class="rq-entity">
                    <div class="rq-av rq-av-md" :style="{ background: item.color }">{{ item.initials }}</div>
                    <div>
                      <div class="rq-ename">{{ item.name }}</div>
                      <div class="rq-esub">{{ item.sub }}</div>
                    </div>
                  </div>
                </td>
                <td><span class="rq-ttag" :class="item.type === 'Company' ? 'tag-co' : 'tag-dr'">{{ item.type }}</span></td>
                <td class="rq-dim rq-sm">{{ item.date }}</td>
                <td>
                  <div class="rq-acts">
                    <button class="rq-btn-ok" :disabled="isLoading || isActionBusy(item)" @click.stop="$emit('approve-item', item)">
                      <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1.5 5.5l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                      Approve
                    </button>
                    <button class="rq-btn-no" :disabled="isLoading || isActionBusy(item)" @click.stop="$emit('reject-item', item)">
                      <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M2 2l7 7M9 2l-7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
                      Reject
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="!pendingApprovals.length"><td colspan="4">
                <div class="rq-empty">
                  <div class="rq-empty-ico">
                    <CircleCheck :size="17" class="rq-empty-check" />
                  </div>
                  <b>All caught up!</b>
                  <span>No pending approvals.</span>
                </div>
              </td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="rq-card rq-grid-branch placement-card">
        <div class="rq-card-hd">
          <span class="rq-card-title">Placement by Branch</span>
          <span class="rq-pill rq-pill-blue">AY 2024–25</span>
        </div>
        <div v-if="branchStats.length > 0" class="branch-list">
          <div v-for="b in branchStats" :key="b.name" class="branch-row">
            <div class="branch-meta">
              <span class="branch-name">{{ b.name }}</span>
              <span class="branch-stat">{{ b.placed }} placed / {{ b.total }} students</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: branchFillWidth(b.placed, b.total), background: b.color }"></div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="empty-icon-wrap">
            <BarChart2 :size="16" class="empty-icon" />
          </div>
          <p class="empty-title">No placement data yet</p>
          <p class="empty-sub">Data appears here once placement drives are completed</p>
        </div>
        <div class="card-footer">
          <span class="footer-summary">{{ totalPlaced }} of {{ totalStudents }} students placed</span>
        </div>
      </div>

      <div class="rq-card rq-grid-audit">
        <div class="rq-card-hd">
          <span class="rq-card-title">Activity Audit Trail</span>
          <div class="audit-actions">
            <select v-model="auditFilter" class="audit-filter" aria-label="Filter audit activity">
              <option value="all">All</option>
              <option value="students">Students</option>
              <option value="companies">Companies</option>
            </select>
            <button v-if="hasMoreAuditRows" class="rq-ghost" @click="toggleAuditRows">
              {{ showAllAudit ? 'Show less' : 'View all →' }}
            </button>
          </div>
        </div>
        <div class="rq-tbl-wrap">
          <table class="rq-tbl" aria-label="Audit trail">
            <thead><tr>
              <th scope="col">Action</th>
              <th scope="col">Actor</th>
              <th scope="col">Target</th>
              <th scope="col">Time</th>
            </tr></thead>
            <tbody>
              <template v-if="auditDisplayRows.length">
                <tr v-for="row in auditDisplayRows" :key="row.key" :class="{ 'audit-divider-row': row.type === 'divider' }">
                  <td v-if="row.type === 'divider'" colspan="4">
                    <span class="audit-date-divider">{{ row.label }}</span>
                  </td>
                  <template v-else>
                    <td>
                      <div class="rq-log-row">
                        <span class="rq-log-dot" :class="'dot-' + row.status"></span>
                        {{ row.action }}
                        <span v-if="row.count > 1" class="audit-count-badge">×{{ row.count }}</span>
                      </div>
                    </td>
                    <td class="rq-sm rq-dim">{{ row.actor }}</td>
                    <td class="rq-sm rq-dim">{{ row.target }}</td>
                    <td class="rq-sm rq-dim rq-mono">{{ row._timeLabel }}</td>
                  </template>
                </tr>
              </template>
              <tr v-else>
                <td colspan="4" class="rq-sm rq-dim">No activity recorded yet.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="rq-card rq-grid-recent">
        <div class="rq-card-hd">
          <span class="rq-card-title">Recent Applications</span>
          <button v-if="recentApplications.length > 0" class="rq-ghost" @click="$emit('switch-view', 'students')">View all →</button>
        </div>
        <table v-if="recentApplications.length > 0" class="data-table" aria-label="Recent applications">
            <thead><tr>
              <th scope="col" style="width: 35%">Student</th>
              <th scope="col" style="width: 40%">Drive</th>
              <th scope="col" style="width: 25%">Status</th>
            </tr></thead>
            <tbody>
              <tr v-for="a in recentApplications" :key="a.id">
                <td>
                  <div class="cell-main">{{ a.student }}</div>
                  <div class="cell-sub">{{ a.roll }}</div>
                </td>
                <td>
                  <div class="cell-main">{{ a.drive }}</div>
                  <div class="cell-sub">{{ a.company || '-' }}</div>
                </td>
                <td>
                  <span :class="['status-badge', statusBadgeClass(a.status)]">
                    {{ formatStatusLabel(a.status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        <div v-else class="empty-state recent-empty-state">
          <div class="empty-icon-wrap">
            <FileText :size="16" class="empty-icon" />
          </div>
          <p class="empty-title">No applications yet</p>
          <p class="empty-sub">Applications appear here once students apply to a placement drive</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import { BarChart2, CircleCheck, FileText } from 'lucide-vue-next'
import { parseServerDate } from '../../utils/dateTime'

export default {
  name: 'DashboardOverview',
  components: {
    BarChart2,
    CircleCheck,
    FileText
  },
  props: {
    kpiCards: { type: Array, required: true },
    pendingApprovals: { type: Array, required: true },
    branchStats: { type: Array, required: true },
    auditLog: { type: Array, required: true },
    recentApplications: { type: Array, required: true },
    isLoading: { type: Boolean, default: false },
    errorMessage: { type: String, default: '' },
    pendingCompanyActions: { type: Object, default: () => ({}) },
    pendingDriveActions: { type: Object, default: () => ({}) },
    pct: { type: Function, required: true }
  },
  data() {
    return {
      auditFilter: 'all',
      showAllAudit: false
    }
  },
  emits: ['switch-view', 'approve-item', 'reject-item', 'retry'],
  computed: {
    totalPlaced() {
      return this.branchStats.reduce((sum, branch) => sum + Number(branch.placed || 0), 0)
    },
    totalStudents() {
      return this.branchStats.reduce((sum, branch) => sum + Number(branch.total || 0), 0)
    },
    normalizedAuditRows() {
      return this.auditLog
        .map((log, index) => {
          const parsedDate = this.parseAuditDate(log.timestamp || log.time)
          const ts = parsedDate ? parsedDate.getTime() : 0
          return {
            ...log,
            _order: index,
            _timestamp: ts,
            _dateKey: parsedDate ? this.auditDateKey(parsedDate) : 'unknown',
            _dateLabel: parsedDate ? this.formatAuditDateDivider(parsedDate) : 'Earlier',
            _timeLabel: parsedDate ? this.formatAuditTime(parsedDate) : String(log.time || '-'),
            _category: this.auditCategory(log)
          }
        })
        .sort((a, b) => {
          if (b._timestamp !== a._timestamp) return b._timestamp - a._timestamp
          return a._order - b._order
        })
    },
    filteredAuditRows() {
      if (this.auditFilter === 'all') {
        return this.normalizedAuditRows
      }
      return this.normalizedAuditRows.filter((row) => row._category === this.auditFilter)
    },
    collapsedAuditRows() {
      const grouped = new Map()
      this.filteredAuditRows.forEach((row, index) => {
        const key = `${row._dateKey}|${row.action}|${row.actor}|${row.target}|${row.status}`
        if (grouped.has(key)) {
          grouped.get(key).count += 1
          return
        }
        grouped.set(key, {
          ...row,
          key: `audit-${key}`,
          count: 1,
          _groupOrder: index
        })
      })
      return Array.from(grouped.values()).sort((a, b) => {
        if (b._timestamp !== a._timestamp) return b._timestamp - a._timestamp
        return a._groupOrder - b._groupOrder
      })
    },
    hasMoreAuditRows() {
      return this.collapsedAuditRows.length > 5
    },
    auditDisplayRows() {
      const rows = []
      let currentDateKey = ''
      let visibleEntries = 0

      for (const row of this.collapsedAuditRows) {
        if (!this.showAllAudit && visibleEntries >= 5) break

        if (row._dateKey !== currentDateKey) {
          rows.push({
            type: 'divider',
            key: `divider-${row._dateKey}`,
            label: row._dateLabel
          })
          currentDateKey = row._dateKey
        }

        rows.push({
          ...row,
          type: 'entry'
        })
        visibleEntries += 1
      }

      while (rows.length && rows[rows.length - 1].type === 'divider') {
        rows.pop()
      }

      return rows
    }
  },
  watch: {
    auditFilter() {
      this.showAllAudit = false
    },
    auditLog() {
      this.showAllAudit = false
    }
  },
  methods: {
    toggleAuditRows() {
      this.showAllAudit = !this.showAllAudit
    },
    branchFillWidth(placed, total) {
      const numericPlaced = Number(placed || 0)
      const numericTotal = Number(total || 0)
      if (numericPlaced <= 0 || numericTotal <= 0) {
        return '0%'
      }
      return `${Math.max(8, this.pct(numericPlaced, numericTotal))}%`
    },
    parseAuditDate(value) {
      return parseServerDate(value)
    },
    auditDateKey(date) {
      const y = date.getFullYear()
      const m = String(date.getMonth() + 1).padStart(2, '0')
      const d = String(date.getDate()).padStart(2, '0')
      return `${y}-${m}-${d}`
    },
    formatAuditDateDivider(date) {
      const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate())
      const today = new Date()
      const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate())
      const diffDays = Math.round((todayStart - dayStart) / 86400000)

      if (diffDays === 0) return 'Today'

      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric'
      })
    },
    formatAuditTime(date) {
      return date.toLocaleTimeString(undefined, {
        hour: 'numeric',
        minute: '2-digit'
      })
    },
    auditCategory(log) {
      const text = `${log.action || ''} ${log.target || ''}`.toLowerCase()
      if (text.includes('student')) return 'students'
      if (text.includes('company')) return 'companies'
      return 'other'
    },
    statusBadgeClass(status) {
      const key = String(status || '').trim().toLowerCase()
      const map = {
        applied: 'badge-blue',
        pending: 'badge-blue',
        shortlisted: 'badge-amber',
        selected: 'badge-green',
        approved: 'badge-green',
        rejected: 'badge-red'
      }
      return map[key] || 'badge-gray'
    },
    formatStatusLabel(status) {
      const key = String(status || '').trim().toLowerCase()
      const map = {
        approved: 'Selected',
        pending: 'Applied'
      }
      if (map[key]) {
        return map[key]
      }
      if (!key) {
        return 'Unknown'
      }
      return key.charAt(0).toUpperCase() + key.slice(1)
    },
    isActionBusy(item) {
      if (!item?.entityId) return false
      if (item.entityType === 'company') return !!this.pendingCompanyActions[item.entityId]
      if (item.entityType === 'drive') return !!this.pendingDriveActions[item.entityId]
      return false
    }
  }
}
</script>
