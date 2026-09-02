<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { authApi } from '@/api'
import { useUiStore } from '@/stores/ui'
import { errorMessage, fieldErrors } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const ui = useUiStore()

const form = reactive({ password: '', confirm_password: '' })
const errors = ref({})
const submitting = ref(false)

async function submit() {
  errors.value = {}
  submitting.value = true
  try {
    await authApi.resetPassword({
      // Django's reset link carries both a base64 user id and the token.
      uid: route.params.uid,
      token: route.params.token,
      ...form
    })
    ui.success('Your password has been reset. Please sign in.')
    router.push({ name: 'login' })
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error, 'That reset link is invalid or has expired.'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="container py-5" style="max-width: 420px">
    <h1 class="h4 page-title mb-4">Choose a new password</h1>

    <form class="data-card" @submit.prevent="submit">
      <div class="mb-3">
        <label class="form-label" for="password">New password</label>
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
        <label class="form-label" for="confirm">Confirm new password</label>
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
        {{ submitting ? 'Saving…' : 'Reset password' }}
      </button>
    </form>
  </div>
</template>
