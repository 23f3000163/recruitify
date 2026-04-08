<template>
  <section class="rq-view profile-shell">
    <div class="profile-layout">
      <aside class="profile-left">
        <article class="rq-card profile-card profile-summary-card">
          <div class="profile-avatar">{{ profileInitials }}</div>
          <h2 class="profile-name">{{ displayStudentName }}</h2>
          <p class="profile-subtitle">{{ profileSubtitle }}</p>

          <div class="profile-stats">
            <div class="profile-stat">
              <span class="profile-stat-value">{{ profileForm.cgpa || '-' }}</span>
              <span class="profile-stat-label">CGPA</span>
            </div>
            <div class="profile-stat">
              <span class="profile-stat-value">{{ profileForm.roll_number || '-' }}</span>
              <span class="profile-stat-label">Roll</span>
            </div>
            <div class="profile-stat">
              <span class="profile-stat-value">{{ profileForm.year || '-' }}</span>
              <span class="profile-stat-label">Year</span>
            </div>
          </div>

          <div class="profile-completion">
            <div class="profile-completion-head">
              <span>Profile completion: {{ profilePct }}%</span>
            </div>
            <div class="profile-progress">
              <div class="profile-progress-bar" :style="{ width: profilePct + '%' }"></div>
            </div>
            <p class="profile-completion-hint">Complete your profile to unlock applications</p>
          </div>
        </article>

        <article class="rq-card profile-card">
          <h3 class="profile-panel-title">Skills</h3>
          <div class="profile-skill-list">
            <span
              v-for="skill in skillList"
              :key="skill"
              class="profile-skill-badge"
              :class="skillToneClass(skill)"
            >
              {{ skill }}
              <button type="button" class="profile-skill-remove" :aria-label="'Remove ' + skill" @click="removeSkill(skill)">
                x
              </button>
            </span>
            <span v-if="!skillList.length" class="profile-empty-note">No skills added yet.</span>
          </div>
        </article>

        <article class="rq-card profile-card">
          <h3 class="profile-panel-title">Quick Info</h3>

          <div class="profile-info-row">
            <span class="profile-info-icon" aria-hidden="true">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M2.5 4.5A1.5 1.5 0 014 3h8a1.5 1.5 0 011.5 1.5v7A1.5 1.5 0 0112 13H4a1.5 1.5 0 01-1.5-1.5v-7z" stroke="currentColor" stroke-width="1.3"/>
                <path d="M2.5 5l5.5 4 5.5-4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
            <div class="profile-info-copy">
              <span class="profile-info-key">Phone</span>
              <span class="profile-info-value">{{ profileForm.phone || 'Not set' }}</span>
            </div>
          </div>

          <div class="profile-info-row">
            <span class="profile-info-icon" aria-hidden="true">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M3 2.5h10v11H3z" stroke="currentColor" stroke-width="1.3"/>
                <path d="M3 5.5h10" stroke="currentColor" stroke-width="1.3"/>
              </svg>
            </span>
            <div class="profile-info-copy">
              <span class="profile-info-key">Branch</span>
              <span class="profile-info-value">{{ profileForm.branch || 'Not set' }}</span>
            </div>
          </div>

          <div class="profile-info-row">
            <span class="profile-info-icon" aria-hidden="true">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M8 1.5l5.5 2v4c0 3.3-2.3 5.9-5.5 7-3.2-1.1-5.5-3.7-5.5-7v-4l5.5-2z" stroke="currentColor" stroke-width="1.3"/>
              </svg>
            </span>
            <div class="profile-info-copy">
              <span class="profile-info-key">Resume</span>
              <span class="profile-info-value">{{ resumeFileName || resumeFileDisplayName || 'Not uploaded' }}</span>
            </div>
          </div>
        </article>
      </aside>

      <article class="rq-card profile-right">
        <header class="profile-header">
          <h1 class="rq-card-title">My Profile</h1>
          <p id="student-profile-note" class="rq-row-sub">
            Keep your academic details, resume, skills, and experience summary updated for better drive matching.
          </p>
        </header>

        <p v-if="resumeActionMessage" class="rq-error-text profile-resume-alert" role="alert" aria-live="assertive">{{ resumeActionMessage }}</p>
        <p v-if="errorMessage" class="rq-error-text" role="alert" aria-live="assertive">{{ errorMessage }}</p>

        <div class="profile-tabs" role="tablist" aria-label="Profile sections">
          <button type="button" :class="{ active: activeTab === 'academic' }" @click="activeTab = 'academic'">Academic</button>
          <button type="button" :class="{ active: activeTab === 'resume' }" @click="activeTab = 'resume'">Resume</button>
          <button type="button" :class="{ active: activeTab === 'experience' }" @click="activeTab = 'experience'">Experience</button>
        </div>

        <form
          class="profile-form"
          @submit.prevent="$emit('save-profile')"
          @keydown.enter.prevent="$emit('save-profile')"
          aria-describedby="student-profile-note"
        >
          <section v-show="activeTab === 'academic'" class="profile-tab-panel">
            <h3 class="profile-section-title">Academic</h3>

            <div class="rq-form-grid profile-grid-2">
              <label class="rq-field rq-field-full">
                <span class="rq-form-label">College Name</span>
                <input
                  class="rq-form-input"
                  type="text"
                  :value="profileForm.college_name"
                  @input="updateField('college_name', $event.target.value)"
                  placeholder="College name"
                />
              </label>

              <label class="rq-field">
                <span class="rq-form-label">Branch</span>
                <input
                  class="rq-form-input"
                  type="text"
                  :value="profileForm.branch"
                  @input="updateField('branch', $event.target.value)"
                  placeholder="Branch"
                />
              </label>

              <label class="rq-field">
                <span class="rq-form-label">Year</span>
                <input
                  class="rq-form-input"
                  type="number"
                  min="1"
                  :value="profileForm.year"
                  @input="updateField('year', $event.target.value)"
                  placeholder="Year"
                />
              </label>

              <label class="rq-field">
                <span class="rq-form-label">CGPA</span>
                <input
                  class="rq-form-input"
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
                <span class="rq-form-label">Roll Number</span>
                <input
                  class="rq-form-input"
                  type="text"
                  :value="profileForm.roll_number"
                  @input="updateField('roll_number', $event.target.value)"
                  placeholder="Roll number"
                />
              </label>
            </div>

            <h3 class="profile-section-title">Contact</h3>
            <label class="rq-field">
              <span class="rq-form-label">Phone</span>
              <input
                class="rq-form-input"
                type="tel"
                :value="profileForm.phone"
                @input="updateField('phone', $event.target.value)"
                placeholder="Phone number"
              />
            </label>
          </section>

          <section v-show="activeTab === 'resume'" class="profile-tab-panel">
            <h3 class="profile-section-title">Resume</h3>

            <label class="rq-field">
              <span class="rq-form-label">Upload Resume (PDF, DOC, DOCX)</span>
              <input
                ref="resumeInput"
                class="profile-file-input"
                type="file"
                accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                :disabled="isSaving || isUploadingResume"
                @change="handleResumeSelection"
              />
              <button type="button" class="profile-upload-box" :disabled="isSaving || isUploadingResume" @click="openResumePicker">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                  <path d="M8 11V3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
                  <path d="M5.5 5.5L8 3l2.5 2.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M2.5 11.5v1A1.5 1.5 0 004 14h8a1.5 1.5 0 001.5-1.5v-1" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
                </svg>
                <span>{{ isUploadingResume ? 'Uploading selected file...' : 'Click to upload resume' }}</span>
              </button>
            </label>

            <div v-if="resumeEntries.length" class="profile-file-list">
              <div v-for="entry in resumeEntries" :key="entry.id" class="profile-file-row">
                <div>
                  <p class="profile-file-name">{{ entry.name }}</p>
                  <p class="profile-file-sub">{{ entry.previewUrl ? 'Uploaded file available for preview.' : 'Preview unavailable for this entry.' }}</p>
                </div>
                <div class="profile-file-actions">
                  <button type="button" class="profile-preview-btn" :disabled="!entry.previewUrl" @click="openResumePreview(entry.id)">
                    Preview Resume
                  </button>
                  <button type="button" class="profile-remove-btn" @click="removeResume(entry.id)">
                    Remove
                  </button>
                </div>
              </div>
            </div>
            <p v-else class="profile-empty-note">No resume uploaded yet.</p>

            <details class="profile-url-details">
              <summary>Use Resume URL (optional)</summary>
              <label class="rq-field">
                <span class="rq-form-label">Resume URL</span>
                <input
                  class="rq-form-input"
                  type="url"
                  :value="profileForm.resume_url"
                  @input="updateField('resume_url', $event.target.value)"
                  placeholder="https://example.com/resume.pdf"
                />
              </label>
            </details>
          </section>

          <section v-show="activeTab === 'experience'" class="profile-tab-panel">
            <h3 class="profile-section-title">Skills</h3>
            <label class="rq-field">
              <span class="rq-form-label">Skills</span>
              <input
                class="rq-form-input"
                type="text"
                :value="profileForm.skills"
                @input="handleSkillsInput($event.target.value)"
                placeholder="Python, SQL, Vue, DSA"
              />
              <small class="rq-inline-note">Use comma-separated skills. Duplicates are removed automatically.</small>
            </label>

            <div class="profile-skill-list profile-skill-list-compact" v-if="skillList.length">
              <span
                v-for="skill in skillList"
                :key="'exp-' + skill"
                class="profile-skill-badge"
                :class="skillToneClass(skill)"
              >
                {{ skill }}
              </span>
            </div>

            <h3 class="profile-section-title">Experience</h3>
            <label class="rq-field">
              <span class="rq-form-label">Experience Summary</span>
              <textarea
                class="rq-form-input"
                rows="4"
                maxlength="500"
                :value="profileForm.experience_summary"
                @input="updateField('experience_summary', $event.target.value)"
                placeholder="Summarize internships, projects, and key responsibilities"
              ></textarea>
              <small class="profile-counter">{{ String(profileForm.experience_summary || '').length }}/500</small>
            </label>
          </section>

          <div class="rq-panel-footer rq-panel-footer-start">
            <button class="rq-btn-primary save-btn" type="button" :disabled="isSaving" @click="$emit('save-profile')">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M13 2H4L2 4v9a1 1 0 001 1h10a1 1 0 001-1V3a1 1 0 00-1-1z" stroke="currentColor" stroke-width="1.3" fill="none"/>
                <path d="M5 2h6v4H5z" stroke="currentColor" stroke-width="1.3" fill="none"/>
                <path d="M4.5 9h7M4.5 12h4.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              <span>{{ isSaving ? 'Saving...' : 'Save Profile' }}</span>
            </button>
          </div>
        </form>
      </article>
    </div>

    <div v-if="showResumeModal" class="profile-modal-backdrop" @click.self="closeResumePreview">
      <div class="profile-modal" role="dialog" aria-modal="true" aria-label="Resume preview">
        <div class="profile-modal-header">
          <h3 class="profile-modal-title">{{ resumePreview.name || 'Resume Preview' }}</h3>
          <button type="button" class="profile-modal-close" aria-label="Close preview" @click="closeResumePreview">x</button>
        </div>

        <div class="profile-modal-body">
          <iframe v-if="resumePreview.isPdf" :src="resumePreview.url" class="profile-preview-frame" title="Resume preview"></iframe>
          <div v-else class="profile-preview-fallback">
            <p>Preview is not available for DOC/DOCX files.</p>
            <a class="rq-btn-primary profile-download-link" :href="resumePreview.url" target="_blank" rel="noopener">Download Resume</a>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import { apiClient, parseApiError } from '../../services/api'

export default {
  name: 'StudentProfileView',
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
    isUploadingResume: {
      type: Boolean,
      default: false
    },
    resumeFileName: {
      type: String,
      default: ''
    },
    studentName: {
      type: String,
      default: ''
    },
    errorMessage: {
      type: String,
      default: ''
    }
  },
  emits: ['update-field', 'save-profile', 'upload-resume'],
  data() {
    return {
      activeTab: 'academic',
      showResumeModal: false,
      isOpeningResumePreview: false,
      uploadedResumes: [],
      pendingUploadId: '',
      resumeActionMessage: '',
      resumeActionTimerId: null,
      fetchedResumePreviewUrl: '',
      resumePreview: {
        url: '',
        name: '',
        isPdf: true
      }
    }
  },
  watch: {
    'profileForm.resume_url'(nextUrl) {
      const normalized = String(nextUrl || '').trim()
      if (!normalized || !this.pendingUploadId) {
        return
      }

      const targetIndex = this.uploadedResumes.findIndex((entry) => entry.id === this.pendingUploadId)
      if (targetIndex !== -1) {
        this.uploadedResumes[targetIndex] = {
          ...this.uploadedResumes[targetIndex],
          remoteUrl: normalized
        }
      }
      this.pendingUploadId = ''
    }
  },
  computed: {
    profilePct() {
      const fields = [
        this.profileForm.college_name,
        this.profileForm.branch,
        this.profileForm.year,
        this.profileForm.cgpa,
        this.profileForm.roll_number,
        this.profileForm.phone,
        this.resumeFileName || this.profileForm.resume_url,
        this.profileForm.skills,
        this.profileForm.experience_summary
      ]

      const filled = fields.filter((value) => String(value || '').trim()).length
      return Math.round((filled / fields.length) * 100)
    },
    profileSubtitle() {
      const parts = []
      const branch = String(this.profileForm.branch || '').trim()
      const year = String(this.profileForm.year || '').trim()
      const college = String(this.profileForm.college_name || '').trim()

      if (branch) {
        parts.push(branch)
      }
      if (year) {
        parts.push(`Year ${year}`)
      }
      if (college) {
        parts.push(college)
      }

      return parts.length ? parts.join(' / ') : 'Complete your academic profile'
    },
    profileInitials() {
      const source = this.displayStudentName
      const parts = String(source || '')
        .trim()
        .split(/\s+/)
        .filter(Boolean)

      if (parts.length >= 2) {
        return `${parts[0][0] || ''}${parts[parts.length - 1][0] || ''}`.toUpperCase()
      }

      if (parts.length === 1) {
        return parts[0].slice(0, 2).toUpperCase()
      }

      return 'SP'
    },
    displayStudentName() {
      const incomingName = String(this.studentName || '').trim()
      if (incomingName) {
        return incomingName
      }

      const fallbackName = String(this.profileForm.roll_number || '').trim()
      return fallbackName ? `Student ${fallbackName}` : 'Student Profile'
    },
    skillList() {
      return this.normalizeSkills(this.profileForm.skills)
    },
    resumeFileDisplayName() {
      if (this.resumeFileName) {
        return this.resumeFileName
      }

      const resumeUrl = String(this.profileForm.resume_url || '').trim()
      if (!resumeUrl) {
        return ''
      }

      return this.inferResumeNameFromUrl(resumeUrl)
    },
    resumeEntries() {
      const entries = this.uploadedResumes.map((entry) => ({
        id: entry.id,
        name: entry.name,
        previewUrl: entry.objectUrl || entry.remoteUrl || '',
        isPdf: entry.isPdf || this.isPdfName(entry.name) || this.isPdfName(entry.remoteUrl)
      }))

      if (!entries.length) {
        const resumeUrl = String(this.profileForm.resume_url || '').trim()
        if (resumeUrl || this.resumeFileName) {
          const inferredName = this.resumeFileDisplayName || this.inferResumeNameFromUrl(resumeUrl)
          entries.push({
            id: 'current-resume-url',
            name: inferredName || 'resume-file',
            previewUrl: resumeUrl,
            isPdf: this.isPdfName(inferredName) || this.isPdfName(resumeUrl)
          })
        }
      }

      return entries
    }
  },
  methods: {
    updateField(field, value) {
      this.$emit('update-field', field, value)
    },
    handleResumeSelection(event) {
      const file = event?.target?.files?.[0]
      if (!file) {
        return
      }

      const canCreateObjectUrl =
        typeof URL !== 'undefined' && typeof URL.createObjectURL === 'function'

      const objectUrl = canCreateObjectUrl
        ? URL.createObjectURL(file)
        : ''

      const resumeEntryId = `resume-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
      this.uploadedResumes.unshift({
        id: resumeEntryId,
        name: String(file.name || 'resume-file'),
        objectUrl,
        remoteUrl: '',
        isPdf: String(file.type || '').toLowerCase() === 'application/pdf' || this.isPdfName(file.name)
      })
      this.pendingUploadId = resumeEntryId

      this.resumePreview = {
        url: objectUrl || String(this.profileForm.resume_url || '').trim(),
        name: String(file.name || 'resume-file'),
        isPdf: String(file.type || '').toLowerCase() === 'application/pdf' || this.isPdfName(file.name)
      }
      this.clearResumeActionMessage()

      this.$emit('upload-resume', file)
      event.target.value = ''
    },
    openResumePicker() {
      if (this.isSaving || this.isUploadingResume) {
        return
      }

      const input = this.$refs.resumeInput
      if (input && typeof input.click === 'function') {
        input.click()
      }
    },
    normalizeSkills(rawValue) {
      const parts = String(rawValue || '')
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)

      const deduped = []
      const seen = new Set()

      parts.forEach((item) => {
        const key = item.toLowerCase()
        if (seen.has(key)) {
          return
        }
        seen.add(key)
        deduped.push(item)
      })

      return deduped
    },
    handleSkillsInput(rawValue) {
      this.updateField('skills', String(rawValue || ''))
    },
    removeSkill(skillName) {
      const key = String(skillName || '').trim().toLowerCase()
      if (!key) {
        return
      }

      const remaining = this.skillList.filter((item) => item.toLowerCase() !== key)
      this.updateField('skills', remaining.join(', '))
    },
    skillToneClass(skill) {
      const value = String(skill || '').toLowerCase()
      if (/(^|\b)(ml|ai|nlp|machine learning|deep learning)(\b|$)/.test(value)) {
        return 'tone-purple'
      }
      if (/(^|\b)(backend|api|flask|django|node|sql|database)(\b|$)/.test(value)) {
        return 'tone-green'
      }
      return 'tone-blue'
    },
    isPdfName(nameOrUrl) {
      return /\.pdf($|\?|#)/i.test(String(nameOrUrl || '').trim())
    },
    inferResumeNameFromUrl(url) {
      const safeUrl = String(url || '').trim().split('?')[0].split('#')[0]
      const segments = safeUrl.split('/').filter(Boolean)
      const last = segments.length ? segments[segments.length - 1] : 'resume-file'
      try {
        return decodeURIComponent(last)
      } catch (error) {
        return last
      }
    },
    extractProtectedResumePath(url) {
      const normalized = String(url || '').trim()
      if (!normalized) {
        return ''
      }

      if (/^\/student\/resume(?:\/|$)/i.test(normalized)) {
        return normalized
      }

      if (!/^https?:\/\//i.test(normalized)) {
        return ''
      }

      try {
        const parsed = new URL(normalized)
        if (/^\/student\/resume(?:\/|$)/i.test(parsed.pathname)) {
          return `${parsed.pathname}${parsed.search || ''}`
        }
      } catch (error) {
        return ''
      }

      return ''
    },
    async fetchProtectedResumePreviewUrl(sourceUrl) {
      const protectedPath = this.extractProtectedResumePath(sourceUrl)
      if (!protectedPath) {
        return {
          previewUrl: sourceUrl,
          isPdf: this.isPdfName(sourceUrl)
        }
      }

      const response = await apiClient.get(protectedPath, {
        responseType: 'blob'
      })

      const rawPayload = response?.data
      const blobPayload = rawPayload instanceof Blob ? rawPayload : new Blob([rawPayload || ''])

      const mimeType = String(response?.headers?.['content-type'] || blobPayload.type || '').toLowerCase()
      const isPdf = mimeType ? mimeType.includes('pdf') : this.isPdfName(sourceUrl)

      if (typeof URL === 'undefined' || typeof URL.createObjectURL !== 'function') {
        return {
          previewUrl: sourceUrl,
          isPdf
        }
      }

      const objectUrl = URL.createObjectURL(blobPayload)
      this.fetchedResumePreviewUrl = objectUrl

      return {
        previewUrl: objectUrl,
        isPdf
      }
    },
    clearFetchedResumePreviewUrl() {
      if (!this.fetchedResumePreviewUrl) {
        return
      }

      this.revokeResumeObjectUrl(this.fetchedResumePreviewUrl)
      this.fetchedResumePreviewUrl = ''
    },
    async openResumePreview(resumeId) {
      const targetEntry = this.resumeEntries.find((entry) => entry.id === resumeId)
      if (!targetEntry || !targetEntry.previewUrl || this.isOpeningResumePreview) {
        return
      }

      this.isOpeningResumePreview = true
      this.clearFetchedResumePreviewUrl()

      let resolvedPreviewUrl = targetEntry.previewUrl
      let resolvedIsPdf = targetEntry.isPdf

      try {
        const resolvedPreview = await this.fetchProtectedResumePreviewUrl(targetEntry.previewUrl)
        resolvedPreviewUrl = resolvedPreview.previewUrl
        resolvedIsPdf = resolvedPreview.isPdf
      } catch (error) {
        this.showResumeActionMessage(
          parseApiError(error, 'Unable to load resume preview right now. Please try again.')
        )
        return
      } finally {
        this.isOpeningResumePreview = false
      }

      this.resumePreview = {
        url: resolvedPreviewUrl,
        name: targetEntry.name,
        isPdf: resolvedIsPdf
      }
      this.showResumeModal = true
    },
    closeResumePreview() {
      this.showResumeModal = false
      this.clearFetchedResumePreviewUrl()
    },
    removeResume(resumeId) {
      let shouldPersistResumeRemoval = false

      const targetIndex = this.uploadedResumes.findIndex((entry) => entry.id === resumeId)
      if (targetIndex !== -1) {
        const [removedEntry] = this.uploadedResumes.splice(targetIndex, 1)
        this.revokeResumeObjectUrl(removedEntry?.objectUrl)

        const currentResumeUrl = String(this.profileForm.resume_url || '').trim()
        const removedRemoteUrl = String(removedEntry?.remoteUrl || '').trim()
        const currentResumeName = String(this.resumeFileName || this.resumeFileDisplayName || '')
          .trim()
          .toLowerCase()
        const removedResumeName = String(removedEntry?.name || '').trim().toLowerCase()

        const shouldClearCurrentResume =
          (removedRemoteUrl && removedRemoteUrl === currentResumeUrl) ||
          (currentResumeName && removedResumeName && currentResumeName === removedResumeName)

        if (shouldClearCurrentResume) {
          this.updateField('resume_url', '')
          shouldPersistResumeRemoval = true
        }

        if (this.pendingUploadId === resumeId) {
          this.pendingUploadId = ''
        }
      } else if (resumeId === 'current-resume-url') {
        this.updateField('resume_url', '')
        shouldPersistResumeRemoval = true
      }

      if (this.resumePreview.url && !this.resumeEntries.some((entry) => entry.previewUrl === this.resumePreview.url)) {
        this.closeResumePreview()
      }

      if (shouldPersistResumeRemoval && !this.isSaving && !this.isUploadingResume) {
        this.$nextTick(() => {
          this.$emit('save-profile')
        })
      }

      this.showResumeActionMessage(
        shouldPersistResumeRemoval ? 'Resume removed. Saving profile changes...' : 'Resume removed.'
      )
    },
    showResumeActionMessage(message) {
      this.resumeActionMessage = String(message || '').trim()
      if (!this.resumeActionMessage) {
        return
      }

      if (this.resumeActionTimerId) {
        clearTimeout(this.resumeActionTimerId)
      }

      this.resumeActionTimerId = setTimeout(() => {
        this.resumeActionMessage = ''
        this.resumeActionTimerId = null
      }, 3500)
    },
    clearResumeActionMessage() {
      if (this.resumeActionTimerId) {
        clearTimeout(this.resumeActionTimerId)
        this.resumeActionTimerId = null
      }
      this.resumeActionMessage = ''
    },
    revokeResumeObjectUrl(targetUrl) {
      if (!targetUrl) {
        return
      }

      if (typeof URL !== 'undefined' && typeof URL.revokeObjectURL === 'function') {
        URL.revokeObjectURL(targetUrl)
      }
    }
  },
  beforeUnmount() {
    this.clearFetchedResumePreviewUrl()
    this.uploadedResumes.forEach((entry) => {
      this.revokeResumeObjectUrl(entry?.objectUrl)
    })
    this.clearResumeActionMessage()
  }
}
</script>

<style scoped>
.profile-shell {
  padding: 6px;
}

.profile-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
  padding: 20px;
}

.profile-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.profile-right {
  background: var(--rq-white);
  border-radius: var(--rq-r);
  padding: 20px;
  border: 1px solid var(--rq-border2);
  box-shadow: var(--rq-sh-xs);
}

.profile-card {
  background: var(--rq-white);
  border-radius: var(--rq-r);
  padding: 16px;
  border: 1px solid var(--rq-border2);
  box-shadow: var(--rq-sh-xs);
}

.profile-summary-card {
  border-left: 3px solid var(--rq-blue);
}

.profile-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--rq-blue), var(--rq-purple));
  color: var(--rq-white);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-family: var(--rq-serif);
  margin-bottom: 10px;
}

.profile-name {
  margin: 0;
  font-family: var(--rq-serif);
  font-size: 1rem;
  color: var(--rq-ink);
}

.profile-subtitle {
  margin: 4px 0 0;
  font-size: 0.74rem;
  color: var(--rq-t3);
}

.profile-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  gap: 8px;
}

.profile-stat {
  display: grid;
  gap: 2px;
}

.profile-stat-value {
  font-size: 0.9rem;
  font-weight: 800;
  color: var(--rq-ink);
}

.profile-stat-label {
  font-size: 0.64rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--rq-t4);
}

.profile-completion {
  margin-top: 12px;
  display: grid;
  gap: 6px;
}

.profile-completion-head {
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--rq-t3);
}

.profile-progress {
  height: 6px;
  background: var(--rq-border2);
  border-radius: 6px;
  overflow: hidden;
}

.profile-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--rq-blue), #6366f1);
}

.profile-completion-hint {
  margin: 0;
  font-size: 0.68rem;
  color: var(--rq-t4);
}

.profile-panel-title {
  margin: 0 0 10px;
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--rq-t3);
}

.profile-skill-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.profile-skill-list-compact {
  margin-bottom: 6px;
}

.profile-skill-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: var(--rq-r-full);
  padding: 4px 10px;
  font-size: 0.72rem;
  font-weight: 700;
  border: 1px solid transparent;
}

.profile-skill-badge.tone-blue {
  color: var(--rq-blue);
  background: var(--rq-blue-lt);
  border-color: rgba(37, 99, 235, 0.2);
}

.profile-skill-badge.tone-purple {
  color: #6d28d9;
  background: #ede9fe;
  border-color: #c4b5fd;
}

.profile-skill-badge.tone-green {
  color: var(--rq-green);
  background: var(--rq-green-lt);
  border-color: rgba(5, 150, 105, 0.2);
}

.profile-skill-remove {
  border: none;
  background: transparent;
  color: currentColor;
  font-size: 0.78rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.profile-empty-note {
  color: var(--rq-t4);
  font-size: 0.72rem;
}

.profile-info-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--rq-border2);
}

.profile-info-row:last-child {
  border-bottom: none;
}

.profile-info-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--rq-blue);
  background: var(--rq-blue-lt);
  flex-shrink: 0;
}

.profile-info-copy {
  display: grid;
  gap: 1px;
}

.profile-info-key {
  font-size: 0.65rem;
  color: var(--rq-t4);
  text-transform: uppercase;
  letter-spacing: 0.07em;
}

.profile-info-value {
  font-size: 0.75rem;
  color: var(--rq-ink);
  font-weight: 700;
}

.profile-header {
  margin-bottom: 10px;
}

.profile-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.profile-tabs button {
  padding: 8px 14px;
  border-radius: var(--rq-r-sm);
  border: 1px solid transparent;
  background: #f3f4f6;
  color: var(--rq-t2);
  font-weight: 700;
  cursor: pointer;
}

.profile-tabs button.active {
  background: linear-gradient(135deg, #111111, #333333);
  color: var(--rq-white);
}

.profile-form {
  display: grid;
  gap: 12px;
}

.profile-tab-panel {
  display: grid;
  gap: 10px;
}

.profile-section-title {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--rq-t3);
}

.profile-grid-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.profile-file-input {
  display: none;
}

.profile-upload-box {
  width: 100%;
  border: 1px dashed var(--rq-border2);
  border-radius: var(--rq-r-sm);
  background: var(--rq-blue-lt);
  color: var(--rq-blue);
  padding: 10px 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 0.78rem;
  font-weight: 700;
}

.profile-upload-box:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.profile-file-row {
  margin-top: 8px;
  border: 1px solid var(--rq-border2);
  border-radius: var(--rq-r-sm);
  background: #f9fafb;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.profile-file-list {
  display: grid;
  gap: 8px;
}

.profile-file-name {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--rq-ink);
}

.profile-file-sub {
  margin: 2px 0 0;
  font-size: 0.7rem;
  color: var(--rq-t3);
}

.profile-preview-btn {
  white-space: nowrap;
  border: 1px solid #111111;
  border-radius: var(--rq-r-sm);
  background: linear-gradient(135deg, #111111, #333333);
  color: var(--rq-white);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 6px 10px;
}

.profile-preview-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.profile-file-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.profile-remove-btn {
  border: 1px solid rgba(220, 38, 38, 0.25);
  border-radius: var(--rq-r-sm);
  background: var(--rq-white);
  color: #B91C1C;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 6px 10px;
}

.profile-remove-btn:hover {
  background: #FEF2F2;
}

.profile-url-details {
  margin-top: 8px;
  border: 1px solid var(--rq-border2);
  border-radius: var(--rq-r-sm);
  background: var(--rq-parch);
  padding: 10px;
}

.profile-url-details summary {
  cursor: pointer;
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--rq-t2);
}

.profile-url-details .rq-field {
  margin-top: 10px;
}

.profile-counter {
  display: inline-block;
  margin-top: 4px;
  font-size: 0.68rem;
  color: var(--rq-t4);
}

.save-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: linear-gradient(135deg, #111111, #333333);
  color: var(--rq-white);
  padding: 10px 16px;
  border-radius: 10px;
  font-weight: 700;
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.15);
}

.profile-resume-alert {
  margin-bottom: 8px;
  color: #B91C1C;
}

.save-btn svg {
  color: currentColor;
}

.profile-form .rq-form-input {
  width: 100%;
  background: #f9fafb;
  border: 1px solid var(--rq-border2);
  border-radius: 10px;
  padding: 10px;
  font-size: 0.82rem;
  color: var(--rq-ink);
  transition: all 0.15s ease;
}

.profile-form .rq-form-input:focus {
  border-color: var(--rq-blue);
  background: var(--rq-white);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  outline: none;
}

.profile-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
  padding: 16px;
}

.profile-modal {
  width: min(860px, 100%);
  max-height: 90vh;
  overflow: hidden;
  background: var(--rq-white);
  border-radius: var(--rq-r);
  border: 1px solid var(--rq-border2);
  box-shadow: var(--rq-sh-sm);
  display: flex;
  flex-direction: column;
}

.profile-modal-header {
  padding: 12px 14px;
  border-bottom: 1px solid var(--rq-border2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.profile-modal-title {
  margin: 0;
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--rq-ink);
}

.profile-modal-close {
  border: 1px solid var(--rq-border2);
  background: var(--rq-white);
  border-radius: var(--rq-r-sm);
  width: 30px;
  height: 30px;
  color: var(--rq-t3);
  font-size: 0.95rem;
}

.profile-modal-body {
  padding: 12px;
  overflow: auto;
  background: var(--rq-parch);
}

.profile-preview-frame {
  width: 100%;
  min-height: 70vh;
  border: 1px solid var(--rq-border2);
  border-radius: var(--rq-r-sm);
  background: var(--rq-white);
}

.profile-preview-fallback {
  min-height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  color: var(--rq-t3);
}

.profile-download-link {
  text-decoration: none;
}

@media (max-width: 900px) {
  .profile-layout {
    grid-template-columns: 1fr;
  }

  .profile-grid-2 {
    grid-template-columns: 1fr;
  }

  .profile-file-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
