<template>
  <div class="skeleton-card" :style="{ height }" aria-hidden="true"></div>
</template>

<script>
export default {
  name: 'SkeletonCard',
  props: {
    height: {
      type: String,
      default: '60px'
    }
  }
}
</script>

<style scoped>
.skeleton-card {
  width: 100%;
  border-radius: 10px;
  background: linear-gradient(90deg, #eef1f5 25%, #e2e6ec 37%, #eef1f5 63%);
  background-size: 400% 100%;
  animation: skeleton-shimmer 1.4s ease infinite;
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}
</style>
