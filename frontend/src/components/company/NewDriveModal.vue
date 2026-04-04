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
  emits: ['close', 'submit', 'update-field'],
  methods: {
    onText(field, event) {
      this.$emit('update-field', field, event.target.value)
    },
    onNumber(field, event) {
      const parsed = Number(event.target.value)
      this.$emit('update-field', field, Number.isNaN(parsed) ? 0 : parsed)
    }
  }
}
</script>
