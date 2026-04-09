<template>
  <div class="rq-modal-overlay" @click.self="$emit('close')" role="dialog" aria-modal="true" aria-label="Create new placement drive">
    <div class="rq-modal rq-modal-lg">
      <div class="rq-modal-hd">
        <div>
          <div class="rq-ename" style="font-size:0.95rem">Create Placement Drive</div>
          <div class="rq-esub">Will be reviewed by admin before going live</div>
        </div>
        <button class="rq-modal-close" @click="$emit('close')" aria-label="Close">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
          </svg>
        </button>
      </div>

      <div class="rq-modal-body">
        <div class="rq-form-row">
          <div class="rq-form-group">
            <label class="rq-form-label">Drive Title *</label>
            <input :value="newDrive.title" @input="onText('title', $event)" class="rq-form-input" placeholder="e.g. Software Engineer Intern" />
          </div>
          <div class="rq-form-group">
            <label class="rq-form-label">Role Type *</label>
            <select :value="newDrive.type" @change="onText('type', $event)" class="rq-form-input rq-select-field">
              <option value="Full-time">Full-time</option>
              <option value="Internship">Internship</option>
              <option value="Part-time">Part-time</option>
            </select>
          </div>
        </div>

        <div class="rq-form-row">
          <div class="rq-form-group">
            <label class="rq-form-label">CTC / Stipend *</label>
            <input :value="newDrive.salary" @input="onText('salary', $event)" class="rq-form-input" placeholder="e.g. 18 or 40" />
          </div>
          <div class="rq-form-group">
            <label class="rq-form-label">Application Deadline *</label>
            <input :value="newDrive.deadline" @input="onText('deadline', $event)" class="rq-form-input" type="date" />
          </div>
        </div>

        <div class="rq-form-row">
          <div class="rq-form-group">
            <label class="rq-form-label">Minimum CGPA</label>
            <input :value="newDrive.minCgpa" @input="onNumber('minCgpa', $event)" class="rq-form-input" type="number" step="0.1" min="0" max="10" placeholder="e.g. 7.5" />
          </div>
          <div class="rq-form-group">
            <label class="rq-form-label">Eligible Branches</label>
            <input :value="newDrive.branches" @input="onText('branches', $event)" class="rq-form-input" placeholder="e.g. CSE, ECE or All" />
          </div>
        </div>

        <div class="rq-form-row">
          <div class="rq-form-group">
            <label class="rq-form-label">Eligible Years *</label>
            <div class="year-options">
              <label v-for="year in [1, 2, 3, 4]" :key="year" class="year-option">
                <input
                  type="checkbox"
                  :checked="Array.isArray(newDrive.eligible_years) && newDrive.eligible_years.includes(year)"
                  @change="toggleEligibleYear(year, $event.target.checked)"
                />
                {{ year }}{{ year === 1 ? 'st' : year === 2 ? 'nd' : year === 3 ? 'rd' : 'th' }} Year
              </label>
            </div>
          </div>

          <div class="rq-form-group">
            <label class="rq-form-label">Experience Required</label>
            <select :value="newDrive.experience_required" @change="onText('experience_required', $event)" class="rq-form-input rq-select-field">
              <option value="">Select</option>
              <option value="Fresher">Fresher</option>
              <option value="0-1 years">0-1 years</option>
              <option value="1-2 years">1-2 years</option>
              <option value="2+ years">2+ years</option>
            </select>
          </div>
        </div>

        <div class="rq-form-group">
          <label class="rq-form-label">Required Skills</label>
          <div class="skills-input">
            <input
              v-model="skillInput"
              @keydown.enter.prevent="addSkill"
              class="rq-form-input"
              placeholder="Type skill and press Enter"
            />
            <button type="button" class="rq-ghost" @click="addSkill">Add</button>
          </div>

          <div class="skills-tags" v-if="Array.isArray(newDrive.required_skills) && newDrive.required_skills.length">
            <span
              v-for="(skill, index) in newDrive.required_skills"
              :key="`${skill}-${index}`"
              class="skill-tag"
            >
              {{ skill }}
              <button type="button" @click="removeSkill(index)" aria-label="Remove skill">x</button>
            </span>
          </div>
        </div>

        <div class="rq-form-group">
          <label class="rq-form-label">Job Description</label>
          <textarea :value="newDrive.description" @input="onText('description', $event)" class="rq-form-input rq-form-textarea" placeholder="Describe the role, responsibilities, and requirements…" rows="4"></textarea>
        </div>
      </div>

      <div class="rq-modal-ft">
        <button class="rq-ghost" @click="$emit('close')">Cancel</button>
        <button class="rq-btn-primary" @click="$emit('submit')">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M6 1v10M1 6h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
          </svg>
          Submit for Approval
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NewDriveModal',
  props: {
    newDrive: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      skillInput: ''
    }
  },
  emits: ['close', 'submit', 'update-field'],
  methods: {
    onText(field, event) {
      this.$emit('update-field', field, event.target.value)
    },
    onNumber(field, event) {
      const parsed = Number(event.target.value)
      this.$emit('update-field', field, Number.isNaN(parsed) ? 0 : parsed)
    },
    toggleEligibleYear(year, checked) {
      const currentYears = Array.isArray(this.newDrive.eligible_years)
        ? [...this.newDrive.eligible_years]
        : []

      const nextYears = checked
        ? [...currentYears, Number(year)]
        : currentYears.filter((entry) => Number(entry) !== Number(year))

      const normalizedYears = [...new Set(nextYears)]
        .map((entry) => Number(entry))
        .filter((entry) => entry >= 1 && entry <= 4)
        .sort((left, right) => left - right)

      this.$emit('update-field', 'eligible_years', normalizedYears)
    },
    addSkill() {
      const nextSkill = String(this.skillInput || '').trim()
      if (!nextSkill) {
        return
      }

      const currentSkills = Array.isArray(this.newDrive.required_skills)
        ? [...this.newDrive.required_skills]
        : []

      const isDuplicate = currentSkills.some(
        (skill) => String(skill || '').trim().toLowerCase() === nextSkill.toLowerCase()
      )

      if (isDuplicate) {
        this.skillInput = ''
        return
      }

      this.$emit('update-field', 'required_skills', [...currentSkills, nextSkill])
      this.skillInput = ''
    },
    removeSkill(index) {
      const currentSkills = Array.isArray(this.newDrive.required_skills)
        ? [...this.newDrive.required_skills]
        : []

      if (index < 0 || index >= currentSkills.length) {
        return
      }

      currentSkills.splice(index, 1)
      this.$emit('update-field', 'required_skills', currentSkills)
    }
  }
}
</script>

<style scoped>
.year-options {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.year-option {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--rq-t2);
}

.skills-input {
  display: flex;
  gap: 8px;
  align-items: center;
}

.skills-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.skill-tag {
  background: #EEF2FF;
  color: #3730A3;
  padding: 4px 10px;
  border-radius: 8px;
  margin: 4px 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.76rem;
  font-weight: 600;
}

.skill-tag button {
  border: 0;
  background: transparent;
  color: inherit;
  font-size: 0.78rem;
  line-height: 1;
  padding: 0;
}
</style>
