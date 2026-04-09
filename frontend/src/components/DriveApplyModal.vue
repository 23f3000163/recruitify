<template>
  <Transition name="rq-modal">
    <div
      v-if="show && drive"
      class="rq-modal-overlay rq-drive-apply-overlay"
      role="dialog"
      aria-modal="true"
      :aria-label="profileComplete ? `${roleLabel} at ${companyLabel}` : 'Complete your profile'"
      @click.self="$emit('close')"
    >
      <div v-if="profileComplete" class="rq-modal rq-drive-apply-modal">
        <div class="rq-modal-hd rq-drive-modal-hd">
          <div class="rq-drive-head">
            <div class="rq-drive-avatar" :style="{ background: avatarColor }">{{ avatarInitials }}</div>
            <div>
              <p class="rq-drive-overline">Drive Details</p>
              <h2 class="rq-drive-title">{{ roleLabel }}</h2>
              <p class="rq-drive-subtitle">{{ companyLabel }}</p>
            </div>
          </div>

          <button class="rq-modal-close" type="button" aria-label="Close" @click="$emit('close')">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            </svg>
          </button>
        </div>

        <div class="rq-drive-chip-row">
          <span v-for="chip in chipRows" :key="chip.key" class="rq-drive-chip" :class="chip.variant">
            <span class="rq-drive-chip-icon" aria-hidden="true">{{ chip.icon }}</span>
            {{ chip.label }}
          </span>
        </div>

        <div class="rq-modal-body rq-drive-modal-body">
          <div class="rq-modal-section">
            <span class="rq-modal-sec-label">About the Role</span>
            <p class="rq-modal-desc">{{ driveDescription }}</p>
          </div>

          <div class="rq-eligibility-row">
            <div class="rq-eligibility-item" :class="eligCgpa ? 'elig-pass' : 'elig-fail'">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" stroke-width="1.4" />
                <path
                  v-if="eligCgpa"
                  d="M4 6.5l2 2 3-3"
                  stroke="currentColor"
                  stroke-width="1.4"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  v-else
                  d="M4.5 4.5l4 4M8.5 4.5l-4 4"
                  stroke="currentColor"
                  stroke-width="1.4"
                  stroke-linecap="round"
                />
              </svg>
              <span>{{ cgpaCheckLabel }}</span>
            </div>

            <div class="rq-eligibility-item" :class="eligBranch ? 'elig-pass' : 'elig-fail'">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" stroke-width="1.4" />
                <path
                  v-if="eligBranch"
                  d="M4 6.5l2 2 3-3"
                  stroke="currentColor"
                  stroke-width="1.4"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  v-else
                  d="M4.5 4.5l4 4M8.5 4.5l-4 4"
                  stroke="currentColor"
                  stroke-width="1.4"
                  stroke-linecap="round"
                />
              </svg>
              <span>{{ branchCheckLabel }}</span>
            </div>

            <div class="rq-eligibility-item" :class="eligYear ? 'elig-pass' : 'elig-fail'">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" stroke-width="1.4" />
                <path
                  v-if="eligYear"
                  d="M4 6.5l2 2 3-3"
                  stroke="currentColor"
                  stroke-width="1.4"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  v-else
                  d="M4.5 4.5l4 4M8.5 4.5l-4 4"
                  stroke="currentColor"
                  stroke-width="1.4"
                  stroke-linecap="round"
                />
              </svg>
              <span>{{ yearCheckLabel }}</span>
            </div>

            <div class="rq-eligibility-item" :class="alreadyApplied ? 'elig-pass' : 'elig-pass'">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" stroke-width="1.4" />
                <path d="M4 6.5l2 2 3-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span>{{ alreadyApplied ? 'Application already submitted' : 'Profile checks passed' }}</span>
            </div>
          </div>

          <div class="rq-modal-section">
            <span class="rq-modal-sec-label">Selection Process</span>
            <div class="rq-process-track">
              <div v-for="(step, index) in processSteps" :key="`${step}-${index}`" class="rq-process-step">
                <div class="rq-process-node">{{ index + 1 }}</div>
                <span class="rq-process-label">{{ step }}</span>
                <svg
                  v-if="index < processSteps.length - 1"
                  class="rq-process-arrow"
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  aria-hidden="true"
                >
                  <path d="M3.5 7h7M8 4.5L10.5 7 8 9.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div class="rq-modal-ft rq-drive-modal-ft">
          <span class="rq-drive-deadline">Closes {{ deadlineLabel }}</span>
          <div class="rq-drive-actions">
            <button class="rq-ghost" type="button" @click="$emit('close')">Close</button>
            <button
              class="rq-btn-primary rq-btn-drive-apply"
              :class="{
                'is-applied': alreadyApplied,
                'is-disabled': !isEligible
              }"
              type="button"
              :disabled="alreadyApplied || !isEligible"
              @click="onApply"
            >
              {{ applyButtonLabel }}
            </button>
          </div>
        </div>
      </div>

      <div v-else class="rq-modal rq-drive-gate-modal">
        <button class="rq-modal-close rq-drive-gate-close" type="button" aria-label="Close" @click="$emit('close')">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
          </svg>
        </button>

        <div class="rq-gate-visual" aria-hidden="true">
          <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="40" cy="40" r="38" fill="#F7F4EE" stroke="#EDE9E0" stroke-width="1.5" />
            <rect x="22" y="26" width="36" height="34" rx="4" fill="white" stroke="#EDE9E0" stroke-width="1.5" />
            <rect x="32" y="22" width="16" height="8" rx="3" fill="white" stroke="#EDE9E0" stroke-width="1.5" />
            <path d="M30 36h8" stroke="#EDE9E0" stroke-width="1.8" stroke-linecap="round" />
            <circle cx="27" cy="36" r="2.5" fill="#059669" opacity="0.9" />
            <path d="M25.5 36l1.2 1.2 2-2" stroke="white" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M30 43h8" stroke="#EDE9E0" stroke-width="1.8" stroke-linecap="round" />
            <circle cx="27" cy="43" r="2.5" fill="#059669" opacity="0.9" />
            <path d="M25.5 43l1.2 1.2 2-2" stroke="white" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M30 50h14" stroke="#EDE9E0" stroke-width="1.8" stroke-linecap="round" />
            <circle cx="27" cy="50" r="2.5" fill="#EDE9E0" stroke="#D97706" stroke-width="1.5" />
            <circle cx="56" cy="24" r="10" fill="#D97706" />
            <path d="M56 20v5M56 27v1" stroke="white" stroke-width="2" stroke-linecap="round" />
          </svg>
        </div>

        <div class="rq-gate-text">
          <h2 class="rq-gate-title">Profile Incomplete</h2>
          <p class="rq-gate-subtitle">
            You need a complete profile before applying to placement drives.
            Recruiters review your details, so please complete all required fields.
          </p>
        </div>

        <div class="rq-gate-checklist">
          <div
            v-for="item in profileChecklist"
            :key="item.label"
            class="rq-gate-check-row"
            :class="item.done ? 'is-done' : 'is-pending'"
          >
            <span class="rq-gate-check-label">{{ item.label }}</span>
            <span class="rq-gate-check-pill" :class="item.done ? 'done' : 'required'">
              {{ item.done ? 'Done' : 'Required' }}
            </span>
          </div>
        </div>

        <div class="rq-gate-context">
          <div class="rq-drive-avatar rq-drive-avatar-sm" :style="{ background: avatarColor }">{{ avatarInitials }}</div>
          <div class="rq-gate-context-body">
            <span class="rq-gate-context-label">Applying to</span>
            <span class="rq-gate-context-name">{{ roleLabel }} · {{ companyLabel }}</span>
          </div>
          <span class="rq-dc">{{ chipRows[0]?.label || '-' }}</span>
        </div>

        <div class="rq-modal-ft rq-drive-gate-ft">
          <button class="rq-ghost" type="button" @click="$emit('close')">Maybe Later</button>
          <button class="rq-btn-primary" type="button" @click="$emit('navigate-profile')">View Profile Now</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script>
const FALLBACK_PROCESS_STEPS = ['Online Test', 'Technical Interview', 'HR Round']

export default {
  name: 'DriveApplyModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    drive: {
      type: Object,
      default: null
    },
    student: {
      type: Object,
      default: () => ({})
    },
    profileComplete: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'apply', 'navigate-profile'],
  computed: {
    driveId() {
      return Number(this.drive?.drive_id || this.drive?.id || 0)
    },
    roleLabel() {
      return this.drive?.job_title || this.drive?.title || this.drive?.role || 'Role unavailable'
    },
    companyLabel() {
      return (
        this.drive?.company?.name ||
        this.drive?.company?.company_name ||
        this.drive?.company_name ||
        this.drive?.company ||
        '-'
      )
    },
    avatarInitials() {
      const company = String(this.companyLabel || '').trim()
      if (!company || company === '-') return 'D'
      const chunks = company.split(/\s+/).filter(Boolean)
      if (chunks.length === 1) return (chunks[0][0] || 'D').toUpperCase()
      return `${chunks[0][0] || ''}${chunks[1][0] || ''}`.toUpperCase()
    },
    avatarColor() {
      const palette = ['#2563EB', '#059669', '#D97706', '#7C3AED', '#EF4444']
      const seed = this.driveId || this.companyLabel.length
      return palette[Math.abs(seed) % palette.length]
    },
    minCgpa() {
      const direct = this.toNumber(this.drive?.min_cgpa)
      if (direct > 0) return direct
      const alt = this.toNumber(this.drive?.minCgpa)
      if (alt > 0) return alt
      return this.toNumber(this.drive?.required_cgpa)
    },
    studentCgpa() {
      return this.toNumber(this.student?.cgpa)
    },
    eligibleBranches() {
      const branchList = this.drive?.eligible_branches || this.drive?.eligibleBranches || this.drive?.branches
      if (Array.isArray(branchList)) {
        return branchList
          .map((item) => String(item || '').trim().toUpperCase())
          .filter(Boolean)
      }

      if (typeof branchList === 'string' && branchList.trim()) {
        return branchList
          .split(',')
          .map((item) => item.trim().toUpperCase())
          .filter(Boolean)
      }

      if (typeof this.drive?.branchLabel === 'string' && this.drive.branchLabel !== '-') {
        return this.drive.branchLabel
          .split(',')
          .map((item) => item.trim().toUpperCase())
          .filter(Boolean)
      }

      return []
    },
    studentBranch() {
      return String(this.student?.branch || '').trim().toUpperCase()
    },
    eligibleYears() {
      const yearList = this.drive?.eligible_years || this.drive?.eligibleYears
      if (Array.isArray(yearList)) {
        return yearList
          .map((item) => Number(item))
          .filter((item) => Number.isInteger(item) && item > 0)
      }

      if (typeof this.drive?.yearLabel === 'string') {
        const extracted = this.drive.yearLabel.match(/\d+/g) || []
        return extracted
          .map((item) => Number(item))
          .filter((item) => Number.isInteger(item) && item > 0)
      }

      return []
    },
    requiredSkillsList() {
      const skillSource = this.drive?.required_skills || this.drive?.requiredSkills
      const entries = Array.isArray(skillSource)
        ? skillSource
        : String(skillSource || '').split(',')

      return [...new Set(entries
        .map((item) => String(item || '').trim())
        .filter(Boolean))]
    },
    studentYear() {
      const parsed = Number(this.student?.year)
      if (!Number.isInteger(parsed) || parsed <= 0) {
        return 0
      }
      return parsed
    },
    eligCgpa() {
      if (this.minCgpa <= 0 || this.studentCgpa <= 0) {
        return true
      }
      return this.studentCgpa >= this.minCgpa
    },
    eligBranch() {
      if (!this.eligibleBranches.length || !this.studentBranch) {
        return true
      }
      return this.eligibleBranches.includes(this.studentBranch)
    },
    eligYear() {
      if (!this.eligibleYears.length || !this.studentYear) {
        return true
      }
      return this.eligibleYears.includes(this.studentYear)
    },
    isOpen() {
      if (this.drive?.is_open === false || this.drive?.isOpen === false) {
        return false
      }
      return true
    },
    alreadyApplied() {
      return Boolean(this.drive?.already_applied || this.drive?.applied)
    },
    isEligible() {
      if (!this.isOpen) return false
      if (this.drive?.is_eligible === false || this.drive?.isEligible === false) return false
      return this.eligCgpa && this.eligBranch && this.eligYear
    },
    applyButtonLabel() {
      if (this.alreadyApplied) return 'Applied'
      if (!this.isOpen) return 'Closed'
      if (!this.isEligible) return 'Not Eligible'
      return 'Apply Now'
    },
    cgpaCheckLabel() {
      if (this.minCgpa <= 0) {
        return `CGPA ${this.studentCgpa || '-'} meets drive criteria`
      }
      if (this.eligCgpa) {
        return `CGPA ${this.studentCgpa} ≥ required ${this.minCgpa}`
      }
      return `CGPA ${this.studentCgpa || '-'} < required ${this.minCgpa}`
    },
    branchCheckLabel() {
      if (!this.eligibleBranches.length) {
        return `${this.studentBranch || 'Branch'} eligible`
      }
      if (this.eligBranch) {
        return `${this.studentBranch || 'Branch'} eligible`
      }
      return `${this.studentBranch || 'Branch'} not eligible`
    },
    yearCheckLabel() {
      if (!this.eligibleYears.length) {
        return `Year ${this.studentYear || '-'} eligible`
      }
      if (!this.studentYear) {
        return `Required year: ${this.eligibleYears.join(', ')}`
      }
      if (this.eligYear) {
        return `Year ${this.studentYear} eligible`
      }
      return `Year ${this.studentYear} not in ${this.eligibleYears.join(', ')}`
    },
    driveDescription() {
      return (
        this.drive?.description ||
        this.drive?.job_description ||
        this.drive?.summary ||
        'Review the role details, eligibility, and process before applying.'
      )
    },
    processSteps() {
      if (Array.isArray(this.drive?.process) && this.drive.process.length) {
        return this.drive.process
      }
      return FALLBACK_PROCESS_STEPS
    },
    deadlineLabel() {
      return this.formatDeadline(this.drive?.application_deadline || this.drive?.deadline)
    },
    chipRows() {
      const branchLabel =
        this.drive?.branchLabel ||
        (this.eligibleBranches.length ? this.eligibleBranches.slice(0, 2).join(', ') : '-')
      const cgpaLabel =
        this.drive?.cgpaLabel ||
        (this.minCgpa > 0 ? `CGPA ${this.minCgpa}+` : 'CGPA -')
      const yearLabel =
        this.drive?.yearLabel ||
        this.formatYears(this.eligibleYears)
      const skillsLabel =
        this.drive?.skillsLabel ||
        this.formatSkills(this.requiredSkillsList)
      const salaryLabel =
        this.drive?.salary ||
        this.formatSalary(this.drive?.salary_lpa)

      return [
        { key: 'salary', icon: '💰', label: salaryLabel, variant: 'chip-salary' },
        { key: 'branch', icon: '🎓', label: branchLabel || '-', variant: 'chip-branch' },
        { key: 'cgpa', icon: '📊', label: cgpaLabel, variant: 'chip-cgpa' },
        { key: 'year', icon: '📚', label: yearLabel, variant: 'chip-year' },
        { key: 'skills', icon: '🛠️', label: skillsLabel, variant: 'chip-skill' },
        { key: 'deadline', icon: '📅', label: this.deadlineLabel, variant: 'chip-deadline' }
      ]
    },
    profileChecklist() {
      return [
        { label: 'Full name', done: Boolean(String(this.student?.full_name || '').trim()) },
        { label: 'Email address', done: Boolean(String(this.student?.email || '').trim()) },
        { label: 'Phone number', done: Boolean(String(this.student?.phone || '').trim()) },
        { label: 'Branch', done: Boolean(String(this.student?.branch || '').trim()) },
        { label: 'CGPA', done: Boolean(String(this.student?.cgpa || '').trim()) },
        { label: 'Resume URL', done: Boolean(String(this.student?.resume_url || '').trim()) }
      ]
    }
  },
  methods: {
    toNumber(value) {
      const parsed = Number(value)
      return Number.isNaN(parsed) ? 0 : parsed
    },
    formatSalary(value) {
      const parsed = Number(value)
      if (Number.isNaN(parsed) || parsed <= 0) return '-'
      return `₹${parsed.toLocaleString('en-IN')} LPA`
    },
    formatDeadline(value) {
      if (!value || value === '-') return '-'
      const parsed = new Date(value)
      if (Number.isNaN(parsed.getTime())) {
        return String(value)
      }
      return parsed.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric'
      })
    },
    formatYears(values) {
      const years = Array.isArray(values)
        ? values
            .map((item) => Number(item))
            .filter((item) => Number.isInteger(item) && item > 0)
        : []

      if (!years.length) {
        return 'Year -'
      }

      return `Year ${years.join(', ')}`
    },
    formatSkills(values) {
      const skills = Array.isArray(values)
        ? values
            .map((item) => String(item || '').trim())
            .filter(Boolean)
        : []

      if (!skills.length) {
        return 'Skills -'
      }

      if (skills.length <= 2) {
        return skills.join(', ')
      }

      return `${skills.slice(0, 2).join(', ')} +${skills.length - 2}`
    },
    onApply() {
      if (!this.driveId || this.alreadyApplied || !this.isEligible) {
        return
      }

      this.$emit('apply', this.driveId)
      this.$emit('close')
    }
  }
}
</script>

<style scoped>
.rq-drive-apply-overlay {
  backdrop-filter: blur(5px);
}

.rq-drive-apply-modal {
  width: min(560px, 100%);
}

.rq-drive-modal-hd {
  border-bottom: 0;
  padding-bottom: 8px;
}

.rq-drive-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rq-drive-avatar {
  width: 42px;
  height: 42px;
  border-radius: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 0.92rem;
  font-weight: 800;
  flex-shrink: 0;
}

.rq-drive-avatar-sm {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  font-size: 0.72rem;
}

.rq-drive-title {
  font-size: 1rem;
  line-height: 1.2;
  font-weight: 800;
  color: var(--rq-ink);
}

.rq-drive-overline {
  font-size: 0.62rem;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--rq-t4);
  font-weight: 800;
  margin-bottom: 2px;
}

.rq-drive-subtitle {
  margin-top: 2px;
  font-size: 0.76rem;
  color: var(--rq-t3);
  font-weight: 600;
}

.rq-drive-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 16px 8px;
  margin-top: 4px;
  border-top: 1px solid var(--rq-border2);
}

.rq-drive-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--rq-border2);
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--rq-t2);
  background: var(--rq-parch);
}

.rq-drive-chip-icon {
  font-size: 0.74rem;
}

.chip-salary {
  background: #ECFDF5;
  color: #065F46;
  border-color: rgba(5, 150, 105, 0.2);
}

.chip-cgpa {
  background: #EFF6FF;
  color: #1E40AF;
  border-color: rgba(37, 99, 235, 0.2);
}

.chip-year {
  background: #EEF2FF;
  color: #1E3A8A;
  border-color: rgba(79, 70, 229, 0.22);
}

.chip-skill {
  background: #FFF7ED;
  color: #9A3412;
  border-color: rgba(234, 88, 12, 0.25);
}

.chip-deadline {
  background: #FFFBEB;
  color: #92400E;
  border-color: rgba(217, 119, 6, 0.2);
}

.rq-drive-modal-body {
  gap: 14px;
}

.rq-modal-section {
  display: grid;
  gap: 8px;
}

.rq-modal-sec-label {
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--rq-t4);
}

.rq-modal-desc {
  font-size: 0.8rem;
  line-height: 1.65;
  color: var(--rq-t2);
}

.rq-eligibility-row {
  border: 1px solid var(--rq-border2);
  border-radius: 8px;
  background: var(--rq-parch);
  padding: 10px;
  display: grid;
  gap: 7px;
}

.rq-eligibility-item {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 0.74rem;
  font-weight: 600;
}

.elig-pass {
  color: var(--rq-green);
}

.elig-fail {
  color: #B91C1C;
}

.rq-process-track {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.rq-process-step {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.rq-process-node {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--rq-blue);
  color: #fff;
  font-size: 0.62rem;
  font-weight: 800;
}

.rq-process-label {
  font-size: 0.74rem;
  color: var(--rq-t2);
  font-weight: 600;
}

.rq-process-arrow {
  color: var(--rq-t4);
}

.rq-drive-modal-ft {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rq-drive-deadline {
  font-size: 0.7rem;
  color: var(--rq-t4);
  font-family: var(--rq-mono);
}

.rq-drive-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.rq-btn-drive-apply.is-applied {
  background: var(--rq-green);
}

.rq-btn-drive-apply.is-disabled {
  background: var(--rq-t4);
  border-color: var(--rq-t4);
  opacity: 0.75;
}

.rq-drive-gate-modal {
  width: min(430px, 100%);
  position: relative;
}

.rq-drive-gate-close {
  position: absolute;
  top: 12px;
  right: 12px;
}

.rq-gate-visual {
  display: flex;
  justify-content: center;
  padding: 28px 20px 10px;
}

.rq-gate-text {
  text-align: center;
  display: grid;
  gap: 8px;
  padding: 0 22px 14px;
}

.rq-gate-title {
  font-size: 1.15rem;
  font-weight: 700;
  font-family: var(--rq-serif);
  color: var(--rq-ink);
}

.rq-gate-subtitle {
  font-size: 0.78rem;
  line-height: 1.6;
  color: var(--rq-t3);
}

.rq-gate-checklist {
  margin: 0 16px 14px;
  border: 1px solid var(--rq-border2);
  border-radius: 8px;
  overflow: hidden;
}

.rq-gate-check-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--rq-border2);
}

.rq-gate-check-row:last-child {
  border-bottom: 0;
}

.rq-gate-check-row.is-pending {
  background: #FFFBEB;
}

.rq-gate-check-label {
  flex: 1;
  font-size: 0.76rem;
  color: var(--rq-t2);
  font-weight: 600;
}

.rq-gate-check-pill {
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-radius: 999px;
  padding: 2px 7px;
}

.rq-gate-check-pill.required {
  background: #FFFBEB;
  color: #B45309;
  border: 1px solid #FCD34D;
}

.rq-gate-check-pill.done {
  background: #ECFDF5;
  color: #047857;
  border: 1px solid #86EFAC;
}

.rq-gate-context {
  margin: 0 16px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid var(--rq-border2);
  border-radius: 8px;
  background: var(--rq-parch);
  padding: 9px 10px;
}

.rq-gate-context-body {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 1px;
}

.rq-gate-context-label {
  font-size: 0.62rem;
  color: var(--rq-t4);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.rq-gate-context-name {
  font-size: 0.75rem;
  color: var(--rq-ink);
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rq-dc {
  font-size: 0.62rem;
  font-weight: 700;
  color: var(--rq-t2);
  background: var(--rq-white);
  border: 1px solid var(--rq-border2);
  border-radius: 999px;
  padding: 2px 8px;
}

.rq-drive-gate-ft {
  justify-content: flex-end;
}

@media (max-width: 680px) {
  .rq-drive-modal-ft {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .rq-drive-actions {
    width: 100%;
  }

  .rq-drive-actions .rq-ghost,
  .rq-drive-actions .rq-btn-primary {
    flex: 1;
    justify-content: center;
  }
}
</style>
