<template>
  <section class="not-found">
    <div class="not-found-card">
      <p class="not-found-code">404</p>
      <h1 class="not-found-title">Page not found</h1>
      <p class="not-found-text">The page you're looking for doesn't exist or has moved.</p>
      <router-link class="not-found-link" to="/">Go back home</router-link>
    </div>
  </section>
</template>

<script>
export default {
  name: 'NotFound'
}
</script>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: #f8fafc;
}

.not-found-card {
  text-align: center;
  max-width: 420px;
}

.not-found-code {
  font-size: 64px;
  font-weight: 700;
  color: #2563eb;
  margin: 0;
}

.not-found-title {
  font-size: 24px;
  font-weight: 600;
  color: #0f172a;
  margin: 8px 0;
}

.not-found-text {
  color: #64748b;
  margin: 0 0 20px;
}

.not-found-link {
  display: inline-block;
  padding: 10px 20px;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
  text-decoration: none;
  font-weight: 600;
}

.not-found-link:hover {
  background: #1d4ed8;
}
</style>
