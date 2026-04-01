<template>
  <section class="cq-overview">
    <div class="cq-kpi-grid">
      <article v-for="card in cards" :key="card.id" class="cq-kpi-card">
        <p class="cq-kpi-label">{{ card.label }}</p>
        <p class="cq-kpi-value">{{ card.value }}</p>
        <p class="cq-kpi-sub">{{ card.sub }}</p>
      </article>
    </div>

    <div class="cq-grid">
      <article class="cq-panel">
        <header class="cq-panel-head">
          <h2>Drive Pipeline Snapshot</h2>
          <p>Phase 1 scaffold ready for live endpoint binding</p>
        </header>

        <ul class="cq-pipeline-list">
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
      </article>

      <article class="cq-panel">
        <header class="cq-panel-head">
          <h2>Priority Actions</h2>
          <p>Suggested next moves for your recruitment cycle</p>
        </header>

        <ul class="cq-action-list">
          <li v-for="action in priorityActions" :key="action.id" class="cq-action-item">
            <div>
              <p class="cq-action-title">{{ action.title }}</p>
              <p class="cq-action-desc">{{ action.description }}</p>
            </div>
            <span class="cq-state-pill">{{ action.state }}</span>
          </li>
        </ul>
      </article>

      <article class="cq-panel cq-panel-wide">
        <header class="cq-panel-head">
          <h2>Recent Applicant Signals</h2>
          <p>This list will auto-populate after company module APIs are added.</p>
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
                <td>{{ row.status }}</td>
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
