<template>
  <section class="rq-view">
    <div class="rq-toolbar">
      <div class="rq-search rq-search-inline" :class="{ 'is-focused': stuSearchFocused }">
        <svg class="rq-search-ico" width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="6" cy="6" r="4.5" stroke="currentColor" stroke-width="1.5"/><path d="M9.5 9.5L12 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        <input :value="stuSearch" @input="$emit('update-stu-search', $event.target.value)" @focus="$emit('set-stu-search-focused', true)" @blur="$emit('set-stu-search-focused', false)" placeholder="Search by name, roll no, email…" class="rq-search-field" aria-label="Search students"/>
      </div>
      <div class="rq-chips">
        <button v-for="b in branchFilterOptions" :key="b" class="rq-chip-btn" :class="{ on: stuBranch === (b === 'All' ? '' : b) }" @click="$emit('update-stu-branch', b === 'All' ? '' : b)">{{ b }}</button>
      </div>
      <div class="rq-table-tools">
        <select class="rq-sel" :disabled="isLoading" :value="stuSortBy" @change="$emit('update-stu-sort-by', $event.target.value)" aria-label="Sort students">
          <option value="created_at">Newest</option>
          <option value="roll_number">Roll</option>
          <option value="branch">Branch</option>
          <option value="year">Year</option>
          <option value="cgpa">CGPA</option>
        </select>
        <button class="rq-ghost rq-ghost-xs" :disabled="isLoading" @click="$emit('toggle-stu-order')">{{ stuOrder === 'asc' ? 'Asc' : 'Desc' }}</button>
      </div>
      <div style="flex: 1"></div>
      <div class="rq-pager">
        <button class="rq-ghost rq-ghost-xs" @click="$emit('prev-stu-page')" :disabled="isLoading || stuPage <= 1">Prev</button>
        <span class="rq-pager-info">Page {{ stuPage }} / {{ Math.max(stuPages, 1) }} · {{ stuTotal }}</span>
        <button class="rq-ghost rq-ghost-xs" @click="$emit('next-stu-page')" :disabled="isLoading || stuPage >= stuPages">Next</button>
      </div>
      <button class="rq-ghost" :disabled="isLoading || isExportBusy" @click="$emit('export', 'students')">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M6 1v7M3 6l3 3 3-3M1 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        {{ exportLabel }}
      </button>
    </div>

    <div v-if="errorMessage" class="rq-state rq-state-error">
      <span>{{ errorMessage }}</span>
      <button class="rq-ghost rq-ghost-xs" @click="$emit('retry')" :disabled="isLoading">Retry</button>
    </div>

    <div class="rq-card">
      <div class="rq-tbl-wrap">
        <table class="rq-tbl" aria-label="Students">
          <thead><tr>
            <th scope="col">Student</th>
            <th scope="col">Roll No</th>
            <th scope="col">Branch/Yr</th>
            <th scope="col">CGPA</th>
            <th scope="col">Applications</th>
            <th scope="col">Status</th>
            <th scope="col">Actions</th>
          </tr></thead>
          <tbody>
            <template v-if="isLoading && !filteredStudents.length">
              <tr v-for="n in 5" :key="`stu-skeleton-${n}`" class="rq-skeleton-row-wrap">
                <td colspan="7">
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
              <tr v-for="s in filteredStudents" :key="s.id">
                <td>
                  <div class="rq-entity">
                    <div class="rq-av rq-av-md" :style="{ background: s.color }">{{ s.initials }}</div>
                    <div><div class="rq-ename">{{ s.name }}</div><div class="rq-esub">{{ s.email }}</div></div>
                  </div>
                </td>
                <td class="rq-mono rq-sm rq-dim">{{ s.roll }}</td>
                <td class="rq-sm rq-dim">{{ s.branch }} · Y{{ s.year }}</td>
                <td><span class="rq-cgpa" :class="s.cgpa >= 8.5 ? 'cgpa-hi' : s.cgpa >= 7 ? 'cgpa-md' : 'cgpa-lo'">{{ s.cgpa }}</span></td>
                <td class="rq-mono rq-tc"><button class="rq-link" :disabled="isLoading" @click="$emit('show-student-apps', s)">{{ s.applications }} apps</button></td>
                <td><span class="rq-status-pill" :class="'pill-' + s.status">{{ s.status }}</span></td>
                <td>
                  <div class="rq-acts">
                    <button v-if="s.status !== 'blacklisted'" class="rq-btn-warn" :disabled="isRowBusy(s.id)" @click="$emit('change-status', s, 'blacklisted')">
                      <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><circle cx="5.5" cy="5.5" r="4.5" stroke="currentColor" stroke-width="1.4"/><path d="M2 2l7 7" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                      Blacklist
                    </button>
                    <button v-else class="rq-ghost rq-ghost-xs" :disabled="isRowBusy(s.id)" @click="$emit('change-status', s, 'active')">↩ Restore</button>
                  </div>
                </td>
              </tr>
              <tr v-if="!filteredStudents.length"><td colspan="7">
                <div class="rq-empty"><div class="rq-empty-ico">👨‍🎓</div><b>No students found</b><span>Adjust search or branch filter.</span></div>
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
  name: 'StudentsTable',
  props: {
    filteredStudents: { type: Array, required: true },
    stuSearch: { type: String, required: true },
    stuSearchFocused: { type: Boolean, required: true },
    stuBranch: { type: String, required: true },
    branchFilterOptions: { type: Array, required: true },
    stuPage: { type: Number, required: true },
    stuPages: { type: Number, required: true },
    stuTotal: { type: Number, required: true },
    stuSortBy: { type: String, required: true },
    stuOrder: { type: String, required: true },
    isLoading: { type: Boolean, default: false },
    errorMessage: { type: String, default: '' },
    pendingStudentActions: { type: Object, default: () => ({}) },
    isExportBusy: { type: Boolean, default: false },
    exportLabel: { type: String, default: 'Export CSV' }
  },
  emits: [
    'update-stu-search',
    'set-stu-search-focused',
    'update-stu-branch',
    'update-stu-sort-by',
    'toggle-stu-order',
    'set-stu-page',
    'prev-stu-page',
    'next-stu-page',
    'retry',
    'export',
    'show-student-apps',
    'change-status'
  ],
  methods: {
    isRowBusy(studentId) {
      return this.isLoading || !!this.pendingStudentActions[studentId]
    }
  }
}
</script>
