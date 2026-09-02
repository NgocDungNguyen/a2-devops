<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: { type: Number, required: true },
  totalPages: { type: Number, required: true },
  maxButtons: { type: Number, default: 7 }
})

const emit = defineEmits(['change'])

/** A sliding window of page numbers, so 200 pages do not render 200 buttons. */
const pages = computed(() => {
  const { currentPage, totalPages, maxButtons } = props
  if (totalPages <= maxButtons) {
    return Array.from({ length: totalPages }, (_, i) => i + 1)
  }
  const half = Math.floor(maxButtons / 2)
  let start = Math.max(1, currentPage - half)
  const end = Math.min(totalPages, start + maxButtons - 1)
  start = Math.max(1, end - maxButtons + 1)
  return Array.from({ length: end - start + 1 }, (_, i) => start + i)
})

function go(page) {
  if (page < 1 || page > props.totalPages || page === props.currentPage) return
  emit('change', page)
}
</script>

<template>
  <nav v-if="totalPages > 1" aria-label="Pagination">
    <ul class="pagination pagination-sm justify-content-center mb-0">
      <li class="page-item" :class="{ disabled: currentPage === 1 }">
        <button class="page-link" type="button" @click="go(currentPage - 1)">
          Previous
        </button>
      </li>

      <li v-if="pages[0] > 1" class="page-item">
        <button class="page-link" type="button" @click="go(1)">1</button>
      </li>
      <li v-if="pages[0] > 2" class="page-item disabled">
        <span class="page-link">…</span>
      </li>

      <li
        v-for="page in pages"
        :key="page"
        class="page-item"
        :class="{ active: page === currentPage }"
      >
        <button class="page-link" type="button" @click="go(page)">{{ page }}</button>
      </li>

      <li v-if="pages[pages.length - 1] < totalPages - 1" class="page-item disabled">
        <span class="page-link">…</span>
      </li>
      <li v-if="pages[pages.length - 1] < totalPages" class="page-item">
        <button class="page-link" type="button" @click="go(totalPages)">
          {{ totalPages }}
        </button>
      </li>

      <li class="page-item" :class="{ disabled: currentPage === totalPages }">
        <button class="page-link" type="button" @click="go(currentPage + 1)">
          Next
        </button>
      </li>
    </ul>
  </nav>
</template>
