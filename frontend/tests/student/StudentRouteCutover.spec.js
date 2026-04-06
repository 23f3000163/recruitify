import { describe, expect, it } from 'vitest'

import router from '../../src/router'
import StudentDashboard from '../../src/views/student/StudentDashboard.vue'

describe('Student route cutover', () => {
  it('maps default student routes to student dashboard', async () => {
    const defaultStudent = router.resolve('/student')
    const v2Alias = router.resolve('/student-v2')

    const defaultLoader = defaultStudent.matched[0]?.components?.default
    const aliasLoader = v2Alias.matched[0]?.components?.default

    expect(typeof defaultLoader).toBe('function')
    expect(typeof aliasLoader).toBe('function')

    const defaultModule = await defaultLoader()
    const aliasModule = await aliasLoader()

    expect(defaultModule.default).toBe(StudentDashboard)
    expect(aliasModule.default).toBe(StudentDashboard)
  })

  it('removes legacy student route after stabilization', () => {
    const hasLegacyRoute = router.getRoutes().some((route) => route.path === '/student-legacy')

    expect(hasLegacyRoute).toBe(false)
  })

  it('uses lazy-loaded component loaders for primary routes', () => {
    const landing = router.resolve('/')
    const login = router.resolve('/login')
    const company = router.resolve('/company')

    expect(typeof landing.matched[0]?.components?.default).toBe('function')
    expect(typeof login.matched[0]?.components?.default).toBe('function')
    expect(typeof company.matched[0]?.components?.default).toBe('function')
  })
})
