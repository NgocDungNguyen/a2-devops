<script setup>
import { ref, watch } from 'vue'

import StarRating from '@/components/common/StarRating.vue'
import { money } from '@/utils/format'

const props = defineProps({
  minPrice: { type: [Number, null], default: null },
  maxPrice: { type: [Number, null], default: null },
  minRating: { type: Number, default: 0 }
})

const emit = defineEmits(['apply', 'reset'])

const PRICE_CEILING = 500

const from = ref(props.minPrice ?? 0)
const to = ref(props.maxPrice ?? PRICE_CEILING)
const rating = ref(props.minRating)

watch(
  () => [props.minPrice, props.maxPrice, props.minRating],
  ([nextMin, nextMax, nextRating]) => {
    from.value = nextMin ?? 0
    to.value = nextMax ?? PRICE_CEILING
    rating.value = nextRating
  }
)

function apply() {
  emit('apply', {
    min_price: Number(from.value) > 0 ? Number(from.value) : null,
    max_price: Number(to.value) < PRICE_CEILING ? Number(to.value) : null,
    min_rating: rating.value || 0
  })
}

function setRating(value) {
  rating.value = value
  apply()
}

function reset() {
  from.value = 0
  to.value = PRICE_CEILING
  rating.value = 0
  emit('reset')
}
</script>

<template>
  <aside class="filter-panel">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h6 class="mb-0">Filters</h6>
      <button class="btn btn-link btn-sm p-0" type="button" @click="reset">Reset</button>
    </div>

    <section class="mb-4">
      <h6 class="mb-2">Price</h6>
      <div class="d-flex align-items-center gap-2 mb-2">
        <input
          v-model.number="from"
          type="number"
          class="form-control form-control-sm"
          min="0"
          :max="PRICE_CEILING"
          aria-label="Minimum price"
        />
        <span class="text-muted">–</span>
        <input
          v-model.number="to"
          type="number"
          class="form-control form-control-sm"
          min="0"
          :max="PRICE_CEILING"
          aria-label="Maximum price"
        />
      </div>

      <input
        v-model.number="to"
        type="range"
        class="form-range"
        min="0"
        :max="PRICE_CEILING"
        step="5"
        aria-label="Maximum price slider"
        @change="apply"
      />
      <div class="d-flex justify-content-between small text-muted">
        <span>{{ money(from) }}</span>
        <span>{{ money(to) }}{{ to >= PRICE_CEILING ? '+' : '' }}</span>
      </div>

      <button class="btn btn-sm btn-outline-primary w-100 mt-2" type="button" @click="apply">
        Apply price
      </button>
    </section>

    <section class="rating-filter">
      <h6 class="mb-2">Customer rating</h6>
      <!--
        A row of "4 stars and up" buttons rather than the six-step slider the
        original used, which mapped 0/20/40/60/80/100 onto 5/4/3/2/1/Any and
        was almost impossible to aim at.
      -->
      <div class="d-grid gap-1">
        <button
          v-for="value in [4, 3, 2, 1]"
          :key="value"
          type="button"
          class="btn btn-sm d-flex align-items-center gap-2"
          :class="rating === value ? 'btn-primary' : 'btn-outline-secondary'"
          @click="setRating(value)"
        >
          <StarRating :model-value="value" :size="13" />
          <span>&amp; up</span>
        </button>

        <button
          type="button"
          class="btn btn-sm"
          :class="rating === 0 ? 'btn-primary' : 'btn-outline-secondary'"
          @click="setRating(0)"
        >
          Any rating
        </button>
      </div>
    </section>
  </aside>
</template>
