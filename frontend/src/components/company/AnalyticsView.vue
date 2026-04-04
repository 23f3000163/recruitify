<template>
  <section class="rq-view">
    <div class="rq-analytics-grid">
      <div class="rq-card">
        <div class="rq-card-hd">
          <span class="rq-card-title">Application Pipeline</span>
          <span class="rq-pill rq-pill-blue">All Drives</span>
        </div>
        <div class="rq-donut-section">
          <div class="rq-donut-fig">
            <svg viewBox="0 0 120 120" width="130" height="130" aria-label="Application stages" role="img">
              <circle cx="60" cy="60" r="46" fill="none" stroke="#E5E7EB" stroke-width="12" />
              <circle
                cx="60"
                cy="60"
                r="46"
                fill="none"
                stroke="#2563EB"
                stroke-width="12"
                stroke-linecap="round"
                :stroke-dasharray="donutCirc"
                :stroke-dashoffset="offerRateOffset"
                transform="rotate(-90 60 60)"
                style="transition: stroke-dashoffset 1s ease"
              />
            </svg>
            <div class="rq-donut-center">
              <div class="rq-donut-val">{{ offerRatePct }}%</div>
              <div class="rq-donut-sub">Offer Rate</div>
            </div>
          </div>
          <div class="rq-donut-legend">
            <div class="rq-leg-row"><span class="rq-leg-dot" style="background:#2563EB"></span><span class="rq-leg-text">Offered</span><span class="rq-leg-val">{{ analytics.offered }}</span></div>
            <div class="rq-leg-row"><span class="rq-leg-dot" style="background:#7C3AED"></span><span class="rq-leg-text">Interview</span><span class="rq-leg-val">{{ analytics.interview }}</span></div>
            <div class="rq-leg-row"><span class="rq-leg-dot" style="background:#059669"></span><span class="rq-leg-text">Shortlisted</span><span class="rq-leg-val">{{ analytics.shortlisted }}</span></div>
            <div class="rq-leg-row"><span class="rq-leg-dot" style="background:#D97706"></span><span class="rq-leg-text">Applied</span><span class="rq-leg-val">{{ analytics.applied }}</span></div>
            <div class="rq-leg-row"><span class="rq-leg-dot" style="background:#E5E7EB"></span><span class="rq-leg-text">Rejected</span><span class="rq-leg-val">{{ analytics.rejected }}</span></div>
          </div>
        </div>
      </div>

      <div class="rq-card rq-col-2">
        <div class="rq-card-hd">
          <span class="rq-card-title">Drive Performance</span>
          <button class="rq-ghost" @click="$emit('export-analytics')">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M6 1v7M3 6l3 3 3-3M1 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            Export
          </button>
        </div>
        <div class="rq-tbl-wrap">
          <table class="rq-tbl" aria-label="Drive performance">
            <thead>
              <tr>
                <th scope="col">Drive</th>
                <th scope="col">Applied</th>
                <th scope="col">Shortlisted</th>
                <th scope="col">Interviewed</th>
                <th scope="col">Offered</th>
                <th scope="col">Conv. Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="drive in myDrives" :key="drive.id">
                <td>
                  <div class="rq-entity">
                    <div class="rq-av rq-av-sm" :style="{ background: drive.avatarColor }">{{ drive.initials }}</div>
                    <span class="rq-ename">{{ drive.title }}</span>
                  </div>
                </td>
                <td class="rq-mono rq-tc">{{ drive.applicants }}</td>
                <td class="rq-mono rq-tc" style="color:var(--rq-green)">{{ stageCount(drive, 1) }}</td>
                <td class="rq-mono rq-tc" style="color:var(--rq-purple)">{{ stageCount(drive, 2) }}</td>
                <td class="rq-mono rq-tc" style="color:var(--rq-blue)">{{ stageCount(drive, 3) }}</td>
                <td>
                  <span class="rq-conv-rate" :class="convClass(stageCount(drive, 3), drive.applicants)">
                    {{ drive.applicants > 0 ? Math.round(stageCount(drive, 3) / drive.applicants * 100) : 0 }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="rq-card rq-col-full">
        <div class="rq-card-hd">
          <span class="rq-card-title">Branch-wise Applicants</span>
        </div>
        <div class="rq-card-body">
          <div class="rq-vchart">
            <div v-for="branch in branchApplicants" :key="branch.name" class="rq-vbar-col">
              <div class="rq-vbar-pct">{{ branch.count }}</div>
              <div class="rq-vbar-track">
                <div class="rq-vbar-fill" :style="{ height: pct(branch.count, maxBranchCount) + '%', background: branch.color }"></div>
              </div>
              <div class="rq-vbar-label">{{ branch.name }}</div>
              <div class="rq-vbar-frac">{{ pct(branch.count, maxBranchCount) }}%</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'AnalyticsView',
  props: {
    analytics: {
      type: Object,
      required: true
    },
    offerRatePct: {
      type: Number,
      required: true
    },
    donutCirc: {
      type: Number,
      required: true
    },
    offerRateOffset: {
      type: Number,
      required: true
    },
    myDrives: {
      type: Array,
      required: true
    },
    branchApplicants: {
      type: Array,
      required: true
    },
    maxBranchCount: {
      type: Number,
      required: true
    }
  },
  emits: ['export-analytics'],
  methods: {
    pct(value, maxValue) {
      return maxValue > 0 ? Math.round((value / maxValue) * 100) : 0
    },
    convClass(offered, total) {
      const ratio = total > 0 ? offered / total : 0
      return ratio >= 0.15 ? 'conv-hi' : ratio >= 0.08 ? 'conv-md' : 'conv-lo'
    },
    stageCount(drive, index) {
      if (!drive || !Array.isArray(drive.stages) || !drive.stages[index]) {
        return 0
      }

      return Number(drive.stages[index].count || 0)
    }
  }
}
</script>
