<template>
  <section class="rq-view">
    <div class="rq-analytics-grid">
      <div class="rq-card">
        <div class="rq-card-hd">
          <span class="rq-card-title">Placement Rate</span>
          <span class="rq-pill rq-pill-green">2024–25</span>
        </div>
        <div class="rq-donut-section">
          <div class="rq-donut-fig">
            <svg viewBox="0 0 120 120" width="130" height="130" aria-label="Placement rate" role="img">
              <circle cx="60" cy="60" r="46" fill="none" stroke="#E5E7EB" stroke-width="12"/>
              <circle cx="60" cy="60" r="46" fill="none" stroke="#2563EB" stroke-width="12" stroke-linecap="round" :stroke-dasharray="donutCirc" :stroke-dashoffset="donutPlacedOffset" transform="rotate(-90 60 60)"/>
            </svg>
            <div class="rq-donut-center">
              <div class="rq-donut-val">{{ placementRatePct }}%</div>
              <div class="rq-donut-sub">Placed</div>
            </div>
          </div>
          <div class="rq-donut-legend">
            <div class="rq-leg-row"><span class="rq-leg-dot" style="background:#2563EB"></span><span>Placed — {{ placedCount }}</span></div>
            <div class="rq-leg-row"><span class="rq-leg-dot" style="background:#D97706"></span><span>In Progress — {{ inProgressCount }}</span></div>
            <div class="rq-leg-row"><span class="rq-leg-dot" style="background:#E5E7EB"></span><span>Not Placed — {{ notPlacedCount }}</span></div>
          </div>
        </div>
      </div>

      <div class="rq-card rq-col-2">
        <div class="rq-card-hd">
          <span class="rq-card-title">Top Recruiting Companies</span>
          <button class="rq-ghost" @click="$emit('export', 'analytics')">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M6 1v7M3 6l3 3 3-3M1 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            Export
          </button>
        </div>
        <div class="rq-tbl-wrap">
          <table class="rq-tbl" aria-label="Top recruiters">
            <thead><tr>
              <th scope="col">#</th>
              <th scope="col">Company</th>
              <th scope="col">Drives</th>
              <th scope="col">Offers</th>
              <th scope="col">Avg Pkg</th>
              <th scope="col">Highest</th>
            </tr></thead>
            <tbody>
              <tr v-for="(co, i) in topCompanies" :key="co.name">
                <td><span class="rq-rank" :class="['gold','silver','bronze'][i] || ''">{{ i + 1 }}</span></td>
                <td>
                  <div class="rq-entity">
                    <div class="rq-av rq-av-sm" :style="{ background: co.color }">{{ co.initials }}</div>
                    <span class="rq-ename">{{ co.name }}</span>
                  </div>
                </td>
                <td class="rq-mono rq-tc">{{ co.drives }}</td>
                <td class="rq-mono rq-tc rq-green">{{ co.offers }}</td>
                <td class="rq-mono rq-tc rq-blue">{{ co.avgPkg }}</td>
                <td class="rq-mono rq-tc rq-purple">{{ co.highest }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="rq-card rq-col-full">
        <div class="rq-card-hd">
          <span class="rq-card-title">Branch-wise Placement</span>
        </div>
        <div class="rq-card-body">
          <div class="rq-vchart">
            <div v-for="b in branchStats" :key="b.name" class="rq-vbar-col">
              <div class="rq-vbar-pct">{{ pct(b.placed, b.total) }}%</div>
              <div class="rq-vbar-track">
                <div class="rq-vbar-fill" :style="{ height: pct(b.placed, b.total) + '%', background: b.color }"></div>
              </div>
              <div class="rq-vbar-label">{{ b.name }}</div>
              <div class="rq-vbar-frac">{{ b.placed }}/{{ b.total }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'AnalyticsPanel',
  props: {
    topCompanies: { type: Array, required: true },
    branchStats: { type: Array, required: true },
    placedCount: { type: Number, required: true },
    inProgressCount: { type: Number, required: true },
    notPlacedCount: { type: Number, required: true },
    placementRatePct: { type: Number, required: true },
    donutCirc: { type: Number, required: true },
    donutPlacedOffset: { type: Number, required: true },
    pct: { type: Function, required: true }
  },
  emits: ['export']
}
</script>
