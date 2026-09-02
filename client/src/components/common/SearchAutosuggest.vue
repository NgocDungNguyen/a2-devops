<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { productApi } from '@/api'
import { useDebounce } from '@/composables/useDebounce'
import { imageOrPlaceholder, money } from '@/utils/format'
import AppIcon from './AppIcon.vue'

const router = useRouter()

const term = ref('')
const suggestions = ref([])
const isOpen = ref(false)
const activeIndex = ref(-1)

const search = useDebounce(async (value) => {
  if (value.trim().length < 2) {
    suggestions.value = []
    isOpen.value = false
    return
  }
  try {
    const { data } = await productApi.search(value.trim())
    suggestions.value = data
    isOpen.value = data.length > 0
    activeIndex.value = -1
  } catch {
    suggestions.value = []
    isOpen.value = false
  }
}, 300)

function onInput() {
  search(term.value)
}

function choose(product) {
  isOpen.value = false
  term.value = ''
  suggestions.value = []
  router.push({ name: 'product', params: { slug: product.slug } })
}

function submit() {
  const value = term.value.trim()
  if (!value) return
  isOpen.value = false
  router.push({ name: 'shop', query: { search: value } })
  term.value = ''
}

function onKeydown(event) {
  if (!isOpen.value) return
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    activeIndex.value = (activeIndex.value + 1) % suggestions.value.length
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    activeIndex.value =
      activeIndex.value <= 0 ? suggestions.value.length - 1 : activeIndex.value - 1
  } else if (event.key === 'Enter' && activeIndex.value >= 0) {
    event.preventDefault()
    choose(suggestions.value[activeIndex.value])
  } else if (event.key === 'Escape') {
    isOpen.value = false
  }
}

function closeSoon() {
  // Delay so a click on a suggestion registers before the list disappears.
  setTimeout(() => {
    isOpen.value = false
  }, 150)
}

function escapeHtml(text) {
  return String(text).replace(
    /[&<>"']/g,
    (character) =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      })[character]
  )
}

/**
 * Bold the part of the name that matched, as the original did.
 *
 * The name is escaped before the <strong> tags go in. Product names are
 * written by merchants, so treating one as trusted markup would let a seller
 * inject script into every shopper's search box.
 */
function highlight(name) {
  const safe = escapeHtml(name)
  const value = term.value.trim()
  if (!value) return safe

  const index = safe.toLowerCase().indexOf(escapeHtml(value).toLowerCase())
  if (index === -1) return safe

  const length = escapeHtml(value).length
  return (
    safe.slice(0, index) +
    `<strong>${safe.slice(index, index + length)}</strong>` +
    safe.slice(index + length)
  )
}
</script>

<template>
  <div class="position-relative flex-grow-1">
    <form class="d-flex" role="search" @submit.prevent="submit">
      <div class="input-group input-group-sm">
        <input
          v-model="term"
          type="search"
          class="form-control"
          placeholder="Search for merchandise…"
          aria-label="Search products"
          autocomplete="off"
          @input="onInput"
          @keydown="onKeydown"
          @focus="isOpen = suggestions.length > 0"
          @blur="closeSoon"
        />
        <button class="btn btn-outline-secondary" type="submit" aria-label="Search">
          <AppIcon name="search" :size="16" />
        </button>
      </div>
    </form>

    <div v-if="isOpen" class="search-suggestions">
      <button
        v-for="(item, index) in suggestions"
        :key="item.id"
        type="button"
        :class="{ 'is-active': index === activeIndex }"
        @mousedown.prevent="choose(item)"
      >
        <img :src="imageOrPlaceholder(item.image_url)" :alt="item.name" />
        <span class="flex-grow-1 min-w-0">
          <span class="d-block text-truncate" v-html="highlight(item.name)" />
          <small class="text-brand">{{ money(item.price) }}</small>
        </span>
      </button>
    </div>
  </div>
</template>
