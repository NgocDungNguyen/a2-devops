<script setup>
import { reactive, ref } from 'vue'

import { merchantApi } from '@/api'
import { useUiStore } from '@/stores/ui'
import { errorMessage, fieldErrors } from '@/utils/format'

const ui = useUiStore()

const form = reactive({
  name: '',
  email: '',
  phone_number: '',
  brand_name: '',
  business: ''
})

const errors = ref({})
const submitting = ref(false)
const submitted = ref(false)

async function submit() {
  errors.value = {}
  submitting.value = true
  try {
    const { data } = await merchantApi.apply({ ...form })
    submitted.value = true
    ui.success(data.detail || 'Application received.')
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error, 'We could not submit your application.'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="container py-4">
    <div class="row g-5 align-items-center">
      <div class="col-12 col-lg-6">
        <h1 class="h3 page-title mb-3">Become an RMIT Store seller</h1>
        <p class="lead">
          Run a label? Put it in front of the whole campus. Tell us about your
          business and we will be in touch.
        </p>
        <img
          src="/images/banners/agreement.svg"
          alt=""
          class="img-fluid mt-4 d-none d-lg-block"
        />
      </div>

      <div class="col-12 col-lg-6">
        <div v-if="submitted" class="data-card text-center py-5">
          <h2 class="h5 mb-3">Thanks — we have your application</h2>
          <p class="text-muted mb-4">
            Our team will review it and email you at
            <strong>{{ form.email }}</strong> with the next steps.
          </p>
          <RouterLink class="btn btn-primary" to="/shop">Back to the shop</RouterLink>
        </div>

        <form v-else class="data-card" @submit.prevent="submit">
          <div class="mb-3">
            <label class="form-label" for="name">Your name</label>
            <input
              id="name"
              v-model="form.name"
              type="text"
              class="form-control"
              :class="{ 'is-invalid': errors.name }"
              required
            />
            <div v-if="errors.name" class="invalid-feedback">{{ errors.name }}</div>
          </div>

          <div class="mb-3">
            <label class="form-label" for="email">Email</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              class="form-control"
              :class="{ 'is-invalid': errors.email }"
              required
            />
            <div v-if="errors.email" class="invalid-feedback">{{ errors.email }}</div>
          </div>

          <div class="mb-3">
            <label class="form-label" for="phone">Phone number</label>
            <input
              id="phone"
              v-model="form.phone_number"
              type="tel"
              class="form-control"
              :class="{ 'is-invalid': errors.phone_number }"
            />
            <div v-if="errors.phone_number" class="invalid-feedback">
              {{ errors.phone_number }}
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label" for="brand">Brand name</label>
            <input
              id="brand"
              v-model="form.brand_name"
              type="text"
              class="form-control"
              :class="{ 'is-invalid': errors.brand_name }"
              required
            />
            <div v-if="errors.brand_name" class="invalid-feedback">
              {{ errors.brand_name }}
            </div>
          </div>

          <div class="mb-4">
            <label class="form-label" for="business">About your business</label>
            <textarea
              id="business"
              v-model="form.business"
              class="form-control"
              :class="{ 'is-invalid': errors.business }"
              rows="4"
              minlength="10"
              required
            />
            <div v-if="errors.business" class="invalid-feedback">{{ errors.business }}</div>
            <div class="form-text">At least ten characters.</div>
          </div>

          <button class="btn btn-primary w-100" type="submit" :disabled="submitting">
            {{ submitting ? 'Submitting…' : 'Submit application' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
