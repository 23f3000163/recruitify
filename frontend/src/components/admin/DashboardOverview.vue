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
        class="rq-kpi"
        :style="{ '--c': kpi.color, '--cl': kpi.colorLt, animationDelay: (i * 70) + 'ms' }"
        @click="kpi.link && $emit('switch-view', kpi.link)"
        :class="{ 'rq-kpi-clickable': kpi.link }"
      >
        <div class="rq-kpi-header">
          <div class="rq-kpi-icon" :style="{ background: kpi.colorLt, color: kpi.color }" v-html="kpi.svg"></div>
          <span class="rq-kpi-delta" :class="kpi.up ? 'up' : 'warn'">{{ kpi.delta }}</span>
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
                <div class="rq-empty"><div class="rq-empty-ico"></div><b>All caught up!</b><span>No pending approvals.</span></div>
              </td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="rq-card rq-grid-branch">
        <div class="rq-card-hd">
          <span class="rq-card-title">Placement by Branch</span>
          <span class="rq-pill rq-pill-blue">AY 2024–25</span>
        </div>
        <div class="rq-card-body">
          <div v-for="b in branchStats" :key="b.name" class="rq-prog-row">
            <div class="rq-prog-meta">
              <span class="rq-prog-name">{{ b.name }}</span>
              <span class="rq-prog-frac"><b>{{ b.placed }}</b><span class="rq-dim">/{{ b.total }}</span></span>
            </div>
            <div class="rq-bar-track">
              <div class="rq-bar-fill" :style="{ width: pct(b.placed, b.total) + '%', background: b.color }"></div>
            </div>
            <span class="rq-prog-pct">{{ pct(b.placed, b.total) }}%</span>
          </div>
        </div>
      </div>

      <div class="rq-card rq-grid-audit">
        <div class="rq-card-hd">
          <span class="rq-card-title">Activity Audit Trail</span>
          <button class="rq-ghost" @click="$emit('export', 'audit')">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M6 1v7M3 6l3 3 3-3M1 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            Export
          </button>
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
              <tr v-for="log in auditLog" :key="log.id">
                <td>
                  <div class="rq-log-row">
                    <span class="rq-log-dot" :class="'dot-' + log.status"></span>
                    {{ log.action }}
                  </div>
                </td>
                <td class="rq-sm rq-dim">{{ log.actor }}</td>
                <td class="rq-sm rq-dim">{{ log.target }}</td>
                <td class="rq-sm rq-dim rq-mono">{{ log.time }}</td>
              </tr>
              <tr v-if="!auditLog.length">
                <td colspan="4" class="rq-sm rq-dim">No activity recorded yet.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="rq-card rq-grid-recent">
        <div class="rq-card-hd">
          <span class="rq-card-title">Recent Applications</span>
          <button class="rq-ghost" @click="$emit('switch-view', 'students')">View all →</button>
        </div>
        <div class="rq-tbl-wrap">
          <table class="rq-tbl" aria-label="Recent applications">
            <thead><tr>
              <th scope="col">Student</th>
              <th scope="col">Drive</th>
              <th scope="col">Status</th>
            </tr></thead>
            <tbody>
              <tr v-for="a in recentApplications" :key="a.id">
                <td>
                  <div class="rq-entity">
                    <div class="rq-av rq-av-sm" :style="{ background: a.color }">{{ a.initials }}</div>
                    <div>
                      <div class="rq-ename rq-sm">{{ a.student }}</div>
                      <div class="rq-esub">{{ a.roll }}</div>
                    </div>
                  </div>
                </td>
                <td class="rq-sm rq-dim">{{ a.drive }}</td>
                <td><span class="rq-status-pill" :class="'pill-' + a.status">{{ a.status }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'DashboardOverview',
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
  emits: ['switch-view', 'approve-item', 'reject-item', 'retry', 'export'],
  methods: {
    isActionBusy(item) {
      if (!item?.entityId) return false
      if (item.entityType === 'company') return !!this.pendingCompanyActions[item.entityId]
      if (item.entityType === 'drive') return !!this.pendingDriveActions[item.entityId]
      return false
    }
  }
}
</script>
