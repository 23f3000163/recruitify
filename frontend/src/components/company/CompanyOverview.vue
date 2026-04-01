<template>
  <section class="cq-overview">
    <div class="cq-kpi-grid">
      <template v-if="cards.length">
        <article v-for="card in cards" :key="card.id" class="cq-kpi-card">
          <p class="cq-kpi-label">{{ card.label }}</p>
          <p class="cq-kpi-value">{{ card.value }}</p>
          <p class="cq-kpi-sub">{{ card.sub }}</p>
        </article>
      </template>
      <article v-else class="cq-kpi-card is-empty">
        <p class="cq-kpi-label">No KPI Data</p>
        <p class="cq-kpi-value">--</p>
        <p class="cq-kpi-sub">Summary metrics will appear once dashboard data is available.</p>
      </article>
    </div>

    <div class="cq-grid">
      <article class="cq-panel">
        <header class="cq-panel-head">
          <h2>Drive Pipeline Snapshot</h2>
          <p>Live distribution of candidates moving through each recruitment stage.</p>
        </header>

        <ul class="cq-pipeline-list" v-if="pipelineStages.length">
          <li v-for="stage in pipelineStages" :key="stage.id" class="cq-pipeline-item">
            <div class="cq-pipeline-meta">
              <span>{{ stage.label }}</span>
              <strong>{{ stage.count }}</strong>
            </div>
            <div class="cq-meter">
              <span class="cq-meter-bar" :style="{ width: stage.percent + '%'}"></span>
            </div>
          </li>
        </ul>
        <p v-else class="cq-empty">No pipeline analytics available right now.</p>
      </article>

      <article class="cq-panel">
        <header class="cq-panel-head">
          <h2>Priority Actions</h2>
          <p>Suggested next moves for your recruitment cycle</p>
        </header>

        <ul class="cq-action-list" v-if="priorityActions.length">
          <li v-for="action in priorityActions" :key="action.id" class="cq-action-item">
            <div>
              <p class="cq-action-title">{{ action.title }}</p>
              <p class="cq-action-desc">{{ action.description }}</p>
            </div>
            <span class="cq-state-pill">{{ action.state }}</span>
          </li>
        </ul>
        <p v-else class="cq-empty">No priority notifications at the moment.</p>
      </article>

      <article class="cq-panel cq-panel-wide">
        <header class="cq-panel-head">
          <h2>Recent Applicant Signals</h2>
          <p>Most recent application movements across your active placement drives.</p>
        </header>

        <div v-if="recentApplicants.length" class="cq-table-wrap">
          <table class="cq-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Role</th>
                <th>Status</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in recentApplicants" :key="row.id">
                <td>{{ row.name }}</td>
                <td>{{ row.role }}</td>
                <td>
                  <span class="cq-status-pill is-applied" :aria-label="`Applicant status ${row.status}`">{{ row.status }}</span>
                </td>
                <td>{{ row.updatedAt }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="cq-empty">No applicant signals yet. Create and publish your first drive to begin tracking pipeline movement.</p>
      </article>
    </div>
  </section>
</template>

<script>
export default {
  name: 'CompanyOverview',
  props: {
    cards: {
      type: Array,
      default: () => []
    },
    pipelineStages: {
      type: Array,
      default: () => []
    },
    priorityActions: {
      type: Array,
      default: () => []
    },
    recentApplicants: {
      type: Array,
      default: () => []
    }
  }
}
</script>
