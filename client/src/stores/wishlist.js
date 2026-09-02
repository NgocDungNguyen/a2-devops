import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { wishlistApi } from '@/api'
import { useCatalogStore } from '@/stores/catalog'

export const useWishlistStore = defineStore('wishlist', () => {
  const items = ref([])
  const loading = ref(false)

  const count = computed(() => items.value.length)
  const likedIds = computed(() => new Set(items.value.map((i) => i.product)))

  async function fetch() {
    loading.value = true
    try {
      const { data } = await wishlistApi.list()
      items.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function toggle(productId, isLiked) {
    await wishlistApi.toggle(productId, isLiked)
    // Keep the shop grid's hearts in step without a second round trip.
    useCatalogStore().applyLiked(productId, isLiked)
    if (!isLiked) {
      items.value = items.value.filter((item) => item.product !== productId)
    } else {
      await fetch()
    }
  }

  function reset() {
    items.value = []
  }

  return { items, loading, count, likedIds, fetch, toggle, reset }
})
