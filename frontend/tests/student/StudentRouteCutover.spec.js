import { describe, expect, it } from 'vitest'

import router from '../../src/router'
import StudentDashboard from '../../src/views/student/StudentDashboard.vue'

describe('Student route cutover', () => {
  it('maps default student routes to student dashboard', () => {
    const defaultStudent = router.resolve('/student')
    const v2Alias = router.resolve('/student-v2')

    expect(defaultStudent.matched[0]?.components?.default).toBe(StudentDashboard)
    expect(v2Alias.matched[0]?.components?.default).toBe(StudentDashboard)
  })

  it('removes legacy student route after stabilization', () => {
    const hasLegacyRoute = router.getRoutes().some((route) => route.path === '/student-legacy')

    expect(hasLegacyRoute).toBe(false)
  })
})
