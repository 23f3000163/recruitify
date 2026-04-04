<template>
  <section class="rq-view">
    <div class="rq-card">
      <div class="rq-card-hd">
        <span class="rq-card-title">Company Information</span>
        <div class="rq-card-hd-l">
          <span class="rq-status-pill" :class="'pill-' + companyProfile.status">{{ companyProfile.status }}</span>
          <button class="rq-ghost" @click="$emit('toggle-edit')">
            {{ profileEditMode ? 'Cancel' : 'Edit' }}
          </button>
        </div>
      </div>
      <div class="rq-card-body">
        <div class="rq-profile-edit-header">
          <div class="rq-av rq-av-xxl" :style="{ background: companyProfile.avatarColor }">{{ companyProfile.initials }}</div>
          <div>
            <div class="rq-ename" style="font-size:1.1rem">{{ companyProfile.name }}</div>
            <div class="rq-esub" style="font-size:0.8rem">{{ companyProfile.domain }}</div>
            <div class="rq-esub" style="margin-top:4px">{{ companyProfile.industry }} · {{ companyProfile.location }}</div>
          </div>
        </div>

        <div class="rq-profile-form">
          <div class="rq-form-row">
            <div class="rq-form-group">
              <label class="rq-form-label">Company Name</label>
              <input
                v-if="profileEditMode"
                :value="profileEdit.name"
                @input="$emit('update-field', 'name', $event.target.value)"
                class="rq-form-input"
                placeholder="Company name"
              />
              <div v-else class="rq-form-val">{{ companyProfile.name }}</div>
            </div>
            <div class="rq-form-group">
              <label class="rq-form-label">Website / Domain</label>
              <input
                v-if="profileEditMode"
                :value="profileEdit.domain"
                @input="$emit('update-field', 'domain', $event.target.value)"
                class="rq-form-input"
                placeholder="company.com"
              />
              <div v-else class="rq-form-val rq-mono">{{ companyProfile.domain }}</div>
            </div>
          </div>

          <div class="rq-form-row">
            <div class="rq-form-group">
              <label class="rq-form-label">HR Contact Name</label>
              <input
                v-if="profileEditMode"
                :value="profileEdit.hrName"
                @input="$emit('update-field', 'hrName', $event.target.value)"
                class="rq-form-input"
                placeholder="HR manager name"
              />
              <div v-else class="rq-form-val">{{ companyProfile.hrName }}</div>
            </div>
            <div class="rq-form-group">
              <label class="rq-form-label">HR Email</label>
              <input
                v-if="profileEditMode"
                :value="profileEdit.hrEmail"
                @input="$emit('update-field', 'hrEmail', $event.target.value)"
                class="rq-form-input"
                placeholder="hr@company.com"
                type="email"
              />
              <div v-else class="rq-form-val rq-mono">{{ companyProfile.hrEmail }}</div>
            </div>
          </div>

          <div class="rq-form-row">
            <div class="rq-form-group">
              <label class="rq-form-label">Industry</label>
              <input
                v-if="profileEditMode"
                :value="profileEdit.industry"
                @input="$emit('update-field', 'industry', $event.target.value)"
                class="rq-form-input"
                placeholder="e.g. Fintech"
              />
              <div v-else class="rq-form-val">{{ companyProfile.industry }}</div>
            </div>
            <div class="rq-form-group">
              <label class="rq-form-label">Location</label>
              <input
                v-if="profileEditMode"
                :value="profileEdit.location"
                @input="$emit('update-field', 'location', $event.target.value)"
                class="rq-form-input"
                placeholder="City, State"
              />
              <div v-else class="rq-form-val">{{ companyProfile.location }}</div>
            </div>
          </div>

          <div class="rq-form-group">
            <label class="rq-form-label">About Company</label>
            <textarea
              v-if="profileEditMode"
              :value="profileEdit.about"
              @input="$emit('update-field', 'about', $event.target.value)"
              class="rq-form-input rq-form-textarea"
              placeholder="Brief description…"
              rows="3"
            ></textarea>
            <div v-else class="rq-form-val rq-form-val-multi">{{ companyProfile.about }}</div>
          </div>

          <div v-if="profileEditMode" class="rq-form-actions">
            <button class="rq-btn-primary" @click="$emit('save')">Save Changes</button>
            <button class="rq-ghost" @click="$emit('cancel')">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'ProfileView',
  props: {
    companyProfile: {
      type: Object,
      required: true
    },
    profileEditMode: {
      type: Boolean,
      required: true
    },
    profileEdit: {
      type: Object,
      required: true
    }
  },
  emits: ['toggle-edit', 'update-field', 'save', 'cancel']
}
</script>
