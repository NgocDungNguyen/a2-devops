<script setup>
import StarRating from '@/components/common/StarRating.vue'
import { shortDate } from '@/utils/format'

defineProps({
  reviews: { type: Array, default: () => [] }
})
</script>

<template>
  <p v-if="!reviews.length" class="text-muted">
    No reviews yet — be the first to write one.
  </p>

  <ul v-else class="list-unstyled d-grid gap-4 mb-0">
    <li v-for="review in reviews" :key="review.id" class="d-flex gap-3">
      <span class="review-avatar flex-shrink-0" aria-hidden="true">
        {{ review.author_initial }}
      </span>

      <div class="flex-grow-1 min-w-0">
        <div class="d-flex flex-wrap align-items-center gap-2">
          <strong>{{ review.title }}</strong>
          <StarRating :model-value="review.rating" :size="14" />
        </div>

        <div class="small text-muted mb-2">
          {{ review.author_name }} · {{ shortDate(review.created_at) }}
          <span v-if="review.is_recommended" class="badge text-bg-light ms-1">
            Recommends this product
          </span>
        </div>

        <p class="mb-0">{{ review.review }}</p>
      </div>
    </li>
  </ul>
</template>
