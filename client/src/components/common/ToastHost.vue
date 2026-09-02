<script setup>
/**
 * Renders the notification toasts, and nothing else.
 *
 * Mounted once in App.vue. Anywhere in the application, any component can call
 * `ui.error('...')` or `ui.success('...')` and a message appears here - the
 * caller does not need a reference to this component, or to be anywhere near
 * it in the tree. The ui store is the post box; this is the noticeboard.
 *
 * `storeToRefs` is needed to pull `toasts` out of the store while keeping it
 * reactive. Plain destructuring - `const { toasts } = ui` - copies the value
 * out and the list would never update. This catches everybody once.
 *
 * `aria-live="polite"` is what makes a screen reader announce a toast that
 * appears without the user having done anything to that part of the page.
 */
import { storeToRefs } from 'pinia'

import { useUiStore } from '@/stores/ui'
import AppIcon from './AppIcon.vue'

const ui = useUiStore()
const { toasts } = storeToRefs(ui)
</script>

<template>
  <div class="toast-host" aria-live="polite" aria-atomic="true">
    <TransitionGroup name="fade">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="alert d-flex align-items-start gap-2 shadow-sm mb-0"
        :class="`alert-${toast.variant}`"
        role="alert"
      >
        <span class="flex-grow-1">{{ toast.message }}</span>
        <button
          type="button"
          class="btn btn-link p-0 text-reset lh-1"
          aria-label="Dismiss"
          @click="ui.dismiss(toast.id)"
        >
          <AppIcon name="close" :size="16" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>
