import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import StudentsTable from '../../src/components/admin/StudentsTable.vue'

const baseProps = {
  filteredStudents: [],
  stuSearch: '',
  stuSearchFocused: false,
  stuBranch: '',
  branchFilterOptions: ['All', 'CSE'],
  stuPage: 1,
  stuPages: 1,
  stuTotal: 0,
  stuSortBy: 'created_at',
  stuOrder: 'desc',
  isLoading: false,
  errorMessage: '',
  pendingStudentActions: {},
  isExportBusy: false,
  exportLabel: 'Export CSV'
}

function buildStudent(applications) {
  return {
    id: `stu-${applications}`,
    name: `Student ${applications}`,
    email: `student${applications}@example.com`,
    roll: `ROLL-${applications}`,
    branch: 'CSE',
    year: 4,
    cgpa: 8.2,
    applications,
    status: 'active',
    initials: 'ST',
    color: '#2563EB',
    appList: []
  }
}

describe('StudentsTable application count label', () => {
  it('formats 0 as 0 Application', () => {
    const wrapper = mount(StudentsTable, {
      props: {
        ...baseProps,
        filteredStudents: [buildStudent(0)]
      }
    })

    expect(wrapper.get('button.rq-link').text()).toBe('0 Application')
  })

  it('formats 1 as 1 Application', () => {
    const wrapper = mount(StudentsTable, {
      props: {
        ...baseProps,
        filteredStudents: [buildStudent(1)]
      }
    })

    expect(wrapper.get('button.rq-link').text()).toBe('1 Application')
  })

  it('formats counts above 1 as plural Applications', () => {
    const wrapper = mount(StudentsTable, {
      props: {
        ...baseProps,
        filteredStudents: [buildStudent(3)]
      }
    })

    expect(wrapper.get('button.rq-link').text()).toBe('3 Applications')
  })
})
