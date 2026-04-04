<template>
  <div class="rq-toast" :class="'toast-' + toast.type" role="alert" aria-live="polite">
    <span class="rq-toast-ico" aria-hidden="true">{{ toast.icon }}</span>
    <span class="rq-toast-msg">{{ toast.message }}</span>
    <button class="rq-toast-x" @click="$emit('dismiss')" aria-label="Dismiss">×</button>
  </div>
</template>

<script>
export default {
  name: 'Toast',
  props: {
    toast: {
      type: Object,
      required: true
    }
  },
  emits: ['dismiss']
}
</script>
