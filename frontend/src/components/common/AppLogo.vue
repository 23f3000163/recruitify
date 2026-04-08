<template>
  <component
    :is="as"
    class="app-logo"
    :href="as === 'a' ? href : undefined"
    :aria-label="ariaLabel"
    @click="handleClick"
  >
    <svg
      v-if="collapsed"
      class="app-logo-svg app-logo-svg-icon"
      width="42"
      height="42"
      viewBox="0 0 42 42"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <rect width="42" height="42" rx="13" fill="#111111"/>
      <defs>
        <clipPath :id="iconLensId">
          <circle cx="18.5" cy="17.5" r="10.5"/>
        </clipPath>
      </defs>
      <circle cx="18.5" cy="17.5" r="10.5" fill="none" stroke="white" stroke-width="2.2"/>
      <circle cx="15.5" cy="13" r="3" fill="white"/>
      <path d="M9.5 21 Q9.5 17.5 15.5 17.5 Q21.5 17.5 21.5 21" fill="white" :clip-path="`url(#${iconLensId})`"/>
      <circle cx="22" cy="14" r="2.4" fill="rgba(255,255,255,0.5)"/>
      <path d="M17 21.5 Q17 18.5 22 18.5 Q27 18.5 27 21.5" fill="rgba(255,255,255,0.38)" :clip-path="`url(#${iconLensId})`"/>
      <line x1="26.5" y1="25" x2="35" y2="34" stroke="white" stroke-width="3" stroke-linecap="round"/>
    </svg>

    <svg
      v-else
      class="app-logo-svg app-logo-svg-lockup"
      width="220"
      height="42"
      viewBox="0 0 220 42"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <rect width="42" height="42" rx="13" fill="#111111"/>
      <defs>
        <clipPath :id="lockupLensId">
          <circle cx="18.5" cy="17.5" r="10.5"/>
        </clipPath>
      </defs>
      <circle cx="18.5" cy="17.5" r="10.5" fill="none" stroke="white" stroke-width="2.2"/>
      <circle cx="15.5" cy="13" r="3" fill="white"/>
      <path d="M9.5 21 Q9.5 17.5 15.5 17.5 Q21.5 17.5 21.5 21" fill="white" :clip-path="`url(#${lockupLensId})`"/>
      <circle cx="22" cy="14" r="2.4" fill="rgba(255,255,255,0.5)"/>
      <path d="M17 21.5 Q17 18.5 22 18.5 Q27 18.5 27 21.5" fill="rgba(255,255,255,0.38)" :clip-path="`url(#${lockupLensId})`"/>
      <line x1="26.5" y1="25" x2="35" y2="34" stroke="white" stroke-width="3" stroke-linecap="round"/>
      <text x="54" y="29" font-family="Georgia, 'Times New Roman', serif" font-size="24" font-weight="700" fill="#111111">Recruitify.</text>
    </svg>
  </component>
</template>

<script setup>
const uid = Math.random().toString(36).slice(2, 10)
const iconLensId = `recruitify-lens-icon-${uid}`
const lockupLensId = `recruitify-lens-lockup-${uid}`

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  },
  as: {
    type: String,
    default: 'a'
  },
  href: {
    type: String,
    default: '#'
  },
  ariaLabel: {
    type: String,
    default: 'Recruitify'
  }
})

const emit = defineEmits(['click'])

function handleClick(event) {
  if (props.as === 'a' && props.href === '#') {
    event.preventDefault()
  }

  emit('click', event)
}
</script>

<style scoped>
.app-logo {
  display: inline-flex;
  align-items: center;
  text-decoration: none;
  min-width: 0;
  color: inherit;
  line-height: 1;
}

.app-logo-svg {
  display: block;
  flex-shrink: 0;
}

.app-logo-svg-icon {
  width: var(--app-logo-icon-size, 36px);
  height: var(--app-logo-icon-size, 36px);
}

.app-logo-svg-lockup {
  width: var(--app-logo-lockup-width, 220px);
  height: var(--app-logo-lockup-height, 42px);
  max-width: 100%;
}
</style>