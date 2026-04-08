import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import StudentDashboard from '../../src/views/student/StudentDashboard.vue'
import { authApi, studentApi } from '../../src/api/api'

vi.mock('../../src/api/api', () => ({
  authApi: {
    getMe: vi.fn()
  },
  studentApi: {
    getDashboard: vi.fn(),
    getProfile: vi.fn(),
    getDrives: vi.fn(),
    applyToDrive: vi.fn(),
    getApplications: vi.fn(),
    scoreResumeForJob: vi.fn(),
    getHistory: vi.fn(),
    getNotifications: vi.fn(),
    markNotificationRead: vi.fn(),
    markAllNotificationsRead: vi.fn(),
    respondToOffer: vi.fn(),
    downloadOfferDocument: vi.fn(),
    downloadPlacementDocument: vi.fn(),
    updateProfile: vi.fn(),
    uploadResume: vi.fn()
  }
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

const dashboardPayload = {
  data: {
    data: {
      summary: {
        applications_total: 4,
        applied: 2,
        shortlisted: 1,
        interviewed: 1,
        selected: 0,
        waitlisted: 0,
        rejected: 0,
        offers_released: 1,
        offers_accepted: 0,
        offers_rejected: 0
      },
      recent_applications: [
        {
          application_id: 91,
          status: 'shortlisted',
          status_label: 'Shortlisted',
          drive: {
            id: 51,
            title: 'Platform Engineer',
            location: 'Bengaluru',
            application_deadline: '2030-06-12T10:00:00+00:00',
            salary_lpa: 18
          },
          company: {
            name: 'Orbit Labs'
          }
        }
      ],
      unread_notifications: 2
    }
  }
}

const applicationsPayload = {
  data: {
    data: {
      items: [
        {
          application_id: 501,
          drive_id: 51,
          status: 'selected',
          status_label: 'Selected',
          updated_at: '2030-06-02T10:00:00+00:00',
          drive: {
            id: 51,
            title: 'Backend Engineer',
            location: 'Remote'
          },
          company: {
            name: 'Acme Labs'
          },
          offer: {
            offer_id: 701,
            status: 'offered',
            position: 'Backend Engineer',
            salary: 1500000
          },
          timeline: []
        }
      ],
      total: 1,
      page: 1,
      pages: 1,
      limit: 10
    }
  }
}

const drivesPayload = {
  data: {
    data: {
      items: [
        {
          drive_id: 63,
          job_title: 'Frontend Developer',
          job_location: 'Pune',
          salary_lpa: 12,
          application_deadline: '2030-06-30T10:00:00+00:00',
          company: {
            name: 'Nimbus Tech',
            industry: 'Software'
          },
          already_applied: false,
          is_eligible: true,
          ineligibility_reasons: [],
          is_open: true
        }
      ],
      total: 1,
      page: 1,
      pages: 1,
      limit: 8
    }
  }
}

const historyPayload = {
  data: {
    data: {
      summary: {
        total_applied: 2,
        offers_received: 1,
        placements_count: 1,
        highest_package: 2100000
      },
      items: [
        {
          application_id: 990,
          status: 'selected',
          status_label: 'Selected',
          updated_at: '2030-06-03T08:30:00+00:00',
          outcome: 'placed',
          drive: {
            job_title: 'SRE Engineer',
            job_location: 'Remote'
          },
          company: {
            company_name: 'Orbit Labs'
          },
          offer: {
            offer_id: 44,
            status: 'offered'
          },
          placement: {
            placement_id: 55,
            position: 'SRE Engineer'
          }
        }
      ],
      total: 1,
      page: 1,
      pages: 1,
      limit: 10
    }
  }
}

const notificationsPayload = {
  data: {
    data: {
      items: [
        {
          notification_id: 801,
          title: 'Interview update',
          message: 'Your interview was rescheduled.',
          created_at: '2030-06-02T12:00:00+00:00',
          is_read: false
        }
      ],
      unread_count: 1,
      total: 1,
      page: 1,
      pages: 1,
      limit: 8
    }
  }
}

const mountWrapper = () =>
  mount(StudentDashboard, {
    global: {
      stubs: {
        StudentSidebar: {
          name: 'StudentSidebar',
          template: `
            <div>
              <button class="to-dashboard" @click="$emit('navigate', 'dashboard')">Dashboard</button>
              <button class="to-drives" @click="$emit('navigate', 'drives')">Drives</button>
              <button class="to-applications" @click="$emit('navigate', 'applications')">Applications</button>
              <button class="to-notifications" @click="$emit('navigate', 'notifications')">Notifications</button>
              <button class="to-profile" @click="$emit('navigate', 'profile')">Profile</button>
              <button class="to-history" @click="$emit('navigate', 'history')">History</button>
            </div>
          `
        },
        StudentTopbar: {
          name: 'StudentTopbar',
          template: '<div class="topbar-stub"></div>'
        }
      }
    }
  })

describe('StudentDashboard step 3B wiring', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()

    authApi.getMe.mockResolvedValue({
      data: {
        data: {
          username: 'priya.student',
          email: 'priya.student@example.com'
        }
      }
    })

    studentApi.getDashboard.mockResolvedValue(dashboardPayload)
    studentApi.getProfile.mockResolvedValue({
      data: {
        data: {
          student: {
            college_name: 'Institute of Technology',
            branch: 'CSE',
            year: 3,
            cgpa: 8.5,
            roll_number: 'CS21B042',
            phone: '9999999999',
            resume_url: 'https://example.com/resume.pdf',
            skills: 'Python, SQL',
            experience_summary: 'Internship at Acme'
          }
        }
      }
    })
    studentApi.getDrives.mockResolvedValue(drivesPayload)
    studentApi.applyToDrive.mockResolvedValue({
      data: {
        data: {
          already_applied: false,
          application: { application_id: 777, status: 'applied' }
        }
      }
    })
    studentApi.getApplications.mockResolvedValue(applicationsPayload)
    studentApi.scoreResumeForJob.mockResolvedValue({
      data: {
        data: {
          analysis: {
            score: 87,
            matched_count: 5,
            recommendation: 'Strong fit',
            matched_keywords: ['python', 'sql', 'api', 'flask', 'backend'],
            missing_keywords: ['redis']
          },
          job: {
            id: 51,
            title: 'Backend Engineer'
          }
        }
      }
    })
    studentApi.getHistory.mockResolvedValue(historyPayload)
    studentApi.getNotifications.mockResolvedValue(notificationsPayload)
    studentApi.respondToOffer.mockResolvedValue({ data: { success: true } })
    studentApi.markNotificationRead.mockResolvedValue({
      data: { data: { unread_count: 0 } }
    })
    studentApi.markAllNotificationsRead.mockResolvedValue({
      data: { data: { unread_count: 0 } }
    })
    studentApi.downloadOfferDocument.mockResolvedValue({
      data: new Blob(['offer text'], { type: 'text/plain' }),
      headers: {
        'content-disposition': 'attachment; filename="offer-letter-44.txt"'
      }
    })
    studentApi.downloadPlacementDocument.mockResolvedValue({
      data: new Blob(['placement text'], { type: 'text/plain' }),
      headers: {
        'content-disposition': 'attachment; filename="placement-confirmation-55.txt"'
      }
    })
    studentApi.updateProfile.mockResolvedValue({
      data: {
        data: {
          student: {
            branch: 'CSE',
            year: 3,
            roll_number: 'CS21B042',
            resume_url: 'https://example.com/resume.pdf'
          }
        }
      }
    })
    studentApi.uploadResume.mockResolvedValue({
      data: {
        data: {
          student: {
            resume_url: 'http://127.0.0.1:5000/student/resume-files/student-1-new.pdf'
          }
        }
      }
    })
  })

  it('loads dashboard, applications, and notifications on bootstrap', async () => {
    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    expect(authApi.getMe).toHaveBeenCalledTimes(1)
    expect(studentApi.getDashboard).toHaveBeenCalledTimes(1)
    expect(studentApi.getProfile).toHaveBeenCalledTimes(1)
    expect(studentApi.getApplications).toHaveBeenCalledTimes(1)
    expect(studentApi.getNotifications).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Platform Engineer')
  })

  it('submits offer response from applications view', async () => {
    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-applications').trigger('click')
    await flushPromises()

    const viewButton = wrapper.findAll('button').find((node) => node.text() === 'View')
    expect(viewButton).toBeTruthy()
    await viewButton.trigger('click')
    await flushPromises()

    const modal = wrapper.find('.rq-application-modal')
    expect(modal.exists()).toBe(true)

    const acceptButton = modal.findAll('button').find((node) => node.text() === 'Accept')
    expect(acceptButton).toBeTruthy()

    await acceptButton.trigger('click')
    await flushPromises()
    await flushPromises()

    expect(studentApi.respondToOffer).toHaveBeenCalledWith(701, { status: 'accepted' })
  })

  it('loads drives and applies for an eligible open drive', async () => {
    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-drives').trigger('click')
    await flushPromises()

    expect(studentApi.getDrives).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Frontend Developer')

    const applyButton = wrapper.findAll('button').find((node) => node.text() === 'Apply Now')
    expect(applyButton).toBeTruthy()

    await applyButton.trigger('click')
    await flushPromises()

    const modal = wrapper.find('.rq-modal')
    expect(modal.exists()).toBe(true)

    const modalApplyButton = modal.findAll('button').find((node) => node.text() === 'Apply Now')
    expect(modalApplyButton).toBeTruthy()
    await modalApplyButton.trigger('click')
    await flushPromises()
    await flushPromises()

    expect(studentApi.applyToDrive).toHaveBeenCalledWith(63)
  })

  it('opens drive details from the Apply action and clears it on section change', async () => {
    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-drives').trigger('click')
    await flushPromises()

    const applyButton = wrapper.findAll('button').find((node) => node.text() === 'Apply Now')
    expect(applyButton).toBeTruthy()

    await applyButton.trigger('click')
    await flushPromises()

    expect(wrapper.vm.selectedDrive?.drive_id).toBe(63)
    expect(wrapper.text()).toContain('Drive Details')

    await wrapper.get('.to-notifications').trigger('click')
    await flushPromises()

    expect(wrapper.vm.selectedDrive).toBeNull()
    expect(wrapper.text()).not.toContain('Drive Details')
  })

  it('applies from drive details modal and closes the modal', async () => {
    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-drives').trigger('click')
    await flushPromises()

    const applyButton = wrapper.findAll('button').find((node) => node.text() === 'Apply Now')
    expect(applyButton).toBeTruthy()
    await applyButton.trigger('click')
    await flushPromises()

    const modal = wrapper.find('.rq-modal')
    expect(modal.exists()).toBe(true)

    const modalApplyButton = modal.findAll('button').find((node) => node.text() === 'Apply Now')
    expect(modalApplyButton).toBeTruthy()
    await modalApplyButton.trigger('click')
    await flushPromises()
    await flushPromises()

    expect(studentApi.applyToDrive).toHaveBeenCalledWith(63)
    expect(wrapper.vm.selectedDrive).toBeNull()
  })

  it('loads history and calls offer/placement document downloads', async () => {
    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-history').trigger('click')
    await flushPromises()

    expect(studentApi.getHistory).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('SRE Engineer')

    const offerButton = wrapper.findAll('button').find((node) => node.text() === 'Offer Letter')
    expect(offerButton).toBeTruthy()
    await offerButton.trigger('click')
    await flushPromises()

    const placementButton = wrapper.findAll('button').find((node) => node.text() === 'Placement Doc')
    expect(placementButton).toBeTruthy()
    await placementButton.trigger('click')
    await flushPromises()

    expect(studentApi.downloadOfferDocument).toHaveBeenCalledWith(44)
    expect(studentApi.downloadPlacementDocument).toHaveBeenCalledWith(55)
  })

  it('marks notifications and saves profile with current schema', async () => {
    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-notifications').trigger('click')
    await flushPromises()

    const markReadButton = wrapper.find('button[aria-label^="Mark notification"]')
    expect(markReadButton).toBeTruthy()

    await markReadButton.trigger('click')
    await flushPromises()

    expect(studentApi.markNotificationRead).toHaveBeenCalledWith(801)

    await wrapper.get('.to-profile').trigger('click')
    await flushPromises()

    await wrapper.find('input[placeholder="College name"]').setValue('My Engineering College')
    await wrapper.find('input[placeholder="Branch"]').setValue('ECE')
    await wrapper.find('input[placeholder="Year"]').setValue('4')
    await wrapper.find('input[placeholder="CGPA"]').setValue('8.9')
    await wrapper.find('input[placeholder="Roll number"]').setValue('CS21B099')
    await wrapper.find('input[placeholder="Phone number"]').setValue('9876543210')
    await wrapper.find('input[placeholder="https://example.com/resume.pdf"]').setValue('https://example.com/new-resume.pdf')
    await wrapper.find('input[placeholder="Python, SQL, Vue, DSA"]').setValue('Vue, Flask, SQL')
    await wrapper.find('textarea[placeholder="Summarize internships, projects, and key responsibilities"]').setValue(
      'Built and shipped two production student portals.'
    )

    const saveButton = wrapper.findAll('button').find((node) => node.text() === 'Save Profile')
    expect(saveButton).toBeTruthy()

    await saveButton.trigger('click')
    await flushPromises()

    expect(studentApi.updateProfile).toHaveBeenCalledWith({
      college_name: 'My Engineering College',
      branch: 'ECE',
      year: 4,
      cgpa: 8.9,
      roll_number: 'CS21B099',
      phone: '9876543210',
      resume_url: 'https://example.com/new-resume.pdf',
      skills: 'Vue, Flask, SQL',
      experience_summary: 'Built and shipped two production student portals.'
    })
  })

  it('keeps comma while typing skills input', async () => {
    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-profile').trigger('click')
    await flushPromises()

    const skillsInput = wrapper.find('input[placeholder="Python, SQL, Vue, DSA"]')
    await skillsInput.setValue('DSA, ')
    await flushPromises()

    expect(wrapper.vm.profileForm.skills).toBe('DSA, ')

    await skillsInput.setValue('DSA, React')
    await flushPromises()

    expect(wrapper.vm.profileForm.skills).toBe('DSA, React')
  })

  it('uploads resume file from profile view and updates resume URL', async () => {
    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.get('.to-profile').trigger('click')
    await flushPromises()

    const fileInput = wrapper.find('input[type="file"]')
    const resumeFile = new File(['resume-content'], 'resume.pdf', { type: 'application/pdf' })

    Object.defineProperty(fileInput.element, 'files', {
      value: [resumeFile],
      configurable: true
    })
    await fileInput.trigger('change')
    await flushPromises()
    await flushPromises()

    expect(studentApi.uploadResume).toHaveBeenCalledTimes(1)
    expect(studentApi.uploadResume).toHaveBeenCalledWith(expect.any(File))
    expect(wrapper.vm.profileForm.resume_url).toContain('/student/resume-files/')
  })

  it('blocks profile save when CGPA is out of range', async () => {
    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    wrapper.vm.profileForm = {
      ...wrapper.vm.profileForm,
      college_name: 'My Engineering College',
      branch: 'ECE',
      year: 4,
      cgpa: 11,
      roll_number: 'CS21B099',
      phone: '9876543210',
      resume_url: 'https://example.com/new-resume.pdf',
      skills: 'Vue, Flask, SQL',
      experience_summary: 'Built and shipped two production student portals.'
    }

    await wrapper.vm.saveProfile()

    expect(studentApi.updateProfile).not.toHaveBeenCalled()
    expect(wrapper.vm.profileError).toContain('CGPA must be between 0 and 10')
  })

  it('scores ATS match for an application and stores result', async () => {
    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.vm.scoreApplicationMatch(wrapper.vm.applications[0])
    await flushPromises()

    expect(studentApi.scoreResumeForJob).toHaveBeenCalledWith(51)
    expect(wrapper.vm.atsScoresByApplication[501]?.analysis?.score).toBe(87)
    expect(wrapper.vm.selectedApplication?.application_id).toBe(501)
    expect(wrapper.vm.isScoringMatch[501]).toBe(false)
  })

  it('shows ATS scoring errors when screener API fails', async () => {
    studentApi.scoreResumeForJob.mockRejectedValueOnce({
      response: {
        data: {
          error: 'ATS scoring failed'
        }
      }
    })

    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    await wrapper.vm.scoreApplicationMatch(wrapper.vm.applications[0])
    await flushPromises()

    expect(studentApi.scoreResumeForJob).toHaveBeenCalledWith(51)
    expect(wrapper.vm.applicationsError).toContain('ATS scoring failed')
    expect(wrapper.vm.isScoringMatch[501]).toBe(false)
  })

  it('shows an info note and skips ATS request when job identifier is missing', async () => {
    const wrapper = mountWrapper()
    await flushPromises()
    await flushPromises()

    const noteSpy = vi.spyOn(wrapper.vm, 'publishActionNote')

    await wrapper.vm.scoreApplicationMatch({
      application_id: 777,
      drive: null,
      drive_id: null,
      job_id: null
    })

    expect(studentApi.scoreResumeForJob).not.toHaveBeenCalled()
    expect(noteSpy).toHaveBeenCalledWith('ATS match is unavailable for this application right now.', 'info')
  })
})
