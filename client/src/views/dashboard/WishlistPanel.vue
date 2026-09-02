<script setup>
import { storeToRefs } from 'pinia'
import { onMounted } from 'vue'

import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import SubPage from '@/components/dashboard/SubPage.vue'
import { useUiStore } from '@/stores/ui'
import { useWishlistStore } from '@/stores/wishlist'
import { errorMessage, imageOrPlaceholder, money, shortDate } from '@/utils/format'

const store = useWishlistStore()
const ui = useUiStore()
const { items, loading } = storeToRefs(store)

onMounted(() => store.fetch())

async function remove(item) {
  try {
    await store.toggle(item.product, false)
    ui.success('Removed from your wishlist.')
  } catch (error) {
    ui.error(errorMessage(error))
  }
}
</script>

<template>
  <SubPage title="Wishlist" description="Products you have saved for later." />

  <LoadingIndicator v-if="loading && !items.length" />

  <p v-else-if="!items.length" class="text-muted">
    Your wishlist is empty.
    <RouterLink to="/shop">Find something you like</RouterLink>.
  </p>

  <ul v-else class="list-unstyled d-grid gap-3 mb-0">
    <li v-for="item in items" :key="item.id" class="data-card d-flex gap-3 align-items-center">
      <img
        :src="imageOrPlaceholder(item.product_image)"
        :alt="item.product_name"
        width="64"
        height="64"
        class="rounded object-fit-cover flex-shrink-0"
      />

      <div class="flex-grow-1 min-w-0">
        <RouterLink
          class="fw-medium d-block text-truncate"
          :to="{ name: 'product', params: { slug: item.product_slug } }"
        >
          {{ item.product_name }}
        </RouterLink>
        <p class="small text-muted mb-0">Added {{ shortDate(item.updated_at) }}</p>
      </div>

      <span class="fw-semibold text-brand">{{ money(item.product_price) }}</span>

      <button class="btn btn-sm btn-outline-danger" type="button" @click="remove(item)">
        Remove
      </button>
    </li>
  </ul>
</template>
