<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { errorMessage, fieldErrors } from '@/utils/format'

const auth = useAuthStore()
const ui = useUiStore()
const router = useRouter()

const form = reactive({
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  is_subscribed: false
})
const errors = ref({})
const submitting = ref(false)

async function submit() {
  errors.value = {}
  submitting.value = true
  try {
    const user = await auth.register({ ...form })
    ui.success(`Welcome to the RMIT Store, ${user.first_name || user.email}.`)
    router.push({ name: 'dashboard' })
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error, 'We could not create your account.'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="container py-5" style="max-width: 460px">
    <h1 class="h4 page-title mb-4">Create an account</h1>

    <form class="data-card" @submit.prevent="submit">
      <div class="row g-3 mb-3">
        <div class="col-6">
          <label class="form-label" for="first-name">First name</label>
          <input
            id="first-name"
            v-model="form.first_name"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': errors.first_name }"
            autocomplete="given-name"
            required
          />
          <div v-if="errors.first_name" class="invalid-feedback">
            {{ errors.first_name }}
          </div>
        </div>
        <div class="col-6">
          <label class="form-label" for="last-name">Last name</label>
          <input
            id="last-name"
            v-model="form.last_name"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': errors.last_name }"
            autocomplete="family-name"
            required
          />
          <div v-if="errors.last_name" class="invalid-feedback">{{ errors.last_name }}</div>
        </div>
      </div>

      <div class="mb-3">
        <label class="form-label" for="email">Email</label>
        <input
          id="email"
          v-model="form.email"
          type="email"
          class="form-control"
          :class="{ 'is-invalid': errors.email }"
          autocomplete="email"
          required
        />
        <div v-if="errors.email" class="invalid-feedback">{{ errors.email }}</div>
      </div>

      <div class="mb-3">
        <label class="form-label" for="password">Password</label>
        <input
          id="password"
          v-model="form.password"
          type="password"
          class="form-control"
          :class="{ 'is-invalid': errors.password }"
          autocomplete="new-password"
          minlength="8"
          required
        />
        <div v-if="errors.password" class="invalid-feedback">{{ errors.password }}</div>
        <div class="form-text">At least eight characters, and not all numbers.</div>
      </div>

      <div class="form-check mb-4">
        <input
          id="subscribe"
          v-model="form.is_subscribed"
          class="form-check-input"
          type="checkbox"
        />
        <label class="form-check-label" for="subscribe">
          Sign me up for the newsletter
        </label>
      </div>

      <button class="btn btn-primary w-100 mb-3" type="submit" :disabled="submitting">
        {{ submitting ? 'Creating account…' : 'Create account' }}
      </button>

      <p class="small text-center mb-0">
        Already have an account? <RouterLink to="/login">Sign in</RouterLink>
      </p>
    </form>
  </div>
</template>
