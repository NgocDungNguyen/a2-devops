<script setup>
defineProps({
  label: { type: String, default: 'Loading…' },
  compact: { type: Boolean, default: false }
})
</script>

<template>
  <div
    class="d-flex align-items-center justify-content-center text-muted gap-2"
    :class="compact ? 'py-2' : 'py-5'"
    role="status"
  >
    <span class="spinner-border spinner-border-sm text-primary" aria-hidden="true" />
    <span>{{ label }}</span>
  </div>
</template>
