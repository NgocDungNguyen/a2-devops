<script setup>
import { reactive, ref } from 'vue'

import { siteApi } from '@/api'
import { useUiStore } from '@/stores/ui'
import { errorMessage, fieldErrors } from '@/utils/format'

const ui = useUiStore()

const form = reactive({ name: '', email: '', message: '' })
const errors = ref({})
const submitting = ref(false)
const submitted = ref(false)

async function submit() {
  errors.value = {}
  submitting.value = true
  try {
    await siteApi.contact({ ...form })
    submitted.value = true
    ui.success('Thanks — we will be in touch shortly.')
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error, 'We could not send your message.'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="container py-4" style="max-width: 640px">
    <h1 class="h3 page-title mb-3">Get in touch</h1>
    <p class="text-muted mb-4">
      Questions about an order, a product or selling with us? Send us a note.
    </p>

    <div v-if="submitted" class="alert alert-success">
      Thanks {{ form.name }} — your message is on its way. We will reply to
      {{ form.email }}.
    </div>

    <form v-else class="data-card" @submit.prevent="submit">
      <div class="mb-3">
        <label class="form-label" for="contact-name">Name</label>
        <input
          id="contact-name"
          v-model="form.name"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.name }"
          required
        />
        <div v-if="errors.name" class="invalid-feedback">{{ errors.name }}</div>
      </div>

      <div class="mb-3">
        <label class="form-label" for="contact-email">Email</label>
        <input
          id="contact-email"
          v-model="form.email"
          type="email"
          class="form-control"
          :class="{ 'is-invalid': errors.email }"
          required
        />
        <div v-if="errors.email" class="invalid-feedback">{{ errors.email }}</div>
      </div>

      <div class="mb-4">
        <label class="form-label" for="contact-message">Message</label>
        <textarea
          id="contact-message"
          v-model="form.message"
          class="form-control"
          :class="{ 'is-invalid': errors.message }"
          rows="5"
          minlength="10"
          required
        />
        <div v-if="errors.message" class="invalid-feedback">{{ errors.message }}</div>
      </div>

      <button class="btn btn-primary" type="submit" :disabled="submitting">
        {{ submitting ? 'Sending…' : 'Send message' }}
      </button>
    </form>
  </div>
</template>
