<template>
  <section class="rq-view">
    <article class="rq-card">
      <header class="rq-card-hd">
        <span class="rq-card-title">{{ title }}</span>
      </header>
      <div class="rq-card-body">
        <p class="rq-placeholder-text">{{ description }}</p>
      </div>
    </article>
  </section>
</template>

<script>
export default {
  name: 'StudentSectionPlaceholder',
  props: {
    title: {
      type: String,
      default: 'Section'
    },
    description: {
      type: String,
      default: 'This section is scaffolded in Step 2 and will be API wired in Step 3.'
    }
  }
}
</script>
