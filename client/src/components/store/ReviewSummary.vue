<script setup>
import { computed } from 'vue'

import StarRating from '@/components/common/StarRating.vue'

const props = defineProps({
  summary: { type: Object, required: true }
})

/** Percentage bars, highest star first. */
const rows = computed(() =>
  [5, 4, 3, 2, 1].map((star) => {
    const count = props.summary.breakdown?.[star] ?? 0
    const total = props.summary.total_reviews || 0
    return { star, count, percent: total ? Math.round((count / total) * 100) : 0 }
  })
)
</script>

<template>
  <div class="row g-4 align-items-center">
    <div class="col-12 col-sm-4 text-center">
      <div class="display-5 fw-semibold text-navy">{{ summary.average || 0 }}</div>
      <StarRating :model-value="summary.average || 0" :size="20" />
      <p class="small text-muted mb-0 mt-1">
        Based on {{ summary.total_reviews }}
        review{{ summary.total_reviews === 1 ? '' : 's' }}
      </p>
    </div>

    <div class="col-12 col-sm-8">
      <div v-for="row in rows" :key="row.star" class="d-flex align-items-center gap-2 mb-1">
        <span class="small text-muted" style="width: 3.2rem">{{ row.star }} star</span>
        <div class="rating-bar flex-grow-1">
          <span :style="{ width: `${row.percent}%` }" />
        </div>
        <span class="small text-muted text-end" style="width: 2.5rem">{{ row.count }}</span>
      </div>
    </div>
  </div>
</template>
