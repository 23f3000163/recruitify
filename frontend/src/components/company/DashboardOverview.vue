<template>
  <section class="rq-view">
    <div class="rq-kpi-grid">
      <div
        v-for="(kpi, index) in kpiCards"
        :key="kpi.id"
        class="rq-kpi"
        :style="{ '--c': kpi.color, '--cl': kpi.colorLt, animationDelay: index * 70 + 'ms' }"
        @click="kpi.link && $emit('open-view', kpi.link)"
        :class="{ 'rq-kpi-clickable': kpi.link }"
        :role="kpi.link ? 'button' : undefined"
      >
        <div class="rq-kpi-header">
          <div class="rq-kpi-icon" :style="{ background: kpi.colorLt, color: kpi.color }" v-html="kpi.svg"></div>
          <span class="rq-kpi-delta" :class="kpi.up ? 'delta-up' : 'delta-warn'">{{ kpi.delta }}</span>
        </div>
        <div class="rq-kpi-val">{{ kpi.value }}</div>
        <div class="rq-kpi-label">{{ kpi.label }}</div>
        <div class="rq-kpi-bar">
          <div class="rq-kpi-bar-fill" :style="{ width: kpi.pct + '%', background: kpi.color }"></div>
        </div>
      </div>
    </div>

    <div class="rq-row-2">
      <div class="rq-card">
        <div class="rq-card-hd">
          <span class="rq-card-title">Company Profile</span>
          <button class="rq-ghost" @click="$emit('open-view', 'profile')">Edit →</button>
        </div>
        <div class="rq-card-body rq-profile-body">
          <div class="rq-profile-header">
            <div class="rq-av rq-av-xl" :style="{ background: companyProfile.avatarColor }">{{ companyProfile.initials }}</div>
            <div class="rq-profile-meta">
              <div class="rq-profile-name">{{ companyProfile.name }}</div>
              <div class="rq-profile-domain">{{ companyProfile.domain }}</div>
              <span class="rq-status-pill" :class="'pill-' + companyProfile.status" style="margin-top:6px;display:inline-block">
                {{ companyProfile.status }}
              </span>
            </div>
          </div>
          <div class="rq-profile-fields">
            <div class="rq-pf-row">
              <span class="rq-pf-key">HR Contact</span>
              <span class="rq-pf-val rq-mono">{{ companyProfile.hrEmail }}</span>
            </div>
            <div class="rq-pf-row">
              <span class="rq-pf-key">Industry</span>
              <span class="rq-pf-val">{{ companyProfile.industry }}</span>
            </div>
            <div class="rq-pf-row">
              <span class="rq-pf-key">Registered</span>
              <span class="rq-pf-val rq-mono">{{ companyProfile.registeredOn }}</span>
            </div>
            <div class="rq-pf-row">
              <span class="rq-pf-key">Location</span>
              <span class="rq-pf-val">{{ companyProfile.location }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="rq-card">
        <div class="rq-card-hd">
          <div class="rq-card-hd-l">
            <span class="rq-card-title">Application Funnel</span>
            <span class="rq-pill rq-pill-blue">All Drives</span>
          </div>
          <button class="rq-ghost" @click="$emit('open-view', 'drives')">Manage drives →</button>
        </div>
        <div class="rq-card-body">
          <div v-for="drive in activeDrivesFunnel" :key="drive.id" class="rq-funnel-row">
            <div class="rq-funnel-meta">
              <div class="rq-av rq-av-sm" :style="{ background: drive.avatarColor }">{{ drive.initials }}</div>
              <div>
                <div class="rq-funnel-name">{{ drive.title }}</div>
                <div class="rq-esub">{{ drive.type }}</div>
              </div>
            </div>
            <div class="rq-funnel-stages">
              <div class="rq-fstage" v-for="stage in drive.stages" :key="stage.label">
                <div class="rq-fstage-val" :style="{ color: stage.color }">{{ stage.count }}</div>
                <div class="rq-fstage-label">{{ stage.label }}</div>
              </div>
            </div>
          </div>
          <div v-if="!activeDrivesFunnel.length" class="rq-empty">
            <div class="rq-empty-ico">📋</div>
            <b>No active drives</b>
            <span>Create your first drive to see the funnel.</span>
          </div>
        </div>
      </div>
    </div>

    <div class="rq-card">
      <div class="rq-card-hd">
        <div class="rq-card-hd-l">
          <span class="rq-card-title">Recent Applications</span>
          <span v-if="pendingApplicationsCount > 0" class="rq-pill rq-pill-amber">{{ pendingApplicationsCount }} to review</span>
        </div>
        <button class="rq-ghost" @click="$emit('open-view', 'applications')">View all →</button>
      </div>
      <div class="rq-tbl-wrap">
        <table class="rq-tbl" aria-label="Recent applications">
          <thead>
            <tr>
              <th scope="col">Student</th>
              <th scope="col">Drive</th>
              <th scope="col">CGPA</th>
              <th scope="col">Applied On</th>
              <th scope="col">Status</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="application in recentApplications.slice(0, 5)" :key="application.id">
              <td>
                <div class="rq-entity">
                  <div class="rq-av rq-av-md" :style="{ background: application.color }">{{ application.initials }}</div>
                  <div>
                    <div class="rq-ename">{{ application.student }}</div>
                    <div class="rq-esub">{{ application.roll }} · {{ application.branch }}</div>
                  </div>
                </div>
              </td>
              <td class="rq-sm rq-dim">{{ application.drive }}</td>
              <td>
                <span class="rq-cgpa" :class="application.cgpa >= 8.5 ? 'cgpa-hi' : application.cgpa >= 7 ? 'cgpa-md' : 'cgpa-lo'">
                  {{ application.cgpa }}
                </span>
              </td>
              <td class="rq-sm rq-dim rq-mono">{{ application.date }}</td>
              <td>
                <span class="rq-status-pill" :class="'pill-app-' + application.status">{{ application.status }}</span>
              </td>
              <td>
                <div class="rq-acts" v-if="application.status === 'applied' || application.status === 'pending'">
                  <button class="rq-btn-ok" @click="$emit('shortlist', application)" :disabled="!canManageActions">
                    <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                      <path d="M1.5 5.5l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                    Shortlist
                  </button>
                  <button class="rq-btn-no" @click="$emit('reject', application)" title="Reject" :disabled="!canManageActions">
                    <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                      <path d="M2 2l7 7M9 2l-7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
                    </svg>
                  </button>
                </div>
                <span v-else class="rq-dim rq-sm">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'DashboardOverview',
  props: {
    kpiCards: {
      type: Array,
      required: true
    },
    activeDrivesFunnel: {
      type: Array,
      required: true
    },
    companyProfile: {
      type: Object,
      required: true
    },
    pendingApplicationsCount: {
      type: Number,
      required: true
    },
    recentApplications: {
      type: Array,
      required: true
    },
    canManageActions: {
      type: Boolean,
      default: true
    }
  },
  emits: ['open-view', 'shortlist', 'reject']
}
</script>
