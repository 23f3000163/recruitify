<template>
  <div
    v-if="message"
    class="rq-action-note"
    :class="`tone-${tone}`"
    role="status"
    aria-live="polite"
  >
    {{ message }}
  </div>
</template>

<script>
export default {
  name: 'StudentToast',
  props: {
    message: {
      type: String,
      default: ''
    },
    tone: {
      type: String,
      default: 'info'
    }
  }
}
</script>
