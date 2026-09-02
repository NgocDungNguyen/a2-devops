<script setup>
import { reactive, ref } from 'vue'

import StarRating from '@/components/common/StarRating.vue'
import { useAuthStore } from '@/stores/auth'
import { useReviewsStore } from '@/stores/reviews'
import { useUiStore } from '@/stores/ui'
import { errorMessage, fieldErrors } from '@/utils/format'

const props = defineProps({
  productId: { type: Number, required: true }
})

const emit = defineEmits(['created'])

const auth = useAuthStore()
const reviews = useReviewsStore()
const ui = useUiStore()

const form = reactive({
  title: '',
  review: '',
  rating: 5,
  is_recommended: true
})
const errors = ref({})
const submitting = ref(false)

async function submit() {
  errors.value = {}
  submitting.value = true
  try {
    await reviews.create({ product: props.productId, ...form })
    ui.success('Thanks — your review has been published.')
    Object.assign(form, { title: '', review: '', rating: 5, is_recommended: true })
    emit('created')
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error, 'We could not publish your review.'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="data-card">
    <h3 class="h6 mb-3">Write a review</h3>

    <p v-if="!auth.isAuthenticated" class="text-muted mb-0">
      <RouterLink to="/login">Sign in</RouterLink> to review this product.
    </p>

    <form v-else @submit.prevent="submit">
      <div class="mb-3">
        <label class="form-label" for="review-title">Title</label>
        <input
          id="review-title"
          v-model="form.title"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.title }"
          maxlength="200"
          required
        />
        <div v-if="errors.title" class="invalid-feedback">{{ errors.title }}</div>
      </div>

      <div class="mb-3">
        <label class="form-label" for="review-body">Your review</label>
        <textarea
          id="review-body"
          v-model="form.review"
          class="form-control"
          :class="{ 'is-invalid': errors.review }"
          rows="4"
          required
        />
        <div v-if="errors.review" class="invalid-feedback">{{ errors.review }}</div>
      </div>

      <div class="mb-3">
        <span class="form-label d-block">Rating</span>
        <StarRating v-model="form.rating" :size="26" interactive label="Your rating" />
      </div>

      <div class="mb-3">
        <span class="form-label d-block">Would you recommend this product?</span>
        <div class="btn-group btn-group-sm" role="group">
          <button
            type="button"
            class="btn"
            :class="form.is_recommended ? 'btn-primary' : 'btn-outline-secondary'"
            @click="form.is_recommended = true"
          >
            Yes
          </button>
          <button
            type="button"
            class="btn"
            :class="!form.is_recommended ? 'btn-primary' : 'btn-outline-secondary'"
            @click="form.is_recommended = false"
          >
            No
          </button>
        </div>
      </div>

      <button class="btn btn-primary" type="submit" :disabled="submitting">
        {{ submitting ? 'Publishing…' : 'Publish review' }}
      </button>
    </form>
  </div>
</template>
