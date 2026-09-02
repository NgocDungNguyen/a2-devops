<script setup>
import { onBeforeUnmount, watch } from 'vue'

import AppIcon from './AppIcon.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  side: { type: String, default: 'right' } // 'left' | 'right'
})

const emit = defineEmits(['close'])

function onKeydown(event) {
  if (event.key === 'Escape') emit('close')
}

// Lock the page behind the drawer, and let Escape close it.
watch(
  () => props.open,
  (isOpen) => {
    document.body.style.overflow = isOpen ? 'hidden' : ''
    if (isOpen) {
      window.addEventListener('keydown', onKeydown)
    } else {
      window.removeEventListener('keydown', onKeydown)
    }
  }
)

onBeforeUnmount(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="open" class="drawer-backdrop" @click="emit('close')" />
    </Transition>

    <Transition :name="side === 'left' ? 'slide-left' : 'slide-right'">
      <aside
        v-if="open"
        class="drawer"
        :class="`drawer--${side}`"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
      >
        <header class="drawer__header">
          <h2 class="h6 mb-0 text-uppercase">{{ title }}</h2>
          <button
            type="button"
            class="icon-button"
            aria-label="Close"
            @click="emit('close')"
          >
            <AppIcon name="close" />
          </button>
        </header>

        <div class="drawer__body">
          <slot />
        </div>

        <footer v-if="$slots.footer" class="drawer__footer">
          <slot name="footer" />
        </footer>
      </aside>
    </Transition>
  </Teleport>
</template>
