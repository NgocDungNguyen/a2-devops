import { defineStore } from 'pinia'
import { ref } from 'vue'

import { manageReviewApi, productApi, reviewApi } from '@/api'

const EMPTY_SUMMARY = {
  average: 0,
  total_reviews: 0,
  breakdown: { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
}

export const useReviewsStore = defineStore('reviews', () => {
  const reviews = ref([])
  // Computed by the server in one query, so the stars on a shop card and the
  // bars on the product page can never disagree.
  const summary = ref({ ...EMPTY_SUMMARY })
  const moderationQueue = ref([])
  const pagination = ref({ count: 0, total_pages: 1, current_page: 1 })
  const loading = ref(false)

  async function fetchForProduct(slug, params = {}) {
    loading.value = true
    try {
      const { data } = await productApi.reviews(slug, params)
      reviews.value = data.results
      summary.value = data.summary || { ...EMPTY_SUMMARY }
      pagination.value = {
        count: data.count,
        total_pages: data.total_pages,
        current_page: data.current_page
      }
      return data
    } finally {
      loading.value = false
    }
  }

  async function create(payload) {
    const { data } = await reviewApi.create(payload)
    return data
  }

  async function fetchModerationQueue(params = {}) {
    loading.value = true
    try {
      const { data } = await manageReviewApi.list(params)
      moderationQueue.value = data.results
      pagination.value = {
        count: data.count,
        total_pages: data.total_pages,
        current_page: data.current_page
      }
      return data
    } finally {
      loading.value = false
    }
  }

  async function approve(id) {
    const { data } = await manageReviewApi.approve(id)
    patchQueue(data)
    return data
  }

  async function reject(id) {
    const { data } = await manageReviewApi.reject(id)
    patchQueue(data)
    return data
  }

  function patchQueue(updated) {
    const index = moderationQueue.value.findIndex((r) => r.id === updated.id)
    if (index !== -1) moderationQueue.value[index] = updated
  }

  return {
    reviews,
    summary,
    moderationQueue,
    pagination,
    loading,
    fetchForProduct,
    create,
    fetchModerationQueue,
    approve,
    reject
  }
})
