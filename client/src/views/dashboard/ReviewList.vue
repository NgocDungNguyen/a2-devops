<script setup>
import { storeToRefs } from 'pinia'
import { onMounted, ref } from 'vue'

import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import StarRating from '@/components/common/StarRating.vue'
import SubPage from '@/components/dashboard/SubPage.vue'
import { REVIEW_STATUS_LABELS } from '@/config'
import { useReviewsStore } from '@/stores/reviews'
import { useUiStore } from '@/stores/ui'
import { errorMessage, imageOrPlaceholder, shortDate } from '@/utils/format'

const store = useReviewsStore()
const ui = useUiStore()
const { moderationQueue, loading, pagination } = storeToRefs(store)

const statusFilter = ref('')
const busy = ref(null)

function load(page = 1) {
  return store.fetchModerationQueue({
    page,
    status: statusFilter.value || undefined
  })
}

onMounted(() => load())

const statusBadge = {
  waiting: 'text-bg-warning',
  approved: 'text-bg-success',
  rejected: 'text-bg-dark'
}

async function moderate(review, action) {
  busy.value = review.id
  try {
    if (action === 'approve') {
      await store.approve(review.id)
      ui.success('Review approved and published.')
    } else {
      await store.reject(review.id)
      // Rejecting removes it from the product page and from the average.
      ui.info('Review rejected and removed from the product page.')
    }
  } catch (error) {
    ui.error(errorMessage(error))
  } finally {
    busy.value = null
  }
}
</script>

<template>
  <SubPage title="Reviews" description="Moderate what customers have written." />

  <div class="d-flex gap-2 mb-3" style="max-width: 240px">
    <select
      v-model="statusFilter"
      class="form-select form-select-sm"
      aria-label="Filter by status"
      @change="load()"
    >
      <option value="">All statuses</option>
      <option value="approved">Approved</option>
      <option value="waiting">Waiting approval</option>
      <option value="rejected">Rejected</option>
    </select>
  </div>

  <LoadingIndicator v-if="loading && !moderationQueue.length" />

  <p v-else-if="!moderationQueue.length" class="text-muted">No reviews to show.</p>

  <ul v-else class="list-unstyled d-grid gap-3 mb-0">
    <li v-for="review in moderationQueue" :key="review.id" class="data-card">
      <div class="d-flex flex-wrap gap-3">
        <img
          :src="imageOrPlaceholder(review.product_image)"
          :alt="review.product_name"
          width="56"
          height="56"
          class="rounded object-fit-cover flex-shrink-0"
        />

        <div class="flex-grow-1 min-w-0">
          <div class="d-flex flex-wrap align-items-center gap-2 mb-1">
            <strong>{{ review.title }}</strong>
            <StarRating :model-value="review.rating" :size="14" />
            <span class="badge" :class="statusBadge[review.status]">
              {{ REVIEW_STATUS_LABELS[review.status] }}
            </span>
          </div>

          <p class="small text-muted mb-2">
            {{ review.author_name }} ({{ review.author_email }}) on
            <RouterLink :to="{ name: 'product', params: { slug: review.product_slug } }">
              {{ review.product_name }}
            </RouterLink>
            · {{ shortDate(review.created_at) }}
          </p>

          <p class="mb-0">{{ review.review }}</p>
        </div>

        <div class="d-flex flex-column gap-2 align-self-start">
          <button
            class="btn btn-sm btn-outline-success"
            type="button"
            :disabled="busy === review.id || review.status === 'approved'"
            @click="moderate(review, 'approve')"
          >
            Approve
          </button>
          <button
            class="btn btn-sm btn-outline-danger"
            type="button"
            :disabled="busy === review.id || review.status === 'rejected'"
            @click="moderate(review, 'reject')"
          >
            Reject
          </button>
        </div>
      </div>
    </li>
  </ul>

  <div class="mt-4">
    <PaginationBar
      :current-page="pagination.current_page"
      :total-pages="pagination.total_pages"
      @change="load"
    />
  </div>
</template>
