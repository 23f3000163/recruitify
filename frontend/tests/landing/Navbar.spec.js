import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Navbar from '../../src/components/layout/Navbar.vue'

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

const mountNavbar = (path = '/') => {
  const push = vi.fn().mockResolvedValue(undefined)
  const wrapper = mount(Navbar, {
    global: {
      mocks: {
        $router: { push },
        $route: { path }
      }
    }
  })

  return { wrapper, push }
}

describe('Landing navbar smooth-scroll wiring', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.body.innerHTML = ''
    window.scrollTo = vi.fn()
    Object.defineProperty(window, 'scrollY', {
      configurable: true,
      value: 0
    })
  })

  it('scrolls to top and routes to landing page when triggered outside landing', async () => {
    const { wrapper, push } = mountNavbar('/login')

    vi.spyOn(wrapper.vm, 'waitForElement').mockResolvedValue(true)

    await wrapper.vm.scrollToTop()

    expect(push).toHaveBeenCalledWith('/')
    expect(window.scrollTo).toHaveBeenCalledWith({
      top: 0,
      behavior: 'smooth'
    })
  })

  it('scrolls to section with navbar offset when a target exists', async () => {
    const { wrapper } = mountNavbar('/')

    document.body.innerHTML = '<div id="navbar"></div><section id="who"></section>'

    const navbar = document.getElementById('navbar')
    const section = document.getElementById('who')

    Object.defineProperty(navbar, 'offsetHeight', {
      configurable: true,
      value: 72
    })

    section.getBoundingClientRect = vi.fn(() => ({
      top: 300,
      left: 0,
      right: 0,
      bottom: 0,
      width: 0,
      height: 0,
      x: 0,
      y: 300,
      toJSON: () => ({})
    }))

    Object.defineProperty(window, 'scrollY', {
      configurable: true,
      value: 120
    })

    vi.spyOn(wrapper.vm, 'waitForElement').mockResolvedValue(true)

    await wrapper.vm.scrollToSection('who')

    expect(window.scrollTo).toHaveBeenCalledWith({
      top: 336,
      behavior: 'smooth'
    })
  })

  it('wires nav links to section/top scroll handlers', async () => {
    const { wrapper } = mountNavbar('/')

    const scrollToSectionSpy = vi.spyOn(wrapper.vm, 'scrollToSection').mockResolvedValue()
    const scrollToTopSpy = vi.spyOn(wrapper.vm, 'scrollToTop').mockResolvedValue()

    const links = wrapper.findAll('.nav-link')

    await links[1].trigger('click')
    await links[2].trigger('click')
    await links[3].trigger('click')
    await flushPromises()

    expect(scrollToSectionSpy).toHaveBeenCalledWith('who')
    expect(scrollToSectionSpy).toHaveBeenCalledWith('pipeline')
    expect(scrollToTopSpy).toHaveBeenCalledTimes(1)
  })
})
