<template>
  <section class="rq-view">
    <div class="rq-toolbar">
      <div class="rq-search rq-search-inline" :class="{ 'is-focused': coSearchFocused }">
        <svg class="rq-search-ico" width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="6" cy="6" r="4.5" stroke="currentColor" stroke-width="1.5"/><path d="M9.5 9.5L12 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        <input :value="coSearch" @input="$emit('update-co-search', $event.target.value)" @focus="$emit('set-co-search-focused', true)" @blur="$emit('set-co-search-focused', false)" placeholder="Search companies, industry…" class="rq-search-field" aria-label="Search companies"/>
      </div>
      <div class="rq-chips">
        <button v-for="f in coFilters" :key="f.v" class="rq-chip-btn" :class="{ on: coFilter === f.v }" @click="$emit('update-co-filter', f.v)">{{ f.l }}</button>
      </div>
      <div class="rq-table-tools">
        <select class="rq-sel" :disabled="isLoading" :value="coSortBy" @change="$emit('update-co-sort-by', $event.target.value)" aria-label="Sort companies">
          <option value="created_at">Newest</option>
          <option value="company_name">Name</option>
          <option value="approval_status">Status</option>
          <option value="industry">Industry</option>
        </select>
        <button class="rq-ghost rq-ghost-xs" :disabled="isLoading" @click="$emit('toggle-co-order')">{{ coOrder === 'asc' ? 'Asc' : 'Desc' }}</button>
      </div>
      <div style="flex: 1"></div>
      <div class="rq-pager">
        <button class="rq-ghost rq-ghost-xs" @click="$emit('prev-co-page')" :disabled="isLoading || coPage <= 1">Prev</button>
        <span class="rq-pager-info">Page {{ coPage }} / {{ Math.max(coPages, 1) }} · {{ coTotal }}</span>
        <button class="rq-ghost rq-ghost-xs" @click="$emit('next-co-page')" :disabled="isLoading || coPage >= coPages">Next</button>
      </div>
    </div>

    <div v-if="errorMessage" class="rq-state rq-state-error">
      <span>{{ errorMessage }}</span>
      <button class="rq-ghost rq-ghost-xs" @click="$emit('retry')" :disabled="isLoading">Retry</button>
    </div>

    <div class="rq-card">
      <div class="rq-tbl-wrap">
        <table class="rq-tbl" aria-label="Companies">
          <thead><tr>
            <th scope="col">Company</th>
            <th scope="col">HR Contact</th>
            <th scope="col">Drives</th>
            <th scope="col">Applicants</th>
            <th scope="col">Status</th>
            <th scope="col">Actions</th>
          </tr></thead>
          <tbody>
            <template v-if="isLoading && !filteredCompanies.length">
              <tr v-for="n in 5" :key="`co-skeleton-${n}`" class="rq-skeleton-row-wrap">
                <td colspan="6">
                  <div class="rq-skeleton-row">
                    <span class="rq-skeleton rq-skeleton-avatar"></span>
                    <span class="rq-skeleton rq-skeleton-line rq-skeleton-cell-lg"></span>
                    <span class="rq-skeleton rq-skeleton-line rq-skeleton-cell-sm"></span>
                    <span class="rq-skeleton rq-skeleton-line rq-skeleton-cell-sm"></span>
                  </div>
                </td>
              </tr>
            </template>
            <template v-else>
              <tr v-for="co in filteredCompanies" :key="co.id">
                <td>
                  <div class="rq-entity">
                    <div class="rq-av rq-av-md" :style="{ background: co.color }">{{ co.initials }}</div>
                    <div><div class="rq-ename">{{ co.name }}</div><div class="rq-esub">{{ co.domain }}</div></div>
                  </div>
                </td>
                <td class="rq-sm rq-dim rq-mono">{{ co.hr }}</td>
                <td class="rq-mono rq-tc">{{ co.drives }}</td>
                <td class="rq-mono rq-tc">{{ co.applicants }}</td>
                <td><span class="rq-status-pill" :class="'pill-' + co.status">{{ co.status }}</span></td>
                <td>
                  <div class="rq-acts">
                    <template v-if="co.status === 'pending'">
                      <button class="rq-btn-ok" :disabled="isRowBusy(co.id)" @click="$emit('change-status', co, 'approved')">
                        <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M1.5 5.5l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                        Approve
                      </button>
                      <button class="rq-btn-no" :disabled="isRowBusy(co.id)" @click="$emit('change-status', co, 'rejected')">
                        <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M2 2l7 7M9 2l-7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
                        Reject
                      </button>
                    </template>
                    <button v-if="co.status !== 'blacklisted'" class="rq-btn-warn" :disabled="isRowBusy(co.id)" @click="$emit('change-status', co, 'blacklisted')" title="Blacklist company">
                      <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><circle cx="5.5" cy="5.5" r="4.5" stroke="currentColor" stroke-width="1.4"/><path d="M2 2l7 7" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                      Blacklist
                    </button>
                    <button v-else class="rq-ghost rq-ghost-xs" :disabled="isRowBusy(co.id)" @click="$emit('change-status', co, 'approved')">↩ Restore</button>
                  </div>
                </td>
              </tr>
              <tr v-if="!filteredCompanies.length"><td colspan="6">
                <div class="rq-empty"><div class="rq-empty-ico">🏢</div><b>No companies found</b><span>Try a different filter.</span></div>
              </td></tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'CompaniesTable',
  props: {
    filteredCompanies: { type: Array, required: true },
    coSearch: { type: String, required: true },
    coSearchFocused: { type: Boolean, required: true },
    coFilters: { type: Array, required: true },
    coFilter: { type: String, required: true },
    coPage: { type: Number, required: true },
    coPages: { type: Number, required: true },
    coTotal: { type: Number, required: true },
    coSortBy: { type: String, required: true },
    coOrder: { type: String, required: true },
    isLoading: { type: Boolean, default: false },
    errorMessage: { type: String, default: '' },
    pendingCompanyActions: { type: Object, default: () => ({}) }
  },
  emits: [
    'update-co-search',
    'set-co-search-focused',
    'update-co-filter',
    'update-co-sort-by',
    'toggle-co-order',
    'set-co-page',
    'prev-co-page',
    'next-co-page',
    'retry',
    'change-status'
  ],
  methods: {
    isRowBusy(companyId) {
      return this.isLoading || !!this.pendingCompanyActions[companyId]
    }
  }
}
</script>
