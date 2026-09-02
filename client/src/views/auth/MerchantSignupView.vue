<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { errorMessage, fieldErrors } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const ui = useUiStore()

const form = reactive({
  first_name: '',
  last_name: '',
  password: '',
  confirm_password: ''
})
const errors = ref({})
const submitting = ref(false)

async function submit() {
  errors.value = {}
  submitting.value = true
  try {
    // The server returns a token pair, so accepting the invitation signs the
    // new seller straight in rather than bouncing them to the login form.
    await auth.completeMerchantSignup({ token: route.params.token, ...form })
    ui.success('Your seller account is ready.')
    router.push({ name: 'dashboard' })
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error, 'That invitation link is invalid or has expired.'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="container py-5" style="max-width: 460px">
    <h1 class="h4 page-title mb-2">Set up your seller account</h1>
    <p class="text-muted mb-4">
      Your application has been approved. Choose a password to finish setting up
      your account.
    </p>

    <form class="data-card" @submit.prevent="submit">
      <div class="row g-3 mb-3">
        <div class="col-6">
          <label class="form-label" for="first-name">First name</label>
          <input id="first-name" v-model="form.first_name" type="text" class="form-control" />
        </div>
        <div class="col-6">
          <label class="form-label" for="last-name">Last name</label>
          <input id="last-name" v-model="form.last_name" type="text" class="form-control" />
        </div>
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
      </div>

      <div class="mb-4">
        <label class="form-label" for="confirm">Confirm password</label>
        <input
          id="confirm"
          v-model="form.confirm_password"
          type="password"
          class="form-control"
          :class="{ 'is-invalid': errors.confirm_password }"
          autocomplete="new-password"
          required
        />
        <div v-if="errors.confirm_password" class="invalid-feedback">
          {{ errors.confirm_password }}
        </div>
      </div>

      <button class="btn btn-primary w-100" type="submit" :disabled="submitting">
        {{ submitting ? 'Creating account…' : 'Create seller account' }}
      </button>
    </form>
  </div>
</template>
