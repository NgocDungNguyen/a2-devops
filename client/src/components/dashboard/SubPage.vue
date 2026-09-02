<script setup>
/** Title bar shared by every dashboard screen, with an optional action slot. */
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' }
})
</script>

<template>
  <div class="subpage-header">
    <div>
      <h1 class="h5 page-title mb-0">{{ title }}</h1>
      <p v-if="description" class="small text-muted mb-0 mt-1">{{ description }}</p>
    </div>
    <div v-if="$slots.action" class="d-flex gap-2">
      <slot name="action" />
    </div>
  </div>
</template>
