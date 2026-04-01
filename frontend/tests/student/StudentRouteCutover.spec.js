import { describe, expect, it } from 'vitest'

import router from '../../src/router'
import StudentDashboardV2 from '../../src/views/student/StudentDashboardV2.vue'

describe('Student route cutover', () => {
  it('maps default student routes to V2 dashboard', () => {
    const defaultStudent = router.resolve('/student')
    const v2Alias = router.resolve('/student-v2')

    expect(defaultStudent.matched[0]?.components?.default).toBe(StudentDashboardV2)
    expect(v2Alias.matched[0]?.components?.default).toBe(StudentDashboardV2)
  })

  it('removes legacy student route after stabilization', () => {
    const hasLegacyRoute = router.getRoutes().some((route) => route.path === '/student-legacy')

    expect(hasLegacyRoute).toBe(false)
  })
})
