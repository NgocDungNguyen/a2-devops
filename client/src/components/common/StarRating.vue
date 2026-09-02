<script setup>
import { computed } from 'vue'

/**
 * Star rating, read-only or interactive.
 *
 * Supports half stars in display mode via an SVG clip, so a 4.3 average does
 * not have to round to 4.
 */
const props = defineProps({
  modelValue: { type: Number, default: 0 },
  size: { type: [Number, String], default: 16 },
  interactive: { type: Boolean, default: false },
  label: { type: String, default: 'Rating' }
})

const emit = defineEmits(['update:modelValue'])

const stars = computed(() =>
  [1, 2, 3, 4, 5].map((position) => {
    const fill = Math.max(0, Math.min(1, props.modelValue - (position - 1)))
    return { position, fill }
  })
)

function select(position) {
  if (props.interactive) emit('update:modelValue', position)
}
</script>

<template>
  <div
    class="star-rating"
    :role="interactive ? 'radiogroup' : 'img'"
    :aria-label="interactive ? label : `${label}: ${modelValue} out of 5`"
  >
    <component
      :is="interactive ? 'button' : 'span'"
      v-for="star in stars"
      :key="star.position"
      :type="interactive ? 'button' : undefined"
      :class="interactive ? 'btn btn-link p-0 border-0 text-warning lh-1' : ''"
      :aria-label="interactive ? `${star.position} star${star.position > 1 ? 's' : ''}` : undefined"
      :aria-checked="interactive ? modelValue === star.position : undefined"
      :role="interactive ? 'radio' : undefined"
      @click="select(star.position)"
    >
      <svg :width="size" :height="size" viewBox="0 0 24 24" aria-hidden="true">
        <defs>
          <linearGradient :id="`star-${star.position}-${modelValue}`">
            <stop :offset="`${star.fill * 100}%`" stop-color="currentColor" />
            <stop :offset="`${star.fill * 100}%`" stop-color="transparent" />
          </linearGradient>
        </defs>
        <path
          d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
          :fill="`url(#star-${star.position}-${modelValue})`"
          stroke="currentColor"
          stroke-width="1.2"
        />
      </svg>
    </component>
  </div>
</template>
