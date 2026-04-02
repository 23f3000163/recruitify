<template>
  <section class="rq-view">
    <article class="rq-card">
      <header class="rq-card-hd">
        <span class="rq-card-title">My Profile</span>
      </header>

      <div class="rq-card-body">
        <p id="student-profile-note" class="rq-row-sub">
          Keep your academic details, resume, skills, and experience summary updated for better drive matching.
        </p>

        <p v-if="errorMessage" class="rq-error-text" role="alert" aria-live="assertive">{{ errorMessage }}</p>

        <form
          class="rq-form-grid"
          @submit.prevent="$emit('save-profile')"
          @keydown.enter.prevent="$emit('save-profile')"
          aria-describedby="student-profile-note"
        >
          <label class="rq-field rq-field-full">
            <span>College Name</span>
            <input
              type="text"
              :value="profileForm.college_name"
              @input="updateField('college_name', $event.target.value)"
              placeholder="College name"
            />
          </label>

          <label class="rq-field">
            <span>Branch</span>
            <input
              type="text"
              :value="profileForm.branch"
              @input="updateField('branch', $event.target.value)"
              placeholder="Branch"
            />
          </label>

          <label class="rq-field">
            <span>Year</span>
            <input
              type="number"
              min="1"
              :value="profileForm.year"
              @input="updateField('year', $event.target.value)"
              placeholder="Year"
            />
          </label>

          <label class="rq-field">
            <span>CGPA</span>
            <input
              type="number"
              min="0"
              max="10"
              step="0.01"
              :value="profileForm.cgpa"
              @input="updateField('cgpa', $event.target.value)"
              placeholder="CGPA"
            />
          </label>

          <label class="rq-field">
            <span>Roll Number</span>
            <input
              type="text"
              :value="profileForm.roll_number"
              @input="updateField('roll_number', $event.target.value)"
              placeholder="Roll number"
            />
          </label>

          <label class="rq-field">
            <span>Phone</span>
            <input
              type="tel"
              :value="profileForm.phone"
              @input="updateField('phone', $event.target.value)"
              placeholder="Phone number"
            />
          </label>

          <label class="rq-field rq-field-full">
            <span>Resume URL</span>
            <input
              type="url"
              :value="profileForm.resume_url"
              @input="updateField('resume_url', $event.target.value)"
              placeholder="https://example.com/resume.pdf"
            />
          </label>

          <label class="rq-field rq-field-full">
            <span>Skills</span>
            <input
              type="text"
              :value="profileForm.skills"
              @input="updateField('skills', $event.target.value)"
              placeholder="Python, SQL, Vue, DSA"
            />
          </label>

          <label class="rq-field rq-field-full">
            <span>Experience Summary</span>
            <textarea
              rows="4"
              :value="profileForm.experience_summary"
              @input="updateField('experience_summary', $event.target.value)"
              placeholder="Summarize internships, projects, and key responsibilities"
            ></textarea>
          </label>

          <div class="rq-panel-footer rq-panel-footer-start rq-field-full">
            <button class="rq-btn-primary" type="button" :disabled="isSaving" @click="$emit('save-profile')">
              {{ isSaving ? 'Saving...' : 'Save Profile' }}
            </button>
          </div>
        </form>
      </div>
    </article>
  </section>
</template>

<script>
export default {
  name: 'StudentProfilePanelV2',
  props: {
    profileForm: {
      type: Object,
      default: () => ({
        college_name: '',
        branch: '',
        year: '',
        cgpa: '',
        roll_number: '',
        phone: '',
        resume_url: '',
        skills: '',
        experience_summary: ''
      })
    },
    isSaving: {
      type: Boolean,
      default: false
    },
    errorMessage: {
      type: String,
      default: ''
    }
  },
  emits: ['update-field', 'save-profile'],
  methods: {
    updateField(field, value) {
      this.$emit('update-field', field, value)
    }
  }
}
</script>
